#ifndef WBR_HOST_INS_TASK_H
#define WBR_HOST_INS_TASK_H
/* Only named fields read by VMC_calc.c; never binary-compatible with firmware. */
typedef struct { float Pitch; float Gyro[3]; } INS_t;
#endif
