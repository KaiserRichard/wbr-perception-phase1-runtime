import copy
import unittest
from pathlib import Path

import mujoco
import numpy as np

from sim.wbr_model.build import generate, load_manifest, validate


MANIFEST = Path(__file__).parents[1] / "examples" / "assumed.yaml"


class ManifestBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest(MANIFEST)

    def test_generates_and_steps_headlessly_without_nan(self):
        model = mujoco.MjModel.from_xml_string(generate(self.manifest))
        self.assertEqual(model.nu, 6)
        data = mujoco.MjData(model)
        mujoco.mj_forward(model, data)
        for _ in range(1000):
            mujoco.mj_step(model, data)
            self.assertTrue(np.isfinite(data.qpos).all())
            self.assertTrue(np.isfinite(data.qvel).all())
            self.assertTrue(np.isfinite(data.qacc).all())

    def test_rejects_invalid_inertia_and_mass_sum(self):
        bad = copy.deepcopy(self.manifest)
        bad["inertias"]["base"]["value"]["Ixx"] = -1
        with self.assertRaisesRegex(ValueError, "positive definite"):
            validate(bad)
        bad = copy.deepcopy(self.manifest)
        bad["masses"]["total_robot"]["value"] = 4.0
        with self.assertRaisesRegex(ValueError, "mass sum mismatch"):
            validate(bad)

    def test_rejects_triangle_inequality(self):
        bad = copy.deepcopy(self.manifest)
        bad["inertias"]["base"]["value"].update(Ixx=1.0, Iyy=1.0, Izz=3.0)
        with self.assertRaisesRegex(ValueError, "triangle inequality"):
            validate(bad)


if __name__ == "__main__":
    unittest.main()
