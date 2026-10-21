"""Local fixed-length linear comparison; no rollout, gain fit, or retuning.

Run as ``python -m sim.fivebar.linearize --out <fresh-directory>``.
The reduced controller is synthesized from its actual held-control mj_step;
both continuous plants use matched ZOH for the transfer comparison.
"""

import argparse
import csv
import json
import math
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

import mujoco
import numpy as np
import scipy
from scipy.linalg import expm

from sim.gain_schedule.model import config_at_length
from sim.lqr import synthesize
from sim.planar import INPUT_NAMES, STATE_NAMES, TO_JOINT, Plant as ReducedPlant, load_config
from .compare import FixedLength, full_mass
from .geometry import GeometryError
from .model import Plant


class EquilibriumError(ValueError):
    """A derivative at the requested operating point is too large or nonfinite."""


def positive(value):
    if not math.isfinite(value) or value <= 0:
        raise ValueError('Expected positive finite numerical setting')
    return value


def equilibrium(function, tolerance=1e-7):
    """Check zero state/input without subtracting a bias from the derivative.

    The componentwise absolute tolerance is in [m/s,rad/s,rad/s,m/s²,rad/s²,rad/s²].
    It is a numerical equilibrium tolerance, not a physical balance criterion.
    """
    positive(tolerance)
    residual = np.asarray(function(np.zeros(6), np.zeros(2)), dtype=float)
    if residual.shape != (6,):
        raise ValueError('Derivative must return six state derivatives')
    finite = bool(np.all(np.isfinite(residual)))
    valid = finite and bool(np.max(np.abs(residual)) <= tolerance)
    return {'valid': valid, 'derivative': [float(v) if math.isfinite(v) else None for v in residual],
            'max_abs': float(np.max(np.abs(residual))) if finite else None,
            'componentwise_tolerance': tolerance}


def linearize(function, state_epsilon, input_epsilon, equilibrium_tolerance=1e-7):
    """Centered SI-coordinate differences at genuine zero-state/input equilibrium."""
    positive(state_epsilon)
    positive(input_epsilon)
    residual = equilibrium(function, equilibrium_tolerance)
    if not residual['valid']:
        raise EquilibriumError(f'Invalid zero equilibrium: {residual}')
    state, control = np.zeros(6), np.zeros(2)
    A = np.column_stack([(function(state + dx, control) - function(state - dx, control)) /
                         (2 * state_epsilon) for dx in state_epsilon * np.eye(6)])
    B = np.column_stack([(function(state, control + du) - function(state, control - du)) /
                         (2 * input_epsilon) for du in input_epsilon * np.eye(2)])
    if A.shape != (6, 6) or B.shape != (6, 2) or not np.all(np.isfinite(np.r_[A.ravel(), B.ravel()])):
        raise ValueError('Invalid finite-difference matrices')
    return A, B


def zoh(A, B, dt):
    """Exact zero-order hold via block exponential, including singular A."""
    positive(dt)
    A, B = np.asarray(A, float), np.asarray(B, float)
    if A.ndim != 2 or A.shape[0] != A.shape[1] or B.ndim != 2 or B.shape[0] != A.shape[0]:
        raise ValueError('Incompatible A/B shapes')
    if not np.all(np.isfinite(np.r_[A.ravel(), B.ravel()])):
        raise ValueError('Nonfinite A/B')
    n, m = B.shape
    block = np.zeros((n + m, n + m))
    block[:n, :n], block[:n, n:] = A, B
    discrete = expm(dt * block)
    return discrete[:n, :n], discrete[:n, n:]


def difference(candidate, reference):
    """Raw dimensional metrics, not invariant to state/unit rescaling."""
    candidate, reference = np.asarray(candidate), np.asarray(reference)
    delta = candidate - reference
    norm = float(np.linalg.norm(reference))
    return {'difference': delta.tolist(), 'max_abs': float(np.max(np.abs(delta))),
            'relative_frobenius': float(np.linalg.norm(delta) / norm) if norm else None,
            'max_abs_by_row': np.max(np.abs(delta), axis=1).tolist()}


