#!/usr/bin/env python3
"""
Organisms that generate programs instead of being given them.

Born with:  four seed moves (functions on integers) and one rule: a move
            followed by a move is a move.
Goal:       a behaviour, shown only as examples (input -> output).
Life:       generate chains of moves, shortest first; check each against the
            examples; a pass becomes a new named move (a word); a fail is
            recorded as a fact about what refuted it.

Three ways to learn, three organisms:
  A  learns from its own collisions with reality (keeps words, crosses out fails)
  B  a newborn in A's world: none of A's words, but A's refutations
  C  A's child: born with A's words, in a fresh world

Memory is only:
  - the library of words, ranked by use; the least used learned word is
    forgotten when the library is full (seed moves are never forgotten)
  - refutations, shared through the world: "behaviour b gives the wrong output
    for input x". They are keyed by the example that refuted them, not by the
    goal's name, so a refutation carries over to any goal containing the same
    example.

Perception is finite: a program is known by its outputs on six probe numbers.
Two programs that agree on every probe are one program to the organism.

Run under error-of to record the life as observations:
    ./error-of run python3 examples/organism/organism.py
"""
import json
import sys
from itertools import product

PROBES = (-3, -1, 0, 1, 2, 5)

SEED = {
    "inc": lambda x: x + 1,
    "dec": lambda x: x - 1,
    "dbl": lambda x: x * 2,
    "sq":  lambda x: x * x,
}


def compose(f, g):
    """The one rule: do f, then g."""
    return lambda x: g(f(x))


def observe(**kw):
    """Report a boundary in error-of's protocol (one line on stderr)."""
    print("ERROR-OF " + json.dumps(kw), file=sys.stderr)


class World:
    """What every organism in it shares: refutations, keyed by the refuting example."""

    def __init__(self):
        self.refuted = {}                      # behaviour -> {(x, y), ...}

    def is_refuted(self, behaviour, examples):
        known = self.refuted.get(behaviour)
        return bool(known) and any((x, y) in known for x, y in examples)

    def refute(self, behaviour, facts):
        self.refuted.setdefault(behaviour, set()).update(facts)


class Organism:
    def __init__(self, name, world, library=None, capacity=12, quiet=True):
        self.name, self.world, self.capacity, self.quiet = name, world, capacity, quiet
        self.words = {}                        # name -> [function, uses, is_seed]
        for k, (f, uses, seed) in (library or {k: (v, 0, True) for k, v in SEED.items()}).items():
            self.words[k] = [f, uses, seed]

    @property
    def library(self):
        return {k: (f, u, s) for k, (f, u, s) in self.words.items()}

    def _ranked(self):
        # most used first: the groove deepens where walks have gone before
        return sorted(self.words, key=lambda k: -self.words[k][1])

    def _build(self, combo):
        f = self.words[combo[0]][0]
        for n in combo[1:]:
            f = compose(f, self.words[n][0])
        return f

    @staticmethod
    def behaviour(f):
        return tuple(f(p) for p in PROBES)

    def solve(self, goal, examples, budget=5000, max_len=4):
        """Returns a result dict: program, checks (against the examples), built (generated)."""
        examples = tuple(examples)
        seen, checks, built = set(), 0, 0
        names = self._ranked()
        for length in range(1, max_len + 1):
            for combo in product(names, repeat=length):
                f = self._build(combo)
                built += 1
                b = self.behaviour(f)
                if b in seen or self.world.is_refuted(b, examples):
                    continue
                seen.add(b)
                checks += 1
                if checks > budget:
                    return self._unsolved(goal, checks, built, "budget")
                wrong = {(x, y) for x, y in examples if f(x) != y}
                if not wrong:
                    return self._learn(goal, combo, f, checks, built)
                self.world.refute(b, wrong)
        return self._unsolved(goal, checks, built, "depth")

    def _learn(self, goal, combo, f, checks, built):
        for n in combo:
            self.words[n][1] += 1
        if goal not in self.words:
            self.words[goal] = [f, 1, False]
            self._forget_if_full()
        program = " . ".join(combo)
        if not self.quiet:
            observe(**{"class": "Representation"}, boundary=f"goal {goal}",
                    observation=f"{self.name} found {program} after {checks} checks",
                    transformation=f"new word: {goal}", outcome="continued")
        return {"goal": goal, "program": program, "checks": checks, "built": built}

    def _forget_if_full(self):
        learned = [k for k, (_, _, seed) in self.words.items() if not seed]
        while len(self.words) > self.capacity and learned:
            least = min(learned, key=lambda k: self.words[k][1])
            learned.remove(least)
            del self.words[least]

    def _unsolved(self, goal, checks, built, why):
        if not self.quiet:
            observe(**{"class": "Time"}, boundary=f"goal {goal}",
                    observation=f"{self.name}: no program within {why} after {checks} checks",
                    side="too slow",
                    transformation="learn smaller goals first, so this one is a few words away",
                    outcome="stopped")
        return {"goal": goal, "program": None, "checks": checks, "built": built}


def examples_of(f, xs=(0, 1, -1, 2)):
    return tuple((x, f(x)) for x in xs)


CURRICULUM = [                      # easy to hard; each one is a few words of the last
    ("times4",   examples_of(lambda x: 4 * x)),
    ("plus1_sq", examples_of(lambda x: (x + 1) ** 2)),
    ("4plus1sq", examples_of(lambda x: 4 * (x + 1) ** 2)),
    ("nested",   examples_of(lambda x: ((x + 1) ** 2 + 1) ** 2)),
    ("deep",     examples_of(lambda x: (4 * (x + 1) ** 2 + 1) ** 2 * 4)),
]

UNSEEN = ("unseen", examples_of(lambda x: 16 * ((x + 1) ** 2 + 1) ** 2))   # never in the curriculum

RENAMED = ("square_of_next", CURRICULUM[1][1])   # same behaviour as plus1_sq, a different name


def live(organism, goals):
    return [organism.solve(g, ex) for g, ex in goals]


def report(label, results):
    print(f"\n{label}")
    for r in results:
        print(f"  {r['goal']:<15} checks={r['checks']:<5} built={r['built']:<6} program: {r['program']}")
    print(f"  total checks {sum(r['checks'] for r in results)}, "
          f"generated {sum(r['built'] for r in results)}")


def main():
    quiet = "--quiet" in sys.argv

    seed_only = Organism("seed", World(), quiet=True)
    report("Seed only, learns nothing (each goal from scratch)",
           [Organism("seed", World(), quiet=True).solve(g, ex) for g, ex in CURRICULUM])

    world = World()
    a = Organism("A", world, quiet=quiet)
    report("A: learns from its own collisions with reality", live(a, CURRICULUM))

    b = Organism("B", world, quiet=quiet)
    report("B: newborn in A's world (A's refutations, none of A's words)", live(b, CURRICULUM))
    report("B on a goal under a new name, same behaviour", live(b, [RENAMED]))

    c = Organism("C", World(), library=a.library, quiet=quiet)
    report("C: A's child (A's words, fresh world)", live(c, CURRICULUM))

    report("Unseen goal, seed-only newborn", live(Organism("n", World(), quiet=quiet), [UNSEEN]))
    report("Unseen goal, C (inherited words)", live(c, [UNSEEN]))
    print(f"\nC's library: {', '.join(c._ranked())}")


if __name__ == "__main__":
    main()
