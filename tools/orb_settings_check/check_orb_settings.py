#!/usr/bin/env python3
"""Validate ORB-SLAM3 OpenCV FileStorage settings using the Python stdlib."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import platform
import re
import shutil
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = HERE / "config" / "check_config.json"
VERSION = "1.0"


class SettingsError(ValueError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def number(value: str) -> float:
    try:
        result = float(value.strip())
    except ValueError as exc:
        raise SettingsError(f"not a numeric scalar: {value!r}") from exc
    if not math.isfinite(result):
        raise SettingsError(f"non-finite number: {value!r}")
    return result


def scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value[0:1] in ("\"", "'"):
        quote = value[0]
        if len(value) < 2 or value[-1] != quote:
            raise SettingsError(f"unterminated quoted scalar: {value!r}")
        return value[1:-1]
    if value in ("true", "True"):
        return True
    if value in ("false", "False"):
        return False
    try:
        n = number(value)
        return int(n) if n.is_integer() and not re.search(r"[.eE]", value) else n
    except SettingsError:
        if value.startswith("[") and value.endswith("]"):
            return [scalar(x) for x in split_values(value[1:-1])]
        return value


def split_values(raw: str) -> list[str]:
    """Split comma-separated OpenCV matrix data, respecting quoted strings."""
    out: list[str] = []
    start = 0
    quote = ""
    for i, char in enumerate(raw):
        if quote:
            if char == quote:
                quote = ""
        elif char in ("\"", "'"):
            quote = char
        elif char == ",":
            out.append(raw[start:i].strip())
            start = i + 1
    tail = raw[start:].strip()
    if tail:
        out.append(tail)
    return out


def parse_opencv_yaml(path: Path) -> dict[str, Any]:
    """Parse flat OpenCV FileStorage settings and !!opencv-matrix nodes."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "%YAML:1.0":
        raise SettingsError("first line must be the OpenCV FileStorage %YAML:1.0 header")
    values: dict[str, Any] = {}
    i = 1
    while i < len(lines):
        raw = lines[i]
        i += 1
        line = raw.split("#", 1)[0].strip()
        if not line or line == "---":
            continue
        if ":" not in line:
            raise SettingsError(f"unsupported YAML line {i}: {raw}")
        key, rhs = line.split(":", 1)
        key = key.strip()
        if not key or key in values:
            raise SettingsError(f"empty or duplicate key on line {i}: {key!r}")
        rhs = rhs.strip()
        if "!!opencv-matrix" in rhs:
            rows = cols = None
            data_text = ""
            while i < len(lines):
                item = lines[i].split("#", 1)[0].strip()
                i += 1
                if not item:
                    continue
                if item.startswith("rows:"):
                    rows = int(item.split(":", 1)[1].strip())
                elif item.startswith("cols:"):
                    cols = int(item.split(":", 1)[1].strip())
                elif item.startswith("dt:"):
                    continue
                elif item.startswith("data:"):
                    data_text = item.split(":", 1)[1].strip()
                    if "[" in data_text:
                        data_text = data_text[data_text.find("[") + 1 :]
                    while "]" not in data_text and i < len(lines):
                        data_text += " " + lines[i].split("#", 1)[0].strip()
                        i += 1
                    if "]" not in data_text:
                        raise SettingsError(f"unterminated matrix data for {key}")
                    data_text = data_text[: data_text.rfind("]")]
                    break
                else:
                    raise SettingsError(f"unsupported matrix field for {key}: {item}")
            if rows is None or cols is None or not data_text:
                raise SettingsError(f"incomplete OpenCV matrix {key}")
            entries = [number(v) for v in split_values(data_text)]
            if len(entries) != rows * cols:
                raise SettingsError(f"matrix {key} declares {rows}x{cols}, has {len(entries)} values")
            values[key] = {"rows": rows, "cols": cols, "data": entries}
        else:
            values[key] = scalar(rhs)
    return values


