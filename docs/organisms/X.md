# X: a frozen proposer answers a question

Compare with [A](A.md), [B](B.md), [C](C.md). Code: `examples/reconstruct/fib.py`.

## Goal
Answer a question. The procedure is assumed to exist already.

## Input
A problem statement (the cue): the 50,000,000th Fibonacci number, mod 1,000,000,007.

## What is fixed
- The proposer: frozen. It proposes a program for the cue and never changes.
- The fabric: each candidate runs in its own process, limited to 3 seconds and 200 MB.
- error-of: captures each run and classifies what happened, with a side.
- The gate: an independent check, by a different method.

## What it learns during the run
Nothing. It carries only the last two sides from one try to the next.

## One step, at the lowest level
1. The proposer reads the last two sides and proposes a program.
2. The fabric runs it inside its limits; error-of captures and classifies it.
3. An output: the gate checks it. Pass: stop.
4. A failure: its side becomes the newest of the two remembered sides. Go to 1.

## Example (real run)
| tick | proposal | error-of says | next |
|---|---|---|---|
| 1 | store every value | Memory: too big | trade time for space |
| 2 | keep only two values | Time: too slow | trade space for time |
| 3 | halve the index each step | 364822946, gate passes | done |

At tick 3 the two remembered sides together (too big, too slow) say that neither
trade alone works, so the walk itself has to change.

## Memory
The last two sides. Nothing else.

## Output
An answer: a value.

## Honest note
The proposer is a fixed table written by hand. The seat is meant for a trained
model. This is today's usual AI: trained once, frozen, then asked.
