"""Preregistered original-reference metrics, including failed cases."""
import numpy as np
from scipy.stats import t as student_t
from .protocol import DT, POLICY_DT, TOL, DELAYS


def recovery(times, within, event):
    count = 0
    for time, ok in zip(times, within):
        if time < event-1e-9:
            continue
        count = count+1 if ok else 0
        # Consecutive sample endpoints span a complete continuous held tick window.
        if count >= 501:
            return float(time-event)
    return None


def episode_metrics(env):
    times = np.array([r[0] for r in env.samples])
    e = np.array([r[1] for r in env.samples])
    requests = np.array([r[2] for r in env.samples])
    torque = np.array([r[3] for r in env.samples])
    within = np.all(abs(e) <= TOL+1e-12, axis=1)
    complete = bool(times[-1] >= 10-1e-9 and not env.failed)
    rec = [recovery(times, within, event) for event in (0., 3.15)]
    deadline = all(r is not None and r <= 5+1e-9 for r in rec)
    final = times >= (9 if env.case['command'] == 0 else 8)-1e-9
    precision_window = times >= 8-1e-9
    # No survivor-only means: missing final-window precision propagates as unavailable.
    E = float(np.mean(np.mean((e[precision_window]/TOL)**2, axis=1))) if complete else None
    rmse = np.sqrt(np.mean(e[final]**2, axis=0)) if np.any(final) else np.full(6, np.inf)
    if env.case['command'] == 0:
        strict_window = bool(np.any(final) and np.all(within[final]))
    else:
        strict_window = bool(np.any(final) and rmse[0] <= .02 and rmse[1] <= .03 and
                             np.all(np.max(abs(e[final, 2:]), axis=0) <= TOL[2:]+1e-12))
    a = np.array(env.actions)
    limits = env.runtime.limits
    caps = bool(np.all(abs(requests) <= limits+1e-12) and np.all(abs(torque) <= limits+1e-12) and
                (not len(a) or (np.all(abs(a[:, 1]) <= .03+1e-12) and
                 np.all(abs(a[:, 2]) <= .2+1e-12) and
                 np.all(abs(np.diff(np.r_[0., a[:, 1]]))/POLICY_DT <= .1+1e-10))))
    return dict(survived=complete, strict=bool(complete and strict_window and deadline and caps),
                numerical_failure=env.numerical, collision=env.collision, caps_respected=caps,
                E=E, E_observed=float(np.mean(np.mean((e/TOL)**2, axis=1))),
                final_window_complete=complete, recovery_s=rec,
                x_rmse=float(rmse[0]) if np.isfinite(rmse[0]) else None,
                v_rmse=float(rmse[1]) if np.isfinite(rmse[1]) else None,
                peak_angles_rates=np.max(abs(e[:, 2:]), axis=0).tolist(),
                effort_Nm2_s=float(sum(r[4] for r in env.samples)),
                peak_torque_Nm=np.max(abs(torque), axis=0).tolist(),
                saturation_channel_seconds=float(sum(r[5] for r in env.samples)),
                torque_slew_500hz_peak=float(np.max(abs(np.diff(torque, axis=0)))/DT) if len(torque)>1 else 0.,
                request_slew_100hz_peak=float(np.max(abs(np.diff(np.r_[0., a[:, 1]])))/POLICY_DT) if len(a) else 0.,
                rejected_requests=env.rejects, clipped_requests=env.clips, actuator_clipped_ticks=env.actuator_clips,
                action_mean=float(np.mean(a[:, 0])) if len(a) else 0.,
                action_sd=float(np.std(a[:, 0])) if len(a) else 0., duration_s=float(times[-1]))


def strata(rows):
    groups = {'overall': rows, 'reference': [r for r in rows if r['case']['delay_s'] <= .005],
              'difficult': [r for r in rows if r['case']['delay_s'] > .005]}
    groups.update({f'{d}ms': [r for r in rows if abs(r['case']['delay_s']-d/1000)<1e-9] for d in DELAYS})
    result = {}
    for name, group in groups.items():
        if not group:
            continue
        result[name] = dict(n=len(group), strict=float(np.mean([r['strict'] for r in group])),
                            survival=float(np.mean([r['survived'] for r in group])),
                            failed=sum(not r['survived'] for r in group),
                            strict_failed=sum(not r['strict'] for r in group),
                            numerical_failures=sum(r['numerical_failure'] for r in group),
                            E=float(np.mean([r['E'] for r in group])) if all(r['E'] is not None for r in group) else None,
                            E_observed_all_cases=float(np.mean([r['E_observed'] for r in group])))
    return result


def compare(baseline, policies):
    if len(baseline) != 200 or len(policies) != 5 or any(len(p)!=200 for p in policies):
        raise ValueError('Final endpoint requires baseline200 and five independent seed panels200')
    if any([r['case'] for r in p] != [r['case'] for r in baseline] for p in policies):
        raise ValueError('Cases must be paired in frozen order')
    A, B = strata(baseline), [strata(p) for p in policies]
    diff = np.array([s['difficult']['strict']-A['difficult']['strict'] for s in B])
    mean = float(np.mean(diff)); half = float(student_t.ppf(.975, 4)*np.std(diff, ddof=1)/np.sqrt(5))
    engineering = [bool(s['overall']['strict'] >= .95 and s['overall']['survival'] >= .95 and
                        all(s[f'{d}ms']['strict'] >= A[f'{d}ms']['strict']-.05-1e-12 for d in DELAYS) and
                        all(r['caps_respected'] and not r['numerical_failure'] for r in p))
                   for s, p in zip(B, policies)]
    regressions = all(s[k]['strict'] >= A[k]['strict']-.05-1e-12 for s in B for k in ('overall','reference'))
    valid = not any(r['numerical_failure'] for rows in [baseline, *policies] for r in rows)
    ceiling = all(A[f'{d}ms']['strict'] >= .95 for d in DELAYS)
    return dict(baseline=A, seeds={str(i):s for i,s in enumerate(B)}, seed_differences=diff.tolist(),
                mean_difficult_gain=mean, paired_seed_t95=[mean-half, mean+half], df=4,
                engineering_per_seed=engineering, valid=valid, baseline_ceiling=ceiling,
                pass_endpoint=bool(valid and not ceiling and all(engineering) and regressions and mean>=.1-1e-12 and mean-half>0),
                limitation='Five seed-level differences share a baseline; interval is imprecise.')