def parse_plain_yaml(path: Path) -> dict[str, Any]:
    """Read flat calibration key/scalar YAML used by lab IMU and camchain files."""
    out: dict[str, Any] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key in out:
            raise SettingsError(f"duplicate calibration key {key!r} at line {lineno}")
        value = value.strip()
        if value.startswith("["):
            out[key] = [number(x.strip().strip("[]")) for x in value.strip("[] ").split(",")]
        else:
            out[key] = scalar(value)
    return out


def matrix(values: dict[str, Any], key: str) -> list[list[float]]:
    value = values[key]
    if not isinstance(value, dict) or value.get("rows") != 4 or value.get("cols") != 4:
        raise SettingsError(f"{key} must be a 4x4 !!opencv-matrix")
    data = value["data"]
    return [data[r * 4 : (r + 1) * 4] for r in range(4)]


def det3(m: list[list[float]]) -> float:
    a, b, c = m
    return a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0])


def norm3(vector: list[float]) -> float:
    return math.sqrt(sum(x * x for x in vector))


class Checker:
    def __init__(self, settings: dict[str, Any], config: dict[str, Any], profile_name: str | None,
                 stream: dict[str, float] | None, imu_cal: dict[str, Any], baseline: float | None,
                 imu_cal_label: str, baseline_label: str):
        self.v = settings
        self.config = config
        self.profile_name = profile_name
        self.profile = config.get("profiles", {}).get(profile_name) if profile_name else None
        self.stream = stream
        self.imu_cal = imu_cal
        self.baseline = baseline
        self.imu_cal_label = imu_cal_label
        self.baseline_label = baseline_label
        self.criteria: list[dict[str, Any]] = []
        self.notes: list[str] = []
        self.thresholds = config["thresholds"]

    def add(self, ident: str, description: str, ok: bool | None, measured: Any,
            unit: str, threshold: str, source: str, note: str | None = None) -> None:
        status = "BLOCKED" if ok is None else ("PASS" if ok else "FAIL")
        self.criteria.append({"id": ident, "description": description, "measured": measured,
                              "unit": unit, "threshold": threshold, "status": status,
                              "evidence": "settings.yaml", "threshold_source": source})
        if note:
            self.notes.append(note)

    def t(self, key: str) -> tuple[float, str]:
        item = self.thresholds[key]
        return float(item["value"]), item["source"]

    def required(self, keys: list[str], ident: str) -> bool:
        missing = [key for key in keys if key not in self.v]
        self.add(ident, "Required Stereo-Inertial settings are present for the declared Camera.type",
                 not missing, missing or len(keys), "missing keys or count", "all listed keys present",
                 "SOURCE-SUPPORTED: ORB-SLAM3 src/Settings.cc readCamera1/readCamera2/readImageInfo/readIMU/readORB/readViewer")
        return not missing

    def run(self) -> list[dict[str, Any]]:
        v = self.v
        self.add("opencv_yaml", "OpenCV FileStorage format 1.0 and supported YAML subset parse",
                 v.get("File.version") == "1.0", v.get("File.version"), "version", '"1.0"',
                 "SOURCE-SUPPORTED: ORB-SLAM3 System.cc selects Settings for File.version 1.0")
        kind = v.get("Camera.type")
        self.add("camera_type", "Declared stereo camera type is supported", kind in ("PinHole", "Rectified", "KannalaBrandt8"), kind,
                 "type", "PinHole | Rectified | KannalaBrandt8", "SOURCE-SUPPORTED: ORB-SLAM3 Settings.cc readCamera1")
        base = ["File.version", "Camera.type", "Camera.width", "Camera.height", "Camera.fps", "Camera.RGB",
                "Stereo.ThDepth", "IMU.T_b_c1", "IMU.NoiseGyro", "IMU.NoiseAcc", "IMU.GyroWalk",
                "IMU.AccWalk", "IMU.Frequency", "ORBextractor.nFeatures", "ORBextractor.scaleFactor",
                "ORBextractor.nLevels", "ORBextractor.iniThFAST", "ORBextractor.minThFAST"]
        camera_keys = ([f"Camera{i}.{k}" for i in (1, 2) for k in ("fx", "fy", "cx", "cy")] if kind in ("PinHole", "KannalaBrandt8") else
                       [f"Camera1.{k}" for k in ("fx", "fy", "cx", "cy")])
        if kind == "PinHole":
            base += ["Stereo.T_c1_c2"]
            for i in (1, 2):
                if f"Camera{i}.k1" in v:
                    base += [f"Camera{i}.{k}" for k in ("k1", "k2", "p1", "p2")]
        elif kind == "Rectified":
            base += ["Stereo.b"]
        elif kind == "KannalaBrandt8":
            base += ["Stereo.T_c1_c2"] + [f"Camera1.{k}" for k in ("k1", "k2", "k3", "k4")] + [
                "Camera1.overlappingBegin", "Camera1.overlappingEnd", "Camera2.overlappingBegin", "Camera2.overlappingEnd"]
        base += camera_keys
        viewer_keys = ["Viewer.KeyFrameSize", "Viewer.KeyFrameLineWidth", "Viewer.GraphLineWidth", "Viewer.PointSize",
                       "Viewer.CameraSize", "Viewer.CameraLineWidth", "Viewer.ViewpointX", "Viewer.ViewpointY",
                       "Viewer.ViewpointZ", "Viewer.ViewpointF"]
        self.required(base, "required_settings")
        self.required(viewer_keys, "viewer_settings")
        self.add("optional_flags", "Optional behavior flags are reported", True,
                 {k: v[k] for k in ("IMU.InsertKFsWhenLost", "Camera.RGB", "Viewer.imageViewScale") if k in v},
                 "settings", "informational", "SOURCE-SUPPORTED: optional flags read by ORB-SLAM3 Settings.cc")
        flags = {k: v.get(k) for k in ("Camera.RGB", "IMU.InsertKFsWhenLost") if k in v}
        flags_valid = all(isinstance(value, (int, float)) and not isinstance(value, bool)
                          and float(value).is_integer() and int(value) in (0, 1)
                          for value in flags.values())
        self.add("operating_flags", "Present RGB and keyframe-loss flags use supported integer booleans",
                 flags_valid, flags, "0 or 1", "present flags must be integer 0|1",
                 "SOURCE-SUPPORTED: ORB-SLAM3 Settings.cc casts Camera.RGB and IMU.InsertKFsWhenLost to bool")

        width = self._num("Camera.width")
        height = self._num("Camera.height")
        fps = self._num("Camera.fps")
        rate = self._num("IMU.Frequency")
        stream_values_ok = (width is not None and height is not None and fps is not None and rate is not None
                            and width.is_integer() and height.is_integer() and fps.is_integer()
                            and width > 0 and height > 0 and fps > 0 and rate > 0)
        self.add("stream_values", "Image dimensions and rates are positive; dimensions and image fps are integers",
                 stream_values_ok, {"width": width, "height": height, "fps": fps, "imu_frequency_hz": rate},
                 "pixels, Hz", "width/height/fps integer > 0; IMU frequency > 0",
                 "SOURCE-SUPPORTED: ORB-SLAM3 Settings.cc reads image dimensions/fps as integers and IMU.Frequency as a positive sample rate")
        th_depth = self._num("Stereo.ThDepth")
        self.add("stereo_depth_threshold", "Stereo.ThDepth is positive",
                 None if th_depth is None else th_depth > 0, th_depth, "depth multiplier", "> 0",
                 "SOURCE-SUPPORTED parameter with positive interpretation; ORB-SLAM3 uses it as close/far threshold multiplier")
        expected = self.profile or self.stream
        if expected:
            ewidth, eheight, efps = (expected.get("width"), expected.get("height"), expected.get("fps"))
            if all(x is not None for x in (width, height, fps)):
                good = width == ewidth and height == eheight and abs(fps - float(efps)) <= self.t("profile_rate_abs_tolerance_hz")[0]
                source = expected.get("source", "CLI-provided stream profile") if self.profile else "ASSUMED: explicit CLI stream profile supplied by caller"
                self.add("camera_profile", "Camera width, height, and fps match the selected named/CLI stream profile",
                         good, {"width": width, "height": height, "fps": fps},
                         "pixels, Hz", f"{ewidth}x{eheight} at {efps} Hz", source)
            else:
                self.add("camera_profile", "Camera width, height, and fps match the selected stream profile", False,
                         None, "pixels, Hz", "profile match", "PROPOSED: required values must be numeric")
            expected_rate = expected.get("gyro_rate_hz")
            tol, src = self.t("profile_rate_abs_tolerance_hz")
            self.add("imu_profile_rate", "IMU.Frequency matches the selected stream gyro rate",
                     None if rate is None else abs(rate - float(expected_rate)) <= tol,
                     rate, "Hz", f"{expected_rate} +/- {tol} Hz", expected.get("source", src) if self.profile else src)
        else:
            needed = ["width", "height", "fps", "gyro_rate_hz"]
            has = self.stream is not None and all(k in self.stream for k in needed)
            self.add("camera_profile", "Camera width, height, and fps match explicit CLI stream profile",
                     None if not has else (width == self.stream["width"] and height == self.stream["height"] and abs((fps or 0)-self.stream["fps"]) <= self.t("profile_rate_abs_tolerance_hz")[0]),
                     {"width": width, "height": height, "fps": fps}, "pixels, Hz", "explicit CLI values required",
                     "ASSUMED: stream profile supplied by caller")
            self.add("imu_profile_rate", "IMU.Frequency matches explicit CLI stream gyro rate",
                     None if not has else abs((rate or 0)-self.stream["gyro_rate_hz"]) <= self.t("profile_rate_abs_tolerance_hz")[0],
                     rate, "Hz", "explicit CLI gyro rate", "ASSUMED: stream profile supplied by caller")

        focal_ok = True
        focal_info = {}
        for i in (1, 2) if kind in ("PinHole", "KannalaBrandt8") else (1,):
            fx, fy, cx, cy = (self._num(f"Camera{i}.{x}") for x in ("fx", "fy", "cx", "cy"))
            if None in (fx, fy, cx, cy) or not width or not height or min(fx or 0, fy or 0) <= 0:
                focal_ok = False
                continue
            rel = abs(fx - fy) / max(fx, fy)
            focal_ok &= rel <= self.t("fx_fy_relative_tolerance")[0] and 0 <= cx < width and 0 <= cy < height
            focal_info[str(i)] = {"fx_fy_relative_difference": rel, "cx": cx, "cy": cy}
        self.add("intrinsics", "Focal lengths are positive and approximately equal; principal points lie inside each image",
                 focal_ok, focal_info or None, "relative error, pixels", f"fx/fy rel error <= {self.t('fx_fy_relative_tolerance')[0]}; 0<=cx<width, 0<=cy<height",
                 self.t("fx_fy_relative_tolerance")[1])

        transforms: list[tuple[str, list[list[float]]]] = []
        for key in ("Stereo.T_c1_c2", "IMU.T_b_c1"):
            if key not in v:
                if key == "Stereo.T_c1_c2" and kind == "Rectified":
                    continue
                continue
            try:
                transforms.append((key, matrix(v, key)))
            except SettingsError as exc:
                self.add("matrix_shape_" + key.replace(".", "_"), f"{key} has a valid 4x4 OpenCV matrix", False,
                         str(exc), "matrix", "4x4", "SOURCE-SUPPORTED: ORB-SLAM3 Settings.cc reads homogeneous 4x4 transforms")
        rot_ok, rot_data = True, {}
        for key, m in transforms:
            r = [row[:3] for row in m[:3]]
            orth_error = max(abs(sum(r[k][i] * r[k][j] for k in range(3)) - (1 if i == j else 0))
                             for i in range(3) for j in range(3))
            determinant = det3(r)
            bottom_error = max(abs(m[3][i] - ([0, 0, 0, 1][i])) for i in range(4))
            trans = norm3([m[i][3] for i in range(3)])
            rot_ok &= orth_error <= self.t("rotation_orthonormal_abs_tolerance")[0]
            rot_ok &= abs(determinant - 1) <= self.t("rotation_determinant_abs_tolerance")[0]
            rot_ok &= bottom_error <= self.t("homogeneous_row_abs_tolerance")[0]
            rot_ok &= trans <= self.t("max_translation_m")[0]
            rot_data[key] = {"orthonormal_max_abs_error": orth_error, "determinant": determinant,
                             "translation_m": trans, "homogeneous_row_max_abs_error": bottom_error}
        # Rectified encodes baseline as a scalar and has no stereo rotation matrix.
        self.add("transform_geometry", "Stereo and camera-to-IMU transforms are valid rigid transforms with plausible translation",
                 rot_ok if transforms else None, rot_data or None, "m, matrix error",
                 f"rotation/determinant/bottom row tolerances from config; translation <= {self.t('max_translation_m')[0]} m",
                 "; ".join(self.t(k)[1] for k in ("rotation_orthonormal_abs_tolerance", "rotation_determinant_abs_tolerance", "homogeneous_row_abs_tolerance", "max_translation_m")))

        stereo_baseline = norm3([matrix(self._as_values(), "Stereo.T_c1_c2")[i][3] for i in range(3)]) if "Stereo.T_c1_c2" in v and isinstance(v["Stereo.T_c1_c2"], dict) and v["Stereo.T_c1_c2"].get("rows") == 4 and v["Stereo.T_c1_c2"].get("cols") == 4 else self._num("Stereo.b")
        if stereo_baseline is None:
            self.add("stereo_baseline", "Stereo baseline agrees with the calibration reference", None, None, "m", "calibration comparison unavailable", self.baseline_label)
        elif self.baseline is None or self.baseline <= 0:
            self.add("stereo_baseline", "Stereo baseline agrees with calibration reference", None, stereo_baseline, "m", "calibration reference required", self.baseline_label)
        elif stereo_baseline <= 0:
            self.add("stereo_baseline", "Stereo baseline is positive and agrees with calibration reference",
                     False, {"settings_m": stereo_baseline, "calibration_m": self.baseline}, "m",
                     "settings and calibration baseline > 0", self.baseline_label)
        else:
            tol, src = self.t("baseline_relative_tolerance")
            self.add("stereo_baseline", "Stereo baseline agrees with calibration reference",
                     abs(stereo_baseline - self.baseline) / self.baseline <= tol,
                     {"settings_m": stereo_baseline, "calibration_m": self.baseline}, "m",
                     f"relative difference <= {tol}", self.baseline_label + "; " + src)

        noise_pairs = [("IMU.NoiseGyro", "gyroscope_noise_density"), ("IMU.NoiseAcc", "accelerometer_noise_density"),
                       ("IMU.GyroWalk", "gyroscope_random_walk"), ("IMU.AccWalk", "accelerometer_random_walk")]
        positive = all((x := self._num(key)) is not None and x > 0 for key, _ in noise_pairs)
        unit_results = {}
        compare_ok = self.imu_cal is not None
        for setting, calibration in noise_pairs:
            a, b = self._num(setting), self.imu_cal.get(calibration) if self.imu_cal else None
            if a is None or b is None or not isinstance(b, (int, float)) or b <= 0:
                compare_ok = False
                unit_results[setting] = None
            else:
                unit_results[setting] = abs(a - b) / b
                compare_ok &= unit_results[setting] <= self.t("imu_noise_relative_tolerance")[0]
        self.add("imu_noise_positive", "All four continuous-time IMU noise fields are present and positive",
                 positive, {k: self._num(k) for k, _ in noise_pairs}, "continuous-time SI density", "> 0",
                 "SOURCE-SUPPORTED units: tools/calib_tools/README.md; positivity threshold is mathematically required")
        tol, src = self.t("imu_noise_relative_tolerance")
        self.add("imu_noise_calibration", "IMU noise values agree with selected calibration after unit conversion",
                 compare_ok, unit_results, "relative difference", f"<= {tol}; gyro rad/s/sqrt(Hz), accel m/s^2/sqrt(Hz), walks per calib_tools README",
                 self.imu_cal_label + "; " + src,
                 "Values are compared as continuous-time densities; ORB discretizes them internally based on IMU.Frequency.")

        sane, extractor = True, {}
        e = self.thresholds["extractor"]
        for key, lo, hi in (("ORBextractor.nFeatures", e["nFeatures_min"], e["nFeatures_max"]),
                            ("ORBextractor.nLevels", e["nLevels_min"], e["nLevels_max"]),
                            ("ORBextractor.iniThFAST", e["fast_threshold_min"], e["fast_threshold_max"]),
                            ("ORBextractor.minThFAST", e["fast_threshold_min"], e["fast_threshold_max"])):
            x = self._num(key)
            valid = x is not None and x.is_integer() and lo <= x <= hi
            sane &= valid
            extractor[key] = x
        scale = self._num("ORBextractor.scaleFactor")
        scale_ok = scale is not None and e["scaleFactor_min_exclusive"] < scale <= e["scaleFactor_max"]
        sane &= scale_ok
        extractor["ORBextractor.scaleFactor"] = scale
        self.add("extractor_sane", "ORB extractor counts, pyramid scale, levels, and FAST thresholds are sane",
                 sane, extractor, "ORB settings", str({k: v for k, v in e.items() if k != "source"}), e["source"])

        viewer_max, viewer_source = self.t("viewer_positive_max")
        viewer_valid = all((x := self._num(k)) is not None and 0 < x < viewer_max for k in viewer_keys[:6])
        for k in ("Viewer.ViewpointX", "Viewer.ViewpointY", "Viewer.ViewpointZ", "Viewer.ViewpointF"):
            viewer_valid &= self._num(k) is not None
        self.add("viewer_values", "Viewer dimensions are positive and bounded; viewpoints are finite",
                 viewer_valid, {k: self._num(k) for k in viewer_keys}, "Viewer units", f"positive Viewer sizes < {viewer_max}; finite viewpoints", viewer_source)
        return self.criteria

    def _as_values(self) -> dict[str, Any]:
        return self.v

    def _num(self, key: str) -> float | None:
        value = self.v.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
            return float(value)
        return None


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def calibration_baseline(path: Path) -> float | None:
    # Kalibr camchains store cam1.T_cn_cnm1 as a nested sequence. Read just
    # that block, keeping this validator independent of PyYAML.
    lines = path.read_text(encoding="utf-8").splitlines()
    active = False
    rows: list[list[float]] = []
    for raw in lines:
        line = raw.split("#", 1)[0].strip()
        if line == "T_cn_cnm1:":
            active = True
            continue
        if active:
            if not line.startswith("-"):
                break
            body = line[1:].strip().strip("[] ")
            rows.append([number(x.strip()) for x in body.split(",")])
            if len(rows) == 4:
                break
    if len(rows) == 4 and all(len(row) == 4 for row in rows):
        return norm3([rows[i][3] for i in range(3)])
    return None


