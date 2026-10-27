"""
Shortest route A -> Z visiting every node exactly once, run on pc_model.py.
The Reader side (this file) turns coordinates into a distance table and
writes the rows; the model only walks the rows.
"""
import math, itertools
from pc_model import model, ADD, SUB, MUL, JMP, LT, EQ, LOAD, JZ, EMIT, STOP, STORE

# Example nodes (approximate coordinates). A is the start, Z is the end.
NODES = [
    ("A Shaniwar Wada",   18.5196, 73.8554),
    ("B Aga Khan Palace", 18.5524, 73.9015),
    ("C Sinhagad Fort",   18.3664, 73.7559),
    ("D Pune Airport",    18.5821, 73.9197),
    ("E Hinjewadi",       18.5913, 73.7389),
    ("F Koregaon Park",   18.5362, 73.8940),
    ("G Katraj",          18.4529, 73.8652),
    ("Z Lonavala",        18.7546, 73.4062),
]

def metres(p, q):
    (la1, lo1), (la2, lo2) = map(math.radians, p), map(math.radians, q)
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return round(2 * 6_371_000 * math.asin(math.sqrt(h)))

n = len(NODES)
D = [metres(a[1:], b[1:]) for a in NODES for b in NODES]

# memory layout
V, P = n * n, n * n + n
T, B = P + n, P + 2 * n
lit = lambda k: -k - 1

def assemble(lines):
    pos, rows = {}, []
    for x in lines:
        if isinstance(x, str): pos[x] = len(rows)
        else: rows.append(x)
    return [(op, d, pos[a] if isinstance(a, str) else a, b) for op, d, a, b in rows]

# R0 depth  R1 cost  R2 best  R3 n  R4 node  R5..R7 scratch
ROWS = assemble([
 "loop", (EQ, 7, 0, lit(n - 1)), (JZ, 7, "try", 0),
   (ADD, 5, lit(P - 1), 0), (LOAD, 6, 5, 0), (MUL, 5, 6, 3), (ADD, 5, 5, lit(n - 1)),
   (LOAD, 5, 5, 0), (ADD, 5, 5, 1), (LT, 7, 5, 2), (JZ, 7, "back", 0),
   (ADD, 2, 5, lit(0)), (ADD, 4, lit(0), lit(0)),
 "copy", (LT, 7, 4, 0), (JZ, 7, "back", 0),
   (ADD, 5, lit(P), 4), (LOAD, 6, 5, 0), (ADD, 5, lit(B), 4), (STORE, 0, 5, 6),
   (ADD, 4, 4, lit(1)), (JMP, 0, "copy", 0),
 "try", (ADD, 5, lit(T), 0), (LOAD, 4, 5, 0), (LT, 7, lit(n - 2), 4), (JZ, 7, "cont", 0), (JMP, 0, "back", 0),
 "cont", (ADD, 6, 4, lit(1)), (STORE, 0, 5, 6),
   (ADD, 5, lit(V), 4), (LOAD, 6, 5, 0), (JZ, 6, "free", 0), (JMP, 0, "loop", 0),
 "free", (ADD, 5, lit(P - 1), 0), (LOAD, 6, 5, 0), (MUL, 6, 6, 3), (ADD, 6, 6, 4), (LOAD, 6, 6, 0),
   (ADD, 6, 6, 1), (LT, 7, 6, 2), (JZ, 7, "loop", 0),
   (ADD, 1, 6, lit(0)), (ADD, 5, lit(P), 0), (STORE, 0, 5, 4),
   (ADD, 5, lit(V), 4), (STORE, 0, 5, lit(1)), (ADD, 0, 0, lit(1)),
   (ADD, 5, lit(T), 0), (STORE, 0, 5, lit(1)), (JMP, 0, "loop", 0),
 "back", (SUB, 0, 0, lit(1)), (JZ, 0, "end", 0),
   (ADD, 5, lit(P), 0), (LOAD, 4, 5, 0), (ADD, 5, lit(V), 4), (STORE, 0, 5, lit(0)),
   (ADD, 5, lit(P - 1), 0), (LOAD, 6, 5, 0), (MUL, 6, 6, 3), (ADD, 6, 6, 4), (LOAD, 6, 6, 0),
   (SUB, 1, 1, 6), (JMP, 0, "loop", 0),
 "end", (EMIT, 0, 2, lit(0)), (ADD, 4, lit(0), lit(0)),
 "out", (LT, 7, 4, lit(n - 1)), (JZ, 7, "stop", 0),
   (ADD, 5, lit(B), 4), (LOAD, 6, 5, 0), (EMIT, 0, 6, lit(0)), (ADD, 4, 4, lit(1)), (JMP, 0, "out", 0),
 "stop", (STOP, 0, 0, 0),
])

if __name__ == "__main__":
    mem = D + [0] * (4 * n)
    mem[V + 0] = mem[V + n - 1] = 1          # A used, Z reserved for the end
    mem[T + 1] = 1                           # first candidate at depth 1
    out, ticks = model(mem, {0: 1, 2: 10**12, 3: n}, ROWS)
    best, order = out[0][0], [o[0] for o in out[1:]] + [n - 1]
    print("model :", " -> ".join(NODES[i][0][0] for i in order), f"= {best/1000:.1f} km  ({ticks} ticks, {len(ROWS)} rows)")
    # independent check by trying every order
    mids = range(1, n - 1)
    cost = lambda o: sum(D[a * n + b] for a, b in zip(o, o[1:]))
    chk = min(([0, *p, n - 1] for p in itertools.permutations(mids)), key=cost)
    print("check :", " -> ".join(NODES[i][0][0] for i in chk), f"= {cost(chk)/1000:.1f} km")
