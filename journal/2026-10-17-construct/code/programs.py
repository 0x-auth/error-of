"""
Every earlier problem, run on pc_model.py with the model untouched.
Only the input rows differ. Labels are a writing convenience: they are
turned into plain row numbers before the model sees anything.
"""
from pc_model import model, ADD, SUB, MUL, JMP, LT, EQ, LOAD, JZ, EMIT, STOP

def lit(n):            # literal value n as an argument
    return -n - 1

def assemble(lines):
    """lines: rows (op, d, a, b) or label strings. Returns plain numeric rows."""
    pos, rows = {}, []
    for x in lines:
        if isinstance(x, str): pos[x] = len(rows)
        else: rows.append(x)
    return [(op, d, pos[a] if isinstance(a, str) else a, b) for op, d, a, b in rows]

# 18!   R0=k R1=acc
FACT = assemble([
    "top", (LT, 7, lit(18), 0), (JZ, 7, "mul", 0), (JMP, 0, "done", 0),
    "mul", (MUL, 1, 1, 0), (ADD, 0, 0, lit(1)), (JMP, 0, "top", 0),
    "done", (EMIT, 0, 1, lit(0)), (STOP, 0, 0, 0)])

# Fibonacci n   R0=a R1=b R2=k R3=n R4=tmp
FIB = assemble([
    "top", (LT, 7, 2, 3), (JZ, 7, "done", 0),
    (ADD, 4, 0, 1), (ADD, 0, 1, lit(0)), (ADD, 1, 4, lit(0)), (ADD, 2, 2, lit(1)),
    (JMP, 0, "top", 0),
    "done", (EMIT, 0, 0, lit(0)), (STOP, 0, 0, 0)])

def prime_check(tag, on_composite, on_prime):
    """is R2 prime? trial division using only MUL, LT, SUB. R3=d*d R4=rem R5=d R7=test"""
    return [
        (ADD, 5, lit(2), lit(0)),
        tag + "d", (MUL, 3, 5, 5), (LT, 7, 2, 3), (JZ, 7, tag + "m0", 0), (JMP, 0, on_prime, 0),
        tag + "m0", (ADD, 4, 2, lit(0)),
        tag + "m", (LT, 7, 4, 5), (JZ, 7, tag + "s", 0),
        (JZ, 4, on_composite, 0), (ADD, 5, 5, lit(1)), (JMP, 0, tag + "d", 0),
        tag + "s", (SUB, 4, 4, 5), (JMP, 0, tag + "m", 0)]

# first 20 twin primes   R0=p R1=count R2=x
TWINS = assemble([
    "top", (ADD, 2, 0, lit(0)), *prime_check("a", "next", "second"),
    "second", (ADD, 2, 0, lit(2)), *prime_check("b", "next", "found"),
    "found", (EMIT, 0, 0, 2), (ADD, 1, 1, lit(1)), (LT, 7, 1, lit(20)), (JZ, 7, "end", 0),
    "next", (ADD, 0, 0, lit(1)), (JMP, 0, "top", 0),
    "end", (STOP, 0, 0, 0)])

# count and highest prime below 100   R0=p R1=count R6=highest
PRIMES = assemble([
    "top", (LT, 7, 0, lit(100)), (JZ, 7, "end", 0),
    (ADD, 2, 0, lit(0)), *prime_check("c", "next", "yes"),
    "yes", (ADD, 1, 1, lit(1)), (ADD, 6, 0, lit(0)),
    "next", (ADD, 0, 0, lit(1)), (JMP, 0, "top", 0),
    "end", (EMIT, 0, 1, 6), (STOP, 0, 0, 0)])

if __name__ == "__main__":
    print("18!                 ", model([], {0: 1, 1: 1}, FACT)[0][0][0])
    print("Fibonacci 50        ", model([], {1: 1, 3: 50}, FIB)[0][0][0])
    c, h = model([], {0: 2}, PRIMES)[0][0]
    print("primes below 100     count", c, " highest", h)
    print("first 20 twin primes", model([], {0: 3}, TWINS)[0])
