"""Small host C/ONNX forward parity checks; no rollout or training."""
import argparse
import ctypes
import importlib.util
import json
from pathlib import Path
import subprocess

import numpy as np
import torch

from .export import contract, load_completed


OUTPUT_NAMES = ("raw", "bounded", "held_Nm", "command_Nm")


class HostPolicy:
    def __init__(self, folder):
        folder = Path(folder).resolve()
        library = folder / "policy_host.so"
        subprocess.run(["cc", "-std=c99", "-O2", "-Wall", "-Wextra", "-Werror",
                        "-ffp-contract=off", "-shared", "-fPIC", str(folder / "policy.c"),
                        "-lm", "-o", str(library)], check=True, capture_output=True, text=True)
        self.lib = ctypes.CDLL(str(library))
        self.f32 = np.ctypeslib.ndpointer(dtype=np.float32, flags="C_CONTIGUOUS")
        self.f64 = np.ctypeslib.ndpointer(dtype=np.float64, flags="C_CONTIGUOUS")
        self.lib.wbr_policy.argtypes = [self.f64, self.f32, self.f32, self.f32]
        self.lib.wbr_compose.argtypes = [self.f32, self.f32, self.f32]
        self.lib.wbr_encode.argtypes = [self.f64, self.f64, self.f64, ctypes.c_double, self.f64]
        for name in ("wbr_policy", "wbr_compose", "wbr_encode"):
            getattr(self.lib, name).restype = ctypes.c_int

    def predict(self, encoded, lqr):
        raw, bounded, held, command = [np.zeros(2, np.float32) for _ in range(4)]
        code = self.lib.wbr_policy(np.ascontiguousarray(encoded, dtype=np.float64), raw, bounded, held)
        if code or self.lib.wbr_compose(held, np.ascontiguousarray(lqr, dtype=np.float32), command):
            raise ValueError("C rejected nonfinite policy/controller input")
        return raw, bounded, held, command


def vectors(actor, count=64):
    rng = np.random.default_rng(20261020)
    x = rng.uniform(-3, 3, (count, 15))
    # Explicit fitted clipping boundaries and finite large inputs.
    x[:6] = np.asarray([np.zeros(15), actor.mean.numpy(),
                       actor.mean.numpy() + actor.clip_obs * np.sqrt(actor.var.numpy() + actor.epsilon),
                       actor.mean.numpy() - actor.clip_obs * np.sqrt(actor.var.numpy() + actor.epsilon),
                       np.full(15, 1000.), np.full(15, -1000.)])
    lqr = rng.uniform(-8, 8, (count, 2)).astype(np.float32)
    return x, lqr


def validate(actor, model, norm, folder):
    x, lqr = vectors(actor)
    with torch.no_grad():
        expected = [v.numpy() for v in actor(torch.from_numpy(x), torch.from_numpy(lqr))]
    # Independent SB3 + VecNormalize reference, with statistics frozen.
    mean_before, var_before = norm.obs_rms.mean.copy(), norm.obs_rms.var.copy()
    predicted, _ = model.predict(norm.normalize_obs(x), deterministic=True)
    np.testing.assert_allclose(expected[1], predicted, atol=2e-6, rtol=2e-6)
    p, config = contract()
    limits = np.asarray(p["plant"]["torque_limits_Nm"], dtype=np.float32)
    held_reference = predicted * limits
    if actor.arm == "residual":
        held_reference *= config["residual_cap_fraction"]
    command_reference = np.clip(held_reference + (lqr if actor.arm == "residual" else 0),
                                -limits, limits)
    np.testing.assert_allclose(expected[2], held_reference, atol=2e-6, rtol=2e-6)
    np.testing.assert_allclose(expected[3], command_reference, atol=2e-6, rtol=2e-6)
    np.testing.assert_array_equal(mean_before, norm.obs_rms.mean)
    np.testing.assert_array_equal(var_before, norm.obs_rms.var)
    host = HostPolicy(folder)
    actual = np.asarray([host.predict(a, b) for a, b in zip(x, lqr)]).transpose(1, 0, 2)
    errors = {}
    for name, c, ref in zip(OUTPUT_NAMES, actual, expected):
        np.testing.assert_allclose(c, ref, atol=3e-5, rtol=3e-5, err_msg=name)
        errors[name] = float(np.max(np.abs(c-ref)))
    result = {"c_status": "PASS", "vectors": len(x), "encoded_bound_abs": float(abs(x).max()),
              "lqr_bound_abs_Nm": 8, "atol": 3e-5, "rtol": 3e-5,
              "max_abs_error": errors, "sb3_vecnormalize_reference": "PASS",
              "sb3_action_composition_reference": "PASS"}
    onnx_path = Path(folder) / "policy.onnx"
    if not onnx_path.exists():
        result["onnx"] = {"status": "PENDING", "reason": "No ONNX artifact; dependency unavailable or export not run"}
    elif any(importlib.util.find_spec(name) is None for name in ("onnx", "onnxruntime")):
        result["onnx"] = {"status": "PENDING", "reason": "onnx or onnxruntime unavailable"}
    else:
        import onnx
        import onnxruntime as ort
        onnx.checker.check_model(onnx.load(str(onnx_path)))
        options = ort.SessionOptions()
        options.intra_op_num_threads = options.inter_op_num_threads = 1
        session = ort.InferenceSession(str(onnx_path), options, providers=["CPUExecutionProvider"])
        if [output.name for output in session.get_outputs()] != list(OUTPUT_NAMES):
            raise ValueError("Unexpected ONNX output interface")
        torch_errors, c_errors = {}, {}
        # Check both batched validation and the one-observation inference ABI.
        for batch in (len(x), 1):
            outputs = session.run(list(OUTPUT_NAMES), {"encoded": x[:batch], "lqr_Nm": lqr[:batch]})
            for name, output, ref, c in zip(OUTPUT_NAMES, outputs, expected, actual):
                if output.shape != (batch, 2) or output.dtype != np.float32 or not np.isfinite(output).all():
                    raise ValueError(f"Invalid ONNX output: {name}")
                np.testing.assert_allclose(output, ref[:batch], atol=3e-5, rtol=3e-5, err_msg=name)
                np.testing.assert_allclose(output, c[:batch], atol=3e-5, rtol=3e-5, err_msg=name)
                torch_errors[name] = max(torch_errors.get(name, 0.), float(abs(output-ref[:batch]).max()))
                c_errors[name] = max(c_errors.get(name, 0.), float(abs(output-c[:batch]).max()))
        result["onnx"] = {"status": "PASS", "checker": "PASS", "vectors": len(x),
                          "batch_sizes": [len(x), 1], "providers": session.get_providers(),
                          "max_abs_error_vs_pytorch": torch_errors,
                          "max_abs_error_vs_c": c_errors}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-dir", type=Path, required=True)
    parser.add_argument("--export-dir", type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    actor, model, norm, hashes = load_completed(args.checkpoint_dir)
    manifest = json.loads((args.export_dir / "manifest.json").read_text())
    if hashes != manifest["source_sha256"] or actor.arm != manifest["arm"]:
        raise ValueError("Export manifest does not identify this completed checkpoint")
    result = validate(actor, model, norm, args.export_dir)
    (args.export_dir / "parity.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
