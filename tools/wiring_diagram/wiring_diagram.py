#!/usr/bin/env python3
"""Fritzing-style breadboard wiring diagrams from a YAML spec.

Every wire is routed by explicit waypoints written in the spec; the tool never
routes on its own.  It resolves pin coordinates (Fritzing .fzp connector ->
breadboard-view SVG element centre), draws boards, a generated breadboard,
resistors and LEDs, then checks the geometry and marks violations in magenta.

  python wiring_diagram.py spec.yaml --print-pins nuc 'D[0-9]|PB'   # pin x,y
  python wiring_diagram.py spec.yaml --output-dir figs --grid       # draft
  python wiring_diagram.py spec.yaml --output-dir figs --strict     # final
"""
from __future__ import annotations

import argparse
import html
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

MIN_GAP = 8          # parallel wires closer than this (px) count as a shared lane
PIN_CLEARANCE = 7    # a wire may not pass this close to another wire's pin
MAX_JOG = 25         # longest sideways jog allowed while a wire is still over its own board
AXIS_TOL = 1.5       # |dx| or |dy| below this counts as axis-aligned (pin grids are not exact)
TEXT_W = 0.56        # average glyph width / font size, for text boxes

RESISTOR_CODES = ["#000000", "#8b4513", "#e00000", "#ff8c00", "#ffd700",
                  "#00a000", "#0050ff", "#8a2be2", "#808080", "#ffffff"]


# ---------------------------------------------------------------- spec / parts
def load_spec(path):
    import yaml
    return yaml.safe_load(Path(path).read_text())


def element_centre(el):
    tag = el.tag.rsplit("}", 1)[-1]
    f = lambda k: float(el.get(k, 0) or 0)
    if tag in ("circle", "ellipse"):
        c = (f("cx"), f("cy"))
    elif tag == "rect":
        c = (f("x") + f("width") / 2, f("y") + f("height") / 2)
    elif tag == "line":
        c = ((f("x1") + f("x2")) / 2, (f("y1") + f("y2")) / 2)
    elif tag == "g":
        kids = []
        for k in el:
            ka, kb, kc, kd, ke, kf = parse_transform(k.get("transform"))
            x, y = element_centre(k)
            kids.append((ka * x + kc * y + ke, kb * x + kd * y + kf))
        if not kids:
            raise ValueError(f"empty group {el.get('id')!r}")
        c = (sum(k[0] for k in kids) / len(kids), sum(k[1] for k in kids) / len(kids))
    else:  # path/polygon: centre of the absolute coordinate extent
        nums = [float(n) for n in re.findall(r"-?\d*\.?\d+(?:e-?\d+)?", el.get("d", el.get("points", "")))]
        if len(nums) < 2:
            raise ValueError(f"no geometry for SVG element {el.get('id')!r}")
        xs, ys = nums[0::2], nums[1::2]
        c = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    return c


def parse_transform(t):
    """SVG transform attribute -> affine matrix (a, b, c, d, e, f)."""
    m = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    for name, args in re.findall(r"(\w+)\s*\(([^)]*)\)", t or ""):
        v = [float(x) for x in re.split(r"[\s,]+", args.strip()) if x]
        if name == "translate":
            n = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == "scale":
            n = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == "matrix":
            n = tuple(v)
        elif name == "rotate":
            r = math.radians(v[0])
            n = (math.cos(r), math.sin(r), -math.sin(r), math.cos(r), 0, 0)
            if len(v) == 3:
                n = mat_mul(mat_mul((1, 0, 0, 1, v[1], v[2]), n), (1, 0, 0, 1, -v[1], -v[2]))
        else:
            raise ValueError(f"unsupported SVG transform {name!r}")
        m = mat_mul(m, n)
    return m


def mat_mul(m, n):
    a, b, c, d, e, f = m
    A, B, C, D, E, F = n
    return (a * A + c * B, b * A + d * B, a * C + c * D, b * C + d * D, a * E + c * F + e, b * E + d * F + f)


