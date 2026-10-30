# Evidence status — 2026-10-30

BLOCKED: recording attempted for `3-box13` and `4-approach`, both at
10 fps (ASSUMED presentation rate). MuJoCo 3.3.7 model compilation succeeds,
but `mujoco.Renderer` fails with:

```text
mujoco.cgl.cgl.CGLError: invalid CoreGraphics connection
```

`MUJOCO_GL=glfw` was also attempted; the installed MuJoCo Darwin backend still
selects CGL and fails identically. No rendered GIFs/PNGs exist, and no rendered
frames have been visually inspected. Do not treat this directory as completed
visual evidence. See `docs/scene_twin/RUN_RECEIPT.md` for numerical results.

To produce evidence in a graphical Mac session, from the repository root:

```sh
VENV=~/Desktop/Research/wbr-lab-ops/.venv
ARCHIVE=~/wbr-evidence-archive/lab-day-20261025
"$VENV/bin/python" -m tools.scene_twin.view --run "$ARCHIVE/3-box13" --record /tmp/twin-box13-evidence --fps 10
"$VENV/bin/python" -m tools.scene_twin.view --run "$ARCHIVE/4-approach" --record /tmp/twin-approach-evidence --fps 10
```

After visually checking early/middle/late PNGs for the box and both tyres on the
floor, copy each GIF plus representative PNGs and `frames.csv` into a matching
run directory here. Keep each GIF under 3 MB (ASSUMED delivery limit).
