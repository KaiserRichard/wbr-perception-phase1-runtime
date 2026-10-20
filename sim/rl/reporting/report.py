"""Normalize saved v1 aggregates and v2 archives without reading trajectories."""

import csv
import html
import json
import math
from pathlib import Path


METRICS = ("duration_s", "recovery_time_after_event_s", "penalized_recovery_s",
           "command_effort_Nm2_s", "applied_effort_Nm2_s")
NOTES = [
    "SIMULATION / ASSUMED. Descriptive saved evidence only; no hardware claim.",
    "Every declared seed is shown; no best-seed selection, pooled episode CI, or new uncertainty estimate.",
    "The frozen LQR panel appears once. Reuse across policy seeds or versions creates no new LQR replicates.",
    "Strict success uses saved acceptance. Survival means full duration, no fall/displacement/numerical failure; it is not strict success.",
    "Unknown or unfinished slots remain unavailable, not zero successes. Saved MISSING_POLICY slots retain explicit failure values.",
    "Continuous means require every expected slot. Available-only diagnostics retain their episode denominators.",
    "Recovery is after event end (balance: reset; push: pulse end). Null recovery is not zero; penalized recovery is a separate metric.",
    "Effort is mean per-episode integral of squared torque, [wheel, hip], Nm² s. Early termination shortens exposure; see duration.",
    "Versions differ in training recipe and action rate. A cross-version difference is not an isolated algorithm effect.",
    "No trace, checkpoint or replay is loaded. A running archive is a non-atomic snapshot, not a completed experiment.",
]


class Reader:
    """Hard input budgets prevent accidental large evidence loads."""

    def __init__(self):
        self.sources = []
        self.bytes = 0

    def read(self, path):
        path = Path(path)
        if path.suffix != ".json":
            raise ValueError(f"Only JSON summaries are supported: {path}")
        size = path.stat().st_size
        if size > 16 * 1024**2 or self.bytes + size > 64 * 1024**2 or len(self.sources) >= 4096:
            raise ValueError(f"Saved JSON input budget exceeded: {path}")
        with path.open("rb") as stream:
            raw = stream.read(16 * 1024**2 + 1)
        if len(raw) > 16 * 1024**2:
            raise ValueError(f"Saved JSON input budget exceeded: {path}")
        data = json.loads(raw, parse_constant=lambda s: (_ for _ in ()).throw(
            ValueError(f"Nonfinite JSON number: {s}")))
        self.bytes += len(raw)
        self.sources.append(str(path.resolve()))
        return data


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"Expected finite numeric metric, got {value!r}")
    return value


def average(values, weights):
    if not values:
        return None
    if isinstance(values[0], list):
        if any(not isinstance(v, list) or len(v) != len(values[0]) for v in values):
            raise ValueError("Inconsistent metric vector shapes")
        return [average([v[i] for v in values], weights) for i in range(len(values[0]))]
    return sum(number(v) * w for v, w in zip(values, weights)) / sum(weights)


def metric(parts, total):
    """Combine summary means with observation counts, never equal panel weights."""
    available = sum(n for _, n in parts)
    value = average([v for v, _ in parts], [n for _, n in parts])
    return {"mean": value if total and available == total else None,
            "available_only_mean": value, "available_episodes": available,
            "total_episodes": total}


def validate_metric(key, value):
    if key.endswith("effort_Nm2_s"):
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError(f"Expected [wheel, hip] for {key}")
        values = value
    else:
        values = [value]
    if any(number(v) < 0 for v in values):
        raise ValueError(f"Negative saved physical metric: {key}")
    return value


def count_metric(count, available, total):
    if available > total or count > available or count < 0:
        raise ValueError("Invalid saved count/denominator")
    return {"count": count if available else None, "available_episodes": available,
            "total_episodes": total,
            "rate": count / total if total and available == total else None}


def base_row(version, controller, seed, condition, expected, observed, state, rate, plant_rate):
    return dict(version=version, controller=controller, seed=seed, condition=condition,
                expected_episodes=expected, observed_episodes=observed, state=state,
                policy_action_hz=rate, plant_control_hz=plant_rate,
                reference_reused=controller == "lqr")