def pin_centre(el, parents):
    """Element centre in SVG user space, applying its own and every ancestor's transform."""
    x, y = element_centre(el)
    node = el
    while node is not None:
        a, b, c, d, e, f = parse_transform(node.get("transform"))
        x, y = a * x + c * y + e, b * x + d * y + f
        node = parents.get(node)
    return x, y


def viewbox(root):
    vb = root.get("viewBox")
    if vb:
        return tuple(map(float, re.split(r"[,\s]+", vb.strip())))
    num = lambda v: float(re.match(r"[\d.]+", v).group())
    return 0.0, 0.0, num(root.get("width")), num(root.get("height"))


class Part:
    """A placed SVG part: local SVG coordinates -> canvas coordinates."""

    def __init__(self, spec, base):
        self.spec = spec
        self.id = spec["id"]
        self.root = ET.parse(base / spec["svg"]).getroot()
        self.vb = viewbox(self.root)
        self.scale = float(spec.get("scale", 1))
        self.rot = float(spec.get("rotation", 0))
        self.x, self.y = float(spec["x"]), float(spec["y"])
        by_id = {e.get("id"): e for e in self.root.iter() if e.get("id")}
        parents = {ch: par for par in self.root.iter() for ch in par}
        refs = {}
        if spec.get("fzp"):
            for c in ET.parse(base / spec["fzp"]).getroot().iter("connector"):
                p = c.find("./views/breadboardView/p")
                if p is not None and p.get("svgId"):
                    refs.setdefault(c.get("name"), p.get("svgId"))
                    refs[c.get("id")] = p.get("svgId")
        if spec.get("svg_pin_prefix"):
            pre = spec["svg_pin_prefix"]
            refs.update({k[len(pre):]: k for k in by_id if k.startswith(pre)})
        for name, val in (spec.get("extra_pins") or {}).items():
            refs[name] = refs.get(val, val) if isinstance(val, str) else val
        self.pins = {}
        for name, ref in refs.items():
            if isinstance(ref, str):
                if ref not in by_id:
                    raise KeyError(f"{self.id}.{name}: SVG element {ref!r} not found")
                self.pins[name] = self.to_canvas(pin_centre(by_id[ref], parents))
            else:
                self.pins[name] = self.to_canvas(ref)
        w, h = self.vb[2], self.vb[3]
        corners = [self.to_canvas((self.vb[0] + a, self.vb[1] + b)) for a, b in ((0, 0), (w, 0), (w, h), (0, h))]
        self.box = (min(c[0] for c in corners), min(c[1] for c in corners),
                    max(c[0] for c in corners), max(c[1] for c in corners))

    def to_canvas(self, p):
        lx, ly = (p[0] - self.vb[0]) * self.scale, (p[1] - self.vb[1]) * self.scale
        a = math.radians(self.rot)
        return (round(self.x + lx * math.cos(a) - ly * math.sin(a), 1),
                round(self.y + lx * math.sin(a) + ly * math.cos(a), 1))

    def svg(self):
        body = "".join(ET.tostring(ch, encoding="unicode") for ch in self.root)
        # Prefix ids so several SVGs (or two copies of one) do not clash.
        pre = f"{self.id}__"
        body = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{pre}{m.group(1)}"', body)
        body = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{pre}{m.group(1)})", body)
        body = re.sub(r'href="#([^"]+)"', lambda m: f'href="#{pre}{m.group(1)}"', body)
        vx, vy = self.vb[:2]
        return (f'<g transform="translate({self.x} {self.y}) rotate({self.rot}) '
                f'scale({self.scale}) translate({-vx} {-vy})">{body}</g>')