def closed_loop(A, B, K, dt):
    """Sampled u=-Kx; margin is 1-rho, NOT a gain or phase margin."""
    positive(dt)
    A, B, K = np.asarray(A, float), np.asarray(B, float), np.asarray(K, float)
    if A.shape != (6, 6) or B.shape != (6, 2) or K.shape != (2, 6):
        raise ValueError('Expected A(6,6), B(6,2), K(2,6) in declared state/input order')
    if not np.all(np.isfinite(np.r_[A.ravel(), B.ravel(), K.ravel()])):
        raise ValueError('Nonfinite closed-loop matrices')
    matrix = A - B @ K
    poles = sorted(np.linalg.eigvals(matrix), key=lambda p: (float(p.real), float(p.imag)))
    rho = float(max(abs(p) for p in poles))
    return {'matrix': matrix.tolist(), 'poles_real_imag': [[float(p.real), float(p.imag)] for p in poles],
            'rho': rho, 'margin_to_unit_circle': 1 - rho, 'stable': rho < 1,
            'dominant_decay_tau_s': -dt / math.log(rho) if 0 < rho < 1 else None}


def mechanics(reduced, fixed):
    """M qdd = G u - b; distinguish G from B_acc=M^-1 G."""
    state, zero = np.zeros(6), np.zeros(2)
    mf, bf, _ = fixed.terms(state, zero)
    gf = np.column_stack([fixed.terms(state, u)[2] for u in np.eye(2)])
    d = reduced.data(state)
    mr, br = TO_JOINT.T @ full_mass(reduced.model, d) @ TO_JOINT, TO_JOINT.T @ d.qfrc_bias
    columns = []
    for u in np.eye(2):
        reduced.forward(d, u)
        columns.append(TO_JOINT.T @ d.qfrc_actuator)
    gr = np.column_stack(columns)
    ar, af, hybrid = np.linalg.solve(mr, gr), np.linalg.solve(mf, gf), np.linalg.solve(mf, gr)
    return {'reduced_mass': mr.tolist(), 'fivebar_mass': mf.tolist(),
            'reduced_bias': br.tolist(), 'fivebar_bias': bf.tolist(),
            'reduced_generalized_input_map': gr.tolist(), 'fivebar_generalized_input_map': gf.tolist(),
            'reduced_acceleration_input_jacobian': ar.tolist(),
            'fivebar_acceleration_input_jacobian': af.tolist(),
            'mass_difference': difference(mf, mr), 'generalized_input_difference': difference(gf, gr),
            'acceleration_input_difference': difference(af, ar),
            'mass_effect_at_reduced_map': (hybrid - ar).tolist(),
            'map_effect_at_fivebar_mass': np.linalg.solve(mf, gf - gr).tolist(),
            'decomposition': '(Mf^-1-Mr^-1) Gr + Mf^-1 (Gf-Gr); path-dependent attribution',
            'mass_eigenvalues': {'reduced': np.linalg.eigvalsh(mr).tolist(),
                                 'fivebar': np.linalg.eigvalsh(mf).tolist()}}


