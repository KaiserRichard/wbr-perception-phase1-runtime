import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import wiring_diagram as wd


def wire(i, a, b):
    return {"id": i, "from": f"{i}.a", "to": f"{i}.b", "colour": "#000"}, (i, [a, b])


class PinTests(unittest.TestCase):
    def test_fzp_pin_with_ancestor_transform(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "p.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 10">'
                                        '<g transform="translate(2,1)"><rect id="pad" x="4" y="2" width="4" height="2"/></g></svg>')
            (root / "p.fzp").write_text('<module><connectors><connector id="connector0" name="SIG"><views><breadboardView>'
                                        '<p svgId="pad"/></breadboardView></views></connector></connectors></module>')
            p = wd.Part({"id": "p", "svg": "p.svg", "fzp": "p.fzp", "x": 100, "y": 50, "scale": 2}, root)
            self.assertEqual(p.pins["SIG"], (116.0, 58.0))

    def test_breadboard_holes(self):
        bb = wd.Breadboard({"id": "bb", "x": 0, "y": 0, "pitch": 10})
        self.assertEqual(bb.pins["a1"][0], bb.pins["j1"][0])
        self.assertLess(bb.pins["T-1"][1], bb.pins["a1"][1])


class RouteTests(unittest.TestCase):
    def test_axis_waypoints(self):
        self.assertEqual(wd.build_route((0, 0), (50, 80), ["y=-20", "x=50"]),
                         [(0, 0), (0, -20), (50, -20), (50, 80)])

    def check(self, routes, obstacles=None):
        wires = [{"id": n, "from": "x.a", "to": "y.b"} for n in routes]
        own = {n: ("x", "y") for n in routes}
        return wd.check(wires, routes, obstacles or {}, [], (1000, 1000), own)

    def test_shared_lane_rejected(self):
        bad = self.check({"a": [(0, 10), (100, 10)], "b": [(50, 14), (150, 14)]})
        self.assertTrue(any("parallel" in m for m, _ in bad))

    def test_separate_lanes_and_crossing_allowed(self):
        self.assertEqual(self.check({"a": [(0, 10), (100, 10)], "b": [(50, 0), (50, 100)]}), [])

    def test_crossing_foreign_part_rejected(self):
        bad = self.check({"a": [(0, 50), (300, 50)]}, {"z": (100, 0, 200, 100)})
        self.assertTrue(any("crosses part z" in m for m, _ in bad))

    def test_diagonal_rejected(self):
        bad = self.check({"a": [(0, 0), (40, 40)]})
        self.assertTrue(any("diagonal" in m for m, _ in bad))


if __name__ == "__main__":
    unittest.main()
