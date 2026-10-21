#!/usr/bin/env python3
"""Tiny deterministic LQR lab. No MuJoCo, training, network or hardware access."""
import os
for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_name] = "1"

import argparse
import json
from pathlib import Path
import numpy as np
from scipy.linalg import solve_discrete_are
from scipy.signal import cont2discrete


def solve_lqr(a, b, q, r):
    p = solve_discrete_are(a, b, q, r)
    k = np.linalg.solve(r + b.T @ p @ b, b.T @ p @ a)
    residual = a.T @ p @ a - p - a.T @ p @ b @ k + q
    relative = np.linalg.norm(residual) / max(1.0, np.linalg.norm(q))
    radius = max(abs(np.linalg.eigvals(a - b @ k)))
    if relative > 1e-9 or radius >= 1:
        raise RuntimeError("DARE residual or sampled stability check failed")
    return p, k, relative, radius


def scalar():
    # x_next = x + u, Q = R = 1. Positive Riccati root is the golden ratio.
    p_hand = (1 + np.sqrt(5.0)) / 2
    k_hand = p_hand / (1 + p_hand)
    p, k, _, _ = solve_lqr(np.ones((1, 1)), np.ones((1, 1)),
                            np.ones((1, 1)), np.ones((1, 1)))
    np.testing.assert_allclose([p[0, 0], k[0, 0]], [p_hand, k_hand], atol=1e-12)
    x = np.zeros(41)
    x[0] = 1
    for t in range(40):
        x[t + 1] = (1 - k_hand) * x[t]
    u = -k_hand * x[:-1]
    # Telescoping Bellman identity, including the terminal remaining value.
    np.testing.assert_allclose(np.sum(x[:-1]**2 + u**2) + p_hand*x[-1]**2,
                               p_hand*x[0]**2, atol=1e-12)
    print(f"Scalar P={p_hand:.6f}, K={k_hand:.6f}, pole={1-k_hand:.6f}")
    return x


def cartpole():
    # Point mass on a massless rod. theta=0 upright, positive leans RIGHT.
    # State [cart x, cart velocity, theta, theta velocity]; force is +right.
    mass_cart, mass_tip, length, gravity, dt = 1.0, 0.1, 0.5, 9.81, 0.02
    a = np.array([[0, 1, 0, 0], [0, 0, -mass_tip*gravity/mass_cart, 0],
                  [0, 0, 0, 1], [0, 0, (mass_cart+mass_tip)*gravity/(mass_cart*length), 0]])
    b = np.array([[0], [1/mass_cart], [0], [-1/(mass_cart*length)]])
    ad, bd, _, _, _ = cont2discrete((a, b, np.eye(4), np.zeros((4, 1))), dt)
    q, r = dt*np.diag([10., 1., 100., 1.]), dt*np.array([[0.1]])
    _, k, residual, radius = solve_lqr(ad, bd, q, r)
    controllability = np.concatenate([np.linalg.matrix_power(ad, j) @ bd for j in range(4)], axis=1)
    assert np.linalg.matrix_rank(controllability) == 4
    state = np.zeros((401, 4))
    state[0, 2] = np.deg2rad(5)
    for j in range(400):
        state[j+1] = (ad - bd @ k) @ state[j]
    assert np.linalg.norm(state[-1]) < 0.01*np.linalg.norm(state[0])
    print("Cart-pole K=" + np.array2string(k[0], precision=6))
    print(f"Cart-pole controllability rank=4, spectral radius={radius:.6f}")
    print(f"Cart-pole relative DARE residual={residual:.2e} (expected <1e-9)")
    return dt*np.arange(401), state, (-state[:-1] @ k.T).ravel()


def read_wbr(path):
    data = json.loads(path.read_text())
    k = np.asarray(data["nominal"]["K"], dtype=float)
    assert k.shape == (2, 6) and np.all(np.isfinite(k))
    print("WBR nominal K shape=(2, 6); SIMULATION / ASSUMED")
    print(np.array2string(k, precision=6))
    # Tilt only; demonstrate row-by-state multiplication, not a rollout.
    state = np.array([0, np.deg2rad(5), 0, 0, 0, 0])
    print("WBR nominal command at leg +5 deg (Nm)=" + np.array2string(-k @ state, precision=6))
    for profile in data["delay_aware"]:
        gain = np.asarray(profile["K"])
        assert gain.shape == (2, 8+2*profile["history_steps"])
        print(f"WBR archived delay {profile['delay_ms']} ms: K shape={gain.shape}")
    print("PASS: scalar identity, cart-pole DARE/stability, WBR matrix dimensions")


