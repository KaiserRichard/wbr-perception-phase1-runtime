import json
from pathlib import Path
import time
from sim.rl.g1.evaluation import evaluate
from sim.rl.g1.protocol import panel, write_json

if __name__ == '__main__':
    cases = panel(True)[::4]  # One existing development case at each frozen delay.
    run = Path('/private/tmp/wbr-g1-par-20261031-run2/seed-0')
    started = time.monotonic()
    baseline = evaluate(cases, jobs=5)
    policy = evaluate(cases, run, jobs=5)
    receipt = dict(jobs=5, development_only=True, counts_as_final=False,
                   cases=cases, baseline=baseline, policy=policy,
                   elapsed_s=time.monotonic()-started,
                   projected_1200_case_s=40*(baseline['elapsed_s']+5*policy['elapsed_s']))
    write_json('/private/tmp/wbr-g1-par-evaluation.json', receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('baseline','policy')}), flush=True)
