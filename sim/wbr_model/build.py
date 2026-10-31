"""Validate a WBR physical-parameter manifest and generate MuJoCo MJCF."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import re

import mujoco

try:
    import yaml
except ImportError:  # Keep the v1 schema usable in the project's MuJoCo-only env.
    yaml = None


SOURCES = {"team_report", "CAD", "ASSUMED"}
TENSOR_FIELDS = ("Ixx", "Iyy", "Izz", "Ixy", "Ixz", "Iyz")


def _split_flow(text, separator):
    parts, start, depth, quote = [], 0, 0, None
    for i, char in enumerate(text):
        if quote:
            if char == quote and (i == 0 or text[i - 1] != "\\"):
                quote = None
        elif char in "'\"":
            quote = char
        elif char in "[{(":
            depth += 1
        elif char in "]})":
            depth -= 1
        elif char == separator and depth == 0:
            parts.append(text[start:i].strip())
            start = i + 1
    parts.append(text[start:].strip())
    return parts


def _yaml_scalar(text):
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        result = {}
        for pair in _split_flow(text[1:-1], ","):
            key, value = _split_flow(pair, ":")[:2]
            result[str(_yaml_scalar(key))] = _yaml_scalar(value)
        return result
    if text.startswith("[") and text.endswith("]"):
        return [_yaml_scalar(item) for item in _split_flow(text[1:-1], ",") if item]
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        return text[1:-1]
    if text in ("null", "Null", "NULL", "~", ""):
        return None
    if text.lower() in ("true", "false"):
        return text.lower() == "true"
    if re.fullmatch(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", text):
        return float(text) if any(c in text for c in ".eE") else int(text)
    return text


def _load_v1_yaml_subset(text):
    """Parse the v1 manifest's indentation maps and flow scalars without PyYAML."""
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        rows.append((indent, line.strip()))

    def block(index, indent):
        mapping = {}
        while index < len(rows) and rows[index][0] == indent:
            _, row = rows[index]
            if row.startswith("-") or ":" not in row:
                raise ValueError("without PyYAML, manifests must use the documented mapping-based v1 subset")
            key, raw = row.split(":", 1)
            key = str(_yaml_scalar(key))
            index += 1
            if raw.strip():
                mapping[key] = _yaml_scalar(raw)
            elif index < len(rows) and rows[index][0] > indent:
                mapping[key], index = block(index, rows[index][0])
            else:
                mapping[key] = None
        return mapping, index

    if not rows:
        return None
    result, end = block(0, rows[0][0])
    if end != len(rows):
        raise ValueError("invalid indentation in manifest")
    return result


def load_manifest(path):
    text = Path(path).read_text()
    if yaml is not None:
        return yaml.safe_load(text)
    return _load_v1_yaml_subset(text)


def _value(entry, name, unit):
    if not isinstance(entry, dict) or set(("value", "unit", "source")) - entry.keys():
        raise ValueError(f"{name}: expected value, unit, and source fields")
    if entry["unit"] != unit:
        raise ValueError(f"{name}: expected unit {unit!r}, got {entry['unit']!r}")
    if entry["source"] not in SOURCES:
        raise ValueError(f"{name}: source must be one of {sorted(SOURCES)}")
    v = entry["value"]
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise ValueError(f"{name}: value must be a finite number")
    return float(v)


def _tensor(entry, name):
    if not isinstance(entry, dict) or entry.get("unit") != "kg m^2" or entry.get("source") not in SOURCES:
        raise ValueError(f"{name}: inertia requires unit 'kg m^2' and a valid source")
    vals = entry.get("value")
    if not isinstance(vals, dict) or set(vals) != set(TENSOR_FIELDS):
        raise ValueError(f"{name}: value must define {', '.join(TENSOR_FIELDS)}")
    q = [vals[k] for k in TENSOR_FIELDS]
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in q):
        raise ValueError(f"{name}: tensor entries must be finite numbers")
    ixx, iyy, izz, ixy, ixz, iyz = map(float, q)
    # Principal moments are eigenvalues of the symmetric COM inertia tensor.
    import numpy as np
    tensor = np.array([[ixx, ixy, ixz], [ixy, iyy, iyz], [ixz, iyz, izz]])
    moments = np.linalg.eigvalsh(tensor)
    if moments[0] <= 0:
        raise ValueError(f"{name}: inertia tensor must be positive definite")
    if moments[2] > moments[0] + moments[1] + 1e-12:
        raise ValueError(f"{name}: principal moments violate the triangle inequality")
    return " ".join(f"{x:.12g}" for x in (ixx, iyy, izz, ixy, ixz, iyz))


