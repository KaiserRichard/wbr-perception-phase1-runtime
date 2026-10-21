#!/usr/bin/env python3
"""Plot two archived issued-command traces. Never loads a policy or simulates."""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
import argparse
import json
from pathlib import Path
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('saved-torque.svg'))
    args = parser.parse_args()
    root = Path(__file__).parent
    a = np.loadtxt(root/'data/issued-torque.csv', delimiter=',', skiprows=1)
    meta = json.loads((root/'data/evidence.json').read_text())
    assert a.shape == (1000, 5) and np.all(np.isfinite(a))
    assert np.all(np.diff(a[:, 0]) > 0)
    assert np.all(abs(a[:, [1, 3]]) <= 2+1e-10)
    assert np.all(abs(a[:, [2, 4]]) <= 4+1e-10)
    print(f"Saved samples={len(a)}, time={a[0,0]:.2f}..{a[-1,0]:.2f}s (every fifth 500Hz tick)")
    print('Case: delay=5ms, push, noise seed=1000; residual training seed=0')
    for name in ['lqr', 'residual']:
        m = meta[name]['metrics']
        effort = np.asarray(m['command_effort_Nm2_s'])
        survived = m.get('survived', m['checks']['full_duration'] and m['checks']['no_fall'])
        print(f"{name}: strict={m['success']}, survived={survived}, command effort Nm2s="
              + np.array2string(effort, precision=6))
    print('Effort is copied from full-resolution archived metrics, not this thinned plot.')
    print('PASS: finite data, time order, pair torque caps; one illustration, no superiority claim')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    plt.rcParams.update({'svg.fonttype':'none', 'font.size':10})
    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    for i, ax in enumerate(axes):
        ax.plot(a[:,0], a[:,1+i], 'k', lw=1, label='Delay-aware LQR')
        ax.plot(a[:,0], a[:,3+i], color='.55', lw=1, label='LQR + PPO (total issued)')
        ax.axvspan(3, 3.15, color='.8', alpha=.5, label='6N push')
        ax.set_ylabel(['Wheel-pair (Nm)','Virtual hip-pair (Nm)'][i])
        ax.legend(loc='upper right', fontsize=8)
    axes[-1].set_xlabel('Time (s)')
    fig.suptitle('Saved 5ms push case: issued torque, thinned to 100Hz for display')
    fig.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, bbox_inches='tight', metadata={'Date':None})
    plt.close(fig)
    # A separate deterministic signal diagram, produced by this same script.
    fig, ax = plt.subplots(figsize=(9, 3.3))
    boxes=[(.1,.65,'LQR at 500Hz'),(.1,.12,'PPO at 100Hz\nbounded correction'),
           (.44,.4,'Sum + total\ntorque clipping'),(.75,.4,'Delay + lag\nplant')]
    for x,y,label in boxes:
        ax.add_patch(Rectangle((x,y),.21,.23,fill=False,lw=1.5))
        ax.text(x+.105,y+.115,label,ha='center',va='center')
    for start,end in [((.31,.765),(.44,.54)),((.31,.235),(.44,.49)),((.65,.515),(.75,.515))]:
        ax.annotate('',end,start,arrowprops={'arrowstyle':'->'})
    ax.plot([.855,.855,.055,.055],[.4,.05,.05,.765],color='k',lw=1)
    for y in [.765,.235]:
        ax.annotate('',(.1,y),(.055,y),arrowprops={'arrowstyle':'->'})
    ax.text(.5,-.02,'Causal measured/estimated feedback to both controllers',ha='center')
    ax.set(xlim=(0,1),ylim=(-.15,1));ax.axis('off')
    fig.tight_layout()
    fig.savefig(args.out.with_name('residual-signal-path.svg'),bbox_inches='tight',metadata={'Date':None})
    plt.close(fig)


if __name__ == '__main__':
    main()
