#!/usr/bin/env python3
"""
X: a frozen proposer answers a question; error-of reads every failure.

Cue:      the 50,000,000th Fibonacci number, mod 1,000,000,007.
Fabric:   each candidate runs in its own process, limited to 3 seconds and
          200 MB. error-of captures it and classifies what happened.
Memory:   only the last two sides (too big, too slow, ...). No history.
Gate:     an independent check (2x2 matrix power, a different method).

The proposer here is a fixed table that reads the last two sides; the seat is
meant for a trained model.
"""
import os
import sys
import tempfile
import textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from error_of import core

N, P = 50_000_000, 1_000_000_007
TIME_S, SPACE_MB = 3, 200

FABRIC = f"""
import resource, sys
resource.setrlimit(resource.RLIMIT_AS, ({SPACE_MB} << 20, {SPACE_MB} << 20))
n, p = int(sys.argv[1]), {P}
"""

CANDIDATES = {
    "store every value": """
        f = [0, 1] + [0] * (n - 1)
        for i in range(2, n + 1):
            f[i] = (f[i-1] + f[i-2]) % p
        print(f[n])
    """,
    "keep only two values": """
        a, b = 0, 1
        for _ in range(n):
            a, b = b, (a + b) % p
        print(a)
    """,
    "halve the index each step": """
        def fd(k):
            if k == 0: return 0, 1
            a, b = fd(k >> 1)
            c = a * ((2 * b - a) % p) % p
            d = (a * a + b * b) % p
            return (d, (c + d) % p) if k & 1 else (c, d)
        print(fd(n)[0])
    """,
}


def propose(prev_side, last_side):
    """Next proposal from the last two sides only."""
    if last_side is None:
        return "store every value"                    # the plainest walk first
    if {prev_side, last_side} == {"too big", "too slow"}:
        return "halve the index each step"            # neither trade works: change the walk
    if last_side == "too big":
        return "keep only two values"                 # trade time for space
    return "halve the index each step"


def gate(output):
    def mul(a, b):
        return [[(a[0][0]*b[0][0] + a[0][1]*b[1][0]) % P, (a[0][0]*b[0][1] + a[0][1]*b[1][1]) % P],
                [(a[1][0]*b[0][0] + a[1][1]*b[1][0]) % P, (a[1][0]*b[0][1] + a[1][1]*b[1][1]) % P]]
    r, m, k = [[1, 0], [0, 1]], [[1, 1], [1, 0]], N
    while k:
        if k & 1:
            r = mul(r, m)
        m, k = mul(m, m), k >> 1
    return output.strip() == str(r[0][1])


def run(name, workdir):
    path = os.path.join(workdir, name.replace(" ", "_") + ".py")
    with open(path, "w") as f:
        f.write(FABRIC + textwrap.dedent(CANDIDATES[name]))
    case = core.build_case(core.capture([sys.executable, "-I", path, str(N)], timeout=TIME_S))
    if case["exit_code"] == -9 and not case["side"]:   # killed by the fabric for memory
        case["side"] = "too big"
    return case


def main():
    prev_side = last_side = None
    with tempfile.TemporaryDirectory() as workdir:
        for tick in range(1, 6):
            name = propose(prev_side, last_side)
            case = run(name, workdir)
            if case["exit_code"] == 0 and gate(case["stdout"]):
                print(f"tick {tick}: {name:<26} -> {case['stdout'].strip()}, gate passes")
                return 0
            side = case["side"] or "wrong"
            classes = ", ".join(h["class"] for h in case["inferences"]) or "none"
            print(f"tick {tick}: {name:<26} -> {side} ({classes})")
            prev_side, last_side = last_side, side
    print("budget of ticks used up")
    return 1


if __name__ == "__main__":
    sys.exit(main())