def _vector(entry, name, unit):
    if not isinstance(entry, dict) or entry.get("unit") != unit or entry.get("source") not in SOURCES:
        raise ValueError(f"{name}: expected a {unit} vector and valid source")
    values = entry.get("value")
    if not isinstance(values, list) or len(values) != 3 or any(
            isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in values):
        raise ValueError(f"{name}: value must be a finite three-element vector")
    return " ".join(f"{float(x):.12g}" for x in values)


def validate(manifest):
    if not isinstance(manifest, dict):
        raise ValueError("manifest root must be a mapping")
    if manifest.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if manifest.get("model", {}).get("leg_representation") != "equivalent_slider":
        raise ValueError("model.leg_representation must be 'equivalent_slider' in schema v1")
    model = manifest["model"]
    gravity = _value(model.get("gravity"), "model.gravity", "m/s^2")
    timestep = _value(model.get("timestep"), "model.timestep", "s")
    if gravity <= 0 or timestep <= 0:
        raise ValueError("gravity and timestep must be positive")
    length = model.get("leg_length_limits", {})
    lo = _value(length.get("min"), "model.leg_length_limits.min", "m")
    hi = _value(length.get("max"), "model.leg_length_limits.max", "m")
    if not 0 < lo < hi:
        raise ValueError("leg length limits must satisfy 0 < min < max")
    hip_limits = model.get("hip_angle_limits", {})
    hip_min = _value(hip_limits.get("min"), "model.hip_angle_limits.min", "rad")
    hip_max = _value(hip_limits.get("max"), "model.hip_angle_limits.max", "rad")
    if not hip_min < hip_max:
        raise ValueError("hip angle limits must satisfy min < max")
    masses = manifest.get("masses", {})
    body_mass = _value(masses.get("base"), "masses.base", "kg")
    leg_mass = _value(masses.get("each_leg"), "masses.each_leg", "kg")
    wheel_mass = _value(masses.get("each_wheel"), "masses.each_wheel", "kg")
    declared = _value(masses.get("total_robot"), "masses.total_robot", "kg")
    if min(body_mass, leg_mass, wheel_mass, declared) <= 0:
        raise ValueError("all masses must be positive")
    calculated = body_mass + 2 * leg_mass + 2 * wheel_mass
    if not math.isclose(calculated, declared, rel_tol=1e-8, abs_tol=1e-9):
        raise ValueError(f"mass sum mismatch: components total {calculated:g} kg, declared {declared:g} kg")
    components = {"base": body_mass, "leg": leg_mass, "wheel": wheel_mass}
    com = {part: _vector(manifest.get("com", {}).get(part), f"com.{part}", "m") for part in components}
    inertias = {part: _tensor(manifest.get("inertias", {}).get(part), f"inertias.{part}")
                for part in components}
    geometry = manifest.get("geometry", {})
    lengths = {key: _value(geometry.get(key), f"geometry.{key}", "m") for key in (
        "l1", "l2", "l3", "l4", "l5", "wheel_radius", "wheel_track",
        "wheel_width", "link_radius")}
    if any(x <= 0 for x in lengths.values()):
        raise ValueError("geometry lengths must be positive")
    base_size = _vector(geometry.get("base_half_size"), "geometry.base_half_size", "m")
    base_size_values = [float(x) for x in base_size.split()]
    if any(x <= 0 for x in base_size_values):
        raise ValueError("geometry.base_half_size values must be positive")
    motors = {}
    for key, unit in (("wheel_torque", "N m"), ("hip_torque", "N m"), ("leg_force", "N")):
        motors[key] = _value(manifest.get("actuators", {}).get(key), f"actuators.{key}", unit)
        if motors[key] <= 0:
            raise ValueError(f"actuators.{key} must be positive")
    return {"gravity": gravity, "timestep": timestep, "min_length": lo, "max_length": hi,
            "hip_min": hip_min, "hip_max": hip_max,
            "masses": components, "com": com, "inertias": inertias, "geometry": lengths,
            "base_half_size": base_size,
            "actuators": motors}


