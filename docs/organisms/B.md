# B: a newborn learns from A's mistakes

Compare with [X](X.md), [A](A.md), [C](C.md). Code: `examples/organism/organism.py`.

## Goal
The same as A: find a program from examples.

## Input
The same examples A was given.

## What is fixed
The same as A: four seed moves, one rule, six probe numbers.

## What it starts with
Only the four seed moves, none of A's words. But it lives in A's world, so it
sees A's refutations: which behaviours were wrong, and which example showed it.

## One step, at the lowest level
The same as A:
1. Take the next chain, shortest first.
2. Fingerprint it on the six probes.
3. Refuted by one of this goal's examples (by A or by B itself): skip it.
4. Otherwise check it against the examples. Pass: a new word. Fail: refute it.

## Example (real run, the goal "add one, then square")
Every chain A checked and found wrong is skipped without a check.
The first one left standing is `inc . sq`: one check, pass.

## Refutations follow the example, not the name
- The same behaviour under a new name ("square_of_next"): a newborn in A's world
  needs 1 check.
- A goal that shares only some examples: fewer checks than in a fresh world.
- A refutation never blocks a right answer: `inc` was refuted for `times4` by
  1 -> 4, and is still found in 1 check for "next", where 1 -> 2.

## Memory
Its own words, plus the shared refutations.

## Output
A program.

## Result over five goals
5 checks in total; A needed 106.

## Honest note
"Checks" counts only checks against the examples. B still generated all 147
chains A generated. What A's mistakes save is the checking, not the generating.
If checking is the expensive part (running a real program, a real experiment),
the saving is large.
