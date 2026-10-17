"""error-of core: capture -> normalize -> classify -> infer -> report -> store.

Every inference carries the rule that produced it (design principle:
"explain every inference"). The original stdout/stderr are kept verbatim
("preserve original errors"). The knowledge base is append-only JSONL
("learn without rewriting history").
"""
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

# --------------------------------------------------------------------- capture

def capture(argv, timeout=None):
    t0 = time.monotonic()
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        out, err, code = p.stdout, p.stderr, p.returncode
    except FileNotFoundError as e:
        out, err, code = "", f"{e}", 127
    except subprocess.TimeoutExpired as e:
        out = e.stdout or ""
        err = (e.stderr or "") + f"\n[error-of] timeout after {timeout}s"
        code = 124
        out = out.decode() if isinstance(out, bytes) else out
        err = err.decode() if isinstance(err, bytes) else err
    return {
        "command": argv,
        "stdout": out,
        "stderr": err,
        "exit_code": code,
        "runtime_s": round(time.monotonic() - t0, 4),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "cwd": os.getcwd(),
        },
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


# ------------------------------------------------- self-reported observations
# A program can describe its own boundary by printing one line to stderr:
#   ERROR-OF {"class": ..., "boundary": ..., "assumption": ..., ...}
# Those are taken as first-hand observations and ranked above pattern guesses.

OBS_RE = re.compile(r"^ERROR-OF\s+(\{.*\})\s*$", re.M)


def self_reports(stderr):
    found = []
    for m in OBS_RE.finditer(stderr):
        try:
            d = json.loads(m.group(1))
            d["source"] = "self-report"
            found.append(d)
        except json.JSONDecodeError:
            pass
    return found


# ------------------------------------------------------------------- classify
# Each rule: class, regex, boundary, assumption, possible invariant, transformations.

RULES = [
    ("Syntax", r"SyntaxError|syntax error near unexpected token|unexpected EOF|IndentationError",
     "the parser's grammar",
     "the text is written in the language of the program that reads it",
     "an interpreter accepts only its own grammar",
     ["check the interpreter matches the file (python vs bash: shebang or `python file.py`)",
      "look for a wrapped or merged line near the reported position"]),
    ("Context", r"command not found|No such file or directory|not a git repository|ModuleNotFoundError|ImportError|cannot find module",
     "what exists in this environment",
     "a name the program refers to exists where it is run",
     "a reference is only valid inside the context that defines it",
     ["install or activate the missing piece (venv, package, PATH)",
      "make the dependency explicit (requirements file, shebang, absolute path)"]),
    ("Memory", r"MemoryError|out of memory|Killed|std::bad_alloc|Cannot allocate memory",
     "available memory",
     "the whole state fits in memory at once",
     "state size grows with input; memory does not",
     ["stream or chunk instead of materialising everything",
      "replace enumeration by a closed form or recurrence"]),
    ("Precision", r"OverflowError|int too large to convert to float|FloatingPointError|ZeroDivisionError|\b(inf|nan)\b",
     "the number representation",
     "floats can stand in for the exact values",
     "an exact quantity should survive the round trip",
     ["use exact types (int, Fraction, Decimal, symbolic)",
      "keep values in a representation where the operation is closed"]),
    ("Time", r"timeout|Timed out|TimeoutExpired|deadline exceeded",
     "the time budget",
     "the work finishes within the allowed time",
     "cost grows with input size",
     ["reduce complexity, cache, or parallelise",
      "make progress resumable"]),
    ("Storage", r"No space left on device|Disk quota exceeded|ENOSPC",
     "disk capacity",
     "there is room to write",
     "writes need free space",
     ["clean caches and build outputs", "write elsewhere or compress"]),
    ("Permissions", r"Permission denied|Operation not permitted|EACCES|EPERM",
     "the permission boundary",
     "this process may touch this resource",
     "access is granted per identity and path",
     ["run with the right identity or path", "request the permission explicitly"]),
    ("Authentication", r"\b401\b|403 Forbidden|Unauthorized|invalid token|authentication failed",
     "identity verification",
     "the caller is who the service expects",
     "credentials expire and are scoped",
     ["refresh or rescope the credential"]),
    ("Network", r"Connection refused|Name or service not known|ECONNRESET|Network is unreachable|\b429\b|Too Many Requests",
     "reachability",
     "the remote side is reachable and willing",
     "a remote resource can refuse or be absent",
     ["retry with backoff", "use a local copy or a different route"]),
    ("Representation", r"ValueError|TypeError|invalid literal|could not convert|UnicodeDecodeError|KeyError",
     "the shape of the data",
     "the data has the form the code expects",
     "input form and code form must match",
     ["validate and normalise at the boundary", "choose a representation where the case is legal"]),
]


