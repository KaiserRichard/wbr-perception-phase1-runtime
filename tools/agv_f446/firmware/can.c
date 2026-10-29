#include "f446.h"
#include "can.h"
#define CAN1 0x40006400u
#define CAN2 0x40006800u
#define CREG(b,o) REG((b)+(o))
#define MCR 0x00u
#define MSR 0x04u
#define TSR 0x08u
#define RF0R 0x0Cu
#define IER 0x14u
#define ESR 0x18u
#define BTR 0x1Cu
#define TI0R 0x180u
#define TDT0R 0x184u
#define TDL0R 0x188u
#define TDH0R 0x18Cu
#define RI0R 0x1B0u
#define RDT0R 0x1B4u
#define RDL0R 0x1B8u
#define RDH0R 0x1BCu
static void gpio_can(unsigned pin){GPIOB_MODER=(GPIOB_MODER&~(3u<<(2*pin)))|(2u<<(2*pin));GPIOB_OSPEEDR|=3u<<(2*pin);GPIOB_PUPDR&=~(3u<<(2*pin));GPIOB_AFRH=(GPIOB_AFRH&~(15u<<(4*(pin-8))))|(9u<<(4*(pin-8)));}
/* Shared filters are offsets from CAN1, not from CAN1 + 0x200 again.
 * Caller holds FINIT while configuring mask-mode, FIFO0, accept-all banks. */
static void filter(unsigned bank){uint32_t f=CAN1;REG(f+0x204u)&=~(1u<<bank);REG(f+0x20cu)|=1u<<bank;REG(f+0x214u)&=~(1u<<bank);REG(f+0x240u+bank*8u)=0;REG(f+0x244u+bank*8u)=0;REG(f+0x21cu)|=1u<<bank;}
static void one_init(uint32_t b){CREG(b,MCR)=1u; while(!(CREG(b,MSR)&1u)){} CREG(b,MCR)=1u|(1u<<6); /* INRQ + ABOM */ CREG(b,BTR)=(1u<<20)|(10u<<16)|2u; CREG(b,MCR)&=~1u; while(CREG(b,MSR)&1u){} }
void can_init(void){RCC_AHB1ENR|=1u<<1;RCC_APB1ENR|=(1u<<25)|(1u<<26);(void)RCC_APB1ENR;gpio_can(8);gpio_can(9);gpio_can(12);gpio_can(13);one_init(CAN1);one_init(CAN2);REG(CAN1+0x200u)=(REG(CAN1+0x200u)&~(0x3fu<<8))|(14u<<8)|1u;filter(0);filter(14);REG(CAN1+0x200u)&=~1u;}
/* IDE=1 selects extended identifiers; RTR stays zero for payload data frames. */
int can_send(unsigned bus,uint32_t id,const uint8_t d[8]){uint32_t b=bus?CAN2:CAN1,tsr=CREG(b,TSR);unsigned m;for(m=0;m<3u;m++)if(tsr&(1u<<(26u+m)))break;if(m==3u)return -1;uint32_t o=m*0x10u;CREG(b,TI0R+o)=((id&0x1fffffffu)<<3)|(1u<<2);CREG(b,TDT0R+o)=8u;CREG(b,TDL0R+o)=d[0]|((uint32_t)d[1]<<8)|((uint32_t)d[2]<<16)|((uint32_t)d[3]<<24);CREG(b,TDH0R+o)=d[4]|((uint32_t)d[5]<<8)|((uint32_t)d[6]<<16)|((uint32_t)d[7]<<24);CREG(b,TI0R+o)|=1u;return 0;}
int can_receive(unsigned bus,uint32_t *id,uint8_t d[8],uint8_t *len){uint32_t b=bus?CAN2:CAN1;if(!(CREG(b,RF0R)&3u))return 0;uint32_t rir=CREG(b,RI0R),dlc=CREG(b,RDT0R);*id=(rir>>3)&0x1fffffffu;*len=dlc&15u;uint32_t l=CREG(b,RDL0R),h=CREG(b,RDH0R);for(unsigned i=0;i<4;i++){d[i]=(uint8_t)(l>>(8*i));d[i+4]=(uint8_t)(h>>(8*i));}CREG(b,RF0R)|=1u<<5;return 1;}
int can_bus_off(unsigned bus){return (CREG(bus?CAN2:CAN1,ESR)&(1u<<2))!=0;}
