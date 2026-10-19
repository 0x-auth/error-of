# A: an organism finds programs from examples

Compare with [X](X.md), [B](B.md), [C](C.md). Code: `examples/organism/organism.py`.

## Goal
Find the procedure itself. A is shown what the procedure should do and has to
discover a program that does it.

## Input
Examples of the behaviour: 0 gives 1, 1 gives 4, -1 gives 0, 2 gives 9.
(The hidden procedure is "add one, then square". A is never told that.)

## What is fixed
- Four seed moves: inc (x+1), dec (x-1), dbl (x*2), sq (x*x). Never forgotten.
- One rule: a move followed by a move is a move.
- Perception: six probe numbers, -3, -1, 0, 1, 2, 5. A program is known by its
  outputs on them; two programs that agree on all six are one program to A.

## What it learns during the run
- A program that passes becomes a new word.
- Words are ranked by use; the most used are tried first.
- When the library is full, the least used learned word is forgotten.
- A program that fails is refuted by the example it got wrong. The refutation
  holds for any goal that contains the same example.

## One step, at the lowest level
1. Take the next chain of words, shortest first, most used first.
2. Fingerprint it on the six probes.
3. Already seen, or refuted by one of this goal's examples: skip it.
4. Otherwise check it against the examples.
5. All match: it becomes a word. Stop.
6. Any mismatch: record which examples refuted it. Go to 1.

## Example (real run; A had already learned `times4`)
`inc`, `dec`, `dbl`, `sq` are skipped without a check: they were refuted by the
example 1 -> 4, which `times4` and this goal share. A learned that from its own
earlier mistake on a different goal.

| check | program | refuted by |
|---|---|---|
| 1 | times4 | 0 -> 1 |
| 5 | times4 . inc | 1 -> 4 |
| 8 | inc . dbl | 0 -> 1 |
| 9 | inc . times4 | 0 -> 1 |
| 10 | inc . sq | pass: new word `plus1_sq` |

## Memory
Its words, ranked by use, and the refutations. No list of attempts.

## Output
A program, kept as a word.

## Result over five goals, easy to hard
106 checks, all solved. The hardest needs 7 seed moves; A finds it as two of its
own words, `4plus1sq . 4plus1sq`. Learning nothing, the same search uses 340
checks and fails the hardest goal.