def compare_length(reference, length, projection_epsilons, state_epsilons, input_epsilons,
                   equilibrium_tolerance=1e-7):
    cfg = config_at_length(reference, length)
    if (cfg['controller']['solver'] != 'DARE' or cfg['simulation']['dt_s'] != .002 or
            cfg['controller']['state_order'] != STATE_NAMES or cfg['controller']['input_order'] != INPUT_NAMES):
        raise ValueError('Requires existing DARE, 2 ms, six-state/two-input convention')
    if len(state_epsilons) != len(input_epsilons) or not state_epsilons or not projection_epsilons:
        raise ValueError('Need paired state/input refinements and projection epsilons')
    for value in [*projection_epsilons, *state_epsilons, *input_epsilons, equilibrium_tolerance]:
        positive(value)
    result = {'length_m': length, 'config': cfg, 'status': 'pending', 'refinements': []}
    # Preserve geometry and equilibrium rejection; do not move or debias the point.
    try:
        full, reduced = Plant(cfg), ReducedPlant(cfg)
        coordinates = np.array([0., 0., 0., length])
        angles = full.geometry.inverse(length, math.pi / 2)
        cartesian, virtual = full.geometry.jacobians(angles)
        result['geometry'] = {'motor_angles_rad': angles.tolist(),
                              'cartesian_jacobian': cartesian.tolist(), 'virtual_jacobian': virtual.tolist(),
                              'virtual_jacobian_singular_values_mixed_units': np.linalg.svd(virtual, compute_uv=False).tolist(),
                              'closure_m': full.closure_error(full.data(coordinates))}
        result['equilibrium'] = {'reduced': equilibrium(reduced.derivative, equilibrium_tolerance), 'fivebar': []}
        for pe in projection_epsilons:
            fixed = FixedLength(full, pe)
            result['equilibrium']['fivebar'].append({'projection_epsilon': pe,
                                                     **equilibrium(fixed.derivative, equilibrium_tolerance)})
        eqs = [result['equilibrium']['reduced'], *result['equilibrium']['fivebar']]
        if not all(e['valid'] for e in eqs):
            result['status'] = 'invalid_equilibrium'
            return result

        # Required order: continuous A/B comparison first, then reduced gain transfer.
        reduced_matrices = [linearize(reduced.derivative, se, ie, equilibrium_tolerance)
                            for se, ie in zip(state_epsilons, input_epsilons)]
        for pe in projection_epsilons:
            fixed = FixedLength(full, pe)
            for index, (se, ie) in enumerate(zip(state_epsilons, input_epsilons)):
                ar, br = reduced_matrices[index]
                af, bf = linearize(fixed.derivative, se, ie, equilibrium_tolerance)
                result['refinements'].append({'projection_epsilon': pe, 'state_epsilon': se, 'input_epsilon_Nm': ie,
                                              'A_reduced': ar.tolist(), 'B_reduced': br.tolist(),
                                              'A_fivebar': af.tolist(), 'B_fivebar': bf.tolist()})
        selected = result['refinements'][-1]
        ar, br, af, bf = [np.asarray(selected[key]) for key in ('A_reduced', 'B_reduced', 'A_fivebar', 'B_fivebar')]
        result['selected_refinement'] = len(result['refinements']) - 1
        result['continuous_difference'] = {'A': difference(af, ar), 'B': difference(bf, br)}
        result['mechanics'] = mechanics(reduced, FixedLength(full, projection_epsilons[-1]))
        result['acceleration_jacobian_check'] = {
            'reduced': difference(br[3:], result['mechanics']['reduced_acceleration_input_jacobian']),
            'fivebar': difference(bf[3:], result['mechanics']['fivebar_acceleration_input_jacobian'])}
        K, design = synthesize(reduced)  # Fresh existing reduced DARE; Q/R unchanged.
        result['reduced_synthesis'] = design
        dt = cfg['simulation']['dt_s']
        arz, brz = zoh(ar, br, dt)
        afz, bfz = zoh(af, bf, dt)
        result['zoh'] = {'A_reduced': arz.tolist(), 'B_reduced': brz.tolist(),
                         'A_fivebar': afz.tolist(), 'B_fivebar': bfz.tolist()}
        result['closed_loop'] = {
            'reduced_actual_step': closed_loop(design['A_discrete_actual'], design['B_discrete_actual'], K, dt),
            'reduced_zoh': closed_loop(arz, brz, K, dt), 'fivebar_zoh': closed_loop(afz, bfz, K, dt)}
        result['reduced_actual_step_minus_selected_zoh'] = {
            'A': difference(design['A_discrete_actual'], arz), 'B': difference(design['B_discrete_actual'], brz)}
        for sample in result['refinements']:
            sample['difference_from_selected'] = {key: difference(sample[key], selected[key])
                                                  for key in ('A_reduced', 'B_reduced', 'A_fivebar', 'B_fivebar')}
            az, bz = zoh(sample['A_fivebar'], sample['B_fivebar'], dt)
            sample['fivebar_zoh_with_reduced_K'] = closed_loop(az, bz, K, dt)
        result['status'] = 'valid_local_linearization'
    except GeometryError as exc:
        result.update(status='rejected_geometry', error=str(exc))
    except EquilibriumError as exc:
        result.update(status='invalid_equilibrium', error=str(exc))
    return result


def pole_text(record):
    return ', '.join(f'{r:.9f}{i:+.9f}j' if abs(i) > 1e-12 else f'{r:.9f}'
                     for r, i in record['poles_real_imag'])


