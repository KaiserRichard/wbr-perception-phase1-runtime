#!/usr/bin/env python3
"""Hand-check GAE/PPO on three transitions; optional technical SVG figure."""
import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
import argparse
from pathlib import Path
import numpy as np


def clipped(ratio, advantage, epsilon=0.2):
    return np.minimum(ratio*advantage, np.clip(ratio, 1-epsilon, 1+epsilon)*advantage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figure", type=Path, help="Optional SVG output")
    args = parser.parse_args()
    rewards = np.array([1., 0., 2.])
    values = np.array([.5, .4, .2, 0.])
    gamma, lam = .9, .8
    delta = rewards + gamma*values[1:] - values[:-1]
    advantage = np.zeros(3)
    running = 0.
    for t in reversed(range(3)):
        running = delta[t] + gamma*lam*running
        advantage[t] = running
    np.testing.assert_allclose(delta, [.86, -.22, 1.8], atol=1e-12)
    np.testing.assert_allclose(advantage, [1.63472, 1.076, 1.8], atol=1e-12)
    ratio = np.array([1.3, .7, 1.1])
    objective = clipped(ratio, advantage)
    np.testing.assert_allclose(objective, [1.961664, .7532, 1.98], atol=1e-12)
    negative = clipped(np.array([1.3, .7]), np.array([-2., -2.]))
    np.testing.assert_allclose(negative, [-2.6, -1.6])
    # A timeout bootstraps; a true terminal does not.
    terminal_delta = 2. - .2
    timeout_delta = 2. + gamma*.7 - .2
    np.testing.assert_allclose([terminal_delta, timeout_delta], [1.8, 2.43])
    for name, value in [('TD delta', delta), ('GAE advantage', advantage),
                        ('Value target', values[:-1]+advantage),
                        ('Clipped contributions', objective), ('Negative A example', negative)]:
        print(name + '=' + np.array2string(value, precision=6))
    print(f"Mean clipped objective={objective.mean():.6f}")
    print(f"Final delta: terminal={terminal_delta:.2f}, timeout bootstrap={timeout_delta:.2f}")
    print("Rollout count: 8 envs x 250 steps = 2000 total transitions, not 16000")
    print("PASS: hand GAE, both PPO advantage signs, termination versus truncation")
    if args.figure:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.rcParams['svg.fonttype'] = 'none'
        x = np.linspace(.4, 1.6, 201)
        fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
        for ax, a in zip(axes, [2., -2.]):
            ax.plot(x, x*a, '--', color='.6', label='Unclipped')
            ax.plot(x, clipped(x, a), 'k', label='PPO minimum')
            ax.axvline(.8, color='.6', lw=.7)
            ax.axvline(1.2, color='.6', lw=.7)
            ax.set(xlabel='Probability ratio', ylabel='Objective contribution', title=f'Advantage = {a:+g}')
            ax.legend()
        fig.suptitle('Exact PPO objective examples; no trained robot data')
        fig.tight_layout()
        args.figure.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.figure, bbox_inches='tight', metadata={'Date':None})
        plt.close(fig)


if __name__ == '__main__':
    main()
