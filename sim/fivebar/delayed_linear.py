"""Fixed-length LOCAL LINEAR delay/lag comparison, without nonlinear rollouts.

Fresh reduced DARE gains come from the existing actual MuJoCo RK4 runtime.
The two comparison plants instead use exact continuous coupling and transport.
Run: python -m sim.fivebar.delayed_linear --out <fresh-directory>
"""

import argparse
from dataclasses import asdict, replace
import csv
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
import traceback

import mujoco
import numpy as np
import scipy

from sim.augmented import AugmentedRuntime, RuntimeConfig, TIME_EPS
from sim.augmented_lqr import linearize as runtime_linearize, synthesize_augmented
from sim.planar import INPUT_NAMES, STATE_NAMES, load_config
from .linearize import compare_length, difference, positive, zoh


LENGTHS = (.12, .16, .20, .21)
DELAYS = (.002, .003, .004, .005)
DT, LAG = .002, .005
PROJECTION_EPS = (1e-5, 3e-6, 1e-6)
STATE_EPS = INPUT_EPS = (1e-4, 1e-5, 1e-6)
STRESS_MARKER = Path('/private/tmp/wbr-control-margins-20261022/STRESS_FIRST_RUN.json')


def transport_segments(delay, dt):
    """(duration, prior-command index), newest history=1, current command=0.

    For delay >= dt the new command cannot affect this tick's mechanics or
    filter endpoint. An arrival exactly at the end affects the NEXT interval.
    TIME_EPS matches the existing runtime's boundary tolerance, not tick rounding.
    """
    positive(dt)
    positive(delay)
    if delay < dt:
        raise ValueError('This comparison requires transport delay >= control dt')
    history = math.ceil(delay / dt - TIME_EPS)
    arrival = delay - (history - 1) * dt
    if abs(arrival - dt) <= TIME_EPS:
        return history, [(dt, history)]
    return history, [(arrival, history), (dt - arrival, history - 1)]


def exact_lift(Ac, Bc, dt, delay, lag):
    """Exponential hold on [physical x, actuator tau], then history shift.

    Generic n physical coordinates/m torques permits analytic scalar fixtures;
    production uses n=6, m=2 and z=[x,tau,u[k-1],...,u[k-h]]. All are SI units.
    No integration-substep, mean-torque approximation, or DARE is used here.
    """
    Ac, Bc = np.asarray(Ac, float), np.asarray(Bc, float)
    if (Ac.ndim != 2 or Ac.shape[0] != Ac.shape[1] or Bc.ndim != 2 or
            Bc.shape[0] != Ac.shape[0] or Bc.shape[1] == 0 or
            not np.all(np.isfinite(np.r_[Ac.ravel(), Bc.ravel()]))):
        raise ValueError('Expected finite compatible continuous A/B')
    positive(lag)
    h, segments = transport_segments(delay, dt)
    n, m = Bc.shape
    ny, nz = n + m, n + m + m * h
    aa, bb = np.zeros((ny, ny)), np.zeros((ny, m))
    aa[:n, :n], aa[:n, n:] = Ac, Bc
    aa[n:, n:], bb[n:] = -np.eye(m) / lag, np.eye(m) / lag
    # Carry a linear map from original [z,u] through each arrival interval.
    mapping = np.zeros((ny, nz + m))
    mapping[:, :ny] = np.eye(ny)
    arrivals = []
    elapsed = 0.
    for duration, previous in segments:
        selector = np.zeros((m, nz + m))
        offset = ny + (previous - 1) * m if previous else nz
        selector[:, offset:offset + m] = np.eye(m)
        az, bz = zoh(aa, bb, duration)
        mapping = az @ mapping + bz @ selector
        arrivals.append({'start_s': elapsed, 'end_s': elapsed + duration,
                         'prior_command_index': previous,
                         'submitted_s': -previous * dt,
                         'arrives_s': delay - previous * dt})
        elapsed += duration
    full = np.zeros((nz, nz + m))
    full[:ny] = mapping
    full[ny:ny + m, nz:] = np.eye(m)  # New u becomes history item 1.
    if h > 1:
        full[ny + m:nz, ny:nz - m] = np.eye(m * (h - 1))
    return full[:, :nz], full[:, nz:], {
        'continuous_A_augmented': aa.tolist(), 'continuous_B_augmented': bb.tolist(),
        'history_steps': h, 'state_dimension': nz, 'segments': arrivals,
        'method': 'exact expm ZOH per transport arrival; full continuous mechanical/filter coupling',
        'new_command_arrives_s': delay,
    }


