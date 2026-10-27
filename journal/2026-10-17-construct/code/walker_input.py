"""
Input vector for the frozen Walker: 22 dimensions, fixed length.

 idx  slot            meaning
 0    K               one constant the problem needs (100, 18, i ...)
 1    S0              start of the current state S (the clock / position)
 2    LO0             start of the low remembered value
 3    HI0             start of the high remembered value
 4-6  S rule          op, a, b      how S moves each tick
 7-9  test            pred, a, b    the one binary test per tick
10-12 LO rule         op, a, b      applied when the test is true
13-15 HI rule         op, a, b      applied when the test is true
16-18 gate            pred, a, b    stop when true
 19   dx              resolution in bits (0 = exact integer)
 20   budget          max ticks before the walk is cut (TTL)
 21   out             which register is the answer: 1=S 2=LO 3=HI

 args : 1=S 2=LO 3=HI 4=ONE 5=ZERO 6=K
 ops  : 0=KEEP 1=ADD 2=MUL 3=SUB 4=COPY(a)
 preds: 0=TRUE 1=PRIME(a) 2=EVEN(a) 3=GE(a,b) 4=EQ(a,b) 5=GT(a,b)

Each tick, using the values from the start of the tick:
  if test:  LO, HI <- LO rule, HI rule
  S <- S rule
  if gate:  stop
"""

def is_prime(n):
    return n > 1 and all(n % d for d in range(2, int(n**.5) + 1))

OPS = {0: None, 1: lambda a, b: a + b, 2: lambda a, b: a * b,
       3: lambda a, b: a - b, 4: lambda a, b: a}
PREDS = {0: lambda a, b: True, 1: lambda a, b: is_prime(a), 2: lambda a, b: a % 2 == 0,
         3: lambda a, b: a >= b, 4: lambda a, b: a == b,
         5: lambda a, b: a > b}

class WalkError(Exception):
    pass

def walk(v):
    if len(v) != 22:
        raise WalkError("input must have 22 dimensions")
    K, S, LO, HI = v[0:4]
    s_rule, test, lo_rule, hi_rule, gate = v[4:7], v[7:10], v[10:13], v[13:16], v[16:19]
    dx, budget, out = v[19], v[20], v[21]
    seen = set()
    for tick in range(budget):
        src = {0: 0, 1: S, 2: LO, 3: HI, 4: 1, 5: 0, 6: K}
        app = lambda r, cur: cur if r[0] == 0 else OPS[r[0]](src[r[1]], src[r[2]])
        if PREDS[test[0]](src[test[1]], src[test[2]]):
            LO, HI = app(lo_rule, LO), app(hi_rule, HI)
        S = app(s_rule, S)
        src = {0: 0, 1: S, 2: LO, 3: HI, 4: 1, 5: 0, 6: K}
        if PREDS[gate[0]](src[gate[1]], src[gate[2]]):
            return {1: S, 2: LO, 3: HI}[out], tick + 1
        state = (S, LO, HI)
        if state in seen:
            raise WalkError(f"cycle at tick {tick + 1}: state repeats, will never halt")
        seen.add(state)
        if dx and max(abs(S), abs(LO), abs(HI)).bit_length() > dx:
            raise WalkError(f"precision exceeded at tick {tick + 1}: needs more than {dx} bits")
    raise WalkError(f"budget of {budget} ticks used up")

#          K    S0 LO0 HI0  S rule    test      LO rule   HI rule   gate      dx  budget out
COUNT_P = [100, 2, 0, 0,   1,1,4,    1,1,0,    1,2,4,    4,1,0,    3,1,6,    0,  1000,  2]
HIGH_P  = [100, 2, 0, 0,   1,1,4,    1,1,0,    1,2,4,    4,1,0,    3,1,6,    0,  1000,  3]
FACT_18 = [18,  1, 0, 1,   1,1,4,    0,0,0,    0,0,0,    2,3,1,    5,1,6,    0,  1000,  3]
FIB_50  = [50,  0, 0, 1,   1,1,4,    0,0,0,    4,3,0,    1,2,3,    3,1,6,    0,  1000,  2]
FIB_100_IN_64_BITS = FIB_50[:]; FIB_100_IN_64_BITS[0] = 100; FIB_100_IN_64_BITS[19] = 64
LOOP    = [5,   0, 0, 0,   3,4,1,    0,0,0,    0,0,0,    0,0,0,    4,1,6,    0,  1000,  1]

if __name__ == "__main__":
    for name, v in [("count primes < 100", COUNT_P), ("highest prime < 100", HIGH_P),
                    ("18!", FACT_18), ("Fibonacci 50", FIB_50),
                    ("Fibonacci 100, 64-bit cell", FIB_100_IN_64_BITS), ("1 - S forever", LOOP)]:
        try:
            ans, ticks = walk(v)
            print(f"{name:<28} -> {ans}  ({ticks} ticks)")
        except WalkError as e:
            print(f"{name:<28} -> error: {e}")
    diff = [i for i in range(22) if COUNT_P[i] != HIGH_P[i]]
    print("dimensions where the two prime sentences differ:", diff)