# Which way the wall was hit, and which way to move. A boundary says where the
# walk stopped; a side says what to do next. Classes without a side (Syntax,
# Context, ...) are walls with no direction: the fix is to change the input,
# not to move along an axis. Space and time trade against each other.
SIDES = {
    "Memory":    ("too big",    "trade time for space: recompute or keep only what the next step needs"),
    "Storage":   ("too big",    "trade time for space: write less, compress, or stream"),
    "Time":      ("too slow",   "trade space for time: store results instead of recomputing"),
    "Precision": ("too coarse", "use a finer representation: the value needs more than the cell holds"),
}


def classify(stderr, stdout=""):
    text = stderr + "\n" + stdout
    hits = []
    for cls, pat, boundary, assumption, invariant, transforms in RULES:
        m = re.search(pat, text)
        if m:
            side, trade = SIDES.get(cls, (None, None))
            hits.append({
                "class": cls, "boundary": boundary, "assumption": assumption,
                "invariant": invariant, "transformations": transforms,
                "side": side, "trade": trade,
                "evidence": text[max(0, m.start() - 60):m.end() + 60].strip(),
                "rule": pat, "source": "pattern",
            })
    return hits


def case_side(observations, inferences):
    """The case's side: a program's own report first, then the first pattern that has one."""
    for x in list(observations) + list(inferences):
        if x.get("side"):
            return x["side"]
    return None


def signature(stderr):
    """Stable fingerprint of an error, insensitive to paths, numbers and addresses."""
    s = re.sub(r"0x[0-9a-fA-F]+|\d+", "N", stderr)
    s = re.sub(r"(/[\w.\-]+)+", "PATH", s)
    lines = [l.strip() for l in s.splitlines() if l.strip()][-3:]
    return hashlib.sha1("\n".join(lines).encode()).hexdigest()[:12]


# ----------------------------------------------------------------------- store

def kb_path():
    return os.environ.get("ERROR_OF_HOME", os.path.expanduser("~/.error-of")) + "/cases.jsonl"


def store(case):
    path = kb_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(case) + "\n")


def load_cases():
    try:
        with open(kb_path()) as f:
            return [json.loads(l) for l in f if l.strip()]
    except FileNotFoundError:
        return []


# ---------------------------------------------------------------------- report

def build_case(cap):
    obs = self_reports(cap["stderr"])
    pats = classify(cap["stderr"], cap["stdout"]) if cap["exit_code"] != 0 or not obs else []
    sig = signature(cap["stderr"]) if cap["stderr"].strip() else None
    prior = [c for c in load_cases() if sig and c.get("signature") == sig]
    if cap["exit_code"] == 0 and not obs:
        status = "clean"
    elif cap["exit_code"] == 0:
        status = "continued"           # boundaries met and crossed
    else:
        status = "stopped"
    case = dict(cap)
    case.update({
        "id": hashlib.sha1((cap["time"] + " ".join(cap["command"])).encode()).hexdigest()[:10],
        "status": status,
        "observations": obs,
        "inferences": pats if pats else ([] if obs or status == "clean" else [{
            "class": "Unknown", "boundary": "unidentified", "assumption": "unidentified",
            "invariant": None, "transformations": ["add a rule for this signature"],
            "evidence": cap["stderr"][-200:], "rule": None, "source": "fallback"}]),
        "signature": sig,
        "seen_before": len(prior),
    })
    case["side"] = case_side(case["observations"], case["inferences"])
    return case


def to_markdown(c):
    L = [f"# error-of case {c['id']}", "",
         f"- command: `{' '.join(c['command'])}`",
         f"- exit code: {c['exit_code']}   runtime: {c['runtime_s']}s   status: **{c['status']}**",
         f"- signature: {c['signature']}   seen before: {c['seen_before']}",
         f"- side: {c.get('side') or 'none (a wall with no direction)'}", ""]
    if c["observations"]:
        L += ["## Observations (reported by the program itself)", ""]
        for i, o in enumerate(c["observations"], 1):
            L += [f"### {i}. {o.get('class', '?')}: {o.get('boundary', '')}", ""]
            for k in ("observation", "assumption", "invariant", "transformation", "side", "error", "outcome"):
                if o.get(k) is not None:
                    L.append(f"- **{k}:** {o[k]}")
            L.append("")
    if c["inferences"]:
        L += ["## Inferences (from patterns in the output)", ""]
        for i, h in enumerate(c["inferences"], 1):
            L += [f"### {i}. {h['class']}", "",
                  f"- **boundary:** {h['boundary']}",
                  f"- **assumption:** {h['assumption']}",
                  f"- **possible invariant:** {h['invariant']}",
                  *([f"- **side:** {h['side']} ({h['trade']})"] if h.get("side") else []),
                  "- **suggested transformations:**"] + [f"  - {t}" for t in h["transformations"]] + [
                  f"- **because:** matched `{h['rule']}` in: `{h['evidence'][:160]}`", ""]
    L += ["## Original stderr", "", "```", c["stderr"].rstrip() or "(empty)", "```", "",
          "## Original stdout", "", "```", c["stdout"].rstrip()[-4000:] or "(empty)", "```"]
    return "\n".join(L)