def report_markdown(report):
    lines = ['# Fixed-length local linear comparison', '',
             'ASSUMED mechanics only; no nonlinear, contact, hardware, delay or policy-transfer claim.',
             f"Source `{report['source_commit']}` (working-tree changes: {bool(report['source_status'])}); deterministic (no random seed). dt=0.002 s; u=-Kx.",
             'State [x, theta, phi, xdot, thetadot, phidot] uses m, rad, s; inputs [Tw, Th] are aggregate N m.',
             'Fresh existing reduced DARE uses actual held-control MuJoCo RK4 step and dt Q, dt R; both continuous plants use matched ZOH below.',
             'config_at_length keeps masses fixed, scales reduced leg COM by L/L0 and inertia by (L/L0)^2. Fivebar retains four equal rods (leg_mass/4 each), fixed inventory link lengths and 0.006 m inertial radius; it does not consume scaled equivalent-leg COM/inertia. Body/wheel parameters and Q/R match.',
             '', '| L (m) | reduced actual rho | reduced ZOH rho | fivebar ZOH rho | 1-rho | tau (s) |',
             '|---|---:|---:|---:|---:|---:|']
    valid = [case for case in report['lengths'] if case['status'] == 'valid_local_linearization']
    for case in report['lengths']:
        if case['status'] != 'valid_local_linearization':
            lines.append(f"| {case['length_m']:.2f} | {case['status']} | | | | |")
            continue
        cr, rz, fz = [case['closed_loop'][key] for key in ('reduced_actual_step', 'reduced_zoh', 'fivebar_zoh')]
        tau = f"{fz['dominant_decay_tau_s']:.6f}" if fz['dominant_decay_tau_s'] is not None else 'n/a'
        lines.append(f"| {case['length_m']:.2f} | {cr['rho']:.9f} | {rz['rho']:.9f} | {fz['rho']:.9f} | {fz['margin_to_unit_circle']:.9f} | {tau} |")
    lines += ['', 'All six fivebar ZOH poles (reduced actual/ZOH poles also retained in metrics.csv and JSON):', '']
    for case in valid:
        lines.append(f"- L={case['length_m']:.2f}: [{pole_text(case['closed_loop']['fivebar_zoh'])}].")
    lines += ['', '| L | rel A / max abs | rel B / max abs | max equilibrium residual | step-ZOH max A / B |',
              '|---|---:|---:|---:|---:|']
    for case in valid:
        a, b = [case['continuous_difference'][key] for key in ('A', 'B')]
        da, db = [case['reduced_actual_step_minus_selected_zoh'][key]['max_abs'] for key in ('A', 'B')]
        residual = max(e['max_abs'] for e in [case['equilibrium']['reduced'], *case['equilibrium']['fivebar']])
        lines.append(f"| {case['length_m']:.2f} | {a['relative_frobenius']:.6g} / {a['max_abs']:.6g} | {b['relative_frobenius']:.6g} / {b['max_abs']:.6g} | {residual:.3g} | {da:.3g} / {db:.3g} |")
    lines += ['', 'Relative Frobenius/max norms mix units and depend on coordinate scaling; they are not physical percentage errors. The previously noted wheel reaction split is a generalized torque-map difference, not a 17% full B error. JSON/CSV give M, G and actual B_acc=M^-1 G, plus the exact mass/map decomposition (path-dependent). Margin means distance 1-rho, not classical gain/phase margin; tau=-dt/log(rho) is the slowest sampled decay envelope.',
              f"Projection eps {report['settings']['projection_epsilons']}; paired state eps {report['settings']['state_epsilons']} and input eps {report['settings']['input_epsilons_Nm']}. Last listed values select the reported matrices; JSON retains every refinement, residual and pole. No equilibrium bias subtraction."]
    if valid:
        spread = max(abs(sample['fivebar_zoh_with_reduced_K']['rho'] - case['closed_loop']['fivebar_zoh']['rho'])
                     for case in valid for sample in case['refinements'])
        lines.append(f"All {len(valid)} accepted lengths and all their refinements stable: {all(s['fivebar_zoh_with_reduced_K']['stable'] for c in valid for s in c['refinements'])}; max refinement rho deviation {spread:.3g}. Geometry rejections remain explicit.")
        refinements = {key: max(s['difference_from_selected'][key]['max_abs'] for c in valid for s in c['refinements'])
                       for key in ('A_fivebar', 'B_fivebar')}
        lines.append(f"Max fivebar refinement entry differences: A {refinements['A_fivebar']:.3g}, B {refinements['B_fivebar']:.3g} (mixed units). Nested finite differences show numerical spread, not a monotonic convergence/order claim.")
    lines += ['', f"Exact run: `{report['command']}`. Seeds: none. Configs, source, numerical versions/settings and all matrices are retained in comparison.json."]
    return '\n'.join(lines) + '\n'


