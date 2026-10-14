"""Self-healing with a witness.

A heal is a transformation of the INPUT (or representation), never of the code.
A heal is accepted only if an invariant confirms it preserved what must be
preserved. Every attempt, accepted or rejected, is reported as an ERROR-OF
observation, so `error-of run` records the history.

    from error_of.heal import heals, Heal

    @heals(Heal(ValueError, transform=carry, invariant=same_value, name="carry 011->100"))
    def load(s): ...

If no heal applies, or every heal is rejected by its invariant, the original
error is raised unchanged.
"""
import functools
import json
import sys


class Heal:
    def __init__(self, error, transform, invariant, name=None, match=None):
        self.error = error              # exception type this heal answers
        self.transform = transform      # input -> new input
        self.invariant = invariant      # (old input, new input) -> bool
        self.name = name or transform.__name__
        self.match = match              # optional text that must be in the message


def _observe(**kw):
    print("ERROR-OF " + json.dumps(kw, default=str), file=sys.stderr)


def heals(*heal_list, max_rounds=5):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(x, *a, **k):
            current, history = x, []
            for _ in range(max_rounds):
                try:
                    result = fn(current, *a, **k)
                    if history:
                        _observe(**{"class": "Representation"}, boundary=fn.__name__,
                                 observation=f"healed after {len(history)} step(s): {history}",
                                 assumption=f"input was already in the form {fn.__name__} accepts",
                                 transformation=" -> ".join(history), outcome="continued")
                    return result
                except Exception as e:
                    h = next((h for h in heal_list if isinstance(e, h.error)
                              and (h.match is None or h.match in str(e))), None)
                    if h is None:
                        raise
                    candidate = h.transform(current)
                    ok = h.invariant(current, candidate)
                    _observe(**{"class": "Representation"}, boundary=fn.__name__,
                             observation=f"{type(e).__name__}: {e}",
                             transformation=f"{h.name}: {current!r} -> {candidate!r}",
                             invariant=f"{h.invariant.__name__}: {'held' if ok else 'VIOLATED'}",
                             outcome="retry" if ok else "rejected, original error raised")
                    if not ok:
                        raise
                    history.append(f"{h.name}({current!r}->{candidate!r})")
                    current = candidate
            raise RuntimeError(f"{fn.__name__}: not healed after {max_rounds} rounds: {history}")
        return wrapper
    return deco
