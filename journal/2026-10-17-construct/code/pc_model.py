"""
Frozen model, final form: one row per tick, a program counter, memory.

Input = (data, start registers, rows). Each row is 4 numbers (op, dst, a, b).
Registers R0..R7. Arg >= 0 is a register; arg < 0 is the literal -arg-1.
Memory M holds the data (a string becomes its character codes).

Ops
 1 ADD  dst = a + b        5 LT   dst = (a < b)       9  EMIT  output (a, b)
 2 SUB  dst = a - b        6 EQ   dst = (a == b)      10 STOP
 3 MUL  dst = a * b        7 LOAD dst = M[a]
 4 JMP  goto row a         8 JZ   if R[dst] == 0: goto row a
"""
ADD, SUB, MUL, JMP, LT, EQ, LOAD, JZ, EMIT, STOP, STORE = range(1, 12)
# 11 STORE  M[a] = b

def model(data, start, rows, budget=1_000_000):
    M = list(data)
    R = [0] * 8
    for k, v in start.items():
        R[k] = v
    val = lambda x: R[x] if x >= 0 else -x - 1
    pc, out = 0, []
    for tick in range(budget):
        op, d, a, b = rows[pc]
        pc += 1
        if   op == ADD:  R[d] = val(a) + val(b)
        elif op == SUB:  R[d] = val(a) - val(b)
        elif op == MUL:  R[d] = val(a) * val(b)
        elif op == JMP:  pc = a
        elif op == LT:   R[d] = int(val(a) < val(b))
        elif op == EQ:   R[d] = int(val(a) == val(b))
        elif op == LOAD: R[d] = M[val(a)]
        elif op == JZ:   pc = a if R[d] == 0 else pc
        elif op == EMIT: out.append((val(a), val(b)))
        elif op == STOP: return out, tick + 1
        elif op == STORE: M[val(a)] = val(b)
    raise RuntimeError("budget used up")

# Palindromic substrings. R0=i R1=j R2=l R3=r R4=n R5,R6=chars R7=test
PALINDROMES = [
    (LT,   7, 0, 4),      #  0 i < n ?
    (JZ,   7, 21, 0),     #  1 no -> end
    (ADD,  1, 0, -1),     #  2 j = i
    (LT,   7, 1, 4),      #  3 j < n ?
    (JZ,   7, 19, 0),     #  4 no -> next i
    (ADD,  2, 0, -1),     #  5 l = i
    (ADD,  3, 1, -1),     #  6 r = j
    (LT,   7, 2, 3),      #  7 l < r ?
    (JZ,   7, 16, 0),     #  8 no -> it is a palindrome
    (LOAD, 5, 2, 0),      #  9 left char
    (LOAD, 6, 3, 0),      # 10 right char
    (EQ,   7, 5, 6),      # 11 same?
    (JZ,   7, 17, 0),     # 12 no -> not a palindrome
    (ADD,  2, 2, -2),     # 13 l = l + 1
    (SUB,  3, 3, -2),     # 14 r = r - 1
    (JMP,  0, 7, 0),      # 15 back to l < r test
    (EMIT, 0, 0, 1),      # 16 output (i, j)
    (ADD,  1, 1, -2),     # 17 j = j + 1
    (JMP,  0, 3, 0),      # 18 back to j test
    (ADD,  0, 0, -2),     # 19 i = i + 1
    (JMP,  0, 0, 0),      # 20 back to i test
    (STOP, 0, 0, 0),      # 21 end
]

if __name__ == "__main__":
  for s in ["madam", "abca", "abba"]:
    pairs, ticks = model([ord(c) for c in s], {4: len(s)}, PALINDROMES)
    subs = [s[i:j + 1] for i, j in pairs]
    print(f"{s}: {len(subs)} palindromic substrings {subs}, distinct {sorted(set(subs), key=len)}, {ticks} ticks")
  print(f"{len(PALINDROMES)} rows, {4 * len(PALINDROMES)} numbers")
