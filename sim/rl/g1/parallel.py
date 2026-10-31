"""Spawned, single-thread workers with results restored to input order."""
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
import os


def default_jobs():
    return max(1, min(5, (os.cpu_count() or 1)//2))


def jobs_count(value):
    value = int(value)
    if value < 1:
        raise ValueError('--jobs must be at least 1')
    return value


def one_thread():
    # __init__ sets these before numerical imports; repeat for API callers and
    # descendants. Spawn inherits them before importing NumPy/BLAS/PyTorch.
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    import torch
    torch.set_num_threads(1)


def ordered_map(function, tasks, jobs=None, on_error=None):
    tasks = list(tasks)
    jobs = jobs_count(default_jobs() if jobs is None else jobs)
    one_thread()
    if jobs == 1 or len(tasks) <= 1:
        return [function(task) for task in tasks]
    with ProcessPoolExecutor(max_workers=min(jobs, len(tasks)),
                             mp_context=mp.get_context('spawn'),
                             initializer=one_thread) as pool:
        futures = {pool.submit(function, task): i for i, task in enumerate(tasks)}
        results = [None]*len(tasks)
        try:
            for future in as_completed(futures):
                results[futures[future]] = future.result()
        except BaseException:
            for future in futures:
                future.cancel()
            if on_error is not None:
                on_error()
            raise
    return results
