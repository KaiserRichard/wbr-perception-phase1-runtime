#ifndef AGV_CAN_H
#define AGV_CAN_H
#include <stdint.h>
#include "agv_logic.h"
void can_init(void);
int can_send(unsigned bus,uint32_t id,const uint8_t data[8]);
int can_receive(unsigned bus,uint32_t *id,uint8_t data[8],uint8_t *len);
int can_bus_off(unsigned bus);
#endif
