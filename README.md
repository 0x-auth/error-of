# error-of

Errors as observations. See `PRD.md` and `docs/architecture.md`.

```
./error-of run <command ...>     run, capture, classify, report (output/<id>.md, .json)
./error-of report <id>           show a stored case
./error-of search <text>         search stored cases
./error-of patterns              recurring classes and signatures
python3 -m unittest discover tests
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
