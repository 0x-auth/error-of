"""Run: python3 -m unittest discover tests"""
import os, subprocess, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "examples", "organism"))
os.environ.setdefault("ERROR_OF_HOME", tempfile.mkdtemp())
from error_of import core
import organism as O


def correct(o, goal, f, xs=range(-6, 7)):
    w = o.words[goal][0]
    return all(w(x) == f(x) for x in xs)


class Learning(unittest.TestCase):
    def setUp(self):
        self.world = O.World()
        self.a = O.Organism("A", self.world)
        self.results = O.live(self.a, O.CURRICULUM)

    def test_seed_only_cannot_reach_the_deep_goal(self):
        r = O.Organism("s", O.World()).solve(*O.CURRICULUM[-1])
        self.assertIsNone(r["program"])

    def test_a_reaches_every_goal_with_its_own_words(self):
        self.assertTrue(all(r["program"] for r in self.results))
        self.assertEqual(self.results[-1]["program"], "4plus1sq . 4plus1sq")
        self.assertTrue(correct(self.a, "deep", lambda x: (4 * (x + 1) ** 2 + 1) ** 2 * 4))

    def test_b_needs_one_check_per_goal_but_still_generates(self):
        b = O.Organism("B", self.world)
        rb = O.live(b, O.CURRICULUM)
        self.assertEqual([r["checks"] for r in rb], [1] * len(O.CURRICULUM))
        self.assertGreater(sum(r["built"] for r in rb), len(O.CURRICULUM))

    def test_refutations_carry_over_to_a_renamed_goal(self):
        newborn = O.Organism("D", self.world)          # no words learned yet
        r = newborn.solve("square_of_next", O.CURRICULUM[1][1])
        self.assertEqual((r["checks"], r["program"]), (1, "inc . sq"))

    def test_refutations_carry_over_to_an_overlapping_goal(self):
        ex = O.examples_of(lambda x: (x + 1) ** 2, xs=(0, 1, 3, 4))   # shares 0 and 1
        fresh = O.Organism("F", O.World()).solve("g", ex)["checks"]
        shared = O.Organism("G", self.world).solve("g", ex)["checks"]
        self.assertLess(shared, fresh)

    def test_a_refutation_never_blocks_a_right_answer(self):
        # inc was refuted for times4 by (1 -> 4); for "next" (1 -> 2) it is right
        r = O.Organism("H", self.world).solve("next", O.examples_of(lambda x: x + 1))
        self.assertEqual((r["checks"], r["program"]), (1, "inc"))

    def test_c_solves_an_unseen_goal_a_newborn_cannot(self):
        c = O.Organism("C", O.World(), library=self.a.library)
        newborn = O.Organism("n", O.World()).solve(*O.UNSEEN)
        child = c.solve(*O.UNSEEN)
        self.assertIsNone(newborn["program"])
        self.assertIsNotNone(child["program"])
        self.assertTrue(correct(c, "unseen", lambda x: 16 * ((x + 1) ** 2 + 1) ** 2))

    def test_forgetting_keeps_seeds_and_respects_capacity(self):
        small = O.Organism("S", O.World(), capacity=6)
        O.live(small, O.CURRICULUM)
        self.assertLessEqual(len(small.words), 6)
        self.assertTrue(all(k in small.words for k in O.SEED))


class Observed(unittest.TestCase):
    def test_a_life_is_recorded_by_error_of(self):
        cap = core.capture([sys.executable, os.path.join(ROOT, "examples", "organism", "organism.py")])
        case = core.build_case(cap)
        self.assertEqual(case["exit_code"], 0)
        self.assertEqual(case["status"], "continued")
        stopped = [o for o in case["observations"] if o.get("outcome") == "stopped"]
        self.assertTrue(stopped and all(o["side"] == "too slow" for o in stopped))


if __name__ == "__main__":
    unittest.main()
