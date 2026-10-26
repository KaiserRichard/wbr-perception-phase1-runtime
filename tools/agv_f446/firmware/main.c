#include "f446.h"
#include "can.h"
#include "agv_logic.h"
#include <math.h>
#include <stdbool.h>
#include <stdlib.h>
#include <time.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <rcutils/allocator.h>
#include <rmw_microros/rmw_microros.h>
#include <rmw_microros/time_sync.h>
#include <geometry_msgs/msg/twist.h>
#include <std_msgs/msg/bool.h>
#include <std_msgs/msg/u_int8.h>
#include <sensor_msgs/msg/joint_state.h>
#include <sensor_msgs/msg/imu.h>
#include <std_msgs/msg/float64_multi_array.h>
#include <rosidl_runtime_c/string_functions.h>
#include <uxr/client/transport.h>
#define BAUD 115200u
#define RX_SIZE 512u
#define TIMEOUT_US 500000ull
static volatile uint8_t rx[RX_SIZE]; static volatile uint16_t rh,rt; static uint32_t core_hz=84000000u,pclk1=42000000u;
/* Kinematics, wheel signs, 20 rad/s common scaling, and 500 ms watchdog match Microros_H723_USB/docs/topics.md:54-64 and User/Config/robot_config.h:17-37. */
static volatile float cmd_l,cmd_r; static volatile uint64_t cmd_us; static volatile bool command_seen,enabled,estop; static bool hw_enabled;
static agv_feedback_t fb_l,fb_r; static volatile uint64_t fb_l_us,fb_r_us;
enum { ADV_NONE=0, ADV_JUMP=1, ADV_STOP=2, ADV_UNCERTAIN=3 };
static double advisory_data[8];
static uint64_t advisory_us;
static uint32_t advisory_sequence;
static uint8_t advisory_code=ADV_UNCERTAIN;
static bool advisory_seen,imu_present;
static int16_t imu_raw[6];
static float imu_accel[3],imu_gyro[3];
static bool imu_sample_valid;
static uint64_t micros(void);
static bool i2c_wait(uint32_t mask){uint64_t start=micros();while(!(I2C1_SR1&mask)){if(micros()-start>2000u)return false;}return true;}
static void i2c_stop(void){I2C1_CR1|=1u<<9;}
static bool i2c_start(uint8_t address){I2C1_CR1|=1u<<8;if(!i2c_wait(1u))return false;I2C1_DR=address;if(!i2c_wait(1u<<1))return false;(void)I2C1_SR1;(void)I2C1_SR2;return true;}
static void i2c_init(void){RCC_APB1ENR|=1u<<21;GPIOB_MODER=(GPIOB_MODER&~((3u<<12)|(3u<<14)))|(2u<<12)|(2u<<14);GPIOB_OTYPER|=(1u<<6)|(1u<<7);GPIOB_OSPEEDR|=(3u<<12)|(3u<<14);GPIOB_PUPDR=(GPIOB_PUPDR&~((3u<<12)|(3u<<14)))|(1u<<12)|(1u<<14);GPIOB_AFRL=(GPIOB_AFRL&~((15u<<24)|(15u<<28)))|(4u<<24)|(4u<<28);I2C1_CR1=1u<<15;I2C1_CR1=0;I2C1_CR2=pclk1/1000000u;I2C1_CCR=(1u<<15)|(pclk1/(3u*400000u));I2C1_TRISE=(pclk1/1000000u)+1u;I2C1_CR1=1u;}
static bool i2c_write_reg(uint8_t reg,uint8_t value){if(!i2c_start(0xD0u))goto fail;if(!i2c_wait(1u<<7))goto fail;I2C1_DR=reg;if(!i2c_wait(1u<<7))goto fail;I2C1_DR=value;if(!i2c_wait(1u<<2))goto fail;i2c_stop();return true;fail:i2c_stop();return false;}
static bool i2c_read_regs(uint8_t reg,uint8_t *data,uint8_t n){if(!n)return false;if(!i2c_start(0xD0u))goto fail;if(!i2c_wait(1u<<7))goto fail;I2C1_DR=reg;if(!i2c_wait(1u<<2))goto fail;I2C1_CR1|=1u<<8;if(!i2c_wait(1u))goto fail;I2C1_CR1|=1u<<10;I2C1_DR=0xD1u;if(!i2c_wait(1u<<1))goto fail;if(n==1u)I2C1_CR1&=~(1u<<10);(void)I2C1_SR1;(void)I2C1_SR2;for(uint8_t i=0;i<n;i++){if(i==n-1u){I2C1_CR1&=~(1u<<10);i2c_stop();}if(!i2c_wait(1u<<6))goto fail;data[i]=(uint8_t)I2C1_DR;}return true;fail:i2c_stop();return false;}
static bool imu_init(void){uint8_t who=0;if(!i2c_read_regs(0x75u,&who,1u)||who!=0x68u)return false;if(!i2c_write_reg(0x6Bu,0x00u)||!i2c_write_reg(0x1Bu,0x08u)||!i2c_write_reg(0x1Cu,0x08u)||!i2c_write_reg(0x1Au,0x03u))return false;return true;}
static bool imu_read(void){uint8_t b[14];if(!i2c_read_regs(0x3Bu,b,14u))return false;for(unsigned i=0;i<3u;i++)imu_raw[i]=(int16_t)((uint16_t)b[2u*i]<<8|b[2u*i+1u]);for(unsigned i=0;i<3u;i++)imu_raw[i+3u]=(int16_t)((uint16_t)b[8u+2u*i]<<8|b[9u+2u*i]);agv_mpu6050_scale(imu_raw,imu_accel,imu_gyro);imu_sample_valid=true;return true;}
static void *aa(size_t n,void*s){(void)s;return malloc(n);} static void ad(void*p,void*s){(void)s;free(p);} static void *ar(void*p,size_t n,void*s){(void)s;return realloc(p,n);} static void *az(size_t n,size_t z,void*s){(void)s;return calloc(n,z);}
static uint64_t micros(void){static uint32_t last;static uint64_t hi;uint32_t n=TIM2_CNT;if(n<last)hi+=1ull<<32;last=n;return hi|n;}
int clock_gettime(clockid_t c,struct timespec*t){(void)c;uint64_t u=micros();t->tv_sec=u/1000000;t->tv_nsec=(long)(u%1000000)*1000;return 0;}
static void clock_init(void){uint32_t i;RCC_CR|=1u<<18|1u<<16;for(i=0;i<200000&&!(RCC_CR&(1u<<17));i++){}bool h=(RCC_CR&(1u<<17))!=0;if(!h){RCC_CR&=~((1u<<16)|(1u<<18));}uint32_t m=h?8u:16u,src=h?1u:0u;RCC_PLLCFGR=m|(336u<<6)|(1u<<16)|(src<<22)|(7u<<24)|(2u<<28);RCC_CR|=1u<<24;for(i=0;i<2000000&&!(RCC_CR&(1u<<25));i++){}if(!(RCC_CR&(1u<<25))){core_hz=pclk1=16000000u;return;}FLASH_ACR=2u|(1u<<8)|(1u<<9)|(1u<<10);RCC_CFGR=(4u<<10)|2u;for(i=0;i<2000000&&(RCC_CFGR&(3u<<2))!=(2u<<2);i++){} }
__attribute__((unused)) static void af7(unsigned p){GPIOA_MODER=(GPIOA_MODER&~(3u<<(2*p)))|(2u<<(2*p));GPIOA_AFRL=(GPIOA_AFRL&~(15u<<(4*p)))|(7u<<(4*p));GPIOA_OSPEEDR|=2u<<(2*p);}
static void gpioout(unsigned p){GPIOA_MODER=(GPIOA_MODER&~(3u<<(2*p)))|(1u<<(2*p));}
static void set_leds(bool green,bool yellow,bool red,bool blue,bool ld2){GPIOB_BSRR=(green?1u<<5:1u<<21)|(yellow?1u<<4:1u<<20)|(red?1u<<10:1u<<26);GPIOC_BSRR=blue?1u<<7:1u<<23;GPIOA_BSRR=ld2?1u<<5:1u<<21;}
static void peripherals(void){RCC_AHB1ENR|=7u; RCC_APB1ENR|=1u;
#ifdef UROS_USART1
RCC_APB2ENR|=1u<<4;for(unsigned p=9;p<=10;p++){GPIOA_MODER=(GPIOA_MODER&~(3u<<(2*p)))|(2u<<(2*p));GPIOA_AFRH=(GPIOA_AFRH&~(15u<<(4*(p-8))))|(7u<<(4*(p-8)));}RCC_APB1ENR|=1u;
#else
RCC_APB1ENR|=1u<<17;af7(2);af7(3);
#endif
TIM2_PSC=core_hz/1000000u-1u;TIM2_ARR=0xffffffffu;TIM2_EGR=1;TIM2_CR1=1;
#ifdef UROS_USART1
USART_BRR=(pclk1*2u+BAUD/2u)/BAUD;
#else
USART_BRR=(pclk1+BAUD/2u)/BAUD;
#endif
USART_CR1=(1u<<13)|(1u<<3)|(1u<<2)|(1u<<5);
#ifdef UROS_USART1
NVIC_ISER1=1u<<(37u-32u);
#else
NVIC_ISER1=1u<<(38u-32u);
#endif
GPIOA_BSRR=1u<<(5u+16u);gpioout(5);GPIOC_MODER&=~(3u<<26);GPIOC_PUPDR=(GPIOC_PUPDR&~(3u<<26))|(2u<<26);
GPIOB_BSRR=(1u<<21)|(1u<<20)|(1u<<26);GPIOC_BSRR=1u<<23;GPIOB_OTYPER&=~((1u<<5)|(1u<<4)|(1u<<10));
GPIOB_MODER=(GPIOB_MODER&~((3u<<10)|(3u<<8)|(3u<<20)))|(1u<<10)|(1u<<8)|(1u<<20);GPIOC_MODER=(GPIOC_MODER&~(3u<<14))|(1u<<14);can_init();}
void USART2_IRQHandler(void){uint32_t sr=USART_SR;if(sr&((1u<<5)|(1u<<3)|(1u<<1)|(1u<<0))){uint8_t b=(uint8_t)USART_DR;if(sr&(1u<<5)){uint16_t n=(rh+1u)&(RX_SIZE-1u);if(n!=rt){rx[rh]=b;rh=n;}}}}
static bool to(struct uxrCustomTransport*t){(void)t;return true;}static bool tc(struct uxrCustomTransport*t){(void)t;return true;}
static size_t tw(struct uxrCustomTransport*t,const uint8_t*b,size_t n,uint8_t*e){(void)t;for(size_t i=0;i<n;i++){while(!(USART_SR&(1u<<7))){}USART_DR=b[i];}while(!(USART_SR&(1u<<6))){}if(e)*e=0;return n;}
static size_t tr(struct uxrCustomTransport*t,uint8_t*b,size_t n,int ms,uint8_t*e){(void)t;uint64_t start=micros(),limit=ms>0?(uint64_t)ms*1000u:0;size_t k=0;while(k<n&&micros()-start<limit){if(rt!=rh){b[k++]=rx[rt];rt=(rt+1u)&(RX_SIZE-1u);}}if(e)*e=0;return k;}
static void twist_cb(const void*m){const geometry_msgs__msg__Twist*x=m;float vx=(float)x->linear.x,wz=(float)x->angular.z;if(!isfinite(vx)||!isfinite(wz))return;float l,r;agv_kinematics(vx,wz,&l,&r);cmd_l=l;cmd_r=r;cmd_us=micros();command_seen=true;}
static void enable_cb(const void*m){const std_msgs__msg__Bool*x=m;if(estop)return;enabled=x->data;}
static void advisory_cb(const void*m){const std_msgs__msg__Float64MultiArray*x=m;if(!agv_advisory_valid(x->data.data,x->data.size))return;advisory_code=(uint8_t)x->data.data[0];advisory_sequence=(uint32_t)x->data.data[6];advisory_us=micros();advisory_seen=true;}
static void spin_wait_agent(void){while(rmw_uros_ping_agent(100,1)!=RMW_RET_OK){if(!(GPIOC_IDR&(1u<<13)))estop=true;/* Nucleo-64 B1 is active-low (pull-up, button to GND) */bool blink=((micros()/250000u)&1u)!=0;set_leds(false,false,blink,false,false);}}
static int setup(rcl_allocator_t*a,rclc_support_t*s,rcl_node_t*n,rcl_subscription_t*sv,rcl_subscription_t*se,rcl_subscription_t*sa,rcl_publisher_t*pf,rcl_publisher_t*ps,rcl_publisher_t*pi,rclc_executor_t*ex,geometry_msgs__msg__Twist*tv,std_msgs__msg__Bool*ev,std_msgs__msg__Float64MultiArray*av,sensor_msgs__msg__JointState*j,sensor_msgs__msg__Imu*im,std_msgs__msg__UInt8*st){if(rclc_support_init(s,0,NULL,a)!=RCL_RET_OK)return 0;if(rclc_node_init_default(n,"stm32_agv_node","",s)!=RCL_RET_OK)return 0;if(rclc_subscription_init_best_effort(sv,n,ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs,msg,Twist),"/cmd_vel")!=RCL_RET_OK)return 0;if(rclc_subscription_init_default(se,n,ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs,msg,Bool),"/motor_enable")!=RCL_RET_OK)return 0;if(rclc_subscription_init_best_effort(sa,n,ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs,msg,Float64MultiArray),"/terrain_advisory")!=RCL_RET_OK)return 0;if(rclc_publisher_init_best_effort(pf,n,ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs,msg,JointState),"/motor_fb")!=RCL_RET_OK)return 0;if(rclc_publisher_init_default(ps,n,ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs,msg,UInt8),"/motor_status")!=RCL_RET_OK)return 0;if(rclc_publisher_init_best_effort(pi,n,ROSIDL_GET_MSG_TYPE_SUPPORT(sensor_msgs,msg,Imu),"/imu/data")!=RCL_RET_OK)return 0;if(rclc_executor_init(ex,&s->context,3,a)!=RCL_RET_OK)return 0;if(!sensor_msgs__msg__JointState__init(j)||!sensor_msgs__msg__Imu__init(im)||!std_msgs__msg__Float64MultiArray__init(av))return 0;av->data.data=advisory_data;av->data.size=0;av->data.capacity=8;if(!rosidl_runtime_c__String__Sequence__init(&j->name,2))return 0;rosidl_runtime_c__String__assign(&j->name.data[0],"left_wheel");rosidl_runtime_c__String__assign(&j->name.data[1],"right_wheel");if(!rosidl_runtime_c__String__assign(&j->header.frame_id,"base_link")||!rosidl_runtime_c__String__assign(&im->header.frame_id,"imu_link"))return 0;j->position.data=calloc(2,sizeof(double));j->velocity.data=calloc(2,sizeof(double));j->effort.data=calloc(2,sizeof(double));if(!j->position.data||!j->velocity.data||!j->effort.data)return 0;j->position.size=j->position.capacity=2;j->velocity.size=j->velocity.capacity=2;j->effort.size=j->effort.capacity=2;im->orientation_covariance[0]=-1.0;st->data=0;if(rclc_executor_add_subscription(ex,sv,tv,twist_cb,ON_NEW_DATA)!=RCL_RET_OK||rclc_executor_add_subscription(ex,se,ev,enable_cb,ON_NEW_DATA)!=RCL_RET_OK)return 0;return rclc_executor_add_subscription(ex,sa,av,advisory_cb,ON_NEW_DATA)==RCL_RET_OK;}
static void write_param(unsigned bus,uint16_t index,const void*p,uint8_t n){uint8_t d[8];agv_rs_param(d,index,p,n);(void)can_send(bus,agv_rs_id(18,AGV_CAN_MASTER_ID,AGV_MOTOR_ID),d);}
static void motor_setup(void){uint8_t mode=2,z[8]={0};(void)can_send(0,agv_rs_id(4,AGV_CAN_MASTER_ID,AGV_MOTOR_ID),z);(void)can_send(1,agv_rs_id(4,AGV_CAN_MASTER_ID,AGV_MOTOR_ID),z);write_param(0,AGV_RS_RUN_MODE,&mode,1);write_param(1,AGV_RS_RUN_MODE,&mode,1);float zero=0;write_param(0,AGV_RS_SPD_REF,&zero,4);write_param(1,AGV_RS_SPD_REF,&zero,4);hw_enabled=false;}
static void set_speed(unsigned bus,float v){write_param(bus,AGV_RS_SPD_REF,&v,4);}
static void enable_hw(void){uint8_t z[8]={0};(void)can_send(0,agv_rs_id(3,AGV_CAN_MASTER_ID,AGV_MOTOR_ID),z);(void)can_send(1,agv_rs_id(3,AGV_CAN_MASTER_ID,AGV_MOTOR_ID),z);hw_enabled=true;}
static void disable_hw(void){uint8_t z[8]={0};(void)can_send(0,agv_rs_id(4,AGV_CAN_MASTER_ID,AGV_MOTOR_ID),z);(void)can_send(1,agv_rs_id(4,AGV_CAN_MASTER_ID,AGV_MOTOR_ID),z);hw_enabled=false;}
/* Feedback position unwrapping follows robstride_drv.c:216-275 (wrap folding, rail velocity integration, congruent re-anchor). */
static void track_feedback(agv_feedback_t *dst,const agv_feedback_t *src,volatile uint64_t *stamp,float *last_raw,bool *valid){uint64_t now=micros();float p=src->position;bool rail=src->position_code<=64u||src->position_code>=(0xffffu-64u);if(!*valid){*dst=*src;*last_raw=p;*stamp=now;*valid=true;return;}if(rail){float dt=(float)(now-*stamp)*1.0e-6f;if(dt>0.05f)dt=0.05f;if(src->velocity>0.02f||src->velocity< -0.02f)dst->position+=src->velocity*dt;}else{float turns=(dst->position-p)/25.14f;int32_t n=(int32_t)(turns+(turns>=0.0f?0.5f:-0.5f));dst->position=p+(float)n*25.14f;}dst->velocity=src->velocity;dst->torque=src->torque;dst->mode=src->mode;dst->fault=src->fault;dst->motor_id=src->motor_id;dst->master_id=src->master_id;dst->position_code=src->position_code;*last_raw=p;*stamp=now;}
static void consume_can(void){static float raw_l,raw_r;static bool valid_l,valid_r;uint32_t id;uint8_t d[8],n;while(can_receive(0,&id,d,&n)){agv_feedback_t f;if(agv_rs_parse(&f,id,d,n)==0&&f.motor_id==AGV_MOTOR_ID)track_feedback(&fb_l,&f,&fb_l_us,&raw_l,&valid_l);}while(can_receive(1,&id,d,&n)){agv_feedback_t f;if(agv_rs_parse(&f,id,d,n)==0&&f.motor_id==AGV_MOTOR_ID)track_feedback(&fb_r,&f,&fb_r_us,&raw_r,&valid_r);}}
#ifdef CAN_LOOPBACK_TEST
/* Recovered left shaft position remains the midpoint; speed/torque are plausible constants. */
static void loopback_fake(void){static float fake_velocity;uint32_t id;uint8_t d[8],n;while(can_receive(1,&id,d,&n)){uint8_t type=(id>>24)&31u;if(type==4u){fake_velocity=0.0f;}else if(type==18u&&d[0]==(uint8_t)AGV_RS_SPD_REF&&d[1]==(uint8_t)(AGV_RS_SPD_REF>>8)){union{uint32_t u;float f;}v;v.u=(uint32_t)d[4]|((uint32_t)d[5]<<8)|((uint32_t)d[6]<<16)|((uint32_t)d[7]<<24);fake_velocity=v.f;}if(type==3u||type==4u||type==18u){uint16_t vr=agv_float_to_u16(fake_velocity,AGV_RS_FEEDBACK_V_MIN,AGV_RS_FEEDBACK_V_MAX);uint8_t f[8]={0x80,0,(uint8_t)(vr>>8),(uint8_t)vr,0x80,0,0x09,0xC4};(void)can_send(1,((2u<<24)|(AGV_MOTOR_ID<<8)|AGV_CAN_MASTER_ID),f);}}}
#endif
static uint8_t status(uint64_t now){uint8_t s=0;if(now-fb_l_us<250000u)s|=AGV_STATUS_LEFT_FRESH;if(now-fb_r_us<250000u)s|=AGV_STATUS_RIGHT_FRESH;if(can_bus_off(0))s|=AGV_STATUS_CAN1_BUSOFF;if(can_bus_off(1))s|=AGV_STATUS_CAN2_BUSOFF;if(enabled&&!estop)s|=AGV_STATUS_ENABLED;if(!command_seen||now-cmd_us>TIMEOUT_US)s|=AGV_STATUS_TIMEOUT;return s;}
int main(void){clock_init();peripherals();rcutils_allocator_t ca=rcutils_get_zero_initialized_allocator();ca.allocate=aa;ca.deallocate=ad;ca.reallocate=ar;ca.zero_allocate=az;if(!rcutils_set_default_allocator(&ca))for(;;){}if(rmw_uros_set_custom_transport(true,NULL,to,tc,tw,tr)!=RMW_RET_OK)for(;;){}
 i2c_init();imu_present=imu_init();for(;;){spin_wait_agent();rcl_allocator_t a=rcl_get_default_allocator();rclc_support_t sup={0};rcl_node_t node=rcl_get_zero_initialized_node();rcl_subscription_t subv=rcl_get_zero_initialized_subscription(),sube=rcl_get_zero_initialized_subscription(),suba=rcl_get_zero_initialized_subscription();rcl_publisher_t pubf=rcl_get_zero_initialized_publisher(),pubs=rcl_get_zero_initialized_publisher(),pubi=rcl_get_zero_initialized_publisher();rclc_executor_t ex=rclc_executor_get_zero_initialized_executor();geometry_msgs__msg__Twist tv={0};std_msgs__msg__Bool ev={0};std_msgs__msg__Float64MultiArray av={0};sensor_msgs__msg__JointState j={0};sensor_msgs__msg__Imu im={0};std_msgs__msg__UInt8 st={0};if(!setup(&a,&sup,&node,&subv,&sube,&suba,&pubf,&pubs,&pubi,&ex,&tv,&ev,&av,&j,&im,&st)){for(;;){bool blink=((micros()/250000u)&1u)!=0;set_leds(false,false,blink,false,false);}}GPIOA_BSRR=1u<<5;{rmw_ret_t sync_rc=rmw_uros_sync_session(1000);(void)sync_rc;}enabled=false;command_seen=false;motor_setup();uint64_t now=micros(),nextfb=now,nextst=now,nextcmd=now,nextimu=now,nextimupub=now,lastping=now;bool connected=true;while(connected){(void)rclc_executor_spin_some(&ex,1000000ull);now=micros();if(!(GPIOC_IDR&(1u<<13)))estop=true;/* Nucleo-64 B1 is active-low (pull-up, button to GND) */if(estop)enabled=false;
#ifdef CAN_LOOPBACK_TEST
loopback_fake();
#endif
consume_can();if(imu_present&&now>=nextimu){if(!imu_read()){imu_present=false;imu_sample_valid=false;}nextimu=now+20000u;}bool want=enabled&&!estop;if(want&&!hw_enabled)enable_hw();else if(!want&&hw_enabled)disable_hw();bool timed=!command_seen||now-cmd_us>TIMEOUT_US;float l=timed?0.0f:cmd_l,r=timed?0.0f:cmd_r;if(now>=nextcmd){if(hw_enabled){set_speed(0,l);set_speed(1,r);}nextcmd=now+10000u;}if(now>=nextfb){int64_t ns=rmw_uros_epoch_nanos();if(ns>0){j.header.stamp.sec=(int32_t)(ns/1000000000ll);j.header.stamp.nanosec=(uint32_t)(ns%1000000000ll);}j.position.data[0]=fb_l.position*AGV_LEFT_SIGN;j.position.data[1]=fb_r.position*AGV_RIGHT_SIGN;j.velocity.data[0]=fb_l.velocity*AGV_LEFT_SIGN;j.velocity.data[1]=fb_r.velocity*AGV_RIGHT_SIGN;j.effort.data[0]=fb_l.torque*AGV_LEFT_SIGN;j.effort.data[1]=fb_r.torque*AGV_RIGHT_SIGN;{rcl_ret_t rc=rcl_publish(&pubf,&j,NULL);(void)rc;}nextfb=now+50000u;}if(now>=nextimupub){if(imu_present&&imu_sample_valid){int64_t ns=rmw_uros_epoch_nanos();if(ns>0){im.header.stamp.sec=(int32_t)(ns/1000000000ll);im.header.stamp.nanosec=(uint32_t)(ns%1000000000ll);}im.linear_acceleration.x=imu_accel[0];im.linear_acceleration.y=imu_accel[1];im.linear_acceleration.z=imu_accel[2];im.angular_velocity.x=imu_gyro[0];im.angular_velocity.y=imu_gyro[1];im.angular_velocity.z=imu_gyro[2];rcl_ret_t rc=rcl_publish(&pubi,&im,NULL);(void)rc;}nextimupub=now+50000u;}if(now>=nextst){st.data=status(now);if(!imu_present)st.data|=AGV_STATUS_IMU_ABSENT;{rcl_ret_t rc=rcl_publish(&pubs,&st,NULL);(void)rc;}nextst=now+200000u;}bool stale=!advisory_seen||now-advisory_us>300000u;bool uncertain=stale||advisory_code==ADV_UNCERTAIN;bool blink_yellow=((now/125000u)&1u)!=0;bool blink_red=stale&&((now/250000u)&1u)!=0;set_leds(!stale&&advisory_code==ADV_NONE,(!stale&&advisory_code==ADV_JUMP)||(uncertain&&blink_yellow),(!stale&&advisory_code==ADV_STOP)||blink_red,uncertain,true);if(now-lastping>1000000u){lastping=now;if(rmw_uros_ping_agent(100,1)!=RMW_RET_OK)connected=false;}}
rcl_ret_t rc;rcl_ret_t (*volatile sink)(void)=0;(void)sink;set_leds(false,false,false,false,false);rc=rclc_executor_fini(&ex);(void)rc;rc=rcl_publisher_fini(&pubi,&node);(void)rc;rc=rcl_publisher_fini(&pubs,&node);(void)rc;rc=rcl_publisher_fini(&pubf,&node);(void)rc;rc=rcl_subscription_fini(&suba,&node);(void)rc;rc=rcl_subscription_fini(&sube,&node);(void)rc;rc=rcl_subscription_fini(&subv,&node);(void)rc;rc=rcl_node_fini(&node);(void)rc;rc=rclc_support_fini(&sup);(void)rc;av.data.data=NULL;sensor_msgs__msg__Imu__fini(&im);std_msgs__msg__Float64MultiArray__fini(&av);sensor_msgs__msg__JointState__fini(&j);}
}
