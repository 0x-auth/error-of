import random
from collections import Counter
def walk(rng, p_stop=0.4, p_right=0.5):
    a,b,c,d = 0,1,1,0          # left bound a/b, right bound c/d
    path = ""
    while True:
        m = (a+c, b+d)          # mediant = current node
        if rng.random() < p_stop:
            return f"{m[0]}/{m[1]}", path or "·"
        if rng.random() < p_right: a,b = m; path += "R"
        else:                      c,d = m; path += "L"
rng = random.Random(42); N = 100000
cnt = Counter(walk(rng) for _ in range(N))
for (frac,path),k in cnt.most_common(8):
    print(f"{frac:>5}  path {path:<4} p={k/N:.3f}")
print("distinct targets reached:", len(cnt))
