"""Checks actual compiled upstream C, host contracts and runner failure detection."""
import ctypes
from contextlib import redirect_stdout
import io
import json
import math
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from sim.parity import build_reference as builder
from sim.parity import check_student
from sim.parity.reference import CReference, vmc_arguments
from sim.parity.source import load_coefficients, load_vectors, verify_vendor


class ReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="wbr-parity-tests-")
        cls.build = Path(cls.temp.name) / "reference"
        builder.build_reference(cls.build)
        cls.reference = CReference(cls.build)
        cls.vectors = load_vectors()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_original_source_checksums_and_build_receipt(self):
        manifest = verify_vendor()
        self.assertEqual(manifest["commit"], "6855ef8c6da20246251cfd473467c04112bf800f")
        self.assertEqual(self.reference.metadata["verified_vendor_sha256"], manifest["files"])
        self.assertIn("-ffp-contract=off", self.reference.metadata["compiler_command"])
        self.assertIn("-fno-fast-math", self.reference.metadata["compiler_command"])
        self.assertIn("VMC_calc.c", " ".join(self.reference.metadata["compiler_command"]))

    def test_polynomial_order_zero_and_signed_cases(self):
        for case in self.vectors["polynomial_cases"]:
            with self.subTest(case=case["id"]):
                answer = self.reference.scalar_gain(case["coefficients"], case["length_m"])
                self.assertTrue(math.isclose(answer, case["expected"], abs_tol=2e-6, rel_tol=2e-6))

    def test_schedule_matches_source_rows_and_independent_anchors(self):
        coefficients = load_coefficients()
        self.assertEqual(len(coefficients), 12)
        for case in self.vectors["schedule_cases"]:
            with self.subTest(case=case["id"]):
                result = self.reference.schedule(case["length_m"])
                self.assertEqual(len(result), 12)
                for row, gain in zip(coefficients, result, strict=True):
                    self.assertEqual(self.reference.scalar_gain(row, case["length_m"]), gain)
                for anchor in case["anchors"]:
                    self.assertTrue(math.isclose(result[anchor["index"]], anchor["expected"],
                                                 abs_tol=2e-5, rel_tol=2e-6))

    def test_vmc_valid_vectors_and_virtual_work_mapping(self):
        for case in self.vectors["vmc_cases"]:
            with self.subTest(case=case["id"]):
                answer = self.reference.vmc(**vmc_arguments(case))
                self.assertTrue(all(map(math.isfinite, answer.values())))
                self.assertGreater(answer["L0"], 0)
                sign = -1 if case["side"] == "right" else 1
                theta = math.pi/2 + sign*case["pitch_rad"] - answer["phi0"]
                self.assertAlmostEqual(answer["theta"], theta, delta=2e-6)
                self.assertAlmostEqual(answer["dtheta"], sign*case["pitch_rate_rad_s"], delta=2e-6)
                self.assertAlmostEqual(answer["tau0"], answer["j11"]*case["F0_N"] +
                                       answer["j12"]*case["Tp_Nm"], delta=2e-5)
                self.assertAlmostEqual(answer["tau1"], answer["j21"]*case["F0_N"] +
                                       answer["j22"]*case["Tp_Nm"], delta=2e-5)

    def test_vmc_mirrored_states_and_stateless_repeat(self):
        cases = {c["id"]: c for c in self.vectors["vmc_cases"]}
        right = self.reference.vmc(**vmc_arguments(cases["right_positive_pitch"]))
        mirrored = self.reference.vmc(**vmc_arguments(cases["left_mirrored_pitch"]))
        self.assertEqual(right, mirrored)
        self.reference.vmc(**vmc_arguments(cases["crouched_signed_force"]))
        self.assertEqual(right, self.reference.vmc(**vmc_arguments(cases["right_positive_pitch"])))

    def test_vmc_symmetric_pose_has_independent_geometry_anchor(self):
        # Circle intersection by symmetry, independent of the source atan2 solution.
        args = vmc_arguments(self.vectors["vmc_cases"][0])
        args.update(phi1_rad=math.pi/2, phi4_rad=math.pi/2)
        expected_length = .075 + math.sqrt(.14**2 - .04**2)
        for force, torque in ((40, 0), (0, .4)):
            args.update(F0_N=force, Tp_Nm=torque)
            answer = self.reference.vmc(**args)
            self.assertAlmostEqual(answer["L0"], expected_length, delta=2e-7)
            self.assertAlmostEqual(answer["phi0"], math.pi/2, delta=2e-7)
            # Differentiating the two fixed-length closure constraints at symmetry.
            radial = .075*.04/(2*math.sqrt(.14**2-.04**2))
            angular = .075/(2*expected_length)
            self.assertAlmostEqual(answer["tau0"], -radial*force+angular*torque, delta=2e-6)
            self.assertAlmostEqual(answer["tau1"], radial*force+angular*torque, delta=2e-6)

    def test_vmc_near_coincident_knee_guard_boundary(self):
        args = vmc_arguments(self.vectors["vmc_cases"][0])
        # Float32 poses on opposite sides of the documented 1 micrometer guard.
        args.update(phi1_rad=1.0082640648, phi4_rad=2.1333324909)
        with self.assertRaises(ValueError):
            self.reference.vmc(**args)
        args["phi1_rad"] = 1.0082900648
        self.assertTrue(all(map(math.isfinite, self.reference.vmc(**args).values())))

    def test_vmc_jacobian_against_forward_kinematics_finite_difference(self):
        for case in self.vectors["vmc_cases"][:3]:
            args = vmc_arguments(case)
            center = self.reference.vmc(**args)
            for field, length_key, angle_key in (("phi1_rad", "j11", "j12"),
                                                  ("phi4_rad", "j21", "j22")):
                for epsilon in (1e-3, 5e-4):
                    with self.subTest(case=case["id"], joint=field, epsilon=epsilon):
                        positive = dict(args); negative = dict(args)
                        positive[field] += epsilon; negative[field] -= epsilon
                        plus = self.reference.vmc(**positive); minus = self.reference.vmc(**negative)
                        for output, analytic in (("L0", length_key), ("phi0", angle_key)):
                            derivative = (plus[output]-minus[output])/(2*epsilon)
                            self.assertTrue(math.isclose(derivative, center[analytic],
                                                         abs_tol=5e-4, rel_tol=5e-3),
                                            (derivative, center[analytic]))

    def test_invalid_input_is_rejected_without_finite_outputs(self):
        for case in self.vectors["invalid_vmc_cases"]:
            with self.subTest(case=case["id"]), self.assertRaises(ValueError):
                self.reference.vmc(**vmc_arguments(case))
        for value in (math.nan, math.inf, -math.inf, 1e300):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.reference.schedule(value)
        out = (ctypes.c_float*12)()
        status = self.reference.lib.wbr_vmc(9, 1.5, 1.5, 0, 0, .003, 30, .2, out)
        self.assertNotEqual(status, 0)
        self.assertTrue(all(math.isnan(x) for x in out))

    def test_build_rejects_source_tampering_before_compilation(self):
        with tempfile.TemporaryDirectory(prefix="wbr-source-guard-") as directory:
            vendor = Path(directory)/"vendor"
            shutil.copytree(builder.VENDOR, vendor)
            source = vendor/"User/Algorithm/VMC/VMC_calc.c"
            source.write_bytes(source.read_bytes()+b"\n/* tampered test copy */\n")
            with patch.object(builder, "VENDOR", vendor), self.assertRaisesRegex(ValueError, "checksum"):
                builder.build_reference(Path(directory)/"out")

    def test_build_and_library_overwrite_guards(self):
        with self.assertRaises(FileExistsError):
            builder.build_reference(self.build)
        with tempfile.TemporaryDirectory(prefix="wbr-library-guard-") as directory:
            copy = Path(directory)/"reference"
            shutil.copytree(self.build, copy)
            metadata = json.loads((copy/"build_metadata.json").read_text())
            library = copy/metadata["library"]
            library.write_bytes(library.read_bytes()+b"tamper")
            with self.assertRaisesRegex(ValueError, "checksum"):
                CReference(copy)

    def test_malformed_coefficient_initializer_fails(self):
        with self.assertRaises(ValueError):
            builder.extract_coefficients("float Poly_Coefficient[12][4] = {{1,2,3,4}};")

    def test_runner_reports_pending_wrong_shape_and_numeric_mismatch(self):
        def pending(*args):
            raise NotImplementedError("learner TODO")
        self.assertEqual(check_student.evaluate(self.build, pending)["status"], "BLOCKED")
        self.assertEqual(check_student.evaluate(self.build, lambda *args: [0]*12)["status"], "FAIL")
        self.assertEqual(check_student.evaluate(self.build, lambda *args: [[0]*6, [0]*6])["status"], "FAIL")

    def test_runner_positive_control_is_explicitly_c_backed(self):
        # Test double for runner plumbing only, never the student's solution.
        def c_backed_double(coefficients, length):
            gains = [self.reference.scalar_gain(row, length) for row in coefficients]
            return [gains[:6], gains[6:]]
        report = check_student.evaluate(self.build, c_backed_double)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(len(report["cases"]), report["case_count_planned"])

    def test_cli_todo_returns_blocked_and_preserves_existing_report(self):
        def pending(*args):
            raise NotImplementedError("learner TODO")
        with tempfile.TemporaryDirectory(prefix="wbr-report-guard-") as directory:
            report = Path(directory)/"result.json"
            argv = ["check_student", "--build-dir", str(self.build), "--out", str(report)]
            with patch("sys.argv", argv), patch.object(check_student.student, "gain_schedule", pending), redirect_stdout(io.StringIO()):
                self.assertEqual(check_student.main(), 2)
            self.assertEqual(json.loads(report.read_text())["status"], "BLOCKED")
            original = report.read_bytes()
            with patch("sys.argv", argv), redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as caught:
                check_student.main()
            self.assertEqual(caught.exception.code, 2)
            self.assertEqual(original, report.read_bytes())


if __name__ == "__main__":
    unittest.main()