def spectrum(A, B, K, dt):
    """All eigenpairs of A-BK; UNSTABLE remains an ordinary reported result."""
    positive(dt)
    A, B, K = np.asarray(A, float), np.asarray(B, float), np.asarray(K, float)
    if (A.ndim != 2 or A.shape[0] != A.shape[1] or B.ndim != 2 or
            B.shape[0] != len(A) or K.shape != (B.shape[1], len(A)) or
            not np.all(np.isfinite(np.r_[A.ravel(), B.ravel(), K.ravel()]))):
        raise ValueError('Incompatible or nonfinite A/B/K')
    matrix = A - B @ K
    values, vectors = np.linalg.eig(matrix)
    order = sorted(range(len(values)), key=lambda i: (values[i].real, values[i].imag))
    values, vectors = values[order], vectors[:, order]
    rho = float(max(abs(values)))
    return {'status': 'STABLE' if rho < 1 else 'UNSTABLE', 'stable': rho < 1,
            'matrix': matrix.tolist(), 'poles_real_imag': np.c_[values.real, values.imag].tolist(),
            'right_eigenvectors_real': vectors.real.tolist(),
            'right_eigenvectors_imag': vectors.imag.tolist(),
            'eigenvector_convention': 'columns match sorted poles; Euclidean unit norm',
            'eigenpair_residual_max_abs': float(np.max(abs(matrix @ vectors - vectors * values))),
            'rho': rho, 'margin_to_unit_circle': 1 - rho,
            'dominant_decay_tau_s': -dt / math.log(rho) if 0 < rho < 1 else None}


def runtime_discrepancy(actual_a, actual_b, exact_a, exact_b, K):
    """Dimensional entry/norm errors; no arbitrary equivalence PASS threshold."""
    return {'A_actual_minus_exact': difference(actual_a, exact_a),
            'B_actual_minus_exact': difference(actual_b, exact_b),
            'closed_loop_actual_minus_exact': difference(
                np.asarray(actual_a) - np.asarray(actual_b) @ K, exact_a - exact_b @ K),
            'note': 'actual runtime holds exact mean torque per mechanical RK4 substep; '
                    'exact lift continuously couples torque and mechanics; raw norms mix units'}


def compare_delay(source, delay, refine_substep=False):
    """One fresh actual-runtime K applied unchanged to both continuous lifts."""
    cfg = source['config']
    selected = source['refinements'][source['selected_refinement']]
    runtime_cfg = RuntimeConfig(delay_s=delay, motor_time_constant_s=(LAG, LAG),
                                body_angle_std_deg=0., body_gyro_std_rad_s=0.)
    nominal_K = np.asarray(source['reduced_synthesis']['K_used'])
    K, design = synthesize_augmented(cfg, runtime_cfg, nominal_K)
    expected_order = [*STATE_NAMES, 'wheel_torque_estimate_Nm', 'hip_torque_estimate_Nm'] + [
        f'previous_{i}_{axis}_command_Nm'
        for i in range(1, math.ceil(delay / DT - TIME_EPS) + 1) for axis in ('wheel', 'hip')]
    if design['state_order'] != expected_order:
        raise ValueError('Actual-runtime DARE state order does not match lifted state')
    result = {'length_m': source['length_m'], 'delay_s': delay, 'control_dt_s': DT,
              'lag_s': LAG, 'config': cfg, 'runtime_config': asdict(runtime_cfg),
              'state_order': expected_order, 'input_order': INPUT_NAMES,
              'state_dimension': len(expected_order), 'feedback': 'u=-Kz',
              'observer': 'exact known matched delay and lag; noiseless six physical states; '
                          'causally reconstructed torques equal physical torques, exact initial state/history',
              'source_selected_refinement': source['selected_refinement'],
              'source_epsilons': {k: selected[k] for k in (
                  'projection_epsilon', 'state_epsilon', 'input_epsilon_Nm')},
              'reduced_actual_synthesis': design, 'plants': {}, 'refinements': []}
    actual_a, actual_b = np.asarray(design['A_discrete_actual']), np.asarray(design['B_discrete_actual'])
    result['plants']['reduced_actual_runtime'] = {
        'A': actual_a.tolist(), 'B': actual_b.tolist(),
        'closed_loop': spectrum(actual_a, actual_b, K, DT)}
    for name in ('reduced', 'fivebar'):
        a, b, metadata = exact_lift(selected['A_' + name], selected['B_' + name], DT, delay, LAG)
        result['plants'][name + '_exact_lift'] = {
            'A': a.tolist(), 'B': b.tolist(), **metadata, 'closed_loop': spectrum(a, b, K, DT)}
    reduced = result['plants']['reduced_exact_lift']
    ar, br = np.asarray(reduced['A']), np.asarray(reduced['B'])
    result['reduced_actual_discrepancy'] = runtime_discrepancy(actual_a, actual_b, ar, br, K)
    for sample in source['refinements']:
        refined = {k: sample[k] for k in ('projection_epsilon', 'state_epsilon', 'input_epsilon_Nm')}
        for name in ('reduced', 'fivebar'):
            a, b, _ = exact_lift(sample['A_' + name], sample['B_' + name], DT, delay, LAG)
            refined[name] = {'A': a.tolist(), 'B': b.tolist(), 'closed_loop': spectrum(a, b, K, DT)}
        result['refinements'].append(refined)
    # Two preselected conditions only; no nonlinear trajectories and no retuning.
    if refine_substep:
        fine_cfg = replace(runtime_cfg, integration_max_step_s=.000125)
        runtime = AugmentedRuntime(cfg, fine_cfg)
        fine_a, fine_b = runtime_linearize(runtime, cfg['simulation']['finite_difference_epsilon'])
        coarse_error = np.linalg.norm(actual_a - ar)
        fine_error = np.linalg.norm(fine_a - ar)
        result['mechanical_substep_refinement'] = {
            'coarse_step_s': runtime_cfg.integration_max_step_s,
            'fine_runtime_config': asdict(fine_cfg), 'same_K_no_retune': True,
            'A_actual_fine': fine_a.tolist(), 'B_actual_fine': fine_b.tolist(),
            'fine_closed_loop': spectrum(fine_a, fine_b, K, DT),
            'fine_discrepancy': runtime_discrepancy(fine_a, fine_b, ar, br, K),
            'coarse_A_error_frobenius': float(coarse_error),
            'fine_A_error_frobenius': float(fine_error),
            'fine_over_coarse_A_error': float(fine_error / coarse_error) if coarse_error else None,
            'error_decreased': bool(fine_error < coarse_error),
            'interpretation': 'two measured substeps; not an asserted asymptotic order or dynamics equivalence'}
    result['status'] = ('STABLE' if all(p['closed_loop']['stable'] for p in result['plants'].values())
                        else 'UNSTABLE')
    return result