def run(args: argparse.Namespace) -> int:
    started = utcnow()
    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    config_path = args.config
    config = json.loads(config_path.read_text(encoding="utf-8"))
    settings_path = args.settings
    input_missing = settings_path is None or not settings_path.is_file()
    request: dict[str, Any] = {"profile": args.profile, "stream": None, "imu_calibration": None,
                               "calibration": None, "baseline": None, "baseline_label": None,
                               "imu_cal_label": None, "generator_provenance": None}
    if args.profile and args.profile not in config.get("profiles", {}):
        raise SettingsError(f"unknown profile {args.profile!r}; available: {', '.join(config.get('profiles', {}))}")
    stream = None
    if not args.profile and any(x is not None for x in (args.width, args.height, args.fps, args.gyro_rate)):
        if any(x is None for x in (args.width, args.height, args.fps, args.gyro_rate)):
            raise SettingsError("--width, --height, --fps, and --gyro-rate must be supplied together")
        stream = {"width": args.width, "height": args.height, "fps": args.fps, "gyro_rate_hz": args.gyro_rate}
    elif args.profile:
        p = config["profiles"][args.profile]
        request["profile"] = args.profile
        if args.imu_calibration is None and p.get("imu_calibration"):
            args.imu_calibration = (config_path.parent / p["imu_calibration"]).resolve()
        if args.calibration is None and p.get("camera_calibration"):
            args.calibration = (config_path.parent / p["camera_calibration"]).resolve()
        if args.calibration is None and p.get("stereo_baseline_m") is not None:
            request["baseline"] = float(p["stereo_baseline_m"])
            request["baseline_label"] = p["baseline_source"]
    request["stream"] = stream

    if settings_path and settings_path.is_file():
        shutil.copyfile(settings_path, outdir / "settings.yaml")
    provenance_path = args.provenance
    if provenance_path is None and settings_path is not None:
        candidate = settings_path.parent / "provenance.json"
        if candidate.is_file():
            provenance_path = candidate
    if provenance_path is not None and provenance_path.is_file():
        shutil.copyfile(provenance_path, outdir / "provenance.json")
        generated_yaml = provenance_path.parent / "orbslam3.yaml"
        if generated_yaml.is_file():
            shutil.copyfile(generated_yaml, outdir / "generator_settings.yaml")
        request["generator_provenance"] = "provenance.json"
    shutil.copyfile(config_path, outdir / "check_config.json")
    values: dict[str, Any] = {}
    parse_error = None
    if not input_missing:
        try:
            values = parse_opencv_yaml(settings_path)
        except (OSError, SettingsError) as exc:
            parse_error = str(exc)
    imu_cal: dict[str, Any] | None = None
    if args.imu_calibration and args.imu_calibration.is_file():
        imu_cal = parse_plain_yaml(args.imu_calibration)
        shutil.copyfile(args.imu_calibration, outdir / "imu_calibration.yaml")
        request["imu_calibration"] = "imu_calibration.yaml"
        request["imu_cal_label"] = f"{args.imu_calibration}: continuous-time SI values; source/unit metadata in file and tools/calib_tools/README.md"
    if args.calibration and args.calibration.is_file():
        base = calibration_baseline(args.calibration)
        if base is not None:
            request["baseline"] = base
            request["baseline_label"] = f"SOURCE-SUPPORTED: baseline norm read from {args.calibration} cam1.T_cn_cnm1"
        shutil.copyfile(args.calibration, outdir / "stereo_calibration.yaml")
    request["baseline"] = request.get("baseline")
    if args.analyze_only:
        request_path = args.analyze_only / "request.json"
        request = json.loads(request_path.read_text(encoding="utf-8"))
        config = json.loads((args.analyze_only / "check_config.json").read_text(encoding="utf-8"))
        outdir = args.outdir
        outdir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.analyze_only / "settings.yaml", outdir / "settings.yaml")
        shutil.copyfile(args.analyze_only / "check_config.json", outdir / "check_config.json")
        settings_path = outdir / "settings.yaml"
        values = parse_opencv_yaml(settings_path)
        input_missing = False
        parse_error = None
        if request.get("imu_calibration"):
            shutil.copyfile(args.analyze_only / request["imu_calibration"], outdir / "imu_calibration.yaml")
            imu_cal = parse_plain_yaml(outdir / "imu_calibration.yaml")
        if (args.analyze_only / "stereo_calibration.yaml").exists():
            shutil.copyfile(args.analyze_only / "stereo_calibration.yaml", outdir / "stereo_calibration.yaml")
        if request.get("generator_provenance"):
            shutil.copyfile(args.analyze_only / request["generator_provenance"], outdir / "provenance.json")
            if (args.analyze_only / "generator_settings.yaml").exists():
                shutil.copyfile(args.analyze_only / "generator_settings.yaml", outdir / "generator_settings.yaml")
    request_path = outdir / "request.json"
    request_path.write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    notes = ["This is a settings consistency check; a tool PASS on fixture settings is not an N4B/N4C gate PASS.",
             "Camera and IMU timestamp clock domains are not represented or mapped by ORB Settings; this validator performs no timestamp subtraction."]
    if input_missing:
        criteria = [{"id": "input_available", "description": "Settings input is available", "measured": None,
                     "unit": "file", "threshold": "readable YAML file", "status": "BLOCKED", "evidence": "result.json",
                     "threshold_source": "tool input requirement"}]
    elif parse_error:
        criteria = [{"id": "opencv_yaml", "description": "OpenCV FileStorage settings parse", "measured": parse_error,
                     "unit": "parse result", "threshold": "%YAML:1.0 supported subset", "status": "FAIL",
                     "evidence": "settings.yaml", "threshold_source": "ticket requirement: OpenCV FileStorage YAML format 1.0"}]
    else:
        imu_label = request.get("imu_cal_label") or "UNKNOWN: calibration IMU reference not supplied"
        base_label = request.get("baseline_label") or "UNKNOWN: calibration stereo baseline not supplied"
        checker = Checker(values, config, request.get("profile"), request.get("stream"), imu_cal,
                          request.get("baseline"), imu_label, base_label)
        criteria = checker.run()
        notes.extend(checker.notes)
        if request.get("generator_provenance"):
            provenance_file = outdir / "provenance.json"
            expected_file = outdir / "generator_settings.yaml"
            try:
                provenance = json.loads(provenance_file.read_text(encoding="utf-8"))
                expected_hash = provenance["outputs"]["orbslam3.yaml"]["sha256"]
                observed_hash = sha256(expected_file) if expected_file.is_file() else None
                current_hash = sha256(outdir / "settings.yaml")
                good = observed_hash == expected_hash and current_hash == expected_hash
                criteria.append({"id": "generator_provenance", "description": "Settings file agrees byte-for-byte with make_orb_yaml output and its provenance hash",
                                 "measured": {"settings_sha256": current_hash, "generator_sha256": observed_hash,
                                              "provenance_sha256": expected_hash},
                                 "unit": "SHA-256", "threshold": "all three hashes equal",
                                 "status": "PASS" if good else "FAIL", "evidence": "settings.yaml and provenance.json",
                                 "threshold_source": "SOURCE-SUPPORTED: make_orb_yaml.py writes provenance.json outputs.orbslam3.yaml.sha256"})
            except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
                criteria.append({"id": "generator_provenance", "description": "Generator provenance is available and has a valid output hash",
                                 "measured": str(exc), "unit": "provenance parse", "threshold": "valid provenance and generated YAML",
                                 "status": "BLOCKED", "evidence": "provenance.json", "threshold_source": "SOURCE-SUPPORTED: make_orb_yaml.py provenance schema"})
    statuses = {item["status"] for item in criteria}
    overall = "FAIL" if "FAIL" in statuses else ("BLOCKED" if "BLOCKED" in statuses else "PASS")
    raw_files = []
    for p in sorted(outdir.iterdir()):
        if p.is_file() and p.name != "result.json":
            raw_files.append({"path": p.name, "sha256": sha256(p)})
    result = {"check": "orb_settings", "tool_version": VERSION, "status": overall,
              "started_utc": started, "ended_utc": utcnow(),
              "host": {"system": platform.system(), "release": platform.release(), "python": platform.python_version(), "hostname": platform.node()},
              "criteria": criteria, "raw_files": raw_files, "notes": notes}
    (outdir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"ORB settings check: {overall}")
    for item in criteria:
        print(f"{item['status']:7} {item['id']}: {item['description']}")
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[overall]


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("settings", nargs="?", type=Path, help="OpenCV FileStorage settings YAML")
    p.add_argument("--outdir", required=True, type=Path, help="fresh or existing result directory")
    p.add_argument("--profile", help="named profile from config/check_config.json")
    p.add_argument("--width", type=int)
    p.add_argument("--height", type=int)
    p.add_argument("--fps", type=float)
    p.add_argument("--gyro-rate", type=float)
    p.add_argument("--imu-calibration", type=Path, help="flat YAML with continuous-time SI noise fields")
    p.add_argument("--calibration", type=Path, help="Kalibr camchain YAML with cam1.T_cn_cnm1 baseline")
    p.add_argument("--provenance", type=Path, help="make_orb_yaml provenance.json (auto-detected beside settings if present)")
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--analyze-only", type=Path, help="re-run from a prior result directory's saved raw inputs")
    args = p.parse_args(argv)
    if args.analyze_only:
        if args.settings is not None:
            p.error("do not pass settings together with --analyze-only")
    elif args.settings is None:
        p.error("settings YAML is required unless --analyze-only is used")
    return args


if __name__ == "__main__":
    try:
        raise SystemExit(run(parse_args(sys.argv[1:])))
    except (OSError, json.JSONDecodeError, SettingsError) as exc:
        print(f"orb_settings_check: {exc}", file=sys.stderr)
        raise SystemExit(3)