def v1(reader, path):
    data = reader.read(path)
    panels = data["panels"]
    if "lqr" not in panels or not all(isinstance(v, dict) for v in panels.values()):
        raise ValueError("Expected v1 condition panels")
    # Use archived protocol only, never current working-tree defaults.
    protocol_path = path.parent / "source/sim/rl/protocol.json"
    protocol = reader.read(protocol_path) if protocol_path.exists() else None
    hz = 1 / protocol["plant"]["control_period_s"] if protocol else None
    seeds = (protocol["training"]["policy_seeds"] if protocol else
             range(data["n_training_seed_slots"]))
    names = ["lqr", *[f"ppo-{s}" for s in seeds]]
    if set(panels) - set(names):
        raise ValueError("Unexpected v1 policy panels outside declared seed slots")
    policies_path = path.parent / "policies.json"
    policies = reader.read(policies_path) if policies_path.exists() else {}
    condition_counts = ({f"{round(d*1000)}ms-{s['name']}": len(protocol["evaluation"]["noise_seeds"])
                         for d in protocol["plant"]["fixed_delays_s"] for s in protocol["scenarios"]}
                        if protocol else {key: p["episodes"] for key, p in panels["lqr"].items()})
    rows = []
    for name in names:
        seed = None if name == "lqr" else int(name.split("-")[1])
        state = "saved_aggregate"
        if seed is not None:
            complete = policies.get(str(seed), {}).get("complete")
            if complete is None:
                complete = data.get("all_five_full_budget_policies")
            state = "complete" if complete is True else "incomplete_or_unknown"
        groups = panels.get(name, {})
        if set(groups) - set(condition_counts):
            raise ValueError(f"Unexpected v1 conditions: {name}")
        for condition in ["all", *condition_counts]:
            keys = list(condition_counts) if condition == "all" else [condition]
            total = sum(condition_counts[k] for k in keys)
            selected = [groups[k] for k in keys if k in groups]
            observed = sum(p["episodes"] for p in selected)
            if observed > total:
                raise ValueError("Unexpected v1 episode count")
            if any(p["episodes"] > condition_counts[k] for k, p in groups.items()):
                raise ValueError("Unexpected v1 condition episode count")
            row = base_row("v1", "lqr" if seed is None else "ppo", seed, condition,
                           total, observed, state, hz, hz)
            successes = sum(p["success_rate"] * p["episodes"] for p in selected)
            if not math.isclose(successes, round(successes), abs_tol=1e-7):
                raise ValueError("v1 success rates do not represent integral counts")
            row["strict_success"] = count_metric(round(successes), observed, total)
            # Mean duration and fall count cannot reconstruct the joint survival event.
            row["survival"] = count_metric(0, 0, total)
            for key in METRICS:
                parts = []
                for p in selected:
                    item = p.get(key, {})
                    n = item.get("available_episodes", 0)
                    if n < 0 or n > p["episodes"]:
                        raise ValueError("Invalid v1 metric denominator")
                    if n:
                        value = item.get("available_only_mean", item.get("mean"))
                        if value is None:
                            raise ValueError("Available v1 metric lacks a value")
                        parts.append((validate_metric(key, value), n))
                row[key] = metric(parts, total)
            rows.append(row)
    return rows, ["v1 aggregates omit survival counts; survival is unavailable here."]