def write_outputs(report, out):
    (out / 'comparison.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    (out / 'report.md').write_text(report_markdown(report))
    with (out / 'metrics.csv').open('x', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['length_m', 'status', 'model', 'rho', 'margin_to_unit_circle', 'dominant_decay_tau_s', 'poles_real_imag'])
        for case in report['lengths']:
            if 'closed_loop' not in case:
                writer.writerow([case['length_m'], case['status'], '', '', '', '', ''])
            for name, item in case.get('closed_loop', {}).items():
                writer.writerow([case['length_m'], case['status'], name, item['rho'], item['margin_to_unit_circle'],
                                 item['dominant_decay_tau_s'], json.dumps(item['poles_real_imag'])])
    with (out / 'acceleration-inputs.csv').open('x', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['length_m', 'model', 'acceleration', 'unit_per_Nm', 'Tw', 'Th'])
        for case in report['lengths']:
            for name in ('reduced', 'fivebar') if 'mechanics' in case else ():
                for index, row in enumerate(case['mechanics'][name + '_acceleration_input_jacobian']):
                    writer.writerow([case['length_m'], name, ['xddot', 'thetaddot', 'phiddot'][index],
                                     ['m/s^2/(N m)', 'rad/s^2/(N m)', 'rad/s^2/(N m)'][index], *row])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(__file__).parents[1] / 'configs/assumed_planar.json')
    parser.add_argument('--lengths', type=float, nargs='+', default=[.12, .16, .20, .21])
    parser.add_argument('--projection-epsilons', type=float, nargs='+', default=[1e-5, 3e-6, 1e-6])
    parser.add_argument('--state-epsilons', type=float, nargs='+', default=[1e-4, 1e-5, 1e-6])
    parser.add_argument('--input-epsilons', type=float, nargs='+', default=[1e-4, 1e-5, 1e-6])
    parser.add_argument('--equilibrium-tolerance', type=float, default=1e-7)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    cfg = load_config(args.config)
    if args.out.exists():
        parser.error('Output already exists; choose a fresh exclusive directory')
    args.out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    root = Path(__file__).resolve().parents[2]
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    report = {'source_commit': commit,
              'source_status': subprocess.check_output(['git', 'status', '--short'], cwd=root, text=True).strip(),
              'command': shlex.join([sys.executable, '-m', 'sim.fivebar.linearize', *sys.argv[1:]]),
              'cwd': str(root), 'seed': None, 'output_path': str(args.out.resolve()),
              'versions': {'python': sys.version, 'numpy': np.__version__, 'scipy': scipy.__version__, 'mujoco': mujoco.__version__},
              'thread_environment': {key: os.environ.get(key) for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'PYTHONDONTWRITEBYTECODE')},
              'settings': {'projection_epsilons': args.projection_epsilons, 'state_epsilons': args.state_epsilons,
                           'input_epsilons_Nm': args.input_epsilons, 'equilibrium_tolerance': args.equilibrium_tolerance},
              'conventions': {'state': ['x', 'theta', 'phi', 'xdot', 'thetadot', 'phidot'],
                              'state_units': ['m', 'rad', 'rad', 'm/s', 'rad/s', 'rad/s'],
                              'input': ['Tw', 'Th'], 'input_units': ['N m', 'N m'],
                              'angles': 'absolute, upright zero, positive pitch moves COM toward +x',
                              'feedback': 'u=-Kx; aggregate pair torques; positive Th does work Th*(phidot-thetadot)',
                              'wheel': 'positive Tw gives +Tw/r axle force; reaction on reduced virtual leg or fivebar distal left link',
                              'mass_units': [['kg', 'kg m', 'kg m'], ['kg m', 'kg m^2', 'kg m^2'], ['kg m', 'kg m^2', 'kg m^2']],
                              'G_row_units_per_Nm': ['1/m', '1', '1'],
                              'B_acc_row_units_per_Nm': ['m/s^2/(N m)', 'rad/s^2/(N m)', 'rad/s^2/(N m)'],
                              'A_units': 'state derivative row unit / state column unit',
                              'B_units': 'state derivative row unit / (N m)',
                              'difference_caveat': 'raw mixed-unit norms depend on coordinate scaling'},
              'lengths': []}
    for length in args.lengths:
        case = compare_length(cfg, length, args.projection_epsilons, args.state_epsilons,
                              args.input_epsilons, args.equilibrium_tolerance)
        report['lengths'].append(case)
        print(f"L={length:.3f}: {case['status']} " +
              (f"fivebar rho={case['closed_loop']['fivebar_zoh']['rho']:.9f}" if 'closed_loop' in case else str(case.get('error', case.get('equilibrium')))), flush=True)
    report['elapsed_s'] = time.monotonic() - started
    write_outputs(report, args.out)
    print(f'Output: {args.out}', flush=True)


if __name__ == '__main__':
    main()
