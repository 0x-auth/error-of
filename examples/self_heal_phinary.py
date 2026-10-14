#!/usr/bin/env python3
"""Self-healing version of the step-4 idea in error_driven_generator.py.

Two heals for the same error. The naive one (str.replace) is what the original
script did; its invariant catches that it changes the number, so it is
rejected. The carry heal preserves the value and is accepted.

    ../error-of run python3 examples/self_heal_phinary.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from error_of.heal import Heal, heals

PHI = (1 + 5 ** 0.5) / 2


def value(s):
    return sum(PHI ** i for i, d in enumerate(reversed(s)) if d == "1")


def same_value(old, new):
    return abs(value(old) - value(new)) < 1e-9


def naive_replace(s):
    return s.replace("11", "100")


def carry(s):
    d = list("0" + s)
    j = "".join(d).find("11")
    d[j - 1:j + 2] = list("100")
    return "".join(d).lstrip("0") or "0"


def load(s):
    if "11" in s:
        raise ValueError(f"consecutive 11 in {s}")
    return s


naive = heals(Heal(ValueError, naive_replace, same_value, name="replace 11->100"))(load)
proper = heals(Heal(ValueError, carry, same_value, name="carry 011->100"))(load)

if __name__ == "__main__":
    s = bin(11)[2:]
    print(f"input {s} = {value(s):.6f}")
    out = proper(s)
    print(f"carry heal  -> {out} = {value(out):.6f}")
    try:
        naive(s)
    except ValueError as e:
        print(f"naive heal  -> rejected by invariant, original error kept: {e}")