def v2(reader, root):
    declaration = reader.read(root / "run.json")
    config, protocol = declaration["config"], declaration["v1_protocol"]
    report_path = root / "status.json"
    if not report_path.exists():
        report_path = root / "progress.json"
    status = reader.read(report_path) if report_path.exists() else {}
    plant_hz = 1 / protocol["plant"]["control_period_s"]
    action_hz = plant_hz / config["policy_hold_ticks"]
    conditions = {f"{round(d*1000)}ms-{s['name']}": (d, s["name"])
                  for d in protocol["plant"]["fixed_delays_s"] for s in protocol["scenarios"]}
    noises = protocol["evaluation"]["noise_seeds"]
    allowed = {(d, s, n) for d, s in conditions.values() for n in noises}
    smoke = declaration.get("smoke", False)
    initial = [0] if smoke else config["training"]["initial_seeds"]
    extensions = [] if smoke else config["training"]["extension_seeds"]
    rows, notes = [], [f"v2 archive status: {status.get('status', 'IN_PROGRESS_OR_UNKNOWN')}; smoke={smoke}.",
                       "v2 learned direct/residual actions are held; residual LQR feedback still updates at the plant control rate."]
    for arm in config["arms"]:
        for seed in [*initial, *extensions]:
            folder = root / arm / f"seed-{seed}"
            seed_status_path = folder / "status.json"
            seed_status = (reader.read(seed_status_path) if seed_status_path.exists() else
                           status.get("seeds", {}).get(f"{arm}-{seed}", {}))
            outcomes_path = folder / "evaluation/outcomes.json"
            if outcomes_path.exists():
                outcomes = reader.read(outcomes_path)
            else:
                # Bounded compact metric files also support interrupted evaluations.
                paths = sorted((folder / "evaluation").glob("d*-n*.json"))
                if len(paths) > len(allowed):
                    raise ValueError("Too many compact episode metric files")
                outcomes = [reader.read(p) for p in paths]
            seen = set()
            for r in outcomes:
                identity = (r["delay_s"], r["scenario"], r["noise_seed"])
                if (r["controller"] != arm or r["policy_seed"] != seed or
                        identity not in allowed or identity in seen):
                    raise ValueError("Duplicated or unexpected v2 episode identity")
                seen.add(identity)
            extension = status.get("extensions", {}).get(arm)
            scheduled = seed in initial or extension is True or bool(outcomes or seed_status)
            state = seed_status.get("status", "PENDING") if scheduled else (
                "NOT_SCHEDULED" if extension is False else "EXTENSION_UNDECIDED")
            for condition in ["all", *conditions]:
                selected = outcomes if condition == "all" else [r for r in outcomes if
                    (r["delay_s"], r["scenario"]) == conditions[condition]]
                total = (len(allowed) if condition == "all" else len(noises)) if scheduled else 0
                if smoke:
                    # Smoke is a separate implementation check, never a full panel.
                    panel = [(d, s["name"], n) for d in protocol["plant"]["fixed_delays_s"]
                             for s in protocol["scenarios"] for n in noises]
                    panel = panel[:config["smoke"]["evaluation_cases_per_arm"]]
                    total = sum(condition == "all" or (d, s) == conditions[condition] for d, s, _ in panel)
                row = base_row("v2-smoke" if smoke else "v2", arm, seed, condition,
                               total, len(selected), state, action_hz, plant_hz)
                for key, field in [("strict_success", "success"), ("survival", "survived")]:
                    known = [r[field] for r in selected if isinstance(r.get(field), bool)]
                    row[key] = count_metric(sum(known), len(known), total)
                for key in METRICS:
                    row[key] = metric([(validate_metric(key, r[key]), 1)
                                       for r in selected if r.get(key) is not None], total)
                row["training_transitions"] = seed_status.get("policy_transitions")
                row["training_budget"] = seed_status.get("budget")
                rows.append(row)
    return rows, notes


def load_report(v1_path=None, v2_root=None):
    reader = Reader()
    rows, notes = [], list(NOTES)
    if v1_path:
        values, extra = v1(reader, Path(v1_path).resolve())
        rows.extend(values)
        notes.extend(extra)
    if v2_root:
        values, extra = v2(reader, Path(v2_root).resolve())
        rows.extend(values)
        notes.extend(extra)
        notes.append("v2 does not rerun LQR; the supplied v1 reference is historical, not a concurrent v2 replicate.")
    if not rows:
        raise ValueError("Supply --v1-aggregate and/or --v2-archive")
    return {"schema_version": 1, "rows": rows, "notes": notes, "sources": reader.sources,
            "json_bytes_read": reader.bytes}


def label(row):
    seed = "reference" if row["seed"] is None else f"seed {row['seed']}"
    return f"{row['version']} {row['controller']} {seed}"


def fmt(value):
    if value is None:
        return "NA"
    if isinstance(value, list):
        return "[" + ", ".join(fmt(v) for v in value) + "]"
    return f"{value:.5g}"


def continuous_cell(m):
    value = m["mean"]
    if value is None and m["available_only_mean"] is not None:
        return f"NA; available-only {fmt(m['available_only_mean'])} ({m['available_episodes']}/{m['total_episodes']})"
    return f"{fmt(value)} ({m['available_episodes']}/{m['total_episodes']})"


def count_cell(m):
    if m["count"] is None:
        return f"NA (0/{m['total_episodes']} known)"
    return f"{m['count']}/{m['total_episodes']} ({m['available_episodes']} known; rate {fmt(m['rate'])})"


