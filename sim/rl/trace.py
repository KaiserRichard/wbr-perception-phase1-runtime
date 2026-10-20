"""Lossless float64 NPZ chunks, including all actual integration substeps.

Control rows carry both endpoints, so auto-reset and partial last episodes lose
no terminal observation. Policy actions are attached before the next row flush.
No diagnostic field is returned to the actor or critic.
"""

import json
from pathlib import Path

import numpy as np

from sim.rl.environment import encode_observation
from sim.rl.provenance import sha256, write_json


SEGMENT_COLUMNS = ['time_s', 'dt_s', *[f'truth_{i}' for i in range(6)],
                   'torque_start_w', 'torque_start_h', 'torque_end_w', 'torque_end_h',
                   'applied_mean_w', 'applied_mean_h', 'effort_integral_w', 'effort_integral_h',
                   'delayed_w', 'delayed_h', 'source_submitted_s', 'push_N']


class TraceRecorder:
    def __init__(self, out, protocol, chunk_size=1000):
        self.out = Path(out)
        self.out.mkdir(parents=True, exist_ok=False)
        self.protocol, self.chunk_size = protocol, chunk_size
        self.rows, self.segments, self.chunks = [], [], []
        self.total_steps = 0
        self.episode = -1
        self.closed = False
        self.episodes = (self.out / 'episodes.jsonl').open('x')
        write_json(self.out / 'schema.json', {
            'version': 1, 'segment_columns': SEGMENT_COLUMNS,
            'segment_offsets': 'Local half-open row range for each control transition',
            'policy_action_raw': 'Unclipped Gaussian sample during training; Gaussian mean during deterministic evaluation',
            'env_input_action': 'Action received by Gym (already clipped by SB3 during training)',
            'missing_raw': 'raw_action_available=false and NaNs only in raw action slots',
            'endpoints': 'truth/observation/noise before and after, both retained across resets',
            'units': 'SI; normalized action; float64 capture; SB3 neural computation float32'})

    def start_episode(self, info, runtime):
        self.episode += 1
        self.episodes.write(json.dumps({'trace_episode': self.episode, **info,
                                       'first_global_step': self.total_steps}) + '\n')
        self.episodes.flush()

    def record(self, t, runtime):
        if len(self.rows) >= self.chunk_size:
            self.flush()
        result = t['result']
        segments = result.intervals
        offset = len(self.segments)
        for s in segments:
            self.segments.append([s.time_s, s.dt_s, *s.truth_start, *s.torque_start,
                                  *s.torque_end, *s.applied_mean, *s.torque_squared_integral,
                                  *s.delayed_command,
                                  np.nan if s.source_submitted_s is None else s.source_submitted_s,
                                  s.push_N])
        self.rows.append({
            'global_step': self.total_steps + 1, 'episode': self.episode,
            'time_s': t['time_s'], 'actual_dt_s': runtime.time - t['time_s'],
            'truth_before': t['truth_before'], 'truth_after': t['truth_after'],
            'observation_before': encode_observation(t['observation_before'], self.protocol),
            'observation_after': encode_observation(t['observation_after'], self.protocol),
            'measurement_before': t['observation_before'].measurement,
            'measurement_after': t['observation_after'].measurement,
            'noise_before': t['noise_before'], 'noise_after': t['noise_after'],
            'env_input_action': t['raw_command_Nm'] / runtime.limits,
            'policy_action_raw': np.full(2, np.nan), 'raw_action_available': False,
            'bounded_command_Nm': t['bounded_command_Nm'],
            'torque_after_Nm': runtime.torque(), 'push_N': t['push_N'],
            'reward': t['reward'], 'terminated': t['terminated'], 'truncated': t['truncated'],
            'segment_offsets': [offset, len(self.segments)],
        })
        self.total_steps += 1

    def attach_raw(self, action):
        action = np.asarray(action, float)
        if not self.rows or action.shape != (2,) or not np.all(np.isfinite(action)):
            raise ValueError('Invalid raw policy action or no recorded transition')
        if not np.array_equal(np.clip(action, -1, 1), np.clip(self.rows[-1]['env_input_action'], -1, 1)):
            raise ValueError('Raw/clipped action alignment mismatch')
        self.rows[-1]['policy_action_raw'] = action.copy()
        self.rows[-1]['raw_action_available'] = True

    def flush(self):
        if not self.rows:
            return
        name = f'chunk-{len(self.chunks):06d}.npz'
        arrays = {key: np.asarray([row[key] for row in self.rows]) for key in self.rows[0]}
        arrays['segments'] = np.asarray(self.segments, dtype=float)
        with (self.out / name).open('xb') as stream:
            np.savez_compressed(stream, **arrays)
        self.chunks.append({'path': name, 'steps': len(self.rows), 'sha256': sha256(self.out / name)})
        self.rows, self.segments = [], []
        write_json(self.out / 'index.json', {'actual_env_steps': self.total_steps, 'chunks': self.chunks})

    def close(self):
        if not self.closed:
            self.flush()
            self.episodes.close()
            self.closed = True
