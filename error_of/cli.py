"""error-of command line.

    error-of run <command ...>        run, capture, classify, report, store
    error-of report <case-id>         print a stored case as Markdown
    error-of search <text>            find stored cases by class, boundary or text
    error-of patterns                 recurring signatures and classes
    error-of walk <e1> <e2> ...       diagnose a walk from its signed errors
                                      (two remembered errors per step, no history)
"""
import json
import os
import sys
from collections import Counter

from . import core
from . import walk


def cmd_run(argv, out_dir):
    if not argv:
        print("usage: error-of run <command ...>", file=sys.stderr)
        return 2
    cap = core.capture(argv)
    case = core.build_case(cap)
    core.store(case)
    os.makedirs(out_dir, exist_ok=True)
    md, js = (os.path.join(out_dir, f"{case['id']}.{e}") for e in ("md", "json"))
    with open(md, "w") as f:
        f.write(core.to_markdown(case))
    with open(js, "w") as f:
        json.dump(case, f, indent=2)

    # the original output first, untouched
    sys.stdout.write(cap["stdout"])
    sys.stderr.write(cap["stderr"])
    print(f"\n[error-of] {case['status']}  exit={case['exit_code']}  "
          f"{len(case['observations'])} observation(s), {len(case['inferences'])} inference(s)"
          + (f", signature seen {case['seen_before']}x before" if case["seen_before"] else ""),
          file=sys.stderr)
    for o in case["observations"]:
        print(f"[error-of]   {o.get('class')}: {o.get('boundary')} -> {o.get('outcome', '')}",
              file=sys.stderr)
    for h in case["inferences"]:
        print(f"[error-of]   {h['class']}: assumed '{h['assumption']}'", file=sys.stderr)
    if case.get("side"):
        print(f"[error-of]   side: {case['side']}", file=sys.stderr)
    print(f"[error-of] report: {md}", file=sys.stderr)
    return case["exit_code"]


def cmd_report(case_id):
    for c in core.load_cases():
        if c["id"].startswith(case_id):
            print(core.to_markdown(c))
            return 0
    print(f"no case {case_id}", file=sys.stderr)
    return 1


def cmd_search(term):
    t = term.lower()
    n = 0
    for c in core.load_cases():
        blob = json.dumps(c["observations"] + c["inferences"]).lower() + c["stderr"].lower()
        if t in blob:
            classes = sorted({x.get("class") for x in c["observations"] + c["inferences"]})
            print(f"{c['id']}  {c['time']}  {c['status']:<9} {','.join(classes):<30} {' '.join(c['command'])}")
            n += 1
    return 0 if n else 1


def cmd_patterns():
    cases = core.load_cases()
    cls = Counter(x.get("class") for c in cases for x in c["observations"] + c["inferences"])
    sig = Counter(c["signature"] for c in cases if c["signature"])
    print(f"{len(cases)} cases\n\nclasses:")
    for k, v in cls.most_common():
        print(f"  {v:4}  {k}")
    print("\nrecurring signatures:")
    for k, v in sig.most_common():
        if v > 1:
            ex = next(c for c in cases if c["signature"] == k)
            print(f"  {v:4}  {k}  e.g. {' '.join(ex['command'])}")
    return 0


def cmd_walk(values):
    try:
        errors = [float(v) for v in values]
    except ValueError:
        print("usage: error-of walk <signed error> <signed error> ...", file=sys.stderr)
        return 2
    w = walk.Walk()
    last = None
    for e in errors:
        last = w.step(e)
        print(walk.describe(last))
    return 0 if last and last["state"] in ("arrived", "converging") else 1


def main():
    a = sys.argv[1:]
    out_dir = os.environ.get("ERROR_OF_OUT", "output")
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if a[0] == "run":
        return cmd_run(a[1:], out_dir)
    if a[0] == "report" and len(a) > 1:
        return cmd_report(a[1])
    if a[0] == "search" and len(a) > 1:
        return cmd_search(" ".join(a[1:]))
    if a[0] == "patterns":
        return cmd_patterns()
    if a[0] == "walk" and len(a) > 1:
        return cmd_walk(a[1:])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
