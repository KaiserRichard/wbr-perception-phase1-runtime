#ifndef AGV_LOGIC_H
#define AGV_LOGIC_H
#include <stdint.h>
#include <math.h>
#define AGV_WHEEL_R 0.060f
#define AGV_WHEEL_BASE 0.345f
#define AGV_LEFT_SIGN (-1.0f)
#define AGV_RIGHT_SIGN (1.0f)
#define AGV_MAX_RAD_S 20.0f
#define AGV_CAN_MASTER_ID 0xFDu
#define AGV_MOTOR_ID 1u
#define AGV_RS_P_MIN (-12.57f)
#define AGV_RS_P_MAX (12.57f)
#define AGV_RS_V_MIN (-20.0f)
#define AGV_RS_V_MAX (20.0f)
#define AGV_RS_T_MIN (-60.0f)
#define AGV_RS_T_MAX (60.0f)
#define AGV_RS_FEEDBACK_V_MIN (-30.0f)
#define AGV_RS_FEEDBACK_V_MAX (30.0f)
#define AGV_RS_RUN_MODE 0x7005u
#define AGV_RS_SPD_REF 0x700Au
#define AGV_STATUS_LEFT_FRESH 0x01u
#define AGV_STATUS_RIGHT_FRESH 0x02u
#define AGV_STATUS_CAN1_BUSOFF 0x04u
#define AGV_STATUS_CAN2_BUSOFF 0x08u
#define AGV_STATUS_ENABLED 0x10u
#define AGV_STATUS_TIMEOUT 0x20u
#define AGV_STATUS_MODE_MIT 0x40u

typedef struct { float position, velocity, torque; uint8_t mode, fault, motor_id, master_id; uint16_t position_code; } agv_feedback_t;
static inline void agv_kinematics(float vx, float wz, float *left, float *right) {
  /* Double intermediates prevent finite float64 ROS inputs near FLT_MAX from
     overflowing before the common saturation scale is applied. */
  double l=((double)vx-0.5*(double)AGV_WHEEL_BASE*(double)wz)/(double)AGV_WHEEL_R;
  double r=((double)vx+0.5*(double)AGV_WHEEL_BASE*(double)wz)/(double)AGV_WHEEL_R;
  double peak=fmax(fabs(l),fabs(r));
  if (peak>AGV_MAX_RAD_S) { double s=(double)AGV_MAX_RAD_S/peak; l*=s; r*=s; }
  *left=(float)(l*AGV_LEFT_SIGN); *right=(float)(r*AGV_RIGHT_SIGN);
}
static inline uint32_t agv_rs_id(uint8_t type,uint16_t data2,uint8_t target) {
  return (((uint32_t)type&31u)<<24)|(((uint32_t)data2&65535u)<<8)|target;
}
static inline uint16_t agv_float_to_u16(float x,float lo,float hi) {
  if (x<lo) x=lo;
  if (x>hi) x=hi;
  return (uint16_t)((x-lo)*65535.0f/(hi-lo));
}
static inline float agv_u16_to_float(uint16_t x,float lo,float hi) { return x*(hi-lo)/65535.0f+lo; }
static inline void agv_rs_param(uint8_t data[8],uint16_t idx,const void *v,uint8_t n) {
  for (int i=0;i<8;i++) data[i]=0;
  data[0]=(uint8_t)idx; data[1]=(uint8_t)(idx>>8);
  const uint8_t *p=(const uint8_t*)v; for(uint8_t i=0;i<n;i++) data[4+i]=p[i];
}
static inline int agv_rs_parse(agv_feedback_t *o,uint32_t id,const uint8_t d[8],uint8_t len) {
  uint8_t type=(id>>24)&31u; if(!o||!d||len!=8u||(type!=2u&&type!=24u)) return -1;
  o->mode=(id>>22)&3u; o->fault=(id>>16)&63u; o->motor_id=(id>>8)&255u; o->master_id=id&255u;
  o->position_code=(uint16_t)(d[0]<<8|d[1]);
  o->position=agv_u16_to_float(o->position_code,AGV_RS_P_MIN,AGV_RS_P_MAX);
  o->velocity=agv_u16_to_float((uint16_t)(d[2]<<8|d[3]),AGV_RS_FEEDBACK_V_MIN,AGV_RS_FEEDBACK_V_MAX);
  o->torque=agv_u16_to_float((uint16_t)(d[4]<<8|d[5]),AGV_RS_T_MIN,AGV_RS_T_MAX);
  return 0;
}
#endif
