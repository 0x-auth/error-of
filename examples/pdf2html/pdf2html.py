#!/usr/bin/env python3
"""pdf2html -- PDF to HTML, driven by its own errors.

The converter makes assumptions about layout. Each assumption has an
invariant that can be checked against the source. When an invariant is
violated, the violation is reported as an observation (ERROR-OF line on
stderr) and the next representation is tried. The output is the
representation that violates the fewest invariants, together with the
record of what each attempt revealed.

    python3 pdf2html.py input.pdf [output.html]

Invariants
  I1 conservation   every word on the page appears exactly once in the output
  I2 unfused cells  no cell runs a number straight into words
                    (that means two columns were joined into one)
  I3 sums           where a row is labelled total/gross/sum, the numbers above
                    it in the same column add up to it (checked on the source
                    geometry, so it does not depend on the representation)

Requires: pdfminer.six (pure Python; `pip install pdfminer.six`).
"""
import html
import json
import re
import sys

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTTextContainer, LTTextLine

NUM = re.compile(r"^[₹$€£(+-]?\d[\d,]*(\.\d+)?\)?%?$")


def observe(**kw):
    print("ERROR-OF " + json.dumps(kw), file=sys.stderr)


# ------------------------------------------------------------------ geometry

def words_of(path):
    """Words with positions. Word breaks come from pdfminer's space detection
    inside each text line; rows and columns are rebuilt here from positions."""
    pages = []
    for page in extract_pages(path):
        H = page.height
        words = []

        def walk(o):
            if isinstance(o, LTTextLine):
                cur = None
                for ch in o:
                    t = ch.get_text()
                    if isinstance(ch, LTChar) and t.strip():
                        if cur is None:
                            cur = {"text": t, "x0": ch.x0, "x1": ch.x1, "top": H - ch.y1, "size": ch.size}
                        else:
                            cur["text"] += t; cur["x1"] = max(cur["x1"], ch.x1)
                    else:
                        if cur: words.append(cur)
                        cur = None
                if cur: words.append(cur)
            elif hasattr(o, "__iter__"):
                for c in o:
                    walk(c)
        walk(page)
        pages.append({"w": page.width, "h": H, "words": words})
    return pages


def merge_words(words):
    words = sorted(words, key=lambda w: (w["top"], w["x0"]))
    out = []
    for w in words:
        p = out[-1] if out else None
        if p and abs(w["top"] - p["top"]) < w["size"] * 0.5 and 0 <= w["x0"] - p["x1"] < w["size"] * 0.25:
            p["text"] += w["text"]; p["x1"] = w["x1"]
        else:
            out.append(dict(w))
    return out


def lines_of(words):
    L = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        l = L[-1] if L else None
        if l and abs(w["top"] - l["top"]) < l["size"] * 0.45:
            l["words"].append(w)
        else:
            L.append({"top": w["top"], "size": w["size"], "words": [w]})
    for l in L:
        l["words"].sort(key=lambda w: w["x0"])
        l["size"] = max(w["size"] for w in l["words"])
    return L


def cells_of(line, merge_gap):
    C = []
    for w in line["words"]:
        c = C[-1] if C else None
        if c and w["x0"] - c["x1"] < w["size"] * merge_gap:
            c["text"] += " " + w["text"]; c["x1"] = max(c["x1"], w["x1"]); c["n"] += 1
        else:
            C.append({"text": w["text"], "x0": w["x0"], "x1": w["x1"], "n": 1})
    return C


def gutters(rows):
    allc = [c for r in rows for c in r]
    lo, hi = int(min(c["x0"] for c in allc)), int(max(c["x1"] for c in allc)) + 1
    cover = [0] * (hi - lo + 1)
    for r in rows:
        for c in r:
            for x in range(int(c["x0"]), int(c["x1"]) + 1):
                cover[x - lo] += 1
    thr = len(rows) * 0.15
    cols, cur = [], None
    for k, v in enumerate(cover):
        if v > thr:
            if cur is None:
                cur = [k + lo, k + lo]; cols.append(cur)
            else:
                cur[1] = k + lo
        else:
            cur = None
    return cols


