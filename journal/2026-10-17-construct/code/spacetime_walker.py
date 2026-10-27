import math
def run(t, N=1024, start=100, show=True):
    dt, dx = t + 1/t, t - 1/t                 # tick and cell
    reach = math.floor(dt / dx)               # light cone: cells per tick (c=1)
    # frozen model: one fixed weight per cell (a landscape), never updated
    W = [math.exp(-((x-700)/120)**2) * (1 + 0.15*math.cos(x/9)) for x in range(N)]
    S, el, eh, last_dir, ticks = start, 0, N-1, 0, 0
    while True:
        cand = [S+k for k in range(-reach, reach+1) if 0 <= S+k < N]
        cand = [c for c in cand if el <= c <= eh]          # cross out the dissimilar
        nxt = max(cand, key=lambda c: W[c])
        d = (nxt > S) - (nxt < S)
        if d == 0 or eh - el <= 1: break                   # stop: nowhere better / bracket < one cell
        if last_dir and d != last_dir:                     # overshoot -> tighten bracket
            if last_dir > 0: eh = S
            else:            el = S
        S, last_dir, ticks = nxt, d, ticks + 1
    if show:
        print(f"t={t:.3f}  dx={dx:.3f} dt={dt:.3f}  dt^2-dx^2={dt*dt-dx*dx:.3f}  reach={reach}  "
              f"successors={2*reach+1}  ticks={ticks}  end cell={S}  bracket=[{el},{eh}]")
for t in [(1+5**.5)/2, 1.3, 1.1, 3.0]:
    run(t)
