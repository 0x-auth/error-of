"""Run: python3 -m unittest discover tests"""
import math, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("ERROR_OF_HOME", tempfile.mkdtemp())
from error_of import core
from error_of.walk import Walk, diagnose

PHI = (1 + 5 ** 0.5) / 2


def run(errors):
    w = Walk()
    return [w.step(e) for e in errors][-1]


class Side(unittest.TestCase):
    def test_memory_error_is_too_big(self):
        h = core.classify("MemoryError")[0]
        self.assertEqual((h["class"], h["side"]), ("Memory", "too big"))
        self.assertIn("trade time for space", h["trade"])

    def test_timeout_is_too_slow(self):
        h = core.classify("[error-of] timeout after 3s")[0]
        self.assertEqual(h["side"], "too slow")

    def test_syntax_has_no_side(self):
        self.assertIsNone(core.classify("SyntaxError: invalid syntax")[0]["side"])

    def test_self_reported_side_wins(self):
        err = 'ERROR-OF {"class": "Representation", "boundary": "gate", "side": "too low", "error": -3}\nMemoryError'
        cap = dict(command=["x"], stdout="", stderr=err, exit_code=1, runtime_s=0,
                   environment={}, time="t")
        self.assertEqual(core.build_case(cap)["side"], "too low")

    def test_pattern_side_when_no_report(self):
        cap = dict(command=["x"], stdout="", stderr="MemoryError", exit_code=1, runtime_s=0,
                   environment={}, time="t")
        self.assertEqual(core.build_case(cap)["side"], "too big")


class WalkDiagnosis(unittest.TestCase):
    def test_alternating_phi_errors_bracket_and_converge_at_one_over_phi(self):
        d = run([(-1 / PHI) ** n for n in range(6)])
        self.assertEqual(d["state"], "converging")
        self.assertTrue(d["bracketing"])
        self.assertAlmostEqual(d["k"], -(PHI + 1 / PHI), places=9)   # -sqrt(5)
        self.assertAlmostEqual(d["rate"], 1 / PHI, places=9)

    def test_one_sided_shrinking_converges(self):
        d = run([8, 4, 2, 1])
        self.assertEqual((d["state"], d["bracketing"]), ("converging", False))
        self.assertAlmostEqual(d["rate"], 0.5)

    def test_rotation_is_cycling(self):
        # e_n = cos(0.7 n) obeys e_{n+1} + e_{n-1} = 2cos(0.7) e_n, |k| < 2
        d = run([math.cos(0.7 * n) for n in range(1, 5)])
        self.assertEqual(d["state"], "cycling")
        self.assertAlmostEqual(d["k"], 2 * math.cos(0.7), places=9)

    def test_two_value_loop_is_cycling(self):
        # the "1 - S forever" loop: the error flips between the same two values
        self.assertEqual(run([1, -1, 1, -1])["state"], "cycling")   # k = -2, r = -1
        self.assertEqual(run([2, -1, 2, -1])["state"], "cycling")   # |k| < 2

    def test_constant_step_is_drifting(self):
        self.assertEqual(run([10, 9, 8, 7])["state"], "drifting")

    def test_no_change_is_stuck(self):
        self.assertEqual(run([5, 5, 5])["state"], "stuck")

    def test_growing_is_diverging(self):
        d = run([1, 3, 9, 27])
        self.assertEqual(d["state"], "diverging")
        self.assertAlmostEqual(d["rate"], 3.0)

    def test_zero_is_arrived(self):
        self.assertEqual(run([4, -2, 0])["state"], "arrived")

    def test_memory_is_two_errors(self):
        w = Walk()
        for e in [9, 7, 5, 3]:
            w.step(e)
        self.assertEqual(w.edges, (5, 3))

    def test_warming_up(self):
        self.assertEqual(diagnose(None, 3, 2)["state"], "warming up")


if __name__ == "__main__":
    unittest.main()
