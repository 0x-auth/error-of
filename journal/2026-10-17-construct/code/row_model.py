"""
Frozen model, row version.

Input: start values + a list of rows. Each row is 4 numbers:
    (op, dst, a, b)
Registers R0..R7. An arg >= 0 is a register; an arg < 0 is the literal -arg-1
(so -1 means 0, -3 means 2, -21 means 20).

Each tick the model runs every row once, top to bottom. It stops when a
STOP row fires or the budget runs out. It never changes; only the rows do.
"""

def is_prime(n):
    return n > 1 and all(n % d for d in range(2, int(n**.5) + 1))

ADD, MUL, PRIME, AND, GE, EMIT, STOP = range(1, 8)
NAMES = {ADD: "ADD", MUL: "MUL", PRIME: "PRIME", AND: "AND", GE: "GE", EMIT: "EMIT", STOP: "STOP"}

def model(start, rows, budget=100000):
    R = [0] * 8
    for i, v in start.items():
        R[i] = v
    val = lambda x: R[x] if x >= 0 else -x - 1
    out = []
    for _ in range(budget):
        for op, dst, a, b in rows:
            A, B = val(a), val(b)
            if op == ADD:   R[dst] = A + B
            elif op == MUL: R[dst] = A * B
            elif op == PRIME: R[dst] = int(is_prime(A))
            elif op == AND: R[dst] = int(bool(A) and bool(B))
            elif op == GE:  R[dst] = int(A >= B)
            elif op == EMIT and R[dst]: out.append((A, B))
            elif op == STOP and R[dst]: return out
    raise RuntimeError("budget used up")

# Twin primes. R0 = S, R1 = S+2, R2/R3/R4 = tests, R5 = count, R6 = done
TWINS = [
    (PRIME, 2, 0, -1),     # R2 = is S prime
    (ADD,   1, 0, -3),     # R1 = S + 2
    (PRIME, 3, 1, -1),     # R3 = is S+2 prime
    (AND,   4, 2, 3),      # R4 = both
    (EMIT,  4, 0, 1),      # if R4: output (S, S+2)
    (ADD,   5, 5, 4),      # count += R4
    (ADD,   0, 0, -2),     # S = S + 1
    (GE,    6, 5, -21),    # R6 = count >= 20
    (STOP,  6, -1, -1),    # if R6: stop
]

if __name__ == "__main__":
    pairs = model({0: 2}, TWINS)
    print(len(pairs), "pairs:", pairs)
    flat = [n for row in TWINS for n in row]
    print("input vector:", [2] + flat, f"({1 + len(flat)} numbers)")
