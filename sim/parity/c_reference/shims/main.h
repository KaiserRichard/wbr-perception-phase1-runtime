#ifndef WBR_HOST_MAIN_H
#define WBR_HOST_MAIN_H
#include <stdint.h>
#include <math.h>
/* Host libm substitutes: not a CMSIS-DSP accuracy or bit-equivalence claim. */
static inline float arm_sin_f32(float x) { return sinf(x); }
static inline float arm_cos_f32(float x) { return cosf(x); }
#endif
