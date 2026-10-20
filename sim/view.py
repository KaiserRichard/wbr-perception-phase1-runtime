"""Watch the assumed WBR with the existing delay-aware LQR.

macOS: mjpython -m sim.view
Space: pause, P: 6 N push, R: reset. Close the window to stop this demo only.
This is a separate live simulation, not PPO training or a scored experiment.
"""

import argparse
from dataclasses import replace
from pathlib import Path
import time

import mujoco
import numpy as np

from sim.augmented import AugmentedRuntime, load_experiment
from sim.augmented_lqr import synthesize_augmented
from sim.planar import Plant, TO_JOINT


ROOT = Path(__file__).resolve().parents[1]


class Demo:
    def __init__(self, delay_ms):
        self.base, config, effects = load_experiment(
            ROOT / "sim/configs/assumed_actuator_noise.json")
        effects = replace(effects, delay_s=delay_ms / 1000.)
        self.gain, _ = synthesize_augmented(
            self.base, effects, np.asarray(config["frozen_nominal"]["K"]))
        self.runtime = AugmentedRuntime(self.base, effects)
        # The window gets separate model/data: GUI edits cannot change physics.
        self.visual = Plant(self.base)
        self.data = self.visual.data()
        self.paused = False
        self.reset_requested = False
        self.push_requested = False
        self.reset()

    def reset(self):
        self.observation = self.runtime.reset(seed=1000)
        self.manual_push_end_tick = 0
        self.push = 0.
        self.reset_requested = False
        self.push_requested = False

    def key(self, code):
        if code == 32:
            self.paused = not self.paused
        elif code == ord("R"):
            self.reset_requested = True
        elif code == ord("P"):
            self.push_requested = True

    def step(self):
        tick = round(self.runtime.time / self.runtime.dt)
        if self.push_requested:
            self.manual_push_end_tick = tick + round(.15 / self.runtime.dt)
            self.push_requested = False
        p = self.base["protocol"]
        start = round(p["push_start_s"] / self.runtime.dt)
        end = start + round(p["push_duration_s"] / self.runtime.dt)
        auto_push = start <= tick < end
        self.push = p["push_force_N"] if auto_push or (
            tick < self.manual_push_end_tick) else 0.
        command = -self.gain @ self.observation.vector()
        self.observation = self.runtime.step(command, push_N=self.push).observation
        if not np.all(np.isfinite(self.runtime.truth())) or any(self.runtime.warning_counts):
            raise RuntimeError("Demo physics became invalid; see terminal output")

    def visual_state(self):
        state = self.runtime.truth()
        self.data.qpos[:] = TO_JOINT @ state[:3]
        self.data.qvel[:] = TO_JOINT @ state[3:]
        self.data.time = self.runtime.time
        mujoco.mj_forward(self.visual.model, self.data)
        return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay-ms", type=int, choices=(2, 3, 4, 5), default=5)
    parser.add_argument("--duration", type=float, default=0., help="Close after this many wall seconds; 0 keeps window open")
    parser.add_argument("--headless", action="store_true", help="Run one 10 s demo without a window")
    parser.add_argument("--snapshot", type=Path, help="Save the final rendered frame, without overwriting")
    args = parser.parse_args()
    demo = Demo(args.delay_ms)
    if args.headless:
        for _ in range(round(demo.base["protocol"]["duration_s"] / demo.runtime.dt)):
            demo.step()
        demo.visual_state()
        print(f"Headless demo: t={demo.runtime.time:.3f}s, final state={demo.runtime.truth().tolist()}", flush=True)
    else:
        from mujoco import viewer as viewer_api
        print("Opening LIVE LQR demo. Space=pause, P=6 N push, R=reset. Close window to stop demo only.", flush=True)
        with viewer_api.launch_passive(demo.visual.model, demo.data,
                                         key_callback=demo.key,
                                         show_left_ui=False, show_right_ui=False) as viewer:
            with viewer.lock():
                viewer.cam.lookat[:] = [0., 0., .20]
                viewer.cam.distance = 1.05
                viewer.cam.azimuth = 90
                viewer.cam.elevation = -12
            print("MuJoCo window is running; close it to stop this demo only.", flush=True)
            started = time.monotonic()
            while viewer.is_running():
                frame_start = time.monotonic()
                if args.duration and frame_start - started >= args.duration:
                    break
                if demo.reset_requested or demo.runtime.time >= 10. - 1e-12:
                    demo.reset()
                if not demo.paused:
                    # Render ~60 Hz; physics/controller remain at the original 500 Hz.
                    for _ in range(8):
                        demo.step()
                with viewer.lock():
                    state = demo.visual_state()
                viewer.set_texts((mujoco.mjtFontScale.mjFONTSCALE_150,
                                  mujoco.mjtGridPos.mjGRID_TOPLEFT,
                                  "LIVE LQR / ASSUMED planar WBR\n"
                                  f"delay {args.delay_ms} ms; lag 5 ms; body IMU noise\n"
                                  f"t={demo.runtime.time:.2f}s  push={demo.push:.0f}N\n"
                                  f"leg={np.rad2deg(state[1]):+.1f} deg  body={np.rad2deg(state[2]):+.1f} deg\n"
                                  "Space pause | P push | R reset\nSeparate demo; PPO training continues", ""))
                viewer.sync()
                time.sleep(max(0., 1/60 - (time.monotonic() - frame_start)))
    if args.snapshot:
        from PIL import Image
        demo.visual_state()
        camera = mujoco.MjvCamera()
        camera.lookat[:] = [0., 0., .20]
        camera.distance, camera.azimuth, camera.elevation = 1.05, 90, -12
        with mujoco.Renderer(demo.visual.model, height=480, width=640) as renderer:
            renderer.update_scene(demo.data, camera=camera)
            with args.snapshot.open("xb") as stream:
                Image.fromarray(renderer.render()).save(stream, format="PNG")
        print(f"Snapshot: {args.snapshot}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
