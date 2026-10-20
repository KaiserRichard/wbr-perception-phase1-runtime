"""MuJoCo closed-chain scaffold, separate from the existing planar plant."""

import math

import mujoco
import numpy as np

from .geometry import Geometry, vector


def make_mjcf(cfg, geometry=None):
    g = geometry or Geometry.from_inventory(cfg)
    p = {name: item["value"] for name, item in cfg["physics"].items()}
    length, radius = p["leg_length"], p["wheel_radius"]
    q1, q4 = g.inverse(length, math.pi/2)
    b, c, d = g.forward([q1, q4])
    q2 = math.atan2(*(c-b)[::-1])-q1
    q3 = math.atan2(*(c-d)[::-1])-q4
    # Four equal masses sum to the existing equivalent-leg mass. Uniform rods
    # with 6 mm radius are ASSUMED; no claim of matched COM/inertia or CAD data.
    mass, rod_radius = p["leg_mass"]/4, 0.006

    def link(name, link_length):
        axial = mass*rod_radius**2/2
        transverse = mass*(link_length**2/12+rod_radius**2/4)
        return f'''<inertial pos="{link_length/2} 0 0" mass="{mass}" diaginertia="{axial} {transverse} {transverse}"/>
          <geom name="{name}_visual" type="capsule" fromto="0 0 0 {link_length} 0 0" size="{rod_radius}"/>'''

    return f'''<mujoco model="ASSUMED_separate_planar_fivebar">
  <compiler angle="radian" inertiafromgeom="false"/>
  <option timestep="{cfg['simulation']['dt_s']}" gravity="0 0 {-p['gravity']}" integrator="implicitfast" iterations="100" tolerance="1e-10">
    <flag energy="enable"/>
  </option>
  <default>
    <joint limited="false" damping="0" stiffness="0" frictionloss="0"/>
    <geom contype="0" conaffinity="0" rgba="0.2 0.5 0.8 1"/>
    <site size="0.004"/>
    <equality solref="0.01 1" solimp="0.99 0.99 0.001"/>
  </default>
  <worldbody>
    <body name="chassis" pos="0 0 {radius+length}">
      <joint name="body_x" type="slide" axis="1 0 0"/>
      <joint name="body_z" type="slide" axis="0 0 1"/>
      <joint name="body_pitch" type="hinge" axis="0 1 0"/>
      <inertial pos="0 0 {p['body_com']}" mass="{p['body_mass']}" diaginertia="{p['body_inertia']} {p['body_inertia']} {p['body_inertia']}"/>
      <geom name="chassis_visual" type="box" pos="0 0 {p['body_com']}" size="0.06 0.08 0.06" rgba="0.9 0.5 0.2 1"/>
      <body name="upper_left" pos="{-g.l5/2} 0 0" euler="0 {q1} 0">
        <joint name="motor_A" type="hinge" axis="0 1 0" ref="{q1}"/>
        {link('upper_left', g.l1)}
        <body name="lower_left" pos="{g.l1} 0 0" euler="0 {q2} 0">
          <joint name="knee_B" type="hinge" axis="0 1 0" ref="{q2}"/>
          {link('lower_left', g.l2)}
          <site name="ankle_left" pos="{g.l2} 0 0"/>
        </body>
      </body>
      <body name="upper_right" pos="{g.l5/2} 0 0" euler="0 {q4} 0">
        <joint name="motor_E" type="hinge" axis="0 1 0" ref="{q4}"/>
        {link('upper_right', g.l4)}
        <body name="lower_right" pos="{g.l4} 0 0" euler="0 {q3} 0">
          <joint name="knee_D" type="hinge" axis="0 1 0" ref="{q3}"/>
          {link('lower_right', g.l3)}
          <site name="ankle_right" pos="{g.l3} 0 0"/>
        </body>
      </body>
    </body>
    <body name="axle" pos="0 0 {radius}">
      <joint name="axle_x" type="slide" axis="1 0 0" armature="{p['wheel_inertia']/radius**2}"/>
      <inertial pos="0 0 0" mass="{p['wheel_mass']}" diaginertia="{p['wheel_inertia']} {p['wheel_inertia']} {p['wheel_inertia']}"/>
      <site name="axle_center"/>
      <geom name="wheel_visual" type="cylinder" size="{radius} 0.035" euler="1.5707963267948966 0 0" rgba="0.1 0.1 0.1 1"/>
    </body>
  </worldbody>
  <equality>
    <connect name="left_to_axle" site1="ankle_left" site2="axle_center"/>
    <connect name="right_to_axle" site1="ankle_right" site2="axle_center"/>
  </equality>
  <tendon>
    <fixed name="wheel_relative_lower_left">
      <joint joint="axle_x" coef="{1/radius}"/>
      <joint joint="body_pitch" coef="-1"/>
      <joint joint="motor_A" coef="-1"/>
      <joint joint="knee_B" coef="-1"/>
    </fixed>
  </tendon>
  <actuator>
    <motor name="wheel_pair" tendon="wheel_relative_lower_left"/>
    <motor name="motor_A" joint="motor_A"/>
    <motor name="motor_E" joint="motor_E"/>
  </actuator>
</mujoco>
'''