def figures(folder, x, times, state, force, png=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Arc
    folder.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                         "axes.spines.right": False, "svg.fonttype": "none"})

    def save(fig, name):
        fig.savefig(folder / f"{name}.svg", bbox_inches="tight", metadata={"Date": None})
        svg = folder / f"{name}.svg"
        svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
        if png:
            fig.savefig(folder / f"{name}.png", dpi=140, bbox_inches="tight")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.axhline(0, color="0.5", lw=1)
    ax.add_patch(Circle((0, 0.15), .15, fill=False, lw=2))
    ax.plot([0, .28], [.15, .95], "k-", lw=3)
    ax.plot([.28, .17], [.95, 1.35], "k-", lw=7)
    ax.plot([0, 0], [.15, 1.35], "k--", lw=1)
    ax.plot([.28, .28], [.95, 1.45], color=".6", ls="--")
    ax.add_patch(Arc((0, .15), .65, .65, theta1=71, theta2=90, lw=1.5))
    ax.text(.045, .56, r"$\theta$", fontsize=15)
    ax.add_patch(Arc((.28, .95), .6, .6, theta1=90, theta2=105, lw=1.5))
    ax.text(.38, 1.27, r"$\phi$", fontsize=15)
    ax.annotate("+x", (.85, .03), (.35, .03), arrowprops={"arrowstyle": "->"})
    ax.annotate("wheel-pair torque", xy=(-.12, .2), xytext=(-.9, .65),
                arrowprops={"arrowstyle": "->"})
    ax.annotate("virtual hip-pair torque", xy=(.28, .95), xytext=(.7, 1.1),
                arrowprops={"arrowstyle": "->"})
    ax.text(-.9, -.19, "Schematic only: ideal rolling, fixed equivalent leg; no CAD dimensions", fontsize=10)
    ax.set(xlim=(-1, 2), ylim=(-.25, 1.6), aspect="equal")
    ax.axis("off")
    ax.set_title("Reduced WBR coordinates: both pitch angles are absolute")
    save(fig, "wbr-coordinates")

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.8))
    p = (1 + np.sqrt(5))/2
    grid = np.linspace(-1.2, 1.2, 201)
    axes[0].plot(grid, p*grid**2, color="k")
    axes[0].set(xlabel="Scalar state x", ylabel="Optimal remaining cost V(x)", title=r"$V(x)=Px^2$")
    axes[1].plot(np.arange(7), x[:7], "ko-")
    axes[1].set(xlabel="Sample k", ylabel="Scalar state x", title="Closed-loop pole = 0.381966")
    fig.suptitle("Computed scalar teaching example, not WBR measurements")
    fig.tight_layout()
    save(fig, "scalar-value-feedback")

    fig, axes = plt.subplots(3, 1, figsize=(8, 6.6), sharex=True)
    axes[0].plot(times, np.rad2deg(state[:, 2]), "k")
    axes[0].set_ylabel("Tilt (deg)")
    axes[1].plot(times, state[:, 0], "k")
    axes[1].set_ylabel("Cart x (m)")
    axes[2].step(times[:-1], force, color="k", where="post")
    axes[2].set(ylabel="Force (N)", xlabel="Time (s)")
    fig.suptitle("Linear cart-pole + DARE: 5 deg start, no saturation or noise")
    fig.tight_layout()
    save(fig, "cartpole-response")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wbr", type=Path, default=Path(__file__).with_name("data")/"wbr_gains.json")
    parser.add_argument("--figures", type=Path, help="Optionally regenerate the three SVG assets")
    parser.add_argument("--png", action="store_true", help="Also render PNG previews with --figures")
    args = parser.parse_args()
    np.set_printoptions(suppress=True)
    x = scalar()
    times, states, force = cartpole()
    read_wbr(args.wbr)
    if args.figures:
        figures(args.figures, x, times, states, force, args.png)


if __name__ == "__main__":
    main()
