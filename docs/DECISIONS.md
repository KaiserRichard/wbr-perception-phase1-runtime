# Architecture / Research Decisions

Use this file for decisions that should not be reopened every session without new evidence.

Keep entries concise.

---

## ADR-001 — Pi vs STM32 ownership

**Status:** Accepted

**Decision:**

Raspberry Pi owns perception, VIO, SLAM and non-hard-real-time estimation. STM32 owns hard-real-time balancing, controller-side estimation and actuator safety.

**Reason:**

Robot balance must not depend on continued health of the Linux/ROS perception stack.

---

## ADR-002 — Camera IMU vs body IMU

**Status:** Accepted for Phase 1

**Decision:**

Use the D435i IMU for camera-centric VIO development. Keep the body IMU controller-owned. Do not begin naïve multi-IMU fusion.

**Revisit when:**

Independent frames, clock behavior, synchronization and calibration are characterized.

---

## ADR-003 — Upstream ORB-SLAM3 vs ROS 2 wrapper

**Status:** Accepted

**Decision:**

Treat official/upstream ORB-SLAM3 algorithm validation separately from ROS 2 wrapper integration.

**Reason:**

Wrapper/integration failures must not be confused with algorithm failures.

---

## ADR-004 — Evidence before gate promotion

**Status:** Accepted

**Decision:**

Compilation, a successful launch, or a visually plausible map is not sufficient to promote a gate to PASS.

---

## ADR-005 — Adaptive runtime progression

**Status:** Accepted

**Decision:**

Use the progression:

static characterization
-> rule-based policy
-> ablation
-> simple/contextual learned policy
-> reinforcement learning only if justified.
