"""Export trusted, completed v2 checkpoints without constructing a plant."""
import argparse
import hashlib
import importlib.util
import json
import pickle
from pathlib import Path

import numpy as np
import torch
from torch import nn
from stable_baselines3 import PPO
from stable_baselines3.common.distributions import DiagGaussianDistribution
from stable_baselines3.common.torch_layers import FlattenExtractor

ROOT = Path(__file__).resolve().parents[2]


def contract():
    p = json.loads((ROOT / "sim/rl/protocol.json").read_text())
    c = json.loads((ROOT / "sim/rl/v2_config.json").read_text())
    if p["policy_input"]["dimension"] != 15 or c["policy_hold_ticks"] != 5:
        raise ValueError("Exporter supports the frozen 15-input, five-tick v2 contract")
    return p, c


class FrozenActor(nn.Module):
    """Input: fixed-divisor encoded observation BEFORE fitted normalization.

    lqr_Nm is the current tick's causal LQR output (before saturation); direct
    mode ignores it. Exporting this interface does not export the LQR estimator.
    """
    def __init__(self, policy, norm, arm):
        super().__init__()
        p, c = contract()
        if arm not in c["arms"]:
            raise ValueError("Unknown controller arm")
        if (not isinstance(policy.features_extractor, FlattenExtractor)
                or not isinstance(policy.pi_features_extractor, FlattenExtractor)
                or type(policy.action_dist) is not DiagGaussianDistribution
                or policy.squash_output or policy.observation_space.shape != (15,)
                or policy.action_space.shape != (2,)
                or not np.array_equal(policy.action_space.low, [-1, -1])
                or not np.array_equal(policy.action_space.high, [1, 1])):
            raise ValueError("Only flat, unsquashed diagonal-Gaussian Box[-1,1]^2 PPO supported")
        self.actor = nn.Sequential(*list(policy.mlp_extractor.policy_net.children()), policy.action_net)
        width = 15
        for layer in self.actor:
            if isinstance(layer, nn.Linear):
                if layer.in_features != width:
                    raise ValueError("Inconsistent actor dimensions")
                if layer.bias is None or any(not torch.isfinite(v).all() for v in layer.parameters()):
                    raise ValueError("Expected finite actor parameters with linear biases")
                width = layer.out_features
            elif not isinstance(layer, (nn.Tanh, nn.ReLU, nn.Identity)):
                raise ValueError(f"Unsupported layer: {layer}")
        if width != 2 or not norm.norm_obs or isinstance(norm.obs_rms, dict):
            raise ValueError("Expected two actions and flat saved observation statistics")
        mean = np.asarray(norm.obs_rms.mean, dtype=np.float64)
        var = np.asarray(norm.obs_rms.var, dtype=np.float64)
        if (mean.shape != (15,) or var.shape != (15,) or not np.all(np.isfinite(mean))
                or not np.all(np.isfinite(var)) or np.any(var < 0)
                or not np.isfinite(norm.epsilon) or norm.epsilon <= 0
                or not np.isfinite(norm.clip_obs) or norm.clip_obs <= 0):
            raise ValueError("Invalid VecNormalize statistics")
        self.register_buffer("mean", torch.from_numpy(mean.copy()))
        self.register_buffer("var", torch.from_numpy(var.copy()))
        self.register_buffer("limits", torch.tensor(p["plant"]["torque_limits_Nm"], dtype=torch.float32))
        self.epsilon, self.clip_obs = float(norm.epsilon), float(norm.clip_obs)
        self.arm, self.cap = arm, float(c["residual_cap_fraction"])
        self.hold_ticks = c["policy_hold_ticks"]
        self.eval()

    def forward(self, encoded, lqr_Nm):
        normalized = torch.clamp((encoded.double() - self.mean) /
                                 torch.sqrt(self.var + self.epsilon),
                                 -self.clip_obs, self.clip_obs).float()
        raw = self.actor(normalized)
        bounded = torch.clamp(raw, -1., 1.)
        held = bounded * self.limits
        if self.arm == "residual":
            held = held * self.cap
            requested = lqr_Nm + held
        else:
            # Keep the same two-input ABI in ONNX direct mode.
            requested = held + lqr_Nm * 0.
        command = torch.maximum(torch.minimum(requested, self.limits), -self.limits)
        return raw, bounded, held, command


