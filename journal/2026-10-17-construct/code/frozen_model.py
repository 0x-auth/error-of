"""
Frozen deterministic model.

Input  : a tokenised vector (the problem statement), e.g. [FIB, 7] -> "1 7"
Model  : a frozen directed cyclic graph. Each node holds two registers
         (low, high) and a fixed rule; edges are fixed. Nothing is learned
         or updated at run time.
Output : one value. Same input -> same output, always.
"""

# ---- vocabulary (tokeniser) -------------------------------------------
VOCAB = {"FIB": 1, "SQUARE": 2, "SUM_TO": 3}

def tokenise(text):
    """'FIB 7' -> [1, 7]"""
    word, n = text.split()
    return [VOCAB[word], int(n)]

# ---- frozen model: node -> (rule, next node) ---------------------------
# Each rule reads (low, high, k) and returns new (low, high, k).
# k counts down the ticks left; the gate stops the walk when k == 0.
GRAPH = {
    # entry node per task: sets the two remembered states
    "fib_in":    (lambda lo, hi, k: (0, 1, k),           "fib_step"),
    "sq_in":     (lambda lo, hi, k: (0, 0, k),           "sq_step"),
    "sum_in":    (lambda lo, hi, k: (0, 0, k),           "sum_step"),
    # loop nodes: point back to themselves (the cycle)
    "fib_step":  (lambda lo, hi, k: (hi, lo + hi, k - 1), "fib_step"),
    "sq_step":   (lambda lo, hi, k: (lo + 1, hi + 2*lo + 1, k - 1), "sq_step"),
    "sum_step":  (lambda lo, hi, k: (lo + 1, hi + lo + 1, k - 1), "sum_step"),
}
ENTRY = {1: "fib_in", 2: "sq_in", 3: "sum_in"}   # task token -> basin
OUTPUT = {1: lambda lo, hi: lo, 2: lambda lo, hi: hi, 3: lambda lo, hi: hi}

def model(vector):
    task, n = vector
    node = ENTRY[task]                    # problem statement selects the basin
    lo, hi, k = 0, 0, n                   # and the point (n)
    rule, node = GRAPH[node]
    lo, hi, k = rule(lo, hi, k)
    ticks = 0
    while k > 0:                          # gate
        rule, node = GRAPH[node]
        lo, hi, k = rule(lo, hi, k)
        ticks += 1
    return OUTPUT[task](lo, hi), ticks

if __name__ == "__main__":
    for text in ["FIB 0", "FIB 1", "FIB 7", "FIB 50", "SQUARE 12", "SUM_TO 10"]:
        vec = tokenise(text)
        out, ticks = model(vec)
        print(f"{text:<10} vector={vec!s:<10} -> {out}   ({ticks} ticks)")