class Breadboard:
    """Generated half-size breadboard: rails T-/T+, rows a-e | f-j, rails B-/B+."""

    def __init__(self, spec):
        self.spec = spec
        self.id = spec["id"]
        self.x, self.y = float(spec["x"]), float(spec["y"])
        self.cols = int(spec.get("cols", 30))
        self.p = p = float(spec.get("pitch", 18))
        self.w = (self.cols + 3) * p
        rows = {"T-": 1.2, "T+": 2.2, "B-": 16.8, "B+": 17.8}
        rows.update({r: 4.5 + i for i, r in enumerate("abcde")})
        rows.update({r: 10.5 + i for i, r in enumerate("fghij")})
        self.rows = {k: round(self.y + v * p, 1) for k, v in rows.items()}
        self.h = 19.0 * p
        self.box = (self.x, self.y, self.x + self.w, self.y + self.h)
        self.pins = {f"{r}{c}": (self.colx(c), self.rows[r]) for r in rows for c in range(1, self.cols + 1)}

    def colx(self, c):
        return round(self.x + (c + 1) * self.p, 1)

    def svg(self):
        p, x, y, w = self.p, self.x, self.y, self.w
        o = [f'<rect x="{x}" y="{y}" width="{w}" height="{self.h}" rx="6" fill="#f2f0ea" stroke="#c9c5b8" stroke-width="2"/>',
             f'<rect x="{x}" y="{self.rows["e"] + 0.75 * p}" width="{w}" height="{p * 0.5}" fill="#dedad0"/>']
        for r in ("T-", "T+", "B-", "B+"):
            minus = r.endswith("-")
            col = "#2a5bd7" if minus else "#d62828"
            ly = self.rows[r] + (-0.6 * p if minus else 0.6 * p)
            o.append(f'<line x1="{x + p}" y1="{ly}" x2="{x + w - p}" y2="{ly}" stroke="{col}" stroke-width="2"/>')
            gx = x + w - p * 0.75 if minus else x + p * 0.3
            o.append(f'<text x="{gx}" y="{self.rows[r] + 5}" font-size="14" font-weight="bold" fill="{col}">{"−" if minus else "+"}</text>')
        for cx, cy in self.pins.values():
            o.append(f'<rect x="{cx - 3.5}" y="{cy - 3.5}" width="7" height="7" rx="1" fill="#3c3a36"/>')
        for r in "abcdefghij":
            o.append(f'<text x="{x + p * 0.5}" y="{self.rows[r] + 4}" class="bb">{r}</text>')
        for c in [1] + list(range(5, self.cols + 1, 5)):
            o.append(f'<text x="{self.colx(c)}" y="{self.rows["a"] - 0.7 * p}" class="bb" text-anchor="middle">{c}</text>')
        return "\n".join(o)