def load_completed(folder):
    """Only use owner-trusted pickle/zip inputs. Reject incomplete seed folders."""
    folder = Path(folder)
    status = json.loads((folder / "status.json").read_text())
    if status.get("status") != "COMPLETE" or status.get("checkpoint_reload") != "PASS":
        raise ValueError("Refusing a checkpoint without COMPLETE and reload PASS status")
    files = [folder / name for name in ("final.zip", "vecnormalize.pkl", "status.json")]
    hashes = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    model = PPO.load(folder / "final.zip", device="cpu")
    model.policy.set_training_mode(False)
    with (folder / "vecnormalize.pkl").open("rb") as stream:
        norm = pickle.load(stream)
    norm.training, norm.norm_reward = False, False
    actor = FrozenActor(model.policy, norm, status["arm"])
    if any(hashlib.sha256(f.read_bytes()).hexdigest() != hashes[f.name] for f in files):
        raise ValueError("Checkpoint changed while reading")
    return actor, model, norm, hashes


def _array(name, values, dtype="float"):
    values = np.asarray(values).ravel()
    # Hex literals preserve the precise source float32/float64 constants in C99.
    literals = [float(v).hex() + ("f" if dtype == "float" else "") for v in values]
    return f"static const {dtype} {name}[{len(values)}] = {{" + ",".join(literals) + "};\n"


