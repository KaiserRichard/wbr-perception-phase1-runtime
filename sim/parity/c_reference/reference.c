#include "reference.h"
#include "VMC_calc.h"
#include "gain_coefficients.h"
#include <math.h>

float wbr_gain(const float *coefficients4, float length)
{
    float c[4];
    if (!coefficients4 || !isfinite(length)) return NAN;
    for (int i = 0; i < 4; ++i) {
        if (!isfinite(coefficients4[i])) return NAN;
        c[i] = coefficients4[i];
    }
    return LQR_K_calc(c, length);
}

void wbr_schedule(float length, float *out12)
{
    if (!out12) return;
    for (int i = 0; i < 12; ++i)
        out12[i] = wbr_gain(Poly_Coefficient[i], length);
}

int wbr_vmc(int side, float phi1, float phi4, float pitch, float pitch_rate,
            float dt, float axial_force, float hip_torque, float *out12)
{
    const float inputs[] = {phi1, phi4, pitch, pitch_rate, dt, axial_force, hip_torque};
    if (!out12) return 1;
    for (int i = 0; i < 12; ++i) out12[i] = NAN;
    if ((side != 0 && side != 1) || dt <= 0.0f) return 1;
    for (unsigned i = 0; i < sizeof(inputs)/sizeof(inputs[0]); ++i)
        if (!isfinite(inputs[i])) return 1;

    vmc_leg_t v = {0};
    INS_t ins = {0};
    VMC_init(&v);
    v.phi1 = phi1; v.phi4 = phi4;
    ins.Pitch = pitch; ins.Gyro[0] = pitch_rate;
    /* Guard the source square root and degenerate circle intersection first. */
    float dx = v.l5 + v.l4*cosf(phi4) - v.l1*cosf(phi1);
    float dy = v.l4*sinf(phi4) - v.l1*sinf(phi1);
    float bd = hypotf(dx, dy);
    float a = 2.0f*v.l2*dx, b = 2.0f*v.l2*dy;
    float c = v.l2*v.l2 + bd*bd - v.l3*v.l3;
    float disc = a*a + b*b - c*c;
    if (!isfinite(disc) || disc <= 0.0f || bd <= 1e-6f) return 2;
    void (*kinematics)(vmc_leg_t *, INS_t *, float) =
        side == 0 ? VMC_calc_1_right : VMC_calc_1_left;
    kinematics(&v, &ins, dt);
    if (!isfinite(v.L0) || !isfinite(v.phi0) || !isfinite(v.phi2)
        || !isfinite(v.phi3) || v.L0 <= 1e-7f
        || fabsf(sinf(v.phi3-v.phi2)) <= 1e-6f) return 2;
    /* Stateless fixed-pose convention: initialize derivative history and run
       identical kinematics again. No joint velocities are implied. */
    v.last_phi0 = v.phi0;
    v.last_L0 = v.L0;
    v.last_d_L0 = 0.0f;
    v.last_d_theta = v.d_theta;
    kinematics(&v, &ins, dt);
    v.F0 = axial_force; v.Tp = hip_torque;
    VMC_calc_2(&v);
    float values[12] = {v.L0, v.phi0, v.theta, v.d_theta,
                       v.j11, v.j12, v.j21, v.j22,
                       v.torque_set[0], v.torque_set[1], v.l1, v.l5};
    for (int i = 0; i < 12; ++i) if (!isfinite(values[i])) return 3;
    for (int i = 0; i < 12; ++i) out12[i] = values[i];
    return 0;
}
