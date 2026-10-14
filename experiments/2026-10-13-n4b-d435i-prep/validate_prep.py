#!/usr/bin/env python3
"""OFFLINE/SYNTHETIC artifact checks only; uses stdlib, no SDK/network/devices."""
from pathlib import Path
import hashlib
import math
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ORB = ROOT / "third_party/ORB_SLAM3"
EXAMPLE = ORB / "Examples/Stereo-Inertial/stereo_inertial_realsense_D435i.cc"
CAL = ROOT / "experiments/2026-10-13-pi5-env-snapshot/rs_calibration_new_unit.txt"
PIN = "4452a3c4ab75b1cde34e5505a36ec3f9edcdc4c4"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scalars(text):
    result = {}
    for line in text.splitlines():
        m = re.match(r"^([\w.]+):\s*(.*?)\s*(?:#.*)?$", line)
        if m:
            key, value = m.groups()
            assert key not in result, f"duplicate setting {key}"
            result[key] = value
    return result


def translation(text, src, dst):
    m = re.search(r'Extrinsic from "' + src + r'"\s+To\s+"' + dst +
                  r'"\s*:(.*?)(?=\nExtrinsic|\Z)', text, re.S)
    assert m, (src, dst)
    t = re.search(r"Translation Vector:\s*([^\n]+)", m[1])
    r = re.search(r"Rotation Matrix:\s*(.*?)Translation Vector", m[1], re.S)
    return list(map(float, r[1].split())), list(map(float, t[1].split()))


def main():
    head = subprocess.check_output(["git", "-C", str(ORB), "rev-parse", "HEAD"], text=True).strip()
    assert head == PIN
    assert digest(EXAMPLE) == "b03a2c6ca6ad3d5d729a6afd22a2efad1e4f6500ed2fee7885b4e3fa607e66af"
    assert digest(CAL) == "adbcfcdf19372c81686cfa0379d6567a1a7e441f21fd7434f1eef8254738cc73"
    subprocess.run(["git", "-C", str(ORB), "apply", "--check",
                    str(HERE / "stereo_inertial_d435i_file.patch")], check=True)
    calibration = CAL.read_text()
    ours_text = (HERE / "D435i_317422076650_stereo_inertial.yaml").read_text()
    ours = scalars(ours_text)
    upstream = scalars((ORB / "Examples/Stereo-Inertial/RealSense_D435i.yaml").read_text())
    assert ours.keys() == upstream.keys(), "exact Rectified schema key set"
    assert ours["File.version"] == '"1.0"' and ours["Camera.type"] == '"Rectified"'
    measured = {"Camera1.fx", "Camera1.fy", "Camera1.cx", "Camera1.cy", "Stereo.b"}
    for key in ours.keys() - measured - {"IMU.T_b_c1"}:
        assert ours[key] == upstream[key], key
    for stream in ("Infrared 1", "Infrared 2"):
        m = re.search(r'Intrinsic of "' + stream + r'" / 640x480 / \{Y8\}(.*?)(?=\n Intrinsic|\Z)',
                      calibration, re.S)
        assert m, stream
        for field, key in (("Fx", "fx"), ("Fy", "fy"), ("PPX", "cx"), ("PPY", "cy")):
            v = float(re.search(field + r":\s*(\S+)", m[1])[1])
            assert v == float(ours["Camera1." + key]), (stream, field)
        coeffs = re.search(r"Coeffs:\s*([^\n]+)", m[1])[1].split()
        assert list(map(float, coeffs)) == [0] * 5
    identity = [1, 0, 0, 0, 1, 0, 0, 0, 1]
    r_stereo, t_stereo = translation(calibration, "Infrared 1", "Infrared 2")
    assert r_stereo == identity and t_stereo[1:] == [0, 0]
    assert float(ours["Stereo.b"]) == -t_stereo[0] > 0
    matrix = list(map(float, re.search(r"data:\s*\[([^]]+)\]", ours_text, re.S)[1].split(',')))
    assert len(matrix) == 16 and matrix[12:] == [0, 0, 0, 1]
    for dst in ("Gyro", "Accel"):
        r, t = translation(calibration, "Infrared 1", dst)
        inv_r, inv_t = translation(calibration, dst, "Infrared 1")
        assert r == inv_r == identity
        assert [matrix[3], matrix[7], matrix[11]] == t
        assert inv_t == [-x for x in t]
        for point in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)):
            body = [point[i] + t[i] for i in range(3)]
            recovered = [body[i] + inv_t[i] for i in range(3)]
            assert all(math.isclose(recovered[i], point[i], abs_tol=1e-14) for i in range(3))
    assert re.search(r"Accel\s+MOTION_XYZ32F\s+@ 400/200/100 Hz", calibration)
    assert re.search(r"Gyro\s+MOTION_XYZ32F\s+@ 400/200 Hz", calibration)
    # Synthetic nonidentity convention check: +90-degree Z rotation in SDK
    # column-major becomes row-major R, mapping X basis to Y basis.
    sdk = [0, 1, 0, -1, 0, 0, 0, 0, 1]
    rows = [[sdk[col * 3 + row] for col in range(3)] for row in range(3)]
    assert [row[0] for row in rows] == [0, 1, 0]
    print("OFFLINE/SYNTHETIC: pinned source, read-only patch check, schema text, factory readback, transform and rate checks completed")
    print("OpenCV FileStorage / SDK build / N1-N4B-N4C hardware and VIO: OPEN")
    print("source_sha256=" + digest(EXAMPLE))
    print("factory_readback_sha256=" + digest(CAL))


if __name__ == "__main__":
    main()
