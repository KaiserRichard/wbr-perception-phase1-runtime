# Visible simulation

- Owner asked how to watch the simulation. Existing runners were headless; no viewer command existed.
- Added `sim/view.py` and a Finder launcher; README has exact commands/controls. Local Desktop shortcut points to this checkout. Reused installed environment through an ignored `.venv` link; no dependency install.
- Independent LIVE delay-aware LQR demo, default5ms delay/5ms lag/bodyIMUnoise; original500Hz runtime and causal feedback. Visual model/data are separate from physics and training. Automatic6N/.15s push at3s; Space pause,P push,R reset; loops10s.
- Actual `mjpython -m sim.view --duration 12` exited0; native live window then launched with the Desktop/Finder command and remained running. This is an unscored assumed-model demo, not PPO training or new acceptance evidence.
- Actual `python -m sim.view --headless --snapshot .../viewer-frame-02.png` completed10s; final state matches the archived5ms/noise1000 LQR push case to roundoff. Rendered640x480 frame inspected. First720px snapshot exceeded the default640px framebuffer; retained failure, fixed only output size.
- Primary viewer API: https://mujoco.readthedocs.io/en/3.3.7/python.html#passive-viewer . macOS requires `mjpython`.
- Logs/images: /private/tmp/wbr-ppo-v2-20261020/viewer-*. Training supervisor75443/root source remains untouched and progress continued after GUI launch.
- No physics, gains, thresholds, learning exercise, Pi or STM32 changes. Viewer publication/CI pending; no Claude milestone review required for opening the display.