def report_markdown(report):
    rows = report['cases']
    lines = ['# Fixed-length local delay/lag comparison', '',
             f"Source `{report['source_commit']}`; {len(rows)} cases; elapsed {report['elapsed_s']:.3f} s.",
             'Fresh reduced actual-runtime DARE per condition, unchanged Q/R; identical K on both exact lifts.',
             'Control 2 ms, transport 2/3/4/5 ms, lag 5 ms; fractional arrivals split exactly. '
             'Exact known matched torque reconstruction and noiseless physical states assumed.', '',
             '| L m | delay ms | dim | reduced exact rho | fivebar rho | 1-rho | tau s | status |',
             '|---:|---:|---:|---:|---:|---:|---:|---|']
    for case in rows:
        r = case['plants']['reduced_exact_lift']['closed_loop']
        f = case['plants']['fivebar_exact_lift']['closed_loop']
        tau = f['dominant_decay_tau_s']
        lines.append(f"| {case['length_m']:.2f} | {1e3*case['delay_s']:.0f} | {case['state_dimension']} | "
                     f"{r['rho']:.9f} | {f['rho']:.9f} | {f['margin_to_unit_circle']:.9f} | "
                     f"{f'{tau:.6f}' if tau is not None else '—'} | {case['status']} |")
    da = max(c['reduced_actual_discrepancy']['A_actual_minus_exact']['max_abs'] for c in rows)
    db = max(c['reduced_actual_discrepancy']['B_actual_minus_exact']['max_abs'] for c in rows)
    spread = max(abs(s['fivebar']['closed_loop']['rho'] - c['plants']['fivebar_exact_lift']['closed_loop']['rho'])
                 for c in rows for s in c['refinements'])
    stable_refinements = all(s[n]['closed_loop']['stable'] for c in rows for s in c['refinements']
                             for n in ('reduced', 'fivebar'))
    lines += ['', f'Actual reduced RK4/mean-torque vs continuous lift: max entry differences A={da:.6g}, '
              f'B={db:.6g} (raw mixed units). These are separate maps.',
              f'All 3 projection × 3 paired state/input epsilon refinements retained: '
              f'all lifted refinements stable={stable_refinements}; max fivebar rho spread={spread:.3g}.']
    for c in rows:
        if 'mechanical_substep_refinement' in c:
            r = c['mechanical_substep_refinement']
            lines.append(f"Substep 0.25→0.125 ms, L={c['length_m']:.2f}, delay={c['delay_s']*1e3:.0f} ms: "
                         f"A Frobenius error {r['coarse_A_error_frobenius']:.6g}→{r['fine_A_error_frobenius']:.6g} "
                         f"(ratio {r['fine_over_coarse_A_error']:.6f}); same K.")
    nominal = ', '.join(f"{s['length_m']:.2f} m: {s['closed_loop']['fivebar_zoh']['rho']:.9f}"
                        for s in report['continuous_sources'])
    lines += ['', 'Separate six-state nominal experiment (no lag/delay, different gain/state): ' + nominal + '.',
              '**Scope:** assumed upright fixed-length local linear stability only; '
              '0.21 m is excluded from the 104° nonlinear start and used only upright. '
              'No nonlinear fivebar balance, saturation/noise robustness, hardware or length-ramp claim. '
              'Margin is radial distance to the unit circle, not gain/phase margin.', '',
              'All matrices, configurations, state orders, gains, eigenpairs, actual-runtime discrepancies, '
              'continuous sources and numerical settings: `comparison.json`; 16 rows/all poles: `metrics.csv`. '
              'Exact command/source/versions/exits: `execution.json`. Seeds: none.']
    return '\n'.join(lines) + '\n'


