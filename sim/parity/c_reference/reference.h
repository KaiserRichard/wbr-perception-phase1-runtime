#ifndef WBR_HOST_REFERENCE_H
#define WBR_HOST_REFERENCE_H
float wbr_gain(const float *coefficients4, float length);
void wbr_schedule(float length, float *out12);
/* side=0 right, 1 left. status: 0 OK, 1 invalid input, 2 geometry, 3 output. */
int wbr_vmc(int side, float phi1, float phi4, float pitch, float pitch_rate,
            float dt, float axial_force, float hip_torque, float *out12);
#endif
