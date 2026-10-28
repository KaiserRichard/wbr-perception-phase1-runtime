#!/usr/bin/env python3
"""Spec-driven breadboard wiring diagram renderer and geometry self-checker."""
from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)


def load_spec(path):
    raw = Path(path).read_text()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            import yaml
            return yaml.safe_load(raw)
        except ImportError:
            return parse_yaml_subset(raw)


def parse_yaml_subset(raw):
    """Small YAML reader for mappings, lists, inline lists/maps, and scalars."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    lines = [(len(s) - len(s.lstrip()), s.strip()) for s in raw.splitlines()
             if s.strip() and not s.lstrip().startswith("#")]
    def scalar(s):
        s = s.strip()
        if s in ("true", "false", "null", "~"):
            return {"true": True, "false": False, "null": None, "~": None}[s]
        if s.startswith(("'", '"')):
            return json.loads(s) if s.startswith('"') else s[1:-1].replace("''", "'")
        if s.startswith("[") or s.startswith("{"):
            try: return json.loads(s.replace("'", '"'))
            except json.JSONDecodeError: return s
        try: return float(s) if "." in s else int(s)
        except ValueError: return s
    def block(i, indent):
        is_list = lines[i][1].startswith("- ")
        out = [] if is_list else {}
        while i < len(lines) and lines[i][0] == indent:
            text = lines[i][1]
            if is_list:
                if not text.startswith("- "): break
                item = text[2:]; i += 1
                if ":" in item:
                    k, v = item.split(":", 1); obj = {k.strip(): scalar(v)} if v.strip() else {k.strip(): {}}
                    if not v.strip() and i < len(lines) and lines[i][0] > indent:
                        obj[k.strip()], i = block(i, lines[i][0])
                    while i < len(lines) and lines[i][0] > indent:
                        child_indent, child = lines[i]
                        if child_indent == indent + 2 and ":" in child and not child.startswith("-"):
                            ck, cv = child.split(":",1); i += 1
                            if cv.strip(): obj[ck.strip()] = scalar(cv)
                            elif i < len(lines) and lines[i][0] > child_indent: obj[ck.strip()],i=block(i,lines[i][0])
                            else: obj[ck.strip()]={}
                        else: break
                    out.append(obj)
                else: out.append(scalar(item))
            else:
                if text.startswith("- ") or ":" not in text: break
                k,v=text.split(":",1); i+=1
                if v.strip(): out[k.strip()]=scalar(v)
                elif i < len(lines) and lines[i][0] > indent: out[k.strip()],i=block(i,lines[i][0])
                else: out[k.strip()]={}
        return out,i
    if not lines: return {}
    return block(0, lines[0][0])[0]


def bbox_center(el):
    tag = el.tag.rsplit("}", 1)[-1]
    if tag in ("circle", "ellipse"):
        return float(el.get("cx", 0)), float(el.get("cy", 0))
    if tag == "rect":
        return float(el.get("x", 0)) + float(el.get("width", 0))/2, float(el.get("y", 0)) + float(el.get("height", 0))/2
    if tag in ("line",):
        return (float(el.get("x1", 0))+float(el.get("x2", 0)))/2, (float(el.get("y1", 0))+float(el.get("y2", 0)))/2
    if tag == "text":
        return float(el.get("x", 0)), float(el.get("y", 0))
    # Fritzing pads are usually rect/circle; path fallback uses path's declared coordinate extent.
    coords = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", el.get("d", ""))]
    if len(coords) >= 2:
        xs, ys = coords[::2], coords[1::2]
        return (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
    raise ValueError(f"Cannot find a bounding-box centre for SVG element {el.get('id')!r}")


def svg_dimensions(root):
    vb = root.get("viewBox")
    if vb:
        a = list(map(float, re.split(r"[,\s]+", vb.strip())))
        return a[0], a[1], a[2], a[3]
    def num(v): return float(re.match(r"[\d.]+", v).group())
    return 0, 0, num(root.get("width")), num(root.get("height"))


def load_part(part, base):
    p = dict(part); svg_path = (base / p["svg"]).resolve()
    root = ET.parse(svg_path).getroot(); vx,vy,vw,vh=svg_dimensions(root)
    scale=float(p.get("scale", 1)); rotation=float(p.get("rotation", 0)); x=float(p["x"]); y=float(p["y"])
    pins={}
    if p.get("fzp"):
        fzp=ET.parse((base/p["fzp"]).resolve()).getroot()
        connector_svg={}
        for c in fzp.findall(".//connector"):
            pad=c.find("./views/breadboardView/p")
            if pad is not None and pad.get("svgId"):
                connector_svg[c.get("id")]=pad.get("svgId")
                pins[c.get("name")]=pad.get("svgId")
                pins[c.get("id")]=pad.get("svgId")
    else:
        connector_svg={}
    for name,val in p.get("extra_pins", {}).items(): pins[name]=connector_svg.get(val,val) if isinstance(val,str) else val
    def transform(local):
        if isinstance(local, str):
            el=next((e for e in root.iter() if e.get("id")==local),None)
            if el is None: raise KeyError(f"{p['id']}: SVG element {local!r} for pin not found")
            lx,ly=bbox_center(el)
        elif isinstance(local, dict): lx,ly=float(local["x"]),float(local["y"])
        else: lx,ly=map(float,local)
        lx-=vx; ly-=vy
        a=math.radians(rotation); rx=lx*math.cos(a)-ly*math.sin(a); ry=lx*math.sin(a)+ly*math.cos(a)
        return x+rx*scale,y+ry*scale
    resolved={}
    for name, value in pins.items():
        try: resolved[name]=transform(value)
        except KeyError: # FZP values are svg IDs; extra pin coordinates resolve directly.
            if isinstance(value,str): raise
            resolved[name]=transform(value)
    # Header grids name pins by row/column templates; rows/cols may be lists or counts.
    for gname,g in p.get("header_grids", {}).items():
        rows=g.get("rows"); cols=g.get("cols")
        if isinstance(rows,int): rows=[str(i+1) for i in range(rows)]
        if isinstance(cols,int): cols=[str(i+1) for i in range(cols)]
        ox,oy=g["origin"]; px,py=g.get("pitch", [0,0]); naming=g.get("naming", "{row}{col}")
        for ri,row in enumerate(rows):
            for ci,col in enumerate(cols):
                key=naming.format(row=row,col=col,row_index=ri,col_index=ci)
                resolved[key]=transform((float(ox)+ci*float(px),float(oy)+ri*float(py)))
    return {**p,"root":root,"bounds":part_bounds(vw*scale,vh*scale,x,y,rotation),"pins":resolved,"scale":scale,"rotation":rotation,"x":x,"y":y,"svg_path":svg_path,"viewbox":(vx,vy,vw,vh)}


def part_bounds(w,h,x,y,rotation):
    a=math.radians(rotation); pts=[]
    for px,py in ((0,0),(w,0),(w,h),(0,h)):
        pts.append((x+px*math.cos(a)-py*math.sin(a),y+px*math.sin(a)+py*math.cos(a)))
    return (min(q[0] for q in pts),min(q[1] for q in pts),max(q[0] for q in pts),max(q[1] for q in pts))


def resolve(endpoint, parts, rails):
    part,pin=endpoint.split(".",1)
    try: return parts[part]["pins"][pin]
    except KeyError: pass
    try: return rails[part][pin]
    except KeyError: raise KeyError(f"Unknown pin {endpoint!r}")


def collinear_overlap_check(routes):
    violations=[]
    segs=[]
    for name,pts in routes:
        for a,b in zip(pts,pts[1:]):
            if a[0]==b[0] and a[1]==b[1]: continue
            if a[1]==b[1]: axis="h"; lo,hi=sorted((a[0],b[0])); lane=a[1]
            elif a[0]==b[0]: axis="v"; lo,hi=sorted((a[1],b[1])); lane=a[0]
            else:
                violations.append(f"{name} non-orthogonal segment {a} -> {b}"); continue
            segs.append((name,axis,lane,lo,hi,a,b))
    for i,s in enumerate(segs):
        for t in segs[i+1:]:
            if s[0]==t[0] or s[1]!=t[1] or abs(s[2]-t[2])>1e-6: continue
            lo=max(s[3],t[3]); hi=min(s[4],t[4])
            if hi-lo>1e-6: violations.append(f"{s[0]} / {t[0]} collinear overlap at {s[1]}={s[2]} from {lo} to {hi}")
    return violations


def route_simple(start, goal, obstacles=(), bounds=None):
    # Stable two/three-segment route; collision checks are reported after routing.
    if start[0]==goal[0] or start[1]==goal[1]: return [start,goal]
    return [start,(goal[0],start[1]),goal]


def channel_route(start, goal, via, channels, spacing=12, lane_index=0, lane_axis=None):
    pts=[start]
    for item in via:
        if isinstance(item,str):
            if item not in channels: raise KeyError(f"Unknown channel {item!r}")
            x,y,w,h=channels[item]["bounds"]
            axis=channels[item].get("axis", "horizontal")
            offset=lane_index*float(channels[item].get("spacing",spacing))
            if axis in ("horizontal","h"):
                yy=y+offset
                pts.extend([(start[0],yy),(x,yy),(x+w,yy),(goal[0],yy)])
            else:
                xx=x+offset
                pts.extend([(xx,start[1]),(xx,y),(xx,y+h),(xx,goal[1])])
        elif isinstance(item,dict) and "channel" in item:
            pts.extend(channel_route(start,goal,[item["channel"]],channels,spacing,lane_index))
        else: pts.append(tuple(map(float,item)))
    pts.append(goal)
    compact=[]
    for p in pts:
        if compact and p==compact[-1]: continue
        if len(compact)>=2 and (compact[-1][0]-compact[-2][0])*(p[1]-compact[-1][1])==(compact[-1][1]-compact[-2][1])*(p[0]-compact[-1][0]): compact[-1]=p
        else: compact.append(p)
    orth=[]
    for q in compact:
        if orth and q[0]!=orth[-1][0] and q[1]!=orth[-1][1]: orth.append((q[0],orth[-1][1]))
        if not orth or q!=orth[-1]: orth.append(q)
    return orth

def segment_hits_box(a,b,box,inflate=0):
    x0,y0,x1,y1=box; x0-=inflate;y0-=inflate;x1+=inflate;y1+=inflate
    if a[1]==b[1]: return y0 < a[1] < y1 and max(min(a[0],b[0]),x0) < min(max(a[0],b[0]),x1)
    return x0 < a[0] < x1 and max(min(a[1],b[1]),y0) < min(max(a[1],b[1]),y1)


def route_astar(start, goal, obstacles, reservations, bounds, exit_points=(), cell=10):
    # Search grid is aligned to integer cell points; exact pins are joined using short cardinal stubs.
    def escape(pin, other):
        containing=[b for b in obstacles if b[0] < pin[0] < b[2] and b[1] < pin[1] < b[3]]
        if not containing: return pin
        b=containing[0]
        # Exit perpendicular to the nearest body edge; tie-break toward the destination.
        choices=[(pin[0]-b[0],(-1,0)),(b[2]-pin[0],(1,0)),(pin[1]-b[1],(0,-1)),(b[3]-pin[1],(0,1))]
        md=min(v[0] for v in choices); dirs=[v[1] for v in choices if v[0]==md]
        dx,dy=max(dirs,key=lambda d:(other[0]-pin[0])*d[0]+(other[1]-pin[1])*d[1])
        return (pin[0]+dx*(md+12),pin[1]+dy*(md+12))
    start_exit=escape(start,goal); goal_exit=escape(goal,start)
    def snap(p): return (round(p[0]/cell)*cell,round(p[1]/cell)*cell)
    s,g=snap(start_exit),snap(goal_exit); minx,miny,maxx,maxy=bounds
    exits=set(exit_points)
    def blocked(a,b):
        if min(a[0],b[0])<minx or max(a[0],b[0])>maxx or min(a[1],b[1])<miny or max(a[1],b[1])>maxy: return True
        for box in obstacles:
            # Permit only the first/last pin stub to enter its own body.
            if segment_hits_box(a,b,box,4): return True
        for _,c,d in reservations:
            if a[1]==b[1]==c[1]==d[1] and min(max(a[0],b[0]),max(c[0],d[0]))-max(min(a[0],b[0]),min(c[0],d[0]))>0: return True
            if a[0]==b[0]==c[0]==d[0] and min(max(a[1],b[1]),max(c[1],d[1]))-max(min(a[1],b[1]),min(c[1],d[1]))>0: return True
        return False
    dirs=((cell,0),(-cell,0),(0,cell),(0,-cell)); q=[(0,0,s,None)]; came={}; cost={(s,None):0}; final=None
    while q:
        _,gcost,pos,last=heapq.heappop(q); state=(pos,last)
        if state not in cost or gcost!=cost[state]: continue
        if pos==g: final=state;break
        for d in dirs:
            nxt=(pos[0]+d[0],pos[1]+d[1])
            if blocked(pos,nxt): continue
            bend=1 if last is not None and last!=d else 0
            nc=gcost+1+bend*4
            ns=(nxt,d)
            if nc<cost.get(ns,1e30):
                cost[ns]=nc;came[ns]=state;heur=(abs(g[0]-nxt[0])+abs(g[1]-nxt[1]))/cell
                heapq.heappush(q,(nc+heur,nc,nxt,d))
    if final is None:
        # Routing can still use exact custom waypoints; fail with a useful diagnostic.
        raise RuntimeError(f"No orthogonal route found from {start} to {goal}")
    path=[];cur=final
    while cur in came: path.append(cur[0]);cur=came[cur]
    path.append(s);path.reverse()
    compact=[]
    for p in path:
        if len(compact)>=2 and (compact[-1][0]-compact[-2][0])*(p[1]-compact[-1][1])==(compact[-1][1]-compact[-2][1])*(p[0]-compact[-1][0]): compact[-1]=p
        else: compact.append(p)
    # Exact perpendicular pin stubs connect the route to true pad centres.
    full=[start]
    if start_exit!=start: full.extend([start_exit,(s[0],start_exit[1])])
    full.extend(compact[1:])
    if goal_exit!=goal: full.extend([(g[0],goal_exit[1]),goal_exit])
    full.append(goal)
    orth=[]
    for p in full:
        if orth and p[0]!=orth[-1][0] and p[1]!=orth[-1][1]: orth.append((orth[-1][0],p[1]))
        if not orth or p!=orth[-1]: orth.append(p)
    return orth


def render(spec_path, output_dir, png_width=None, strict=False):
    spec_path=Path(spec_path).resolve(); base=spec_path.parent; spec=load_spec(spec_path)
    width,height=spec.get("canvas",[1800,1100]); parts={p["id"]:load_part(p,base) for p in spec.get("parts",[])}
    rails=spec.get("rails",{}); connections=spec.get("connections",[]); channels=spec.get("channels",{})
    points={c["id"]:(resolve(c["from"],parts,rails),resolve(c["to"],parts,rails)) for c in connections}
    obstacles=[p["bounds"] for p in parts.values() if p.get("obstacle",True)]
    obstacles += [tuple(t.get("bounds")) for t in spec.get("text_boxes",[]) if t.get("bounds")]
    # Sort channel users by the endpoint coordinate perpendicular to the lane.
    users={}
    for c in connections:
        for v in c.get("via",[]):
            name=v if isinstance(v,str) else v.get("channel") if isinstance(v,dict) else None
            if name: users.setdefault(name,[]).append(c)
    lane={}
    for name,cs in users.items():
        axis=channels[name].get("axis","horizontal")
        key=0 if axis in ("horizontal","h") else 1
        cs.sort(key=lambda c:(points[c["id"]][0][key]+points[c["id"]][1][key])/2)
        lane.update({(name,c["id"]):i for i,c in enumerate(cs)})
    routes=[]
    for c in connections:
        a,b=points[c["id"]]; vias=c.get("via",[])
        if vias:
            # Channel lane displacement is applied to a centerline selected per channel.
            pts=[a]
            for v in vias:
                if isinstance(v,str):
                    ch=channels[v]; x,y,w,h=ch["bounds"]; axis=ch.get("axis","horizontal"); off=lane[(v,c["id"])]*float(ch.get("spacing",12))
                    if axis in ("horizontal","h"):
                        yy=y+off; pts.extend([(pts[-1][0],yy),(x,yy),(x+w,yy)])
                    else:
                        xx=x+off; pts.extend([(xx,pts[-1][1]),(xx,y),(xx,y+h)])
                elif isinstance(v,dict) and "channel" in v:
                    name=v["channel"]; ch=channels[name]; x,y,w,h=ch["bounds"]; axis=ch.get("axis","horizontal"); off=lane[(name,c["id"])]*float(ch.get("spacing",12))
                    if axis in ("horizontal","h"):
                        yy=y+off; pts.extend([(pts[-1][0],yy),(x,yy),(x+w,yy)])
                    else:
                        xx=x+off; pts.extend([(xx,pts[-1][1]),(xx,y),(xx,y+h)])
                else: pts.append(tuple(map(float,v)))
            pts.append(b)
            # Orthogonalize and compact.
            ortho=[]
            for q in pts:
                if ortho and q[0]!=ortho[-1][0] and q[1]!=ortho[-1][1]: ortho.append((q[0],ortho[-1][1]))
                if not ortho or q!=ortho[-1]: ortho.append(q)
            pts=ortho
        else: pts=route_simple(a,b)
        routes.append((c["id"],pts))
    violations=[]
    for c,(_,pts) in zip(connections,routes):
        if not pts or pts[0]!=points[c["id"]][0] or pts[-1]!=points[c["id"]][1]: violations.append(f"{c['id']} endpoint mismatch: {pts[0] if pts else None} -> {pts[-1] if pts else None}, expected {points[c['id']]}")
        for other in obstacles:
            for a,b in zip(pts,pts[1:]):
                if segment_hits_box(a,b,other,0):
                    own=any(resolve(c[k],parts,rails)==a or resolve(c[k],parts,rails)==b for k in ("from","to"))
                    if not own: violations.append(f"{c['id']} crosses part/text obstacle at segment {a} -> {b}")
    violations.extend(collinear_overlap_check(routes))
    out=[f'<svg xmlns="{SVG}" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
         '<style>text{font-family:Arial,sans-serif;fill:#17212b}.title{font-size:29px;font-weight:bold}.part-title{font-size:18px;font-weight:bold}.pin-label{font-size:12px;font-weight:bold;paint-order:stroke;stroke:white;stroke-width:4px;stroke-linejoin:round}.small{font-size:14px}</style>',
         '<rect width="100%" height="100%" fill="#fff"/>']
    out.append(f'<text x="32" y="38" class="title">{html.escape(spec.get("title","Bench wiring"))}</text>')
    for c,pts in zip(connections,[p for _,p in routes]):
        d="M"+f"{pts[0][0]} {pts[0][1]}"
        for q in pts[1:]: d+=f" L{q[0]} {q[1]}"
        out.append(f'<path d="{d}" fill="none" stroke="{c.get("colour","#333")}" stroke-width="{c.get("width",5)}" stroke-linecap="round" stroke-linejoin="round"/>')
    for p in parts.values():
        vx,vy,vw,vh=p["viewbox"];x,y=p["x"],p["y"];sc=p["scale"];rot=p["rotation"]
        out.append(f'<g transform="translate({x} {y}) rotate({rot}) scale({sc}) translate({-vx} {-vy})">')
        out.extend(ET.tostring(ch,encoding="unicode") for ch in list(p["root"])); out.append('</g>')
        if p.get("title"): out.append(f'<text x="{x}" y="{y-10}" class="part-title">{html.escape(p["title"])}</text>')
    labels=[]
    for c in connections:
        for endpoint,xy in ((c["from"],points[c["id"]][0]),(c["to"],points[c["id"]][1])):
            label=c.get("label",c["id"]); candidates=[(xy[0]+8,xy[1]-8,"left"),(xy[0]+8,xy[1]+16,"left"),(xy[0]-len(label)*7-8,xy[1]-8,"right"),(xy[0]-len(label)*7-8,xy[1]+16,"right"),(xy[0]+18,xy[1]-5,"along")]
            chosen=None
            for tx,ty,align in candidates:
                box=(tx if align!="right" else tx,ty-12,tx+len(label)*7,ty+3)
                coll=any(box[0]<b[2] and b[0]<box[2] and box[1]<b[3] and b[1]<box[3] for b in labels)
                coll=coll or any(segment_hits_box(a,b,box) for _,ps in routes for a,b in zip(ps,ps[1:]))
                if not coll: chosen=(tx,ty,align,box); break
            if chosen is None:
                violations.append(f"{c['id']} label collision at {endpoint} near {xy}"); chosen=candidates[0]+((candidates[0][0],candidates[0][1]-12,candidates[0][0]+len(label)*7,candidates[0][1]+3),)
            tx,ty,align,box=chosen; labels.append(box)
            out.append(f'<text x="{tx}" y="{ty}" text-anchor="{align}">{html.escape(label)}</text>')
    # Violation markers are drawn above all diagram content.
    for msg in violations:
        nums=re.findall(r"\((-?\d+(?:\.\d+)?), (-?\d+(?:\.\d+)?)\)",msg)
        if nums:
            x,y=map(float,nums[0]); out.append(f'<circle cx="{x}" cy="{y}" r="18" fill="none" stroke="#ed00ff" stroke-width="5"/>')
    out.append('</svg>'); svg='\n'.join(out)
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True); sp=output_dir/(spec.get("output","breadboard-wiring")+".svg"); sp.write_text(svg)
    import cairosvg
    cairosvg.svg2pdf(bytestring=svg.encode(),write_to=str(sp.with_suffix(".pdf")))
    cairosvg.svg2png(bytestring=svg.encode(),write_to=str(sp.with_suffix(".png")),output_width=png_width or int(width))
    print("connection | from | to | colour")
    for c in connections: print(f"{c['id']} | {c['from']} | {c['to']} | {c.get('colour','#333')}")
    print("strict check: PASS" if not violations else f"strict check: {len(violations)} violation(s)")
    for v in violations: print("VIOLATION: "+v)
    print(f"rendered {sp} ({len(connections)} connections)")
    if strict and violations: raise RuntimeError(f"Strict check failed with {len(violations)} violation(s)")


def main():
    ap=argparse.ArgumentParser();ap.add_argument("spec");ap.add_argument("--output-dir",default=".");ap.add_argument("--png-width",type=int);ap.add_argument("--strict",action="store_true")
    a=ap.parse_args();render(a.spec,a.output_dir,a.png_width,a.strict)

if __name__=="__main__": main()
