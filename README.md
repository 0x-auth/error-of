# error-of

Errors as observations. See `PRD.md` and `docs/architecture.md`.

```
./error-of run <command ...>     run, capture, classify, report (output/<id>.md, .json)
./error-of report <id>           show a stored case
./error-of search <text>         search stored cases
./error-of patterns              recurring classes and signatures
./error-of walk <e1> <e2> ...    diagnose a walk from its signed errors
python3 -m unittest discover tests
```

How error-of fits a larger loop (reconstruct, run, read the error, keep two edges,
gate): `docs/construct.md`.

## Side and walk

Every case now carries a **side** when the error has a direction: `too big`
(Memory, Storage: trade time for space), `too slow` (Time: trade space for time),
`too coarse` (Precision). Programs can report their own with `"side"` and a signed
`"error"` in the protocol line.

`error_of/walk.py` keeps only the last two errors of a walk toward a target and
reads one number from them, `k = (e_now + e_prev) / e_last`:
|k| < 2 cycling, k = +2 drifting, k < -2 converging while bracketing, and so on.
Cycles are called from three numbers, without a list of visited states.

## Organisms: programs generated, not written

Four small, runnable cases, each with a one-page description in `docs/organisms/`:

| | goal | starts with | learns | code |
|---|---|---|---|---|
| [X](docs/organisms/X.md) | answer a question | a frozen proposer | nothing; carries two sides | `examples/reconstruct/fib.py` |
| [A](docs/organisms/A.md) | find a program from examples | four seed moves | words from successes, refutations from failures | `examples/organism/organism.py` |
| [B](docs/organisms/B.md) | same as A | seed moves, in A's world | from A's refutations | same |
| [C](docs/organisms/C.md) | same as A, plus an unseen goal | A's words | from A's successes | same |

```
python3 examples/reconstruct/fib.py                   # X, ~3 s
./error-of run python3 examples/organism/organism.py  # A, B, C, recorded as observations
```

Knowledge base: `~/.error-of/cases.jsonl` (append-only; override with `ERROR_OF_HOME`).

## Observation protocol

Any program, in any language, can report its own boundary by printing one line to stderr:

```
ERROR-OF {"class": "Representation", "boundary": "...", "observation": "...",
          "assumption": "...", "transformation": "...", "outcome": "..."}
```

These are first-hand observations and are listed above pattern-based inferences.
A run that exits 0 after reporting observations has status `continued`.

## Example: `examples/pdf2html`

```
pip install pdfminer.six
./error-of run python3 examples/pdf2html/pdf2html.py input.pdf out.html
```

Tries layout representations in turn, checks invariants after each one, and reports
every violation as an observation. Case study: `docs/case-studies/pdf2html.md`.

## Self-healing: `error_of/heal.py`

A heal transforms the input, never the code (the PRD lists "automatic code fixer"
as a non-goal). A heal is accepted only if its invariant confirms it preserved what
must be preserved; otherwise the original error is raised unchanged. Every attempt
is reported as an observation. Example: `examples/self_heal_phinary.py`, where the
`str.replace` heal is rejected because it changes the number and the carry heal is
accepted.
