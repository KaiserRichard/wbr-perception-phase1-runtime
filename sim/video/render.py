"""Render an illustrative assumed-planar LQR demo, independently of training."""

import argparse
from contextlib import ExitStack
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
CAPTION = "ASSUMED planar WBR | delay-aware LQR"
LIMITATION = "Ideal rolling / rigid leg; no hardware validation"


def positive_seconds(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("duration must be positive and finite")
    return number


def dimension(value):
    number = int(value)
    if not 240 <= number <= 1920 or number % 2:
        raise argparse.ArgumentTypeError("dimensions must be even, between 240 and 1920")
    return number


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="New .mp4, or one initial .png frame, outside the repository")
    parser.add_argument("--duration", type=positive_seconds, default=10.,
                        help="Video seconds (default: existing 10 s demo; PNG is always t=0)")
    parser.add_argument("--fps", type=int, choices=range(1, 61), default=30)
    parser.add_argument("--width", type=dimension, default=640)
    parser.add_argument("--height", type=dimension, default=480)
    parser.add_argument("--delay-ms", type=int, choices=(2, 3, 4, 5), default=5)
    parser.add_argument("--seed", type=int, default=1000)
    parser.add_argument("--scenario", choices=("balance", "push"), default="push",
                        help="push includes initial balancing and the existing scheduled pulse")
    parser.add_argument("--ffmpeg", default="ffmpeg", help="MP4 encoder executable")
    args = parser.parse_args(argv)
    if args.seed < 0:
        parser.error("seed must be nonnegative")
    args.output = args.output.expanduser().resolve()
    if args.output.is_relative_to(ROOT):
        parser.error("output must be outside this repository (including resolved symlinks)")
    if args.output.suffix.lower() not in (".png", ".mp4"):
        parser.error("output must end in .png or .mp4")
    args.metadata = args.output.with_suffix(args.output.suffix + ".json")
    paths = [args.output, args.metadata]
    if args.output.suffix.lower() == ".mp4":
        paths.append(args.output.with_suffix(args.output.suffix + ".ffmpeg.log"))
    for path in paths:
        if path.exists():
            parser.error(f"refusing to overwrite {path}")
    return args


def frame_ticks(duration, fps, dt):
    """Nearest controller tick at each presentation timestamp, starting at t=0.

    Sampling never changes the controller or integration rate. An MP4 with N
    frames plays for N/fps seconds; the last sample precedes that endpoint.
    """
    return [round(index / (fps * dt)) for index in range(math.ceil(duration * fps))]


def encoder_command(args):
    executable = shutil.which(args.ffmpeg)
    if executable is None:
        raise RuntimeError("MP4 needs FFmpeg with libx264 on the render host; "
                           "no environment was changed. Use .png for one frame.")
    return [executable, "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
            "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size",
            f"{args.width}x{args.height}", "-framerate", str(args.fps),
            "-i", "pipe:0", "-an", "-c:v", "libx264", "-threads", "1",
            "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "fast",
            "-movflags", "+faststart", "-f", "mp4", str(args.output)]


