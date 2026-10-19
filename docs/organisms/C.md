# C: A's child inherits words, not mistakes

Compare with [X](X.md), [A](A.md), [B](B.md). Code: `examples/organism/organism.py`.

## Goal
The same as A: find a program from examples.

## Input
The same examples, then one goal nobody has seen.

## What is fixed
The same as A: four seed moves, one rule, six probe numbers.

## What it starts with
All of A's words and their ranking. A fresh world: none of A's refutations.
B inherits what A got wrong; C inherits what A got right.

## One step, at the lowest level
The same as A. Its learned words are tried first, so a known goal is often
recalled in a check or two instead of searched for.

## Example (real run, the five known goals)
| goal | checks | program |
|---|---|---|
| times4 | 4 | times4 |
| plus1_sq | 1 | plus1_sq |
| deep | 8 | deep |

21 checks for all five; A needed 106 to learn them.

## The test that matters: a goal nobody has seen
Goal: 16 * ((x+1)^2 + 1)^2, given only as examples.

| organism | checks | program |
|---|---|---|
| seed-only newborn | 206 | none: needs 8 seed moves, out of reach |
| C | 78 | `plus1_sq . 4plus1sq . times4` |

C composes inherited words into a program none of them is. That is the claim for
a third kind of intelligence, tested once and at small scale: what was learned
on some goals makes a new goal reachable.

## Memory
Its words, ranked by use, and its own refutations.

## Output
A program.

## Honest note
Every goal here has an exact gate (the examples). Goals with a soft gate, and
carrying learning across goals that are only similar, are still open.