class Plant:
    """Eight tree coordinates, four independent coordinates after loop closure.

    No trained policy, controller, contacts, saturation or hardware interface.
    Motor controls are [wheel_pair, motor_A, motor_E] in N m.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.geometry = Geometry.from_inventory(cfg)
        self.xml = make_mjcf(cfg, self.geometry)
        self.model = mujoco.MjModel.from_xml_string(self.xml)
        self.joints = {name: self.model.joint(name).qposadr[0] for name in
                       ("body_x", "body_z", "body_pitch", "motor_A", "knee_B",
                        "motor_E", "knee_D", "axle_x")}

    def tree_position(self, coordinates):
        """[axle x, absolute leg theta, absolute body phi, length] -> qpos."""
        x, theta, phi, length = vector(coordinates, 4)
        g = self.geometry
        beta = theta-phi+math.pi/2
        q1, q4 = g.inverse(length, beta)
        b, c, d = g.forward([q1, q4])
        q2 = math.atan2(*(c-b)[::-1])-q1
        q3 = math.atan2(*(c-d)[::-1])-q4
        values = dict(body_x=x+length*math.sin(theta),
                      body_z=length*math.cos(theta)-self.cfg['physics']['leg_length']['value'],
                      body_pitch=phi, motor_A=q1, knee_B=q2,
                      motor_E=q4, knee_D=q3, axle_x=x)
        result = np.zeros(self.model.nq)
        for name, value in values.items():
            result[self.joints[name]] = value
        return result

    def tangent(self, coordinates, epsilon=1e-6):
        """Tree velocity map for [x,theta,phi,L]; local to the standing branch."""
        q = vector(coordinates, 4)
        return np.column_stack([(self.tree_position(q+e)-self.tree_position(q-e))/(2*epsilon)
                                for e in epsilon*np.eye(4)])

    def data(self, coordinates=None, velocity=None):
        data = mujoco.MjData(self.model)
        if coordinates is not None:
            data.qpos[:] = self.tree_position(coordinates)
            if velocity is not None:
                data.qvel[:] = self.tangent(coordinates) @ vector(velocity, 4)
        elif velocity is not None:
            raise ValueError("Coordinates are required with a velocity")
        mujoco.mj_forward(self.model, data)
        return data

    def closure_error(self, data):
        center = data.site_xpos[self.model.site("axle_center").id]
        return max(float(np.linalg.norm(data.site_xpos[self.model.site(name).id]-center))
                   for name in ("ankle_left", "ankle_right"))

    def virtual(self, data):
        angles = [data.qpos[self.joints[name]] for name in ("motor_A", "motor_E")]
        length, beta = self.geometry.virtual(angles)
        phi = data.qpos[self.joints["body_pitch"]]
        return np.array([data.qpos[self.joints["axle_x"]], phi+beta-math.pi/2, phi, length])

    def controls(self, coordinates, wheel_Nm, hip_Nm, extension_N=0.):
        """Reduced positive hip moment does work hip*(phi_dot-theta_dot)."""
        _, theta, phi, length = vector(coordinates, 4)
        angles = self.geometry.inverse(length, theta-phi+math.pi/2)
        torque = self.geometry.wrench(angles, extension_N, -hip_Nm)["motor_Nm"]
        return np.r_[wheel_Nm, torque]


def main():
    import json
    from pathlib import Path
    cfg = json.loads((Path(__file__).parents[1]/"configs/assumed_planar.json").read_text())
    plant = Plant(cfg)
    data = plant.data()
    initial = plant.closure_error(data)
    mujoco.mj_step(plant.model, data)
    mujoco.mj_forward(plant.model, data)
    print({"nq": plant.model.nq, "nu": plant.model.nu,
           "initial_closure_m": initial, "one_step_closure_m": plant.closure_error(data),
           "finite": bool(np.all(np.isfinite(data.qpos)))})


if __name__ == "__main__":
    main()
