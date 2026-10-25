#include <assert.h>
#include <math.h>
#include <stdio.h>
#include "../firmware/agv_logic.h"
static void closef(float a,float b,float e){assert(fabsf(a-b)<e);}
int main(void){
 float l,r; agv_kinematics(0.6f,0,&l,&r); closef(l,-10,1e-5f);closef(r,10,1e-5f);
 agv_kinematics(0,1,&l,&r);closef(l,2.875f,1e-4f);closef(r,2.875f,1e-4f);
 agv_kinematics(3.0f,2.0f,&l,&r);assert(fabsf(l)<=20.0001f&&fabsf(r)<=20.0001f);closef(fabsf(l/r),fabsf((3-.345f)/(3+.345f)),1e-4f);
 agv_kinematics(3.0e38f,3.0e38f,&l,&r);assert(isfinite(l)&&isfinite(r)&&fabsf(l)<=20.0001f&&fabsf(r)<=20.0001f);closef(fabsf(l/r),fabsf((1.0f-0.1725f)/(1.0f+0.1725f)),1e-4f);
 assert(agv_rs_id(18,0xfd,1)==0x1200fd01u);
 uint8_t d[8]; uint32_t bits=0x3f800000u; agv_rs_param(d,AGV_RS_SPD_REF,&bits,4);
 assert(d[0]==0x0a&&d[1]==0x70&&d[2]==0&&d[3]==0&&d[4]==0&&d[5]==0&&d[6]==0x80&&d[7]==0x3f);
 uint8_t fb[8]={0x80,0,0x80,0,0x80,0,0,0}; agv_feedback_t parsed;
 assert(agv_rs_parse(&parsed,((2u<<24)|(AGV_MOTOR_ID<<8)|AGV_CAN_MASTER_ID),fb,8)==0);
 assert(parsed.motor_id==AGV_MOTOR_ID&&parsed.master_id==AGV_CAN_MASTER_ID);
 closef(parsed.position,0,0.001f);closef(parsed.velocity,0,0.001f);closef(parsed.torque,0,0.002f);
 assert(agv_rs_parse(&parsed,agv_rs_id(1,0,AGV_CAN_MASTER_ID),fb,8)<0);
 puts("PASS: kinematics, curvature scaling, extended ID, parameter packing, feedback parse/rejection");
 return 0;
}
