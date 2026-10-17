# The construct

How error-of fits into a larger idea: solving by reconstruction and elimination,
with errors as the only signal. Worked out in conversation on 2026-10-17.

## In one paragraph

A cue (the problem statement) goes to a frozen model, which proposes a candidate.
The fabric (interpreter, operating system, their limits) runs it. error-of reads
what happened and turns it into a case. If it failed, only the last two errors are
carried into the next proposal. When the answer passes the gate (an invariant), the
walk stops. Every run also lands in the case store, which slowly shapes the model.
Nobody writes the procedure: the cue selects, the fabric judges, the errors steer.

```
cue -> reconstructor (frozen) -> fabric -> error-of -> gate -> answer
             ^                                  |
             |------ two edges (last two errors)
             |
             '- - - case store (many past runs, the slow loop)
```

## Definitions used here

- **Memory** is not a store of the past. It is the shape left by many events (the
  slow loop), plus the two edges carried during one walk. Nothing that can be
  recomputed is kept; what cannot be recomputed is kept as a pointer.
- **Intelligence** is how many eliminations the model supplies itself, without
  asking the outside. Memory and intelligence are the same machine: one
  reconstructs what was, the other what comes next.
- **The gate** is an invariant that must hold for the answer to be accepted.
  Settling down (no more change) is not the same as solving.
- **An error** is the only signal. It has a boundary (where the walk hit a wall)
  and, where possible, a side (which way to move).

## The fabric

The space of answers is 2^n cells. With one parameter t:

| quantity | value | meaning |
|---|---|---|
| cell | dx = t - 1/t | smallest distinguishable step in space |
| tick | dt = t + 1/t | smallest step in time; never below 2 |
| invariant | dt^2 - dx^2 = 4 | the same for every t |
| speed | dx/dt | always below 1; 1 is the fixed limit |

Space and time trade against each other: storing a result saves recomputing it,
recomputing saves storing it.

## Two remembered errors

Three consecutive errors of a chain where each step depends on the two before it
satisfy

    e_now + e_prev = k * e_last

so one number, k, read from the last two errors and the current one, says what the
walk is doing. The roots of the matching recurrences are t and -1/t (product -1,
the sign flips every step: high, low, high) or t and 1/t (product +1).

| k | behaviour | state |
|---|---|---|
| \|k\| < 2 | errors on a circle, they never settle | cycling |
| k = -2, equal sizes | flips between two values forever | cycling |
| k = +2 | constant step, or no change at all | drifting / stuck |
| k < -2 | shrinking by a fixed ratio, sign flipping | converging, bracketing |
| k > +2 | shrinking by a fixed ratio, same side | converging, one-sided |
| \|k\| > 2, growing | growing by a fixed ratio | diverging |
| e = 0 | | arrived |

The converging rate is the root of r + 1/r = k with |r| < 1. Errors that shrink
like (-1/phi)^n give k = -sqrt(5) and rate 1/phi = 0.618.

Two remembered errors is the minimum: with one, a chain can only grow or shrink
steadily, and can never alternate or bracket a target.

This replaces cycle detection by a list of every visited state.

## What is implemented

| piece | where |
|---|---|
| boundary, assumption, invariant, transformation | `core.RULES`, `core.classify` (already there) |
| **side** of each error | `core.SIDES`, `case["side"]`; self-reports may set `"side"` and `"error"` |
| **walk diagnosis** from two remembered errors | `error_of/walk.py`, `error-of walk <e1> <e2> ...` |
| gate | `heal.py`: a heal is accepted only if its invariant holds (already there) |
| case store | `~/.error-of/cases.jsonl`, append-only (already there) |

Sides assigned by pattern:

| class | side | trade |
|---|---|---|
| Memory, Storage | too big | trade time for space |
| Time | too slow | trade space for time |
| Precision | too coarse | use a finer representation |
| everything else | none | a wall with no direction: change the input |

A program that knows its own error can report it directly:

```
ERROR-OF {"class": "Representation", "boundary": "gate", "side": "too low", "error": -3}
```

Example:

```
$ ./error-of walk 1 -0.618 0.382 -0.236 0.146
tick   3  converging   side=too high  k=-2.236  rate=0.618  bracketing
...
$ ./error-of walk 1 -1 1 -1
tick   3  cycling      side=too high  k=-2.000  rate=1.000  bracketing
```

## Still open

1. **Outcomes should outrank the rule table.** The regex rules are a person-written
   seed; over time, what actually worked should take over.
2. **The case store should learn.** Rank which transformation worked for each
   signature. This is the slow loop, and the change with the most effect.
3. **Keep error-of as observer and judge.** The reconstructor proposes programs
   from outside; error-of keeps its rule of healing the input, never the code.
4. **Guard the gate.** A wrong invariant steers every walk wrong (see the pdf2html
   case study). Two independent invariants that must agree.
5. **Pointers, not contents.** Active context is the question, the two edges and
   what this tick fetched. Everything else stays a pointer until a one-bit
   "does this step need it?" says yes.
6. **Many short walks in parallel**, with the gate crossing out failures, instead
   of one long walk carrying its whole history.
7. **Cost should follow surprise.** When the prediction matches, take the cheap
   path; spend compute only on errors.
8. **Moves must chain.** If base moves are encoded, composing two must give another
   valid move: compose the operations, not their codes.

## Where the ideas came from

- `seed.py` (BAZINGA): predict, measure the error, correct toward a target; the
  arrow of time is the nonzero error. The same law, at the smallest scale.
- error-of: errors as observations with boundary, assumption, invariant and
  transformation; heals accepted only with a witness.
- The early recursive cognition model: it had stop conditions (stability,
  diminishing returns from the last two changes) but no cue and no gate, so it
  stopped when it stopped changing, not when it was right.
