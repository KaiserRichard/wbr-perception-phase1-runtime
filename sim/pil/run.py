"""Lockstep PIL push-recovery panel: MuJoCo on the host, C LQR on the MCU.

Runs the frozen 160-case LQR panel (4 delays x 2 scenarios x 20 noise seeds,
sim/rl/protocol.json) twice: `python` computes u = -K z in NumPy as the
original evaluator does; `pil` sends the six measurements over a serial link
and applies the torque the MCU returns. The PIL episode also computes the
Python command on the same observation, so every tick has a parity check.

    .venv/bin/python -m sim.pil.run --fake --out /path/outside/repo      # fake MCU
    .venv/bin/python -m sim.pil.run --qemu --out ...                     # ARM binary, emulated
    .venv/bin/python -m sim.pil.run --port /dev/cu.usbmodemXXXX --jobs 1 --out ...

The simulation owns the clock (lockstep). `--link-delay-ticks N` applies each
command N extra 2 ms ticks late, an unmodelled latency the controller does
not know about. It is applied identically to both controllers.
"""

import argparse
from collections import deque
from concurrent.futures import ProcessPoolExecutor
import json
import multiprocessing
from pathlib import Path
import re
import shutil
import time

import numpy as np

from sim.rl.environment import WbrEnv, decode_native, load_protocol
from sim.rl.metrics import compute_metrics, trace_arrays
from sim.rl.trace import TraceRecorder

ROOT = Path(__file__).resolve().parents[2]
GAINS = ROOT / "sim/control_c/gains.inc"


def load_gains(path=GAINS):
    """The archived K_used matrices exactly as compiled into the C library."""
    rows = re.findall(r"\{(-?\d[^{}]*)\}", Path(path).read_text())
    values = [np.array([float(v) for v in row.split(",") if v.strip()]) for row in rows]
    return {d: np.vstack(values[2 * i:2 * i + 2]) for i, d in enumerate((2, 3, 4, 5))}


_LINK = {}


def _worker_init(port, emulator):
    from sim.pil.link import FakeMcu, QemuMcu, SerialMcu
    import atexit
    if emulator:
        _LINK["fake"] = {"fake": FakeMcu, "qemu": QemuMcu}[emulator]()
        atexit.register(_LINK["fake"].close)
        _LINK["mcu"] = SerialMcu(_LINK["fake"].path, baud=FakeMcu.BAUD, timeout_s=2.0)
    elif port:
        _LINK["mcu"] = SerialMcu(port)


def episode(task):
    protocol = load_protocol()
    out = Path(task["out"])
    out.mkdir(parents=True, exist_ok=False)
    limits = np.asarray(protocol["plant"]["torque_limits_Nm"])
    gain = load_gains()[task["delay_ms"]]
    recorder = TraceRecorder(out / "trace", protocol)
    env = WbrEnv(recorder=recorder)
    rtt, exec_s, du = [], [], []
    error = None
    queue = deque([np.zeros(2)] * task["link_delay_ticks"])
    try:
        obs, _ = env.reset(options={"delay_s": task["delay_ms"] / 1000, "scenario": task["scenario"],
                                    "noise_seed": task["noise_seed"]})
        first = True
        while True:
            z = decode_native(obs, protocol)
            reference = -gain @ z / limits
            if task["controller"] == "pil":
                reply, seconds = _LINK["mcu"].step(z[:6], task["delay_ms"], reset=first)
                action = np.asarray(reply.requested) / limits
                rtt.append(seconds)
                exec_s.append(reply.exec_s)
                du.append(np.max(abs(action - reference) * limits))
            else:
                action = reference
            first = False
            queue.append(action)
            applied = queue.popleft()
            obs, _, terminated, truncated, _ = env.step(applied)
            recorder.attach_raw(applied)
            if terminated or truncated:
                break
    except Exception as exc:  # retained as an explicit failed outcome, never hidden
        error = f"{type(exc).__name__}: {exc}"
    finally:
        env.close()
    if recorder.total_steps:
        metrics = compute_metrics(out / "trace", task["scenario"], numerical_failure=error is not None, error=error)
        rows, _ = trace_arrays(out / "trace")
        np.save(out / "truth_after.npy", rows["truth_after"])
    else:
        metrics = {"success": False, "status": "EVALUATION_FAILED", "failure_reasons": [error]}
    if not task.get("keep_traces"):
        shutil.rmtree(out / "trace", ignore_errors=True)
    link = {}
    if rtt:
        link = {"round_trip_s": _stats(rtt), "mcu_exec_s": _stats(exec_s),
                "max_abs_torque_diff_vs_python_Nm": float(max(du)), "ticks": len(rtt)}
    result = {**{k: task[k] for k in ("controller", "delay_ms", "scenario", "noise_seed", "link_delay_ticks")},
              "success": metrics["success"], "status": metrics["status"], "error": error,
              "failure_reasons": metrics.get("failure_reasons"),
              "recovery_time_after_event_s": metrics.get("recovery_time_after_event_s"),
              "peak_tilt_deg": metrics.get("peak_tilt_deg"), "control_steps": metrics.get("control_steps"),
              "link": link, "path": str(out)}
    (out / "result.json").write_text(json.dumps(result, indent=1))
    return result


