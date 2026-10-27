"""
Error-driven reconstruction loop, built only from what the fabric provides.

  cue (problem) -> reconstructor proposes a program -> the fabric runs it
  under a time limit and a space limit -> the fabric's reply (error or output)
  is classified into an elimination signal -> only the last two signals are
  kept -> the next proposal is conditioned on them -> stop when the gate passes.

Space and time are interchangeable: a time error asks for more space
(store instead of recompute); a space error asks for more time
(recompute instead of store).
"""
import resource, subprocess, sys, tempfile, textwrap

TIME_LIMIT_S = 3              # the fabric's budget of ticks
SPACE_LIMIT_MB = 200          # the fabric's budget of cells

def _limit_space():
    b = SPACE_LIMIT_MB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (b, b))

def run_in_fabric(code, arg):
    """Run one candidate in its own process. Returns (kind, detail)."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(textwrap.dedent(code))
        path = f.name
    try:
        p = subprocess.run([sys.executable, "-I", path, str(arg)], capture_output=True,
                           text=True, timeout=TIME_LIMIT_S, preexec_fn=_limit_space)
    except subprocess.TimeoutExpired:
        return "time", f"no answer within {TIME_LIMIT_S}s"
    err = p.stderr.strip().splitlines()
    if p.returncode != 0:
        last = err[-1] if err else f"exit code {p.returncode}"
        if "MemoryError" in last or p.returncode in (-9, 137):
            return "space", f"needed more than {SPACE_LIMIT_MB} MB"
        if "RecursionError" in last:
            return "space", "call stack exhausted"
        if "SyntaxError" in last:
            return "syntax", last
        return "exception", last
    return "output", p.stdout.strip()

SIGNAL = {
    "time":      "too slow: trade space for time (store results instead of recomputing)",
    "space":     "too big: trade time for space (recompute or keep only what the next step needs)",
    "syntax":    "not a valid program: same idea, fix the form",
    "exception": "a wrong assumption: the message names it",
    "wrong":     "runs, but lands on the wrong side of the answer",
}

def loop(problem, arg, gate, reconstruct, max_ticks=10):
    """reconstruct(problem, e_low, e_high) -> (name, code). gate(output) -> (ok, side)."""
    e_low = e_high = None                       # the only memory kept
    for tick in range(1, max_ticks + 1):
        name, code = reconstruct(problem, e_low, e_high)
        kind, detail = run_in_fabric(code, arg)
        if kind == "output":
            ok, side = gate(detail)
            if ok:
                print(f"tick {tick}: {name:<26} -> passes the gate")
                return detail
            kind, detail = "wrong", f"{side}"
        signal = SIGNAL[kind]
        print(f"tick {tick}: {name:<26} -> {kind}: {detail}\n{'':<10}signal: {signal}")
        # keep two edges: the newest error, and the one before it
        e_low, e_high = e_high, (kind, detail, signal)
    print("budget of ticks used up")