def markdown(report):
    lines = ["# Saved controller evidence", "", "All seeds, descriptive; per-condition values are in report.json and comparison.csv.", "",
             "| Controller | State | Action / plant Hz | Observed / expected | Strict success | Survival | Duration s | Recovery s | Penalized recovery s | Command effort [wheel, hip] Nm² s | Applied effort [wheel, hip] Nm² s |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in report["rows"]:
        if r["condition"] != "all":
            continue
        cells = [label(r), r["state"], f"{fmt(r['policy_action_hz'])} / {fmt(r['plant_control_hz'])}",
                 f"{r['observed_episodes']} / {r['expected_episodes']}", count_cell(r["strict_success"]),
                 count_cell(r["survival"]), *[continuous_cell(r[k]) for k in METRICS]]
        lines.append("| " + " | ".join(cells) + " |")
    lines.extend(["", *[f"- {n}" for n in report["notes"]], "", "Sources:", "",
                  *[f"- `{p}`" for p in report["sources"]], ""])
    return "\n".join(lines)


def svg_plot(rows, key, title, vector=False):
    """Dependency-free SVG; missing values are text, never zero-height observations."""
    values = []
    for r in rows:
        m = r[key]
        value = m.get("rate") if key in ("strict_success", "survival") else m["mean"]
        values.append(value)
    flat = [v for value in values if value is not None for v in (value if vector else [value])]
    xmax = 1. if key in ("strict_success", "survival") else max(flat, default=1.) * 1.1
    xmax = xmax or 1.
    height = 110 + len(rows) * 64
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{height}" viewBox="0 0 1100 {height}" role="img">',
             f'<title>{html.escape(title)}</title>', '<rect width="100%" height="100%" fill="white"/>',
             '<g font-family="sans-serif" font-size="13" fill="#182838">',
             f'<text x="20" y="26" font-size="18">{html.escape(title)}</text>',
             '<text x="20" y="49">Descriptive all-slot means/rates; NA is unavailable. No confidence intervals. Every seed shown.</text>',
             f'<text x="300" y="70">0</text><text x="850" y="70">{fmt(xmax)}</text>']
    for i, (r, value) in enumerate(zip(rows, values)):
        y = 95 + i * 64
        parts.append(f'<text x="20" y="{y}">{html.escape(label(r))}</text>')
        if value is None:
            m = r[key]
            parts.append(f'<text x="300" y="{y}">NA ({m["available_episodes"]}/{m["total_episodes"]} available)</text>')
        else:
            for j, v in enumerate(value if vector else [value]):
                width = number(v) / xmax * 550
                if width < 0:
                    raise ValueError("Negative saved physical metric")
                parts.append(f'<rect x="300" y="{y-12+j*20}" width="{width:.3f}" height="15" fill="{["#216b91", "#a04e18"][j]}"/>')
                parts.append(f'<text x="870" y="{y+j*20}">{fmt(v)}{[" wheel", " hip"][j] if vector else ""}</text>')
        parts.append(f'<text x="20" y="{y+38}" font-size="11">{html.escape(r["state"])}; {fmt(r["policy_action_hz"])} Hz action; {r["observed_episodes"]}/{r["expected_episodes"]} episodes</text>')
    parts.extend(['</g>', '</svg>'])
    return "\n".join(parts)


def write_report(report, output, protected=()):
    output = Path(output).resolve()
    repository = Path(__file__).resolve().parents[3]
    roots = [repository, *[Path(p).resolve() for p in protected]]
    if any(output == p or p in output.parents for p in roots):
        raise ValueError("Output must be outside the repository and input evidence roots")
    output.mkdir(parents=True, exist_ok=False)
    (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    (output / "comparison.md").write_text(markdown(report))
    with (output / "comparison.csv").open("w", newline="") as stream:
        fields = list(dict.fromkeys(k for row in report["rows"] for k in row))
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in report["rows"]:
            writer.writerow({k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in row.items()})
    rows = [r for r in report["rows"] if r["condition"] == "all"]
    for key, title, vector in [
        ("strict_success", "Strict success rate", False), ("survival", "Survival rate", False),
        ("duration_s", "Mean episode duration (s)", False),
        ("recovery_time_after_event_s", "Recovery after event end (s); null is unavailable", False),
        ("penalized_recovery_s", "Penalized recovery (s); saved failure penalty retained", False),
        ("command_effort_Nm2_s", "Command torque effort (Nm² s); wheel / hip", True),
        ("applied_effort_Nm2_s", "Applied torque effort (Nm² s); wheel / hip", True),
    ]:
        (output / f"{key}.svg").write_text(svg_plot(rows, key, title, vector))