def _stats(values):
    v = np.asarray(values, float)
    return {"n": len(v), "mean": float(v.mean()), "p50": float(np.percentile(v, 50)),
            "p99": float(np.percentile(v, 99)), "max": float(v.max())}


def compare(results):
    """Pair python/pil episodes by condition and summarize the agreement."""
    by = {(r["controller"], r["delay_ms"], r["scenario"], r["noise_seed"]): r for r in results}
    summary = {}
    for controller in sorted({r["controller"] for r in results}):
        rs = [r for r in results if r["controller"] == controller]
        table = {}
        for d in sorted({r["delay_ms"] for r in rs}):
            for s in sorted({r["scenario"] for r in rs}):
                cell = [r for r in rs if r["delay_ms"] == d and r["scenario"] == s]
                rec = [r["recovery_time_after_event_s"] for r in cell if r["success"]]
                table[f"{d}ms-{s}"] = {"success": sum(r["success"] for r in cell), "n": len(cell),
                                       "mean_recovery_s": float(np.mean(rec)) if rec else None}
        summary[controller] = {"success": sum(r["success"] for r in rs), "n": len(rs), "cells": table}
    pil = [r for r in results if r["controller"] == "pil"]
    if pil:
        state_diff, recovery_diff, outcome_mismatch = [], [], 0
        for r in pil:
            ref = by.get(("python", r["delay_ms"], r["scenario"], r["noise_seed"]))
            if ref is None:
                continue
            outcome_mismatch += r["success"] != ref["success"]
            a, b = (np.load(Path(x["path"]) / "truth_after.npy") for x in (r, ref))
            n = min(len(a), len(b))
            state_diff.append(float(np.max(abs(a[:n] - b[:n]))) if n else float("nan"))
            if r["recovery_time_after_event_s"] is not None and ref["recovery_time_after_event_s"] is not None:
                recovery_diff.append(abs(r["recovery_time_after_event_s"] - ref["recovery_time_after_event_s"]))
        links = [r["link"] for r in pil if r["link"]]
        summary["pil_vs_python"] = {
            "paired_episodes": len(state_diff), "outcome_mismatches": outcome_mismatch,
            "max_abs_true_state_diff": max(state_diff) if state_diff else None,
            "max_abs_recovery_time_diff_s": max(recovery_diff) if recovery_diff else None,
            "max_abs_torque_diff_Nm": max(l["max_abs_torque_diff_vs_python_Nm"] for l in links) if links else None,
            "round_trip_s_p50_median": float(np.median([l["round_trip_s"]["p50"] for l in links])) if links else None,
            "round_trip_s_p99_max": max(l["round_trip_s"]["p99"] for l in links) if links else None,
            "round_trip_s_max": max(l["round_trip_s"]["max"] for l in links) if links else None,
            "mcu_exec_s_p50_median": float(np.median([l["mcu_exec_s"]["p50"] for l in links])) if links else None,
            "mcu_exec_s_max": max(l["mcu_exec_s"]["max"] for l in links) if links else None,
        }
    return summary


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    link = p.add_mutually_exclusive_group(required=True)
    link.add_argument("--fake", action="store_true", help="fake MCU (host-compiled C) behind a pty")
    link.add_argument("--qemu", action="store_true", help="ARM firmware build/pil_emu.elf on QEMU (numerics only)")
    link.add_argument("--port", help="serial device of the Nucleo (ST-Link VCP)")
    p.add_argument("--out", required=True, type=Path, help="new directory outside the repository")
    p.add_argument("--controllers", default="python,pil")
    p.add_argument("--delays", default="2,3,4,5")
    p.add_argument("--scenarios", default="balance,push")
    p.add_argument("--noise-seeds", type=int, default=20, help="first N held-out seeds (protocol has 20)")
    p.add_argument("--link-delay-ticks", type=int, default=0)
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--keep-traces", action="store_true")
    a = p.parse_args(argv)
    out = a.out.resolve()
    if ROOT in out.parents or out == ROOT:
        p.error("--out must be outside the repository")
    out.mkdir(parents=True, exist_ok=False)
    if a.port:
        a.jobs = 1  # one physical MCU
    protocol = load_protocol()
    seeds = protocol["evaluation"]["noise_seeds"][:a.noise_seeds]
    tasks = [{"controller": c, "delay_ms": int(d), "scenario": s, "noise_seed": n,
              "link_delay_ticks": a.link_delay_ticks, "keep_traces": a.keep_traces,
              "out": str(out / "episodes" / f"{c}-d{d}-{s}-n{n}")}
             for c in a.controllers.split(",") for d in a.delays.split(",")
             for s in a.scenarios.split(",") for n in seeds]
    started = time.perf_counter()
    with ProcessPoolExecutor(a.jobs, mp_context=multiprocessing.get_context("spawn"),
                             initializer=_worker_init,
                             initargs=(a.port, "fake" if a.fake else "qemu" if a.qemu else None)) as pool:
        results = list(pool.map(episode, tasks))
    summary = {"args": {k: str(v) for k, v in vars(a).items()}, "elapsed_s": time.perf_counter() - started,
               **compare(results)}
    (out / "results.json").write_text(json.dumps(results, indent=1))
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))
    return 0 if all(r["error"] is None for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
