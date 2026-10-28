import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import wiring_diagram as wd


class GeometryTests(unittest.TestCase):
    def test_pin_resolution_from_fzp_svg_id(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "part.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="20" height="10"><rect id="pad" x="4" y="2" width="4" height="2"/></svg>')
            (root / "part.fzp").write_text('<module><connectors><connector id="connector0" name="SIG"><views><breadboardView><p svgId="pad"/></breadboardView></views></connector></connectors></module>')
            p = wd.load_part({"id":"p","svg":"part.svg","fzp":"part.fzp","x":100,"y":50,"scale":2}, root)
            self.assertEqual((p["pins"]["SIG"]), (112.0, 56.0))

    def test_collinear_overlap_rejected(self):
        with self.assertRaisesRegex(AssertionError, "overlap"):
            wd.collinear_overlap_check([("a",[(0,0),(20,0)]),("b",[(10,0),(30,0)])])

    def test_separate_routes_allowed(self):
        self.assertTrue(wd.collinear_overlap_check([("a",[(0,0),(10,0)]),("b",[(0,10),(10,10)])]))


if __name__ == "__main__":
    unittest.main()