def assign(rows, cols):
    grid = []
    for r in rows:
        g = [[] for _ in cols]
        for c in r:
            best = max(range(len(cols)), key=lambda i: min(cols[i][1], c["x1"]) - max(cols[i][0], c["x0"]))
            g[best].append(c["text"])
        grid.append([" ".join(x) for x in g])
    return grid


# ------------------------------------------------------------ representation

def represent(page, merge_gap):
    lines = lines_of(page["words"])
    for l in lines:
        l["cells"] = cells_of(l, merge_gap)
    blocks, i = [], 0
    while i < len(lines):
        if len(lines[i]["cells"]) >= 2:
            j = i + 1
            while (j < len(lines) and len(lines[j]["cells"]) >= 2
                   and lines[j]["top"] - lines[j - 1]["top"] < lines[j]["size"] * 3.2
                   and abs(len(lines[j]["cells"]) - len(lines[j - 1]["cells"])) < 2):
                j += 1
            rows = [l["cells"] for l in lines[i:j]]
            cols = gutters(rows)
            blocks.append({"t": "table", "rows": assign(rows, cols), "cells": [c for r in rows for c in r]})
            i = j
        else:
            l = lines[i]
            blocks.append({"t": "p", "text": l["cells"][0]["text"], "size": l["size"], "cells": l["cells"]})
            i += 1
    return blocks


# ---------------------------------------------------------------- invariants

def tokens(s):
    return s.split()


def check_conservation(page, blocks):
    src = sorted(w["text"] for w in page["words"])
    out = []
    for b in blocks:
        if b["t"] == "p":
            out += tokens(b["text"])
        else:
            for r in b["rows"]:
                for c in r:
                    out += tokens(c)
    out.sort()
    if src == out:
        return []
    from collections import Counter
    a, b = Counter(src), Counter(out)
    lost, extra = list((a - b).elements()), list((b - a).elements())
    return [dict(cls="Representation", boundary="conservation of words",
                 observation=f"lost {lost[:8]} extra {extra[:8]}",
                 assumption="grouping and column assignment keep every word")]


def fused(cell):
    """A number followed by a word in the same cell means two columns were
    joined ('306766 Tax Calculation', 'Payable Days 31.00 Bank A/c').
    A label ending in a number ('April 2025') and percentages are fine."""
    t = tokens(cell)
    for a, b in zip(t, t[1:]):
        if NUM.match(a) and not a.endswith("%") and re.search(r"[A-Za-z]{2,}", b):
            return True
    return False


def check_cells(blocks):
    v = [c for b in blocks if b["t"] == "table" for r in b["rows"] for c in r if fused(c)]
    if not v:
        return []
    return [dict(cls="Representation", boundary="one column per gutter",
                 observation=f"{len(v)} cells run a number straight into words, e.g. {v[:3]}",
                 assumption="words closer than the merge distance belong to the same cell")]


def check_sums(page):
    """Source-side check: for each total-labelled line, walk up the column."""
    lines = lines_of(page["words"])
    results = []
    for k, l in enumerate(lines):
        label = " ".join(w["text"] for w in l["words"] if not NUM.match(w["text"]))
        if not re.search(r"\b(total|gross)\b", label, re.I):
            continue
        for w in l["words"]:
            if not NUM.match(w["text"]):
                continue
            target = float(w["text"].replace(",", "").strip("₹$()"))
            vals = []
            for up in range(k - 1, -1, -1):
                hit = [u for u in lines[up]["words"]
                       if min(u["x1"], w["x1"]) - max(u["x0"], w["x0"]) > 0]
                if not hit:
                    if vals:
                        break
                    continue
                if not NUM.match(hit[0]["text"]):
                    break
                vals.append(float(hit[0]["text"].replace(",", "")))
            if len(vals) >= 2:
                results.append((label.strip()[:40], target, sum(vals), len(vals)))
    return results


# ---------------------------------------------------------------------- html

