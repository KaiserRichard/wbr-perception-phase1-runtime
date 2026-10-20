"""Quick argument/output tests; rendering and encoding are mocked here.

The single actual GPU frame for task B3 is retained outside git; these tests do
not spend another frame or run a rollout while PPO is active.
"""

from contextlib import ExitStack, redirect_stderr
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np
from PIL import Image

from sim.video import render as video


class RendererTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="wbr-video-test-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def args(self, *extra, suffix=".png"):
        return video.parse_args(["--output", str(self.folder / ("demo" + suffix)),
                                 "--width", "320", "--height", "240", *extra])

    def assert_bad_args(self, args):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            video.parse_args(args)
        self.assertEqual(error.exception.code, 2)

    def test_argument_validation(self):
        for extra in (["--duration", "nan"], ["--duration", "inf"],
                      ["--duration", "0"], ["--duration", "-1"],
                      ["--width", "321"], ["--height", "100"],
                      ["--fps", "0"], ["--delay-ms", "6"], ["--seed", "-1"]):
            with self.subTest(extra=extra):
                self.assert_bad_args(["--output", str(self.folder / "a.png"), *extra])

    def test_rejects_repository_output_and_symlink(self):
        self.assert_bad_args(["--output", str(video.ROOT / "a.png")])
        link = self.folder / "repo"
        link.symlink_to(video.ROOT, target_is_directory=True)
        self.assert_bad_args(["--output", str(link / "a.png")])

    def test_rejects_unknown_extension(self):
        self.assert_bad_args(["--output", str(self.folder / "a.gif")])

    def test_does_not_overwrite_output_metadata_or_encoder_log(self):
        for index, suffix in enumerate((".mp4", ".mp4.json", ".mp4.ffmpeg.log")):
            with self.subTest(suffix=suffix):
                path = self.folder / (f"existing{index}" + suffix)
                path.write_text("keep")
                self.assert_bad_args(["--output", str(self.folder / f"existing{index}.mp4")])
                self.assertEqual(path.read_text(), "keep")

    def test_sampling_retains_original_controller_clock(self):
        ticks = video.frame_ticks(10., 30, .002)
        self.assertEqual(len(ticks), 300)
        self.assertEqual(ticks[:4], [0, 17, 33, 50])
        self.assertEqual(ticks[90], 1500)  # Original push starts at 3 seconds.
        self.assertLessEqual(max(abs(t * .002 - i / 30) for i, t in enumerate(ticks)), .001)

    def test_missing_ffmpeg_fails_before_outputs(self):
        args = self.args(suffix=".mp4")
        with patch.object(video.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "MP4 needs FFmpeg"):
                video.render(args)
        self.assertFalse(args.output.exists())
        self.assertFalse(args.metadata.exists())

    def fake_scene(self, stack, args):
        base = json.loads((video.ROOT / "sim/configs/assumed_planar.json").read_text())
        runtime = SimpleNamespace(time=0., dt=.002, config=SimpleNamespace(delay_s=.005),
                                  truth=Mock(return_value=np.array(base["protocol"]["initial_state"])),
                                  reset=Mock(return_value="seeded-observation"))
        demo = SimpleNamespace(base=base, gain=np.zeros((2, 14)), runtime=runtime,
                               visual=SimpleNamespace(model=SimpleNamespace(
                                   vis=SimpleNamespace(global_=SimpleNamespace()))),
                               data=object(), visual_state=Mock())

        def step():
            runtime.time += runtime.dt

        demo.step = Mock(side_effect=step)
        demo_factory = stack.enter_context(patch("sim.view.Demo", return_value=demo))
        renderer = stack.enter_context(patch("mujoco.Renderer"))
        scene_height = args.height - 8 * (max(10, args.width // 80) + 3) - 8
        renderer.return_value.__enter__.return_value.render.return_value = np.full(
            (scene_height, args.width, 3), 150, dtype=np.uint8)
        return demo, demo_factory, renderer

    def test_one_png_frame_has_caption_metadata_and_no_rollout(self):
        args = self.args("--duration", "100")
        with ExitStack() as stack:
            demo, factory, renderer = self.fake_scene(stack, args)
            result = video.render(args)
        factory.assert_called_once_with(5)
        demo.runtime.reset.assert_called_once_with(seed=1000)
        demo.step.assert_not_called()
        renderer.return_value.__enter__.return_value.render.assert_called_once()
        with Image.open(args.output) as image:
            self.assertEqual(image.size, (320, 240))
            self.assertEqual(image.mode, "RGB")
            self.assertGreater(np.asarray(image)[128:, :, :].max(), 200)  # Visible caption.
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["frames_written"], 1)
        self.assertEqual(result["final_time_s"], 0.)
        self.assertIn("ASSUMED planar", result["caption"])
        self.assertFalse(result["scored"])
        self.assertEqual(json.loads(args.metadata.read_text())["frame_ticks"], [0])
        self.assertEqual(result["protocol"]["push_force_N"], 6.)

    def test_balance_suppresses_only_local_demo_pulse(self):
        args = self.args("--scenario", "balance", "--seed", "7")
        with ExitStack() as stack:
            demo, _, _ = self.fake_scene(stack, args)
            result = video.render(args)
        self.assertEqual(result["protocol"]["push_force_N"], 0.)
        demo.runtime.reset.assert_called_once_with(seed=7)
        source = json.loads((video.ROOT / "sim/configs/assumed_planar.json").read_text())
        self.assertEqual(source["protocol"]["push_force_N"], 6.)

    def test_mp4_stream_contract_and_tick_scheduling_without_encoding(self):
        args = self.args("--duration", "0.05", "--fps", "30", suffix=".mp4")
        encoder = Mock(stdin=io.BytesIO())
        encoder.wait.return_value = 0
        encoder.poll.return_value = 0
        with ExitStack() as stack:
            demo, _, _ = self.fake_scene(stack, args)
            stack.enter_context(patch.object(video.shutil, "which", return_value="/fake/ffmpeg"))
            popen = stack.enter_context(patch.object(video.subprocess, "Popen", return_value=encoder))
            result = video.render(args)
        self.assertEqual(result["frames_written"], 2)
        self.assertEqual(demo.step.call_count, 17)
        command = popen.call_args.args[0]
        self.assertIn("libx264", command)
        self.assertEqual(command[command.index("-threads") + 1], "1")
        self.assertEqual(command[-1], str(args.output))
        self.assertIn("-n", command)  # FFmpeg itself must also refuse overwrites.
        self.assertIn("+faststart", command)
        self.assertEqual(popen.call_args.kwargs["stdout"], video.subprocess.DEVNULL)
        self.assertTrue(encoder.stdin.closed)

    def test_encoder_failure_is_recorded_as_failure(self):
        args = self.args("--duration", "0.01", suffix=".mp4")
        encoder = Mock(stdin=io.BytesIO())
        encoder.wait.return_value = 1
        encoder.poll.return_value = 1
        with ExitStack() as stack:
            self.fake_scene(stack, args)
            stack.enter_context(patch.object(video.shutil, "which", return_value="/fake/ffmpeg"))
            stack.enter_context(patch.object(video.subprocess, "Popen", return_value=encoder))
            with self.assertRaisesRegex(RuntimeError, "FFmpeg failed"):
                video.render(args)
        metadata = json.loads(args.metadata.read_text())
        self.assertEqual(metadata["status"], "failed")
        self.assertIn("FFmpeg failed", metadata["error"])
        self.assertTrue(Path(metadata["encoder_log"]).exists())

    def test_renderer_failure_is_retained(self):
        args = self.args()
        with ExitStack() as stack:
            _, _, renderer = self.fake_scene(stack, args)
            renderer.return_value.__enter__.side_effect = RuntimeError("GL unavailable")
            with self.assertRaisesRegex(RuntimeError, "GL unavailable"):
                video.render(args)
        metadata = json.loads(args.metadata.read_text())
        self.assertEqual(metadata["status"], "failed")
        self.assertEqual(metadata["frames_written"], 0)
        self.assertIn("GL unavailable", metadata["error"])
        self.assertTrue(args.output.exists())  # Failed artifacts are retained.


if __name__ == "__main__":
    unittest.main()
