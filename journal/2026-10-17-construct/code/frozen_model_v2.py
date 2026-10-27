"""
Frozen deterministic model, v2.

The model is a fixed executor. It knows two registers (LO, HI), two
operations (ADD, MUL), and how to repeat. It never changes.

The input is a tokenised vector of 10 numbers that carries the problem
itself: the starting states, the rule for each step, how many ticks,
and which register to read.

  [lo0, hi0,  opLO, aLO, bLO,  opHI, aHI, bHI,  n,  out]

  op  : 1 = ADD, 2 = MUL
  arg : 1 = LO, 2 = HI, 3 = ONE, 4 = ZERO
  out : 1 = LO, 2 = HI

Each tick both registers update at once from their old values:
  LO <- opLO(aLO, bLO)
  HI <- opHI(aHI, bHI)
"""

OPS = {1: lambda x, y: x + y, 2: lambda x, y: x * y}

def model(v):
    if len(v) != 10:
        raise ValueError("input must be a vector of 10 numbers")
    lo, hi, o1, a1, b1, o2, a2, b2, n, out = v
    for _ in range(n):
        src = {1: lo, 2: hi, 3: 1, 4: 0}
        lo, hi = OPS[o1](src[a1], src[b1]), OPS[o2](src[a2], src[b2])
    return lo if out == 1 else hi


# ---- problem statements: same frozen model, different vectors ---------
PROBLEMS = {
    "Fibonacci, i=7":    [0, 1,  2, 2, 3,  1, 1, 2,  7, 1],   # LO<-HI*1, HI<-LO+HI
    "Fibonacci, i=50":   [0, 1,  2, 2, 3,  1, 1, 2, 50, 1],
    "Factorial, 18":     [1, 1,  1, 1, 3,  2, 2, 1, 18, 2],   # LO<-LO+1, HI<-HI*LO
    "Sum 1..10":         [1, 0,  1, 1, 3,  1, 2, 1, 10, 2],   # LO<-LO+1, HI<-HI+LO
    "2 to the 20":       [0, 1,  1, 1, 4,  1, 2, 2, 20, 2],   # HI<-HI+HI
}

if __name__ == "__main__":
    for name, v in PROBLEMS.items():
        print(f"{name:<18} {v!s:<44} -> {model(v)}")