def caption_frame(pixels, demo, args):
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (args.width, args.height), (20, 25, 34))
    image.paste(Image.fromarray(pixels), (0, 0))
    font = ImageFont.load_default(size=max(10, args.width // 80))
    state = demo.runtime.truth()
    protocol = demo.base["protocol"]
    pulse = (f"+{protocol['push_force_N']:g} N at {protocol['push_start_s']:.2f}"
             f"-{protocol['push_start_s'] + protocol['push_duration_s']:.2f} s"
             if args.scenario == "push" else "balance only; no push")
    text = [CAPTION,
            f"t={demo.runtime.time:.3f} s | seed={args.seed} | delay={args.delay_ms} ms",
            f"5 ms torque lag; body IMU noise | {pulse}",
            f"x={state[0]:+.3f} m | leg={math.degrees(state[1]):+.1f} deg | "
            f"body={math.degrees(state[2]):+.1f} deg",
            "Illustrative simulation; unscored",
            LIMITATION]
    draw = ImageDraw.Draw(image)
    # Wrap at measured pixel widths so small preview captions remain readable.
    y = pixels.shape[0] + 4
    for line in text:
        words, current = line.split(), ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if draw.textlength(candidate, font=font) > args.width - 12 and current:
                draw.text((6, y), current, font=font, fill="white")
                y += font.size + 3
                current = word
            else:
                current = candidate
        draw.text((6, y), current, font=font, fill="white")
        y += font.size + 3
    return image


def render(args):
    # Resolve optional encoder before creating outputs or synthesizing a gain.
    is_png = args.output.suffix.lower() == ".png"
    command = None if is_png else encoder_command(args)
    import mujoco
    import numpy as np
    from sim.view import Demo

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        metadata_file = stack.enter_context(args.metadata.open("x"))
        output = stack.enter_context(args.output.open("xb")) if is_png else None
        metadata = dict(status="running", caption=CAPTION, limitation=LIMITATION,
                        scenario=args.scenario, seed=args.seed, delay_ms=args.delay_ms,
                        output=str(args.output), width=args.width, height=args.height,
                        mujoco_version=mujoco.__version__, numpy_version=np.__version__,
                        python_version=sys.version.split()[0],
                        gl_backend=os.environ.get("MUJOCO_GL", "platform default"),
                        invocation=sys.argv, frames_written=0,
                        scored=False)

        def save_metadata():
            metadata_file.seek(0)
            json.dump(metadata, metadata_file, indent=2, allow_nan=False)
            metadata_file.write("\n")
            metadata_file.truncate()
            metadata_file.flush()

        save_metadata()
        encoder = None
        try:
            demo = Demo(args.delay_ms)
            demo.observation = demo.runtime.reset(seed=args.seed)
            # Only the viewer instance's automatic pulse is suppressed. Dynamics,
            # feedback, initial state and the source JSON stay unchanged.
            if args.scenario == "balance":
                demo.base["protocol"]["push_force_N"] = 0.
            ticks = [0] if is_png else frame_ticks(args.duration, args.fps, demo.runtime.dt)
            font_size = max(10, args.width // 80)
            scene_height = args.height - 8 * (font_size + 3) - 8
            demo.visual.model.vis.global_.offwidth = args.width
            demo.visual.model.vis.global_.offheight = scene_height
            camera = mujoco.MjvCamera()
            camera.lookat[:] = [0., 0., .20]
            camera.distance, camera.azimuth, camera.elevation = 1.05, 90, -12
            metadata.update(
                control_dt_s=demo.runtime.dt, fps=None if is_png else args.fps,
                requested_duration_s=0. if is_png else args.duration,
                playback_duration_s=0. if is_png else len(ticks) / args.fps,
                frame_ticks=ticks, frame_times_s=[tick * demo.runtime.dt for tick in ticks],
                protocol=demo.base["protocol"],
                runtime=vars(demo.runtime.config), K=demo.gain.tolist(),
                source_sha256={str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in [ROOT / name for name in (
                                   "sim/view.py", "sim/planar.py", "sim/augmented.py",
                                   "sim/augmented_lqr.py", "sim/configs/assumed_planar.json",
                                   "sim/configs/assumed_actuator_noise.json", "sim/video/render.py")]},
                encoder_command=command)
            # Keep errors in a sidecar, avoiding an unbounded subprocess stderr pipe.
            if command:
                error_log = args.output.with_suffix(args.output.suffix + ".ffmpeg.log")
                error_stream = stack.enter_context(error_log.open("xb"))
                encoder = subprocess.Popen(command, stdin=subprocess.PIPE,
                                           stdout=subprocess.DEVNULL, stderr=error_stream)
                metadata["encoder_log"] = str(error_log)
            with mujoco.Renderer(demo.visual.model, height=scene_height,
                                 width=args.width) as renderer:
                tick = 0
                for target in ticks:
                    while tick < target:
                        demo.step()
                        tick += 1
                    demo.visual_state()
                    renderer.update_scene(demo.data, camera=camera)
                    frame = caption_frame(renderer.render(), demo, args)
                    if encoder:
                        encoder.stdin.write(frame.tobytes())
                    else:
                        frame.save(output, format="PNG")
                    metadata["frames_written"] += 1
            if encoder:
                encoder.stdin.close()
                if encoder.wait(timeout=60):
                    raise RuntimeError(f"FFmpeg failed; see {metadata['encoder_log']}")
            metadata.update(status="complete", final_time_s=demo.runtime.time,
                            final_state=demo.runtime.truth().tolist())
        except BaseException as error:
            metadata.update(status="failed", error=f"{type(error).__name__}: {error}")
            raise
        finally:
            try:
                if encoder:
                    if not encoder.stdin.closed:
                        try:
                            encoder.stdin.close()
                        except BrokenPipeError:
                            pass  # Preserve the original encoder failure in metadata.
                    if encoder.poll() is None:
                        encoder.terminate()
                        encoder.wait(timeout=5)
            finally:
                save_metadata()
    return metadata


def main(argv=None):
    args = parse_args(argv)
    try:
        result = render(args)
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Render failed: {error}", file=sys.stderr)
        return 1
    print(f"Saved {result['frames_written']} frame(s): {args.output}\nMetadata: {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
