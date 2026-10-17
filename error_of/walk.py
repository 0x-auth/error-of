"""The walk: two remembered errors, and what they say about where it is going.

A walk toward a target produces one signed error per tick
(error > 0: too high, error < 0: too low, 0: arrived). The walk keeps only
the last two errors. No history, no list of visited states.

From those two and the current one, a single number

    k = (e_now + e_prev) / e_last

says what the walk is doing, because three consecutive values of any
second-order chain satisfy e_now + e_prev = k * e_last:

    |k| < 2          rotating: the errors circle and never settle (cycling)
    k = +2           straight line: constant step or no change (drifting / stuck)
    k = -2           flipping between two equal values: a two-step loop (cycling)
    |k| > 2          geometric: errors shrink or grow by a fixed ratio r,
                     where r + 1/r = k
        k < -2       the sign flips every step: high, low, high (bracketing)
        k > +2       the sign stays: approaching from one side

For a converging walk the rate is the root of r + 1/r = k with |r| < 1.
Errors of the form t^n and (-1/t)^n give k = t + 1/t and k = -(t + 1/t).

This replaces cycle detection by a set of seen states: three numbers the
walk already holds are enough to call a cycle.
"""
import math

STRAIGHT_TOL = 0.05     # how close |k| must be to 2 to count as a straight line


def side(error):
    if error is None:
        return None
    if error > 0:
        return "too high"
    if error < 0:
        return "too low"
    return "arrived"


def diagnose(e_prev, e_last, e_now, tol=STRAIGHT_TOL):
    """Classify a walk from its last three errors. Pure function."""
    out = {"side": side(e_now), "k": None, "rate": None, "bracketing": None}
    if e_now == 0:
        return {**out, "state": "arrived"}
    if e_prev is None or e_last is None:
        return {**out, "state": "warming up"}          # fewer than three points
    if e_last == 0:
        return {**out, "state": "left the target"}     # was exact, now is not
    k = (e_now + e_prev) / e_last
    out["k"] = k
    out["bracketing"] = (e_now > 0) != (e_last > 0)
    if abs(abs(k) - 2) <= tol:
        if k > 0:                                      # straight line: same sign, constant step
            state = "stuck" if e_now == e_last else "drifting"
        elif abs(abs(e_now) - abs(e_last)) <= tol * abs(e_last):
            state = "cycling"                          # r = -1: flips between two values forever
            out["rate"] = 1.0
        else:
            state = "drifting"                         # flips sign, size changes by a constant step
        return {**out, "state": state}
    if abs(k) < 2:
        out["rate"] = 1.0                              # |r| = 1: on the circle
        return {**out, "state": "cycling"}
    small = (k - math.copysign(math.sqrt(k * k - 4), k)) / 2   # root with |r| < 1
    if abs(e_now) < abs(e_last):
        return {**out, "rate": abs(small), "state": "converging"}
    return {**out, "rate": 1 / abs(small), "state": "diverging"}


class Walk:
    """Holds exactly two remembered errors. step() takes the newest one."""

    def __init__(self, tol=STRAIGHT_TOL):
        self.prev = None
        self.last = None
        self.tol = tol
        self.ticks = 0

    def step(self, error):
        d = diagnose(self.prev, self.last, error, self.tol)
        self.prev, self.last = self.last, error
        self.ticks += 1
        d["tick"] = self.ticks
        return d

    @property
    def edges(self):
        return self.prev, self.last


def describe(d):
    k = "" if d["k"] is None else f"k={d['k']:+.3f}"
    rate = "" if d["rate"] is None else f"rate={d['rate']:.3f}"
    br = "" if d["bracketing"] is None else ("bracketing" if d["bracketing"] else "one-sided")
    return "  ".join(x for x in (f"tick {d['tick']:>3}", f"{d['state']:<15}",
                                 f"side={d['side']}", k, rate, br) if x)
