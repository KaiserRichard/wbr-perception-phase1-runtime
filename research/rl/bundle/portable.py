"""Offline G1 dispatch. The v2 benchmark is no longer the bundle entry point."""
import argparse
from contextlib import contextmanager
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'source'))


@contextmanager
def one_job():
    folder=ROOT/'runs'
    folder.mkdir(parents=True,exist_ok=True)
    with (folder/'g1-cpu.lock').open('a+b') as lock:
        if os.name=='nt':
            import msvcrt
            lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['smoke','run','train','resume-latest'])
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--smoke-seconds',type=float,default=600)
    parser.add_argument('--jobs',type=int)
    parser.add_argument('--seed-wall-cap-min',type=float)
    args=parser.parse_args()
    from sim.rl.g1.runner import full,smoke
    if args.mode=='smoke':
        smoke(args.run,args.smoke_seconds,jobs=args.jobs)
    elif args.mode=='resume-latest':
        # Resume the whole queue, never accidentally select smoke/pilot checkpoints.
        candidates=[p for p in args.run.glob('g1-*') if p.is_dir() and not p.name.startswith('g1-smoke-')]
        if not candidates:raise RuntimeError('No G1 queue on USB')
        full(max(candidates,key=lambda p:p.stat().st_mtime_ns),jobs=args.jobs,
             seed_wall_cap_min=args.seed_wall_cap_min)
    else:
        full(args.run,jobs=args.jobs,seed_wall_cap_min=args.seed_wall_cap_min)

if __name__=='__main__':
    with one_job():main()
