"""Closed-chain kinematics and virtual-work mapping in body (u, v-down) axes.

Geometry reference: DM-jump 6855ef8, Trần Nguyên Bình, MIT; see LICENSE
and PROVENANCE.json. Circle intersection and implicit differentiation are
implemented independently here; no gain schedule or firmware is executed.
"""

from dataclasses import dataclass
import math

import numpy as np


class GeometryError(ValueError):
    """Unreachable, singular, or nonfinite configuration."""


def vector(value, size):
    result = np.asarray(value, dtype=float)
    if result.shape != (size,) or not np.all(np.isfinite(result)):
        raise GeometryError(f"Expected {size} finite coordinates")
    return result


def rotation(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array([[c, -s], [s, c]])


@dataclass(frozen=True)
class Geometry:
    l1: float = 0.075
    l2: float = 0.14
    l3: float = 0.14
    l4: float = 0.075
    l5: float = 0.08
    singular_tolerance: float = 1e-9

    def __post_init__(self):
        if any(not math.isfinite(x) or x <= 0 for x in
               (self.l1, self.l2, self.l3, self.l4, self.l5, self.singular_tolerance)):
            raise GeometryError("Lengths and singular tolerance must be positive and finite")

    @classmethod
    def from_inventory(cls, cfg):
        item = cfg["source_geometry_inventory_unused"]
        return cls(item["l1_l4"], item["l2_l3"], item["l2_l3"],
                   item["l1_l4"], item["l5"])

    def forward(self, motor_angles, branch=1):
        """Return B,C,D in pinned source axes: A=(0,0), E=(l5,0).

        branch=+1 selects C left of directed B->D (the source square-root
        branch in the documented standing workspace); -1 selects its mirror.
        Neither branch changes automatically at a singularity.
        """
        q1, q4 = vector(motor_angles, 2)
        if branch not in (-1, 1):
            raise GeometryError("Branch must be +1 or -1")
        b = self.l1 * np.array([math.cos(q1), math.sin(q1)])
        d = np.array([self.l5, 0.]) + self.l4 * np.array([math.cos(q4), math.sin(q4)])
        delta = d - b
        distance = float(np.linalg.norm(delta))
        tol = self.singular_tolerance
        if distance <= tol:
            raise GeometryError("Coincident knees do not determine an ankle")
        if distance >= self.l2 + self.l3 - tol or distance <= abs(self.l2-self.l3) + tol:
            raise GeometryError("Unreachable or tangent knee circles")
        direction = delta / distance
        along = (self.l2**2 - self.l3**2 + distance**2) / (2*distance)
        height2 = self.l2**2 - along**2
        if height2 <= tol**2:
            raise GeometryError("Tangent knee circles")
        normal = np.array([-direction[1], direction[0]])
        c = b + along*direction + branch*math.sqrt(height2)*normal
        return b, c, d

    def virtual(self, motor_angles, branch=1):
        _, c, _ = self.forward(motor_angles, branch)
        offset = c - np.array([self.l5/2, 0.])
        length = float(np.linalg.norm(offset))
        if length <= self.singular_tolerance:
            raise GeometryError("Zero virtual length")
        return np.array([length, math.atan2(offset[1], offset[0])])

    def jacobians(self, motor_angles, branch=1):
        """Return d(Cu,Cv)/d(q1,q4), d(L,beta)/d(q1,q4)."""
        q1, q4 = vector(motor_angles, 2)
        b, c, d = self.forward(motor_angles, branch)
        cb, cd = c-b, c-d
        closure = np.array([cb, cd])
        if abs(np.linalg.det(closure)) <= self.singular_tolerance*self.l2*self.l3:
            raise GeometryError("Parallel distal links: closure Jacobian singular")
        db = self.l1*np.array([-math.sin(q1), math.cos(q1)])
        dd = self.l4*np.array([-math.sin(q4), math.cos(q4)])
        cartesian = np.linalg.solve(closure, np.diag([cb@db, cd@dd]))
        length, beta = self.virtual(motor_angles, branch)
        polar = np.array([[math.cos(beta), math.sin(beta)],
                          [-math.sin(beta)/length, math.cos(beta)/length]])
        virtual = polar @ cartesian
        if np.linalg.svd(virtual, compute_uv=False)[-1] <= self.singular_tolerance:
            raise GeometryError("Motor/virtual Jacobian singular")
        return cartesian, virtual

    def inverse(self, length, beta, elbows=(1, -1), branch=1):
        """IK with explicit elbow signs; default is the outward standing assembly.

        q1=atan2(C-A)+elbows[0]*acos(...), likewise q4 about E.
        Check the requested closure branch rather than silently switching it.
        """
        length, beta = vector([length, beta], 2)
        if length <= self.singular_tolerance or tuple(elbows) not in (
                (1, 1), (1, -1), (-1, 1), (-1, -1)):
            raise GeometryError("Expected positive length and two elbow signs")
        c = np.array([self.l5/2, 0.]) + length*np.array([math.cos(beta), math.sin(beta)])
        angles = []
        for origin, upper, lower, sign in (
                (np.zeros(2), self.l1, self.l2, elbows[0]),
                (np.array([self.l5, 0.]), self.l4, self.l3, elbows[1])):
            delta = c-origin
            radius = float(np.linalg.norm(delta))
            if radius <= abs(upper-lower)+self.singular_tolerance or radius >= upper+lower-self.singular_tolerance:
                raise GeometryError("Unreachable or straight/folded serial chain")
            cosine = (upper**2 + radius**2 - lower**2)/(2*upper*radius)
            angles.append(math.atan2(delta[1], delta[0]) + sign*math.acos(float(np.clip(cosine, -1, 1))))
        q = np.array(angles)
        if np.linalg.norm(self.forward(q, branch)[1]-c) > 1e-8:
            raise GeometryError("Requested elbow and closure branches disagree")
        self.jacobians(q, branch)
        return q

    def wrench(self, motor_angles, force_N, moment_Nm, branch=1):
        """Map [extension force, beta moment] to motor torques and reactions.

        The direct stator moment excludes offset-pin force couples. The total
        chassis wrench about midpoint O includes them. It is the negative
        endpoint wrench; do not add both reactions to a simulated plant.
        """
        load = vector([force_N, moment_Nm], 2)
        _, jacobian = self.jacobians(motor_angles, branch)
        length, beta = self.virtual(motor_angles, branch)
        endpoint = rotation(beta) @ np.array([force_N, moment_Nm/length])
        torque = jacobian.T @ load
        return {"motor_Nm": torque,
                "direct_stator_Nm": float(-np.sum(torque)),
                "endpoint_force_uv_N": endpoint,
                "chassis_force_uv_N": -endpoint,
                "chassis_moment_about_O_Nm": -float(moment_Nm)}