def resistor_svg(a, b, ohms):
    """Axial resistor drawn between two holes (horizontal or vertical)."""
    digits = str(int(ohms))
    bands = [RESISTOR_CODES[int(digits[0])], RESISTOR_CODES[int(digits[1])],
             RESISTOR_CODES[len(digits) - 2], "#c8a43a"]
    (x1, y1), (x2, y2) = a, b
    vert = abs(x1 - x2) < 1e-6
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    L, T = 36, 12
    o = [f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#9a9a9a" stroke-width="3"/>']
    if vert:
        o.append(f'<rect x="{cx - T / 2}" y="{cy - L / 2}" width="{T}" height="{L}" rx="5" fill="#e3c99a" stroke="#8a7350"/>')
        for i, col in enumerate(bands):
            o.append(f'<rect x="{cx - T / 2}" y="{cy - L / 2 + 6 + i * 6.5 + (3 if i == 3 else 0)}" width="{T}" height="3.5" fill="{col}"/>')
    else:
        o.append(f'<rect x="{cx - L / 2}" y="{cy - T / 2}" width="{L}" height="{T}" rx="5" fill="#e3c99a" stroke="#8a7350"/>')
        for i, col in enumerate(bands):
            o.append(f'<rect x="{cx - L / 2 + 6 + i * 6.5 + (3 if i == 3 else 0)}" y="{cy - T / 2}" width="3.5" height="{T}" fill="{col}"/>')
    return "\n".join(o)


def led_svg(anode, cathode, colour):
    """5 mm LED standing on two holes in one row; bent leg = anode (long leg)."""
    (ax, ay), (kx, ky) = anode, cathode
    cx, top = (ax + kx) / 2, min(ay, ky) - 30
    return "\n".join([
        f'<polyline points="{ax},{ay} {ax},{top + 20} {cx - 4},{top + 13}" fill="none" stroke="#9a9a9a" stroke-width="2.5"/>',
        f'<polyline points="{kx},{ky} {kx},{top + 20} {cx + 4},{top + 13}" fill="none" stroke="#9a9a9a" stroke-width="2.5"/>',
        f'<path d="M{cx - 10} {top + 13} v-7 a10 10 0 0 1 20 0 v7 z" fill="{colour}" stroke="#333" stroke-width="1.2"/>',
        f'<rect x="{cx - 12}" y="{top + 12}" width="24" height="4" rx="1" fill="{colour}" stroke="#333" stroke-width="1"/>',
        f'<path d="M{cx - 5} {top + 2} a5 5 0 0 1 5 -5" fill="none" stroke="#fff" stroke-opacity="0.75" stroke-width="1.8"/>',
    ])


# ---------------------------------------------------------------- routing
def build_route(start, goal, via):
    """Waypoints: [x, y] absolute, 'x=N' move horizontally, 'y=N' move vertically."""
    pts = [start]
    for v in via or []:
        cur = pts[-1]
        if isinstance(v, str):
            axis, val = (s.strip() for s in v.split("="))
            pts.append((float(val), cur[1]) if axis == "x" else (cur[0], float(val)))
        else:
            pts.append((float(v[0]), float(v[1])))
    pts.append(goal)
    out = []
    for p in pts:
        if not out or abs(p[0] - out[-1][0]) > 1e-6 or abs(p[1] - out[-1][1]) > 1e-6:
            out.append(p)
    return out


def segments(pts):
    return list(zip(pts, pts[1:]))


def is_h(a, b):
    return abs(a[1] - b[1]) < AXIS_TOL


def inside(p, box):
    return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]


def seg_hits_box(a, b, box):
    x0, y0, x1, y1 = box
    if is_h(a, b):
        return y0 < a[1] < y1 and max(min(a[0], b[0]), x0) < min(max(a[0], b[0]), x1)
    return x0 < a[0] < x1 and max(min(a[1], b[1]), y0) < min(max(a[1], b[1]), y1)


def text_box(x, y, text, size, anchor="start"):
    w = len(text) * size * TEXT_W
    x0 = x - w if anchor == "end" else x - w / 2 if anchor == "middle" else x
    return (x0 - 2, y - size * 0.85, x0 + w + 2, y + size * 0.25)


