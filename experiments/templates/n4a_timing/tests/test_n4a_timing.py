from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest


HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
RUNNER = HERE / "run_n4a_timing.sh"
ANALYZER = HERE / "analyze_n4a_timing.py"
FIXTURE = HERE / "tests/fixtures/n4a_real_throttle_samples.csv"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


timing = load_module("n4a_timing_runner", HERE / "run_n4a_timing.py")


class N4ATimingTests(unittest.TestCase):
    def make_platform(self, root: Path, *, temperature: int = 50000, throttle: str = "0x0") -> dict:
        thermal = root / "sys/class/thermal"
        (thermal / "thermal_zone0").mkdir(parents=True)
        (thermal / "thermal_zone0/temp").write_text(f"{temperature}\n")
        governors = root / "sys/devices/system/cpu"
        (governors / "cpu0/cpufreq").mkdir(parents=True)
        (governors / "cpu0/cpufreq/scaling_governor").write_text("performance\n")
        vc = root / "vcgencmd"
        vc.write_text(f"#!/bin/sh\nprintf 'throttled={throttle}\\n'\n")
        vc.chmod(0o755)
        return {"thermal": thermal, "governors": governors, "vcgencmd": vc}

    def make_config(self, root: Path) -> Path:
        config = json.loads((HERE / "config.json").read_text())
        pre = config["preflight"]
        pre["cooldown_timeout_s"]["value"] = 0.05
        pre["cooldown_poll_period_s"]["value"] = 0.01
        pre["between_run_cooldown_s"]["value"] = 0.0
        pre["process_discovery_timeout_s"]["value"] = 1.0
        pre["process_discovery_poll_period_s"]["value"] = 0.01
        pre["sampler_stop_timeout_s"]["value"] = 1.0
        config["profiling"]["sample_period_s"]["value"] = 0.01
        config["profiling"]["throttle_period_s"]["value"] = 0.01
        path = root / "config.json"
        path.write_text(json.dumps(config))
        return path

    def make_stubs(self, root: Path) -> dict:
        runner = root / "stub_runner.sh"
        runner.write_text(textwrap.dedent("""\
            #!/bin/sh
            set -eu
            bin=$1
            out=$8
            mkdir -p "$out/run01"
            (cd "$out/run01" && "$bin" 0.20) &
            child=$!
            if [ -n "${N4A_ORB_PID_FILE:-}" ]; then printf '%s\\n' "$child" > "$N4A_ORB_PID_FILE"; fi
            wait "$child"
            printf '0\\n' > "$out/run01/exit_code.txt"
            printf 'IMU initialized\\n' > "$out/run01/stdout.log"
        """))
        runner.chmod(0o755)
        sampler = root / "stub_sampler.py"
        sampler.write_text(textwrap.dedent("""
            import argparse, csv, json, signal, time
            p = argparse.ArgumentParser(); p.add_argument('command'); p.add_argument('--pid', type=int)
            p.add_argument('--out'); p.add_argument('--period-s'); p.add_argument('--throttle-period-s')
            a = p.parse_args()
            stop = False
            def done(*_):
                global stop
                stop = True
            signal.signal(signal.SIGINT, done)
            fields = ['monotonic_ns','clock_domain','pid','cpu_count','per_core_cpu_pct_json',
                      'target_cpu_pct_one_core','thread_cpu_pct_json','process_start_ticks','rss_bytes',
                      'pss_bytes','cpu_freq_khz_json','thermal_c_json','throttled_raw','undervoltage_now',
                      'frequency_capped_now','throttled_now','soft_temperature_limit_now','undervoltage_occurred',
                      'frequency_capped_occurred','throttled_occurred','soft_temperature_limit_occurred',
                      'fan_state_json','sample_duration_ns']
            import pathlib
            out = pathlib.Path(a.out); out.mkdir()
            row = {field: 'UNKNOWN' for field in fields}
            row.update(monotonic_ns='1', clock_domain='CLOCK_MONOTONIC', pid=str(a.pid), cpu_count='1',
                       thermal_c_json=json.dumps({'thermal_zone0': {'type': 'cpu-thermal', 'c': 55.0}}),
                       throttled_raw='0x0', fan_state_json='{}', sample_duration_ns='1')
            for field in ('undervoltage_now','frequency_capped_now','throttled_now','soft_temperature_limit_now',
                          'undervoltage_occurred','frequency_capped_occurred','throttled_occurred',
                          'soft_temperature_limit_occurred'):
                row[field] = '0'
            with (out / 'samples.csv').open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerow(row)
            (out / 'metadata.json').write_text(json.dumps({'sample_count': 1}))
            while not stop: time.sleep(0.01)
        """))
        sampler.chmod(0o755)
        return {"runner": runner, "sampler": sampler}

    def create_inputs(self, root: Path) -> dict:
        inputs = {}
        inputs["binary"] = Path("/bin/sleep")
        for name in ("vocab", "settings", "times"):
            path = root / name
            path.write_text("stub\n")
            inputs[name] = path
        inputs["dataset"] = root / "dataset"
        inputs["dataset"].mkdir()
        return inputs

    def command(self, args, *, env=None):
        return subprocess.run(args, cwd=REPO, env=env, text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, check=False)

    def test_valid_stub_capture(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); platform = self.make_platform(root); config = self.make_config(root)
            stubs = self.make_stubs(root); inputs = self.create_inputs(root); out = root / "experiment"
            env = dict(__import__('os').environ, N4A_ORB_PID_FILE=str(root / "orb.pid"))
            proc = self.command(["bash", str(RUNNER), "--config", str(config), "--accuracy-runner", str(stubs["runner"]),
                                 "--profile-tool", str(stubs["sampler"]), "--thermal-root", str(platform["thermal"]),
                                 "--governor-root", str(platform["governors"]), "--vcgencmd", str(platform["vcgencmd"]),
                                 "--lock-file", str(root / "lock"), str(inputs["binary"]), str(inputs["vocab"]),
                                 str(inputs["settings"]), str(inputs["dataset"]), str(inputs["times"]), "MH01", "1", str(out)], env=env)
            self.assertEqual(proc.returncode, 0, proc.stdout)
            self.assertEqual(json.loads((out / "preflight.json").read_text())["status"], "PASS")
            self.assertEqual(json.loads((out / "run01/capture.json").read_text())["status"], "CAPTURED")
            self.assertTrue((out / "run01/profile/samples.csv").is_file())

    def test_preflight_refuses_prior_throttle(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); platform = self.make_platform(root, throttle="0x50005"); config = self.make_config(root)
            proc = self.command(["bash", str(RUNNER), "--preflight-only", "--config", str(config),
                                 "--thermal-root", str(platform["thermal"]), "--governor-root", str(platform["governors"]),
                                 "--vcgencmd", str(platform["vcgencmd"]), "--lock-file", str(root / "lock"),
                                 "/bin/sleep", str(root / "vocab"), str(root / "settings"), str(root / "dataset"),
                                 str(root / "times"), "MH01", "1", str(root / "experiment")])
            self.assertEqual(proc.returncode, 1, proc.stdout)
            result = json.loads((root / "experiment/preflight.json").read_text())
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["prior_throttle_bits"], [0, 2, 16, 18])

    def test_throttled_run_is_excluded_from_aggregate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); experiment = root / "experiment"; experiment.mkdir()
            (experiment / "preflight.json").write_text(json.dumps({"prior_throttle_allowed": False,
                                                                      "criteria": [{"id": "no_prior_throttle_bits",
                                                                                     "measured": {"invalid_bits_set": []}}]}))
            for number, throttled in ((1, False), (2, True)):
                run = experiment / f"run{number:02d}"; engine = run / "accuracy/run01"; engine.mkdir(parents=True)
                (engine / "exit_code.txt").write_text("0\n")
                profile = run / "profile"; profile.mkdir()
                (profile / "run_tracking.csv").write_text("image_s,state,imu_initialized,imu_samples,track_ms\n1,2,1,4,10\n")
                (run / ("throttled" if throttled else "healthy")).write_text("")
            accuracy = root / "accuracy_stub.py"
            accuracy.write_text(textwrap.dedent("""
                import json, pathlib, sys
                out = pathlib.Path(sys.argv[sys.argv.index('--out') + 1]); out.mkdir(parents=True, exist_ok=True)
                (out / 'summary.json').write_text(json.dumps({'status': 'PASS', 'runs': [{'ate_rpe_1m': {'se3': {'ate_translation_m': {'rmse': 0.04}}}}]}))
            """))
            profile = root / "profile_stub.py"
            profile.write_text(textwrap.dedent("""
                import json, pathlib, sys
                command = sys.argv[1]; directory = pathlib.Path(sys.argv[sys.argv.index('--analyze-only') + 1] if command == 'validity' else sys.argv[sys.argv.index('--out') + 1])
                run = directory.parent
                bad = (run / 'throttled').exists()
                if command == 'validity':
                    result = {'status': 'FAIL' if bad else 'PASS', 'criteria': [{'id': 'max_temperature', 'measured': 63.0}], 'raw_files': []}
                    (directory / 'result.json').write_text(json.dumps(result)); raise SystemExit(1 if bad else 0)
                (directory / 'latency.json').write_text(json.dumps({'frame_count': 1, 'tracking_latency_ns': {'p50': 10000000, 'p95': 20000000, 'p99': 30000000}}))
            """))
            gt = root / "gt.csv"; gt.write_text("stub\n"); times = root / "times.txt"; times.write_text("1\n")
            proc = self.command([sys.executable, str(ANALYZER), "--experiment", str(experiment), "--sequence", "MH01",
                                 "--ground-truth", str(gt), "--times", str(times), "--accuracy-tool", str(accuracy),
                                 "--profile-tool", str(profile)])
            self.assertEqual(proc.returncode, 0, proc.stdout)
            result = json.loads((experiment / "summary.json").read_text())
            self.assertEqual(result["valid_run_count"], 1)
            self.assertEqual(result["excluded_run_count"], 1)
            self.assertIn("profile_validity_fail", result["excluded_runs"][0]["reasons"])
            self.assertEqual(result["aggregate"]["accuracy_ate_rmse_se3_m"]["mean"], 0.04)

    def test_real_saved_throttle_fixture_fails_profile_gate(self):
        profile = load_module("n4a_profile_for_fixture", REPO / "tools/eval_pipeline/profile/profile.py")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); shutil.copy2(FIXTURE, root / "samples.csv")
            result = type("Args", (), {"analyze_only": root, "out": root})
            self.assertEqual(profile.validity(result()), 1)
            self.assertEqual(json.loads((root / "result.json").read_text())["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
