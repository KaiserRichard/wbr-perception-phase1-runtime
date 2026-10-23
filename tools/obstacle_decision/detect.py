"""Offline depth obstacle extraction. No transport or actuation authority."""
from dataclasses import dataclass, field
import time
import numpy as np
from tools.ground_plane import plane as gp
from tools.ground_plane import obstacles as go


@dataclass
class Params:
    min_obstacle_height: float = 0.02  # ASSUMED
    corridor_half_width: float = 0.25  # ASSUMED robot half-width plus margin
    min_forward: float = 0.30
    max_forward: float = 3.0
    stride: int = 2
    cell_size: float = 0.02
    min_cells: int = 3
    plane_max_age: int = 3
    plane_gate_deg: float = 30.0


@dataclass
class Cluster:
    distance_m: float
    height_m: float
    width_m: float
    depth_m: float
    point_count: int


@dataclass
class FrameResult:
    plane_valid: bool
    plane_reused: bool
    plane_age: int
    plane_height_m: float
    plane_pitch_rad: float
    plane_roll_rad: float
    nearest: object
    clusters: list = field(default_factory=list)
    timing_ms: float = 0.0


def _components(x, y, z, h, cell):
    keys = np.floor(np.column_stack((x, y))/cell).astype(int)
    groups = {}
    for i, key in enumerate(map(tuple, keys)):
        groups.setdefault(key, []).append(i)
    unseen = set(groups); comps=[]
    while unseen:
        seed=unseen.pop(); stack=[seed]; cells=[seed]
        while stack:
            a,b=stack.pop()
            for q in ((a-1,b),(a+1,b),(a,b-1),(a,b+1)):
                if q in unseen:
                    unseen.remove(q); stack.append(q); cells.append(q)
        ids=np.array([i for k in cells for i in groups[k]])
        comps.append(ids)
    return comps


def process_frame(depth_m, K, params=None, state=None):
    """Return (FrameResult,state); K is 3x3 pinhole intrinsics.

    Ground frame coordinates are forward=optical Z, lateral=-optical X (left),
    up=n·p+d. A +camera-right optical X therefore maps to negative lateral.
    """
    t0=time.perf_counter(); p=params or Params(); state={} if state is None else dict(state)
    fx,fy,cx,cy=K[0,0],K[1,1],K[0,2],K[1,2]
    prev=state.get('plane'); age=state.get('plane_age',0)
    prior=(prev.normal,prev.camera_height) if prev is not None else (np.array([0.,-1.,0.]),0.30)
    est=gp.estimate_plane(depth_m,fx=fx,fy=fy,cx=cx,cy=cy,stride=max(1,p.stride),
        iterations=160,threshold=.012,prior=prior,max_deviation=(np.deg2rad(p.plane_gate_deg),.12),
        min_inliers=40,min_height=.05)
    reused=False
    if est.valid:
        plane=est; age=0; state.update(plane=plane,plane_age=0)
    elif prev is not None and age < p.plane_max_age:
        plane=prev; age+=1; reused=True; state.update(plane_age=age)
    else:
        plane=None; state.pop('plane',None); state['plane_age']=age+1
    if plane is None:
        result=FrameResult(False,False,age,float('nan'),float('nan'),float('nan'),None,[],(time.perf_counter()-t0)*1000)
        return result,state
    h=go.height_image(depth_m,plane.normal,plane.camera_height,fx=fx,fy=fy,cx=cx,cy=cy)
    rows,cols=np.indices(depth_m.shape); dep=np.asarray(depth_m)
    forward=dep; lateral=-(cols-cx)*dep/fx
    mask=np.isfinite(h)&(h>p.min_obstacle_height)&(np.abs(lateral)<=p.corridor_half_width)&(forward>=p.min_forward)&(forward<=p.max_forward)
    rr,cc=np.nonzero(mask); x=forward[mask]; y=lateral[mask]; hh=h[mask]
    clusters=[]
    if len(x):
        for ids in _components(x,y,dep[mask],hh,p.cell_size):
            if len(ids)<p.min_cells: continue
            clusters.append(Cluster(float(np.percentile(x[ids],5)),float(np.percentile(hh[ids],95)),
                float(np.ptp(y[ids])),float(np.ptp(x[ids])),int(len(ids))))
    nearest=min(clusters,key=lambda c:c.distance_m) if clusters else None
    result=FrameResult(bool(est.valid),reused,age,plane.camera_height,plane.pitch,plane.roll,nearest,clusters,(time.perf_counter()-t0)*1000)
    return result,state