def export_c(actor, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    header = '''/* Generated offline; encoded inputs are before VecNormalize. */
#ifndef WBR_POLICY_H
#define WBR_POLICY_H
#define WBR_OBS 15
#define WBR_ACTIONS 2
#define WBR_POLICY_HOLD_TICKS 5
/* Return -1 for nonfinite input; callers must handle errors before control. */
int wbr_policy(const double encoded[15], float raw[2], float bounded[2], float held[2]);
/* Run every 2 ms with current causal LQR, holding policy result for five ticks. */
int wbr_compose(const float held[2], const float lqr_Nm[2], float command[2]);
/* history: three newest-first command pairs, right-padded with zero pairs. */
int wbr_encode(const double measurement[6], const double torque[2],
               const double history[6], double delay_s, double encoded[15]);
#endif
'''
    p, _ = contract()
    divisors = np.r_[p["policy_input"]["sensor_divisors"],
                     p["policy_input"]["torque_estimate_divisors"],
                     np.tile(p["policy_input"]["history_divisors"], 3),
                     p["policy_input"]["delay_divisor_s"]]
    source = '#include "policy.h"\n#include <math.h>\n'
    source += _array("obs_mean", actor.mean.numpy(), "double")
    source += _array("obs_var", actor.var.numpy(), "double")
    source += _array("divisor", divisors, "double")
    source += _array("limits", actor.limits.numpy())
    layers = list(actor.actor)
    width = max([15] + [l.out_features for l in layers if isinstance(l, nn.Linear)])
    for i, layer in enumerate(layers):
        if isinstance(layer, nn.Linear):
            source += _array(f"w{i}", layer.weight.detach().numpy())
            source += _array(f"b{i}", layer.bias.detach().numpy())
    source += '''static float clipf(float x, float cap) { return fmaxf(-cap, fminf(cap, x)); }
int wbr_encode(const double m[6], const double t[2], const double h[6], double d, double e[15]) {
    for (int i=0;i<15;i++) {
        double v = i<6 ? m[i] : i<8 ? t[i-6] : i<14 ? h[i-8] : d;
        if (!isfinite(v)) return -1;
        e[i] = v / divisor[i];
    }
    return 0;
}
'''
    source += f'int wbr_policy(const double e[15], float raw[2], float bounded[2], float held[2]) {{\n float a[{width}], b[{width}];\n'
    source += f''' for (int i=0;i<15;i++) {{
    if (!isfinite(e[i])) return -1;
    double v = (e[i]-obs_mean[i])/sqrt(obs_var[i]+{actor.epsilon.hex()});
    a[i] = (float)fmax(-{actor.clip_obs.hex()}, fmin({actor.clip_obs.hex()}, v));
 }}
'''
    n = 15
    for i, layer in enumerate(layers):
        if isinstance(layer, nn.Linear):
            n = layer.out_features
            source += f''' for (int j=0;j<{n};j++) {{
    float v=b{i}[j];
    for (int k=0;k<{layer.in_features};k++) v += w{i}[j*{layer.in_features}+k]*a[k];
    b[j]=v;
 }}
 for (int j=0;j<{n};j++) a[j]=b[j];
'''
        elif isinstance(layer, nn.Tanh):
            source += f' for (int j=0;j<{n};j++) a[j]=tanhf(a[j]);\n'
        elif isinstance(layer, nn.ReLU):
            source += f' for (int j=0;j<{n};j++) a[j]=fmaxf(0.f,a[j]);\n'
    factor = actor.cap if actor.arm == "residual" else 1.
    source += f''' for (int j=0;j<2;j++) {{
    if (!isfinite(a[j])) return -1;
    raw[j]=a[j]; bounded[j]=clipf(a[j],1.f);
    held[j]=bounded[j]*limits[j]*{float(np.float32(factor)).hex()}f;
 }}
 return 0;
}}
int wbr_compose(const float held[2], const float lqr[2], float command[2]) {{
 for (int j=0;j<2;j++) {{
    if (!isfinite(held[j]) || !isfinite(lqr[j])) return -1;
    float correction=clipf(held[j],limits[j]*{float(np.float32(factor)).hex()}f);
    command[j]=clipf(correction{'+lqr[j]' if actor.arm == 'residual' else ''},limits[j]);
 }}
 return 0;
}}
'''
    (out / "policy.h").write_text(header)
    (out / "policy.c").write_text(source)
    linear = [l for l in layers if isinstance(l, nn.Linear)]
    macs = sum(l.in_features * l.out_features for l in linear)
    return {"layers": [str(l) for l in layers], "macs": macs,
            "parameters": sum(l.weight.numel() + l.bias.numel() for l in linear),
            "hidden_activations": sum(l.out_features for l in linear[:-1]),
            "scratch_bytes": 2 * width * 4}


def export_onnx(actor, out):
    if importlib.util.find_spec("onnx") is None:
        return {"status": "PENDING", "reason": "onnx unavailable; use an isolated environment"}
    path = Path(out) / "policy.onnx"
    torch.onnx.export(actor, (torch.zeros(1, 15, dtype=torch.float64), torch.zeros(1, 2)),
                      str(path), opset_version=17,
                      input_names=["encoded", "lqr_Nm"],
                      output_names=["raw", "bounded", "held_Nm", "command_Nm"],
                      dynamic_axes={name: {0: "batch"} for name in
                                    ["encoded", "lqr_Nm", "raw", "bounded", "held_Nm", "command_Nm"]})
    import onnx
    onnx.checker.check_model(onnx.load(str(path)))
    return {"status": "EXPORTED_CHECKED", "runtime_parity": "PENDING", "file": path.name}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    if args.out.exists():
        parser.error("Use a new output directory; refusing to overwrite artifacts")
    actor, _, norm, hashes = load_completed(args.checkpoint_dir)
    report = export_c(actor, args.out)
    report.update(arm=actor.arm, source_sha256=hashes,
                  input="15 fixed-divisor encoded float64 values, before VecNormalize",
                  obs_mean=actor.mean.tolist(), obs_var=actor.var.tolist(),
                  obs_count=float(norm.obs_rms.count), epsilon=actor.epsilon,
                  clip_obs=actor.clip_obs, action_clip=[-1, 1],
                  torque_limits_Nm=actor.limits.tolist(), residual_cap_fraction=actor.cap,
                  policy_hold_ticks=actor.hold_ticks, control_period_s=0.002,
                  onnx=export_onnx(actor, args.out))
    (args.out / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
