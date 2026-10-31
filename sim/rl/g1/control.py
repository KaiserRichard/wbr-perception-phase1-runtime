"""Fixed 5 ms DARE, with a causal, event-split known-delay predictor."""
from functools import lru_cache
import numpy as np
from scipy.linalg import expm
from sim.augmented import AugmentedRuntime, RuntimeConfig
from sim.augmented_lqr import synthesize_augmented
from sim.lqr import synthesize
from sim.planar import Plant
from .protocol import model_config


@lru_cache(None)
def design():
    cfg = model_config()
    _, nominal = synthesize(Plant(cfg))
    runtime_cfg = RuntimeConfig(delay_s=.005)
    gain, record = synthesize_augmented(cfg, runtime_cfg, np.array(nominal['K_used']))
    Ac, Bc = np.array(nominal['A_continuous']), np.array(nominal['B_continuous'])
    # Continuous nominal mechanics + two nominal causal actuator-filter states.
    F = np.zeros((8, 8)); F[:6, :6] = Ac; F[:6, 6:] = Bc
    F[6:, 6:] = -np.eye(2)/.005
    G = np.zeros((8, 2)); G[6:] = np.eye(2)/.005
    # Express the fixed augmented 5 ms design as a gain on predicted [x,tau].
    K = gain[:, :8] @ np.linalg.inv(expm(F*.005))
    record.update(predictor_gain=K.tolist(), predictor_F=F.tolist(), predictor_G=G.tolist(),
                  predictor='nominal linear mechanics/filter; timestamped known-delay events; no push oracle')
    return K, F, G, record


class Predictor:
    def __init__(self, delay):
        self.delay = delay
        self.K, self.F, self.G, _ = design()
        self.cache = {}

    def advance(self, z, u, dt):
        key = round(dt, 12)
        if key not in self.cache:
            M = np.zeros((10, 10)); M[:8, :8] = self.F; M[:8, 8:] = self.G
            E = expm(M*dt)
            self.cache[key] = E[:8, :8], E[:8, 8:]
        A, B = self.cache[key]
        return A@z+B@u

    def predict(self, runtime):
        obs = runtime.observation()
        z = np.r_[obs.measurement, obs.torque_estimate]
        now, end = runtime.time, runtime.time+self.delay
        # Only issued commands with known arrival timestamps; no future requests.
        events = sorted(runtime.command_history(), key=lambda c: c.arrives_s)
        held = runtime._delayed.copy()  # Causal command hold, never physical truth/torque.
        for c in events:
            if c.arrives_s <= now+1e-12:
                held = c.value
        cursor = now
        for c in events:
            if now+1e-12 < c.arrives_s < end-1e-12:
                z = self.advance(z, held, c.arrives_s-cursor)
                cursor, held = c.arrives_s, c.value
        return self.advance(z, held, end-cursor) if end-cursor > 1e-12 else z

    def command(self, runtime, ref, delta):
        z = self.predict(runtime)
        desired = np.array([ref[0], 0., 0., ref[1]+delta, 0., 0., 0., 0.])
        return -self.K@(z-desired)