def write_outputs(report, out):
    (out / 'comparison.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    (out / 'report.md').write_text(report_markdown(report))
    with (out / 'metrics.csv').open('x', newline='') as stream:
        writer = csv.writer(stream)
        names = ('reduced_actual_runtime', 'reduced_exact_lift', 'fivebar_exact_lift')
        metrics = ('rho', 'margin_to_unit_circle', 'dominant_decay_tau_s', 'status', 'poles_real_imag')
        writer.writerow(['length_m', 'delay_s', 'state_dimension', 'status'] +
                        [name + '_' + metric for name in names for metric in metrics])
        for c in report['cases']:
            writer.writerow([c['length_m'], c['delay_s'], c['state_dimension'], c['status']] +
                            [json.dumps(c['plants'][name]['closed_loop'][metric]) for name in names for metric in metrics])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Output exists; choose a fresh exclusive directory')
    if not STRESS_MARKER.is_file():
        parser.error(f'Conductor stress-first marker required: {STRESS_MARKER}')
    marker = json.loads(STRESS_MARKER.read_text())
    root = Path(__file__).resolve().parents[2]
    cfg = load_config(root / 'sim/configs/assumed_planar.json')
    source_status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True).strip()
    if source_status:
        parser.error('Commit source before production; working tree must be clean')
    args.out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    report = {
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
        'source_status': source_status, 'cwd': str(root), 'seed': None,
        'command': shlex.join([sys.executable, '-m', 'sim.fivebar.delayed_linear', *sys.argv[1:]]),
        'output_path': str(args.out.resolve()), 'stress_first_marker': {'path': str(STRESS_MARKER), 'content': marker},
        'versions': {'python': sys.version, 'numpy': np.__version__, 'scipy': scipy.__version__, 'mujoco': mujoco.__version__},
        'thread_environment': {k: os.environ.get(k) for k in (
            'OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'PYTHONDONTWRITEBYTECODE')},
        'settings': {'lengths_m': LENGTHS, 'delays_s': DELAYS, 'control_dt_s': DT, 'lag_s': LAG,
                     'projection_epsilons': PROJECTION_EPS, 'state_epsilons': STATE_EPS,
                     'input_epsilons_Nm': INPUT_EPS, 'equilibrium_tolerance': 1e-7,
                     'mechanical_substep_refinement_conditions': [[.12, .003], [.21, .005]],
                     'reference_config': cfg},
        'continuous_source': 'fresh unchanged sim.fivebar.linearize.compare_length at recorded source commit',
        'continuous_sources': [], 'cases': [],
    }
    receipt = {k: report[k] for k in ('source_commit', 'source_status', 'cwd', 'command', 'versions',
                                     'thread_environment', 'output_path', 'stress_first_marker')}
    try:
        for length in LENGTHS:
            source = compare_length(cfg, length, PROJECTION_EPS, STATE_EPS, INPUT_EPS)
            report['continuous_sources'].append(source)
            if source['status'] != 'valid_local_linearization':
                raise ValueError(f'Invalid continuous source at L={length}: {source["status"]}')
            for delay in DELAYS:
                case = compare_delay(source, delay, (length, delay) in ((.12, .003), (.21, .005)))
                report['cases'].append(case)
                rho = case['plants']['fivebar_exact_lift']['closed_loop']['rho']
                print(f'L={length:.2f}, delay={delay*1e3:.0f} ms, n={case["state_dimension"]}: '
                      f'{case["status"]}, fivebar rho={rho:.9f}', flush=True)
        report['elapsed_s'] = time.monotonic() - start
        write_outputs(report, args.out)
        receipt['exit_code'] = 0  # Computation complete, independent of STABLE/UNSTABLE.
    except Exception:
        receipt['exit_code'] = 1
        receipt['exception'] = traceback.format_exc()
        (args.out / 'partial.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
        raise
    finally:
        receipt['elapsed_s'] = time.monotonic() - start
        (args.out / 'execution.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    print(f'Output: {args.out}', flush=True)


if __name__ == '__main__':
    main()