CSS = ("body{margin:0;padding:24px 16px;background:#f2f3f5;font:13px/1.45 Arial,sans-serif;color:#1b1f29}"
       ".doc{max-width:900px;margin:auto;background:#fff;padding:28px}h1{font-size:18px}h2{font-size:15px}"
       "p{margin:3px 0}.tw{overflow-x:auto;margin:10px 0}table{border-collapse:collapse;width:100%}"
       "td{border:1px solid #d3d6dd;padding:4px 8px;vertical-align:top}.n{text-align:right;"
       "font-variant-numeric:tabular-nums;white-space:nowrap}hr{border:0;border-top:2px dashed #d3d6dd;margin:22px 0}")


def render(pages_blocks, title):
    out = []
    for blocks in pages_blocks:
        sizes = sorted(b["size"] for b in blocks if b["t"] == "p") or [10]
        med = sizes[len(sizes) // 2]
        for b in blocks:
            if b["t"] == "p":
                tag = "h2" if b["size"] > med * 1.25 else "p"
                out.append(f"<{tag}>{html.escape(b['text'])}</{tag}>")
            else:
                rows = "".join("<tr>" + "".join(
                    f"<td{' class=\"n\"' if c and NUM.match(c) else ''}>{html.escape(c)}</td>" for c in r) + "</tr>"
                    for r in b["rows"])
                out.append(f'<div class="tw"><table>{rows}</table></div>')
        out.append("<hr>")
    return (f"<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\">"
            f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body><div class=\"doc\">"
            + "\n".join(out[:-1]) + "</div></body></html>")


# ---------------------------------------------------------------------- main

REPRESENTATIONS = [
    {"name": "wide cells", "merge_gap": 0.9},
    {"name": "tight cells", "merge_gap": 0.45},
    {"name": "word cells", "merge_gap": 0.2},
]


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else re.sub(r"\.pdf$", "", src, flags=re.I) + ".html"
    pages = words_of(src)
    nwords = sum(len(p["words"]) for p in pages)
    if nwords == 0:
        observe(**{"class": "Representation"}, boundary="text layer",
                observation="the PDF has no extractable text",
                assumption="the PDF stores text, not only an image of text",
                transformation="OCR the page images first", outcome="stopped")
        return 3

    # I3 does not depend on representation: check the source once.
    for label, target, got, n in (r for p in pages for r in check_sums(p)):
        ok = abs(target - got) < 0.5
        print(f"  I3 {'ok  ' if ok else 'FAIL'} {label}: {n} values sum to {got:,.0f}, row says {target:,.0f}")
        if not ok:
            observe(**{"class": "Precision"}, boundary="arithmetic consistency of the source",
                    observation=f"'{label}' says {target} but the column above sums to {got}",
                    assumption="a total row sums the column above it",
                    transformation="flag the row; the document or the column reading is wrong",
                    outcome="reported")

    attempts = []
    for rep in REPRESENTATIONS:
        blocks = [represent(p, rep["merge_gap"]) for p in pages]
        viol = []
        for p, b in zip(pages, blocks):
            viol += check_conservation(p, b) + check_cells(b)
        attempts.append((len(viol), rep, blocks, viol))
        print(f"  representation '{rep['name']}': {len(viol)} violation(s)")
        for v in viol:
            observe(**{"class": v["cls"]}, boundary=v["boundary"], observation=v["observation"],
                    assumption=v["assumption"],
                    transformation=f"try a representation after '{rep['name']}'",
                    outcome="next representation")
        if not viol:
            break

    best = min(attempts, key=lambda a: a[0])
    with open(dst, "w") as f:
        f.write(render(best[2], src))
    tables = sum(1 for bl in best[2] for b in bl if b["t"] == "table")
    print(f"wrote {dst}: {nwords} words, {tables} tables, representation '{best[1]['name']}', "
          f"{best[0]} violation(s) remaining")
    if best[0]:
        observe(**{"class": "Representation"}, boundary="all representations tried",
                observation=f"best still violates {best[0]} invariant(s)",
                assumption="one of the listed representations fits this layout",
                transformation="add a representation (region split, OCR, or a model reading)",
                outcome="output written with known violations")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