def check(wires, routes, obstacles, texts, canvas, own_parts):
    """Return a list of (message, (x, y)) violations."""
    bad = []
    W, H = canvas
    pins = {(w["id"], k): routes[w["id"]][0 if k == "from" else -1] for w in wires for k in ("from", "to")}
    for w in wires:
        segs = segments(routes[w["id"]])
        src, dst = own_parts[w["id"]]
        # Leading segments may stay on the source board and trailing ones on the
        # destination board (escape stubs and short jogs between pin rows).
        lead = 0
        while lead < len(segs) and src in obstacles and inside(segs[lead][0], obstacles[src]) and inside(segs[lead][1], obstacles[src]):
            lead += 1
        if lead < len(segs) and src in obstacles and inside(segs[lead][0], obstacles[src]):
            lead += 1          # the segment that leaves the board
        lead = max(lead, 1)
        trail = 0
        while trail < len(segs) and dst in obstacles and inside(segs[-1 - trail][0], obstacles[dst]) and inside(segs[-1 - trail][1], obstacles[dst]):
            trail += 1
        if trail < len(segs) and dst in obstacles and inside(segs[-1 - trail][1], obstacles[dst]):
            trail += 1         # the segment that enters the board
        trail = max(trail, 1)
        for i, (a, b) in enumerate(segs):
            if not is_h(a, b) and abs(a[0] - b[0]) >= AXIS_TOL:
                bad.append((f"{w['id']}: diagonal segment {a} -> {b}", a))
            for p in (a, b):
                if not (0 <= p[0] <= W and 0 <= p[1] <= H):
                    bad.append((f"{w['id']}: point {p} off canvas", p))
            on_src, on_dst = i < lead, i >= len(segs) - trail
            # sideways jogs fully on the wire's own board must stay short
            jog = (on_src and 0 < i and inside(b, obstacles[src])) or \
                  (on_dst and i < len(segs) - 1 and inside(a, obstacles[dst]))
            if jog:
                if math.dist(a, b) > MAX_JOG:
                    bad.append((f"{w['id']}: {math.dist(a, b):.0f} px run over its own board", ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)))
            for pid, box in obstacles.items():
                mine = (on_src and pid == src) or (on_dst and pid == dst)
                if not mine and seg_hits_box(a, b, box):
                    bad.append((f"{w['id']}: crosses part {pid} on {a} -> {b}", ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)))
            for t, box in texts:
                if seg_hits_box(a, b, box):
                    bad.append((f"{w['id']}: crosses text {t!r}", ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)))
            for (oid, k), p in pins.items():
                if oid == w["id"]:
                    continue
                if is_h(a, b):
                    near = abs(p[1] - a[1]) < PIN_CLEARANCE and min(a[0], b[0]) - PIN_CLEARANCE < p[0] < max(a[0], b[0]) + PIN_CLEARANCE
                else:
                    near = abs(p[0] - a[0]) < PIN_CLEARANCE and min(a[1], b[1]) - PIN_CLEARANCE < p[1] < max(a[1], b[1]) + PIN_CLEARANCE
                if near:
                    bad.append((f"{w['id']}: passes over the {k} pin of {oid} at {p}", p))
    # shared or too-close parallel lanes between different wires
    flat = [(w["id"], a, b) for w in wires for a, b in segments(routes[w["id"]])]
    for i, (n1, a1, b1) in enumerate(flat):
        h1 = is_h(a1, b1)
        for n2, a2, b2 in flat[i + 1:]:
            if n1 == n2 or h1 != is_h(a2, b2):
                continue
            ax = 1 if h1 else 0      # index of the lane coordinate
            lo = max(min(a1[1 - ax], b1[1 - ax]), min(a2[1 - ax], b2[1 - ax]))
            hi = min(max(a1[1 - ax], b1[1 - ax]), max(a2[1 - ax], b2[1 - ax]))
            if abs(a1[ax] - a2[ax]) < MIN_GAP and hi - lo > AXIS_TOL:
                where = ((lo + hi) / 2, a1[ax]) if h1 else (a1[ax], (lo + hi) / 2)
                bad.append((f"{n1} / {n2}: parallel lanes {abs(a1[ax] - a2[ax]):.0f} px apart over {hi - lo:.0f} px", where))
    return bad


def count_crossings(wires, routes):
    flat = [(w["id"], a, b) for w in wires for a, b in segments(routes[w["id"]])]
    n = 0
    for i, (n1, a1, b1) in enumerate(flat):
        for n2, a2, b2 in flat[i + 1:]:
            if n1 == n2 or is_h(a1, b1) == is_h(a2, b2):
                continue
            (ha, hb), (va, vb) = ((a1, b1), (a2, b2)) if is_h(a1, b1) else ((a2, b2), (a1, b1))
            if min(ha[0], hb[0]) < va[0] < max(ha[0], hb[0]) and min(va[1], vb[1]) < ha[1] < max(va[1], vb[1]):
                n += 1
    return n


