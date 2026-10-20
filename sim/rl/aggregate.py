"""Training-seed paired t intervals conditional on the fixed noise panel."""

import numpy as np
from scipy.stats import t

from sim.rl.environment import load_protocol
from sim.rl.metrics import PHYSICAL


COUNTS = ['fall_count', 'training_failure_count', 'numerical_failure_count',
          'other_failure_count', 'unrecovered_count']


def five_seed_interval(values):
    if len(values) != 5:
        raise ValueError('Exactly five training seed slots required; episodes are not replicates')
    if any(v is None for v in values):
        return {'seed_values': values, 'mean': None, 'sample_sd': None, 'ci95': None, 'df': 4,
                'reason': 'At least one seed lacks this physical metric'}
    a = np.asarray(values, float)
    if not np.all(np.isfinite(a)):
        raise ValueError('Nonfinite seed summary')
    mean, sd = np.mean(a, axis=0), np.std(a, axis=0, ddof=1)
    margin = t.ppf(.975, 4) * sd / np.sqrt(5)
    return {'seed_values': values, 'mean': mean.tolist(), 'sample_sd': sd.tolist(),
            'ci95': [(mean - margin).tolist(), (mean + margin).tolist()], 'df': 4}


def summarize(rows):
    result = {'episodes': len(rows), 'success_rate': float(np.mean([r['success'] for r in rows])),
              **{k: sum(r[k] for r in rows) for k in COUNTS}}
    for metric in [*PHYSICAL, 'penalized_recovery_s']:
        vals = [r.get(metric) for r in rows if r.get(metric) is not None]
        available = np.mean(vals, axis=0).tolist() if vals else None
        result[metric] = {'mean': available if len(vals) == len(rows) else None,
                          'available_only_mean': available, 'available_episodes': len(vals),
                          'total_episodes': len(rows)}
    return result


def aggregate(outcomes, policies):
    p = load_protocol()
    conditions = [(d, s['name']) for d in p['plant']['fixed_delays_s'] for s in p['scenarios']]
    panels = [('lqr', None), *[('ppo', seed) for seed in p['training']['policy_seeds']]]
    expected = {(c, seed, d, scenario, n) for c, seed in panels for d, scenario in conditions
                for n in p['evaluation']['noise_seeds']}
    actual = [(r['controller'], r['policy_seed'], r['delay_s'], r['scenario'], r['noise_seed']) for r in outcomes]
    if len(set(actual)) != len(actual) or set(actual) != expected:
        raise ValueError('Missing, duplicated or unexpected held-out episode slots')
    summaries = {}
    for controller, seed in panels:
        name = 'lqr' if seed is None else f'ppo-{seed}'
        summaries[name] = {}
        for delay, scenario in conditions:
            rows = [r for r in outcomes if (r['controller'], r['policy_seed'], r['delay_s'], r['scenario'])
                    == (controller, seed, delay, scenario)]
            summaries[name][f'{round(delay*1000)}ms-{scenario}'] = summarize(rows)
    lqr = summaries['lqr']
    lqr_primary = float(np.mean([v['success_rate'] for v in lqr.values()]))
    seed_primary = [float(np.mean([v['success_rate'] for v in summaries[f'ppo-{s}'].values()])) for s in range(5)]
    primary = five_seed_interval([v - lqr_primary for v in seed_primary])
    paired_conditions = {
        key: five_seed_interval([summaries[f'ppo-{s}'][key]['success_rate'] - lqr[key]['success_rate']
                                 for s in range(5)]) for key in lqr}
    secondary = {}
    for metric in [*PHYSICAL, 'penalized_recovery_s']:
        differences = []
        for seed in range(5):
            terms = []
            for key in lqr:
                if metric == 'peak_tilt_after_push_start_deg' and not key.endswith('push'):
                    continue
                a, b = summaries[f'ppo-{seed}'][key][metric]['mean'], lqr[key][metric]['mean']
                terms.append(None if a is None or b is None else np.asarray(a) - np.asarray(b))
            differences.append(None if any(v is None for v in terms) else np.mean(terms, axis=0).tolist())
        secondary[metric] = five_seed_interval(differences)
    complete = all(policies[s if s in policies else str(s)]['complete'] for s in range(5))
    numerical = sum(r['numerical_failure_count'] for r in outcomes)
    infrastructure = any(r['status'] == 'EVALUATION_FAILED' for r in outcomes)
    eligible = complete and not numerical and not infrastructure
    return {'unit': 'training seed', 'n_training_seed_slots': 5, 'unique_lqr_episodes': 160,
            'ppo_episode_slots': 800, 'all_five_full_budget_policies': complete,
            'training_failure_count': sum(not policies[s if s in policies else str(s)]['complete'] for s in range(5)),
            'missing_policy_episode_slots': sum(r['training_failure_count'] for r in outcomes),
            'primary_ppo_success_rates': seed_primary, 'lqr_success_rate': lqr_primary,
            'primary_paired_ppo_minus_lqr': primary, 'condition_paired_differences_descriptive': paired_conditions,
            'secondary_paired_differences_descriptive': secondary, 'panels': summaries,
            'failure_counts_all_outcomes': {k: sum(r[k] for r in outcomes) for k in COUNTS},
            'claim_eligible': eligible, 'rl_superiority_supported': bool(eligible and primary['ci95'][0] > 0),
            'interval_scope': p['aggregation']['interval_scope'],
            'lqr_uncertainty': 'One shared fixed noise panel; no training-seed variance estimate',
            'missing_metric_rule': 'All-slot means null if any episode lacks data; available-only means retain denominators',
            'caution': 'ASSUMED simulation only. No hardware, sim-to-real or universal robustness claim.'}