def generate(manifest):
    p = validate(manifest)
    g, geo, mass, inertia, act = p["gravity"], p["geometry"], p["masses"], p["inertias"], p["actuators"]
    sides = []
    actuators = []
    for side, sign in (("left", 1), ("right", -1)):
        y = sign * geo["wheel_track"] / 2
        sides.append(f'''<body name="leg_{side}" pos="0 {y:.12g} 0">
          <joint name="hip_{side}" type="hinge" axis="0 1 0" limited="true" range="{p['hip_min']:.12g} {p['hip_max']:.12g}" damping="0.01"/>
          <joint name="leg_length_{side}" type="slide" axis="0 0 -1" limited="true" range="{p['min_length']:.12g} {p['max_length']:.12g}" ref="{(p['min_length']+p['max_length'])/2:.12g}" damping="0.01"/>
          <inertial pos="{p['com']['leg']}" mass="{mass['leg']:.12g}" fullinertia="{inertia['leg']}"/>
          <geom name="leg_geom_{side}" type="capsule" fromto="0 0 0 0 0 {geo['l2']:.12g}" size="{geo['link_radius']:.12g}" mass="0"/>
          <body name="wheel_{side}" pos="0 0 {-((p['min_length']+p['max_length'])/2):.12g}">
            <joint name="wheel_{side}" type="hinge" axis="0 1 0" damping="0.01"/>
            <inertial pos="{p['com']['wheel']}" mass="{mass['wheel']:.12g}" fullinertia="{inertia['wheel']}"/>
            <geom name="wheel_geom_{side}" type="cylinder" size="{geo['wheel_radius']:.12g} {geo['wheel_width']/2:.12g}" euler="1.5707963267948966 0 0" mass="0"/>
          </body>
        </body>''')
        actuators.extend((f'<motor name="wheel_motor_{side}" joint="wheel_{side}" ctrllimited="true" ctrlrange="{-act["wheel_torque"]:.12g} {act["wheel_torque"]:.12g}"/>',
                          f'<motor name="hip_motor_{side}" joint="hip_{side}" ctrllimited="true" ctrlrange="{-act["hip_torque"]:.12g} {act["hip_torque"]:.12g}"/>',
                          f'<motor name="leg_motor_{side}" joint="leg_length_{side}" ctrllimited="true" ctrlrange="{-act["leg_force"]:.12g} {act["leg_force"]:.12g}"/>'))
    lengths_note = " l1={l1:.12g}m l2={l2:.12g}m l3={l3:.12g}m l4={l4:.12g}m l5={l5:.12g}m".format(**geo)
    return f'''<mujoco model="wbr_manifest_generated">
  <!-- Source geometry retained for traceability; linkage is represented by equivalent slider.{lengths_note} -->
  <compiler angle="radian"/>
  <option timestep="{p['timestep']:.12g}" gravity="0 0 {-g:.12g}" integrator="implicitfast"/>
  <default><geom friction="1 0.005 0.0001" condim="3"/><joint armature="0.00001"/></default>
  <worldbody>
      <geom name="floor" type="plane" size="5 2 0.1"/>
    <body name="base" pos="0 0 {geo['wheel_radius'] + (p['min_length']+p['max_length'])/2:.12g}">
      <joint name="base_x" type="slide" axis="1 0 0"/><joint name="base_z" type="slide" axis="0 0 1"/><joint name="pitch" type="hinge" axis="0 1 0"/>
      <inertial pos="{p['com']['base']}" mass="{mass['base']:.12g}" fullinertia="{inertia['base']}"/>
      <geom name="base_geom" type="box" size="{p['base_half_size']}" mass="0"/>
      {''.join(sides)}
    </body>
  </worldbody>
  <actuator>{''.join(actuators)}</actuator>
</mujoco>'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        xml = generate(manifest)
        # Compile before writing so an invalid generated model never replaces output.
        mujoco.MjModel.from_xml_string(xml)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(xml)
    except (OSError, TypeError, KeyError, ValueError, mujoco.MujocoError) as exc:
        parser.error(str(exc))
    except Exception as exc:
        if yaml is None:
            parser.error(str(exc))
        if isinstance(exc, yaml.YAMLError):
            parser.error(str(exc))
        raise
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
