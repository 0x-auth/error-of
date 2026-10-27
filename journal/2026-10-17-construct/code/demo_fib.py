"""
Cue: "Give me the n-th Fibonacci number mod 1,000,000,007, for n = 50,000,000."

The reconstructor here stands in for the frozen model: it reads only the last
two error signals and proposes the next program. The candidates are written
by Claude; the loop, the fabric's limits and the gate are mechanical.
"""
from loop import loop

N, P = 50_000_000, 1_000_000_007

def gate(output):
    # independent check: 2x2 matrix power, a different method from any candidate
    def mul(a, b):
        return [[(a[0][0]*b[0][0] + a[0][1]*b[1][0]) % P, (a[0][0]*b[0][1] + a[0][1]*b[1][1]) % P],
                [(a[1][0]*b[0][0] + a[1][1]*b[1][0]) % P, (a[1][0]*b[0][1] + a[1][1]*b[1][1]) % P]]
    r, m, k = [[1, 0], [0, 1]], [[1, 1], [1, 0]], N
    while k:
        if k & 1: r = mul(r, m)
        m, k = mul(m, m), k >> 1
    truth = r[0][1]
    try: got = int(output)
    except ValueError: return False, "not a number"
    return got == truth, ("too high" if got > truth else "too low")

CANDIDATES = {
 "store every value": """
    import sys
    n, p = int(sys.argv[1]), 1_000_000_007
    f = [0, 1] + [0] * (n - 1)
    for i in range(2, n + 1):
        f[i] = (f[i-1] + f[i-2]) % p
    print(f[n])
 """,
 "keep only two values": """
    import sys
    n, p = int(sys.argv[1]), 1_000_000_007
    a, b = 0, 1
    for _ in range(n):
        a, b = b, (a + b) % p
    print(a)
 """,
 "halve the index each step": """
    import sys
    n, p = int(sys.argv[1]), 1_000_000_007
    def fd(k):
        if k == 0: return 0, 1
        a, b = fd(k >> 1)
        c = a * ((2 * b - a) % p) % p
        d = (a * a + b * b) % p
        return (d, (c + d) % p) if k & 1 else (c, d)
    print(fd(n)[0])
 """,
}

def reconstruct(problem, e_low, e_high):
    """Next proposal from the last two signals only."""
    last = e_high[0] if e_high else None
    prev = e_low[0] if e_low else None
    if last is None:
        name = "store every value"                   # first guess: the plainest walk
    elif last == "space" and prev is None:
        name = "keep only two values"                # space error -> spend time instead
    elif {last, prev} == {"space", "time"}:
        name = "halve the index each step"           # too big AND too slow -> change the walk itself
    else:
        name = "keep only two values"
    return name, CANDIDATES[name]

if __name__ == "__main__":
    out = loop(f"F({N}) mod {P}", N, gate, reconstruct)
    print("answer:", out)
