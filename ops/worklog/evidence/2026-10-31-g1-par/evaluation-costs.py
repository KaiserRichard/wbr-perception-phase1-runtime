import json
from pathlib import Path
import time
from sim.rl.g1.evaluation import evaluate
from sim.rl.g1.parallel import ordered_map
from sim.rl.g1.protocol import panel, write_json


def timed_case(task):
    case, run = task
    began = time.monotonic()
    result = evaluate([case], run, jobs=1)
    return dict(case=case, simulation_and_inference_s=result['elapsed_s'],
                load_and_case_s=time.monotonic()-began,
                duration_s=result['rows'][0]['duration_s'])


if __name__ == '__main__':
    cases = panel(True)[::4]
    run = Path('/private/tmp/wbr-g1-par-20261031-run2/seed-0')
    results = {}
    for arm, checkpoint in [('baseline', None), ('policy', run)]:
        began = time.monotonic()
        costs = ordered_map(timed_case, [(c, checkpoint) for c in cases], jobs=5)
        elapsed = time.monotonic()-began
        # 200 cases/5 workers=40 cases each, one startup/load per worker.
        per_case = max(c['simulation_and_inference_s'] for c in costs)
        results[arm] = dict(costs=costs, five_case_wall_s=elapsed,
                            projected_200_case_wall_s=elapsed+39*per_case)
    results['projected_1200_case_s'] = results['baseline']['projected_200_case_wall_s']+5*results['policy']['projected_200_case_wall_s']
    results.update(jobs=5, development_only=True, counts_as_final=False,
                   method='Pool startup/load once per controller + 40 cases per worker; worst of five measured development delays')
    write_json('/private/tmp/wbr-g1-par-evaluation-costs.json', results)
    print(json.dumps(results), flush=True)