# ---------------------------------------------------------------- render
def resolve(ref, parts):
    pid, pin = ref.split(".", 1)
    try:
        return parts[pid].pins[pin]
    except KeyError:
        raise KeyError(f"unknown pin {ref!r}") from None


def build(spec_path):
    spec_path = Path(spec_path).resolve()
    spec = load_spec(spec_path)
    parts = {p["id"]: Breadboard(p) if p.get("kind") == "breadboard" else Part(p, spec_path.parent)
             for p in spec.get("parts", [])}
    return spec, parts


def render(spec_path, output_dir, png_width=None, strict=False, grid=False):
    spec, parts = build(spec_path)
    W, H = spec.get("canvas", [2400, 1500])
    wires = spec.get("wires", [])
    routes = {w["id"]: build_route(resolve(w["from"], parts), resolve(w["to"], parts), w.get("via"))
              for w in wires}
    own = {w["id"]: (w["from"].split(".")[0], w["to"].split(".")[0]) for w in wires}
    obstacles = {pid: p.box for pid, p in parts.items() if p.spec.get("obstacle", True)}

    texts, text_svg = [], []
    def add_text(x, y, s, size=15, anchor="start", weight="normal", colour="#17212b", style="normal"):
        texts.append((s, text_box(x, y, s, size, anchor)))
        text_svg.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" font-style="{style}" '
                        f'fill="{colour}" text-anchor="{anchor}">{html.escape(s)}</text>')
    if spec.get("title"):
        add_text(32, 46, spec["title"], 30, weight="bold")
    for p in parts.values():
        if p.spec.get("title"):
            tx, ty = p.spec.get("title_xy", [p.box[0], p.box[1] - 12])
            add_text(tx, ty, p.spec["title"], 19, p.spec.get("title_anchor", "start"), weight="bold")
    for n in spec.get("notes", []):
        size = n.get("size", 15)
        for i, line in enumerate(str(n["text"]).split("\n")):
            add_text(n["x"], n["y"] + i * size * 1.3, line, size, n.get("anchor", "start"),
                     n.get("weight", "normal"), n.get("colour", "#17212b"), n.get("style", "normal"))
    legend_svg = []
    lg = spec.get("legend")
    if lg:
        x, y, size = lg["x"], lg["y"], lg.get("size", 15)
        rows = math.ceil(len(lg["items"]) / lg.get("columns", 1))
        if lg.get("title"):
            add_text(x, y, lg["title"], size + 2, weight="bold")
        for i, it in enumerate(lg["items"]):
            cx, cy = x + (i // rows) * lg.get("column_width", 560), y + 30 + (i % rows) * size * 1.65
            dash = ' stroke-dasharray="10 6"' if it.get("dashed") else ""
            legend_svg.append(f'<line x1="{cx}" y1="{cy - 5}" x2="{cx + 40}" y2="{cy - 5}" stroke="{it["colour"]}" '
                              f'stroke-width="6" stroke-linecap="round"{dash}/>')
            add_text(cx + 52, cy, it["label"], size)

    bad = check(wires, routes, obstacles, texts, (W, H), own)

    o = [f'<svg xmlns="{SVG_NS}" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         '<style>text{font-family:Arial,Helvetica,sans-serif}.bb{font-size:10px;fill:#8a877d}</style>',
         f'<rect width="{W}" height="{H}" fill="#ffffff"/>']
    if grid:
        for g in range(0, max(W, H), 50):
            col = "#9fc5ff" if g % 250 == 0 else "#e6efff"
            if g < W:
                o.append(f'<line x1="{g}" y1="0" x2="{g}" y2="{H}" stroke="{col}"/>')
            if g < H:
                o.append(f'<line x1="0" y1="{g}" x2="{W}" y2="{g}" stroke="{col}"/>')
    for p in parts.values():
        o.append(p.svg())
    for c in spec.get("components", []):
        if c["kind"] == "resistor":
            o.append(resistor_svg(resolve(c["from"], parts), resolve(c["to"], parts), c["ohms"]))
        elif c["kind"] == "led":
            o.append(led_svg(resolve(c["anode"], parts), resolve(c["cathode"], parts), c["colour"]))
    for w in wires:
        pts = routes[w["id"]]
        d = "M" + " L".join(f"{x} {y}" for x, y in pts)
        dash = ' stroke-dasharray="14 9"' if w.get("dashed") else ""
        width = w.get("width", 5)
        o.append(f'<path d="{d}" fill="none" stroke="#000" stroke-opacity="0.35" stroke-width="{width + 2.5}" '
                 f'stroke-linejoin="round" stroke-linecap="round"{dash}/>')
        o.append(f'<path d="{d}" fill="none" stroke="{w["colour"]}" stroke-width="{width}" '
                 f'stroke-linejoin="round" stroke-linecap="round"{dash}/>')
        for x, y in (pts[0], pts[-1]):
            o.append(f'<circle cx="{x}" cy="{y}" r="{width * 0.9}" fill="{w["colour"]}" stroke="#222" stroke-width="1.5"/>')
    o.extend(legend_svg)
    for (_, box), t in zip(texts, text_svg):
        o.append(f'<rect x="{box[0]}" y="{box[1]}" width="{box[2] - box[0]}" height="{box[3] - box[1]}" fill="#fff" fill-opacity="0.85"/>')
        o.append(t)
    if grid:
        for g in range(0, max(W, H), 250):
            o.append(f'<text x="{g + 2}" y="12" font-size="12" fill="#2a60c0">{g}</text>' if g < W else "")
            o.append(f'<text x="2" y="{g - 3}" font-size="12" fill="#2a60c0">{g}</text>' if 0 < g < H else "")
    for _, (x, y) in bad:
        o.append(f'<circle cx="{x}" cy="{y}" r="16" fill="none" stroke="#ed00ff" stroke-width="5"/>')
    o.append("</svg>")
    svg = "\n".join(o)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    sp = out / (spec.get("output", "wiring") + ("-grid" if grid else "") + ".svg")
    sp.write_text(svg)
    import cairosvg
    if not grid:
        cairosvg.svg2pdf(bytestring=svg.encode(), write_to=str(sp.with_suffix(".pdf")))
    cairosvg.svg2png(bytestring=svg.encode(), write_to=str(sp.with_suffix(".png")), output_width=png_width or int(W))
    for w in wires:
        print(f"{w['id']:<22} {w['from']:<16} -> {w['to']:<16} {w['colour']}")
    for msg, _ in bad:
        print("VIOLATION:", msg)
    print(f"crossings: {count_crossings(wires, routes)} (allowed, keep low)")
    print(f"check: {'PASS' if not bad else f'{len(bad)} violation(s)'}; wrote {sp.with_suffix('.png')}")
    return 1 if (strict and bad) else 0


def print_pins(spec_path, part_id=None, pattern=None):
    _, parts = build(spec_path)
    for pid, p in parts.items():
        if part_id and pid != part_id:
            continue
        print(f"# {pid} box={tuple(round(v) for v in p.box)}")
        for name, (x, y) in sorted(p.pins.items(), key=lambda kv: (kv[1][1], kv[1][0])):
            if not pattern or re.search(pattern, name):
                print(f"{pid}.{name:<22} {x:8.1f} {y:8.1f}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--output-dir", default=".")
    ap.add_argument("--png-width", type=int)
    ap.add_argument("--strict", action="store_true", help="exit 1 if any check fails")
    ap.add_argument("--grid", action="store_true", help="write <output>-grid.png with a 50 px coordinate grid")
    ap.add_argument("--print-pins", nargs="*", metavar="PART [REGEX]", help="print resolved pin coordinates")
    a = ap.parse_args(argv)
    if a.print_pins is not None:
        return print_pins(a.spec, *a.print_pins[:2])
    return render(a.spec, a.output_dir, a.png_width, a.strict, a.grid)


if __name__ == "__main__":
    sys.exit(main())
