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
  I0 coverage       every character drawn on the page is in some word
                    (checked against all characters, not against the words)
  I1 conservation   every word on the page appears exactly once in the output
  I2 unfused cells  no cell runs a number straight into words
                    (that means two columns were joined into one)
  I3 sums           where a row is labelled total/gross/sum, the numbers above
                    it in the same column add up to it (checked on the source
                    geometry, so it does not depend on the representation)

Graphics (vectors and images) come out as one SVG per page, chosen the same
way; see the graphics section for G1-G3. --no-graphics skips them.

Requires: pdfminer.six (pure Python; `pip install pdfminer.six`).
"""
import html
import json
import re
import sys

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTChar, LTTextContainer, LTTextLine

NUM = re.compile(r"^[₹$€£(+-]?\d[\d,]*(\.\d+)?\)?%?$")


def observe(**kw):
    print("ERROR-OF " + json.dumps(kw), file=sys.stderr)


# ------------------------------------------------------------------ geometry

def words_of(path, all_texts=False):
    """Words with positions. Word breaks come from pdfminer's space detection
    inside each text line; rows and columns are rebuilt here from positions."""
    pages = []
    for page in extract_pages(path, laparams=LAParams(all_texts=all_texts)):
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

        def count(o):
            if isinstance(o, LTChar):
                return 1 if o.get_text().strip() else 0
            return sum(count(c) for c in o) if hasattr(o, "__iter__") else 0
        pages.append({"w": page.width, "h": H, "words": words, "chars": count(page)})
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


# ------------------------------------------------------------------ graphics
#
# Graphics layer: the non-text content of each page (vectors and images) as SVG.
# Same discipline as the text layer: every representation carries assumptions,
# each assumption has an invariant checked against the source, a violation is
# an observation, and the next representation is tried.
#
#   G1 fidelity      the SVG, drawn by the target renderer, matches the source
#                    page drawn by poppler: under 0.5% of pixels off by >32/255,
#                    a pixel matching if its value lies in the range the source
#                    shows within 1 px of it (absorbs anti-aliasing phase);
#                    pixels under the text layer's words are left to I1
#   G2 closure       every reference (href="#id", url(#id)) resolves inside the
#                    page, and no id collides with another page's ids
#   G3 portability   only primitives target renderers agree on: no luminance
#                    <mask> filters (Chromium's print path gets them wrong; this
#                    holds even when G1 runs on cairo, which draws them fine)
#
# Requires: pdftocairo (poppler; `pkg install poppler` on Termux), numpy, Pillow.
# Renderer for G1, first one found: playwright+chromium, cairosvg, rsvg-convert.
import base64
import io
import os
import shutil
import subprocess
import tempfile

GL_PX_TOL = 32        # a pixel "differs" when some channel is off by more than this
GL_FRAC_MAX = 0.005   # G1 holds when under 0.5% of pixels differ
GL_DPI = 100


def _have(cmd):
    return shutil.which(cmd) is not None


class Renderer:
    """Draws an SVG string to an RGB array. Name says how much G1 can be trusted:
    chromium goes through print-to-PDF, the real HTML->PDF path; cairo agrees
    with poppler by construction."""

    def __init__(self):
        self.name, self._pw, self._b, self._page = None, None, None, None
        try:
            from playwright.sync_api import sync_playwright
            self._pw = sync_playwright().start()
            self._b = self._pw.chromium.launch()
            self._page = self._b.new_page()
            self.name = "chromium"
            return
        except Exception:
            self._pw = None
        try:
            import cairosvg  # noqa: F401
            self.name = "cairosvg"
            return
        except Exception:
            pass
        if _have("rsvg-convert"):
            self.name = "rsvg-convert"

    def draw(self, svg, w, h):
        import numpy as np
        from PIL import Image
        if self.name == "chromium":
            # the target path itself: Chromium prints the SVG to PDF, poppler
            # rasterizes that PDF. Print bugs (dropped images, masks) show up here.
            win, hin = w / GL_DPI, h / GL_DPI
            self._page.set_content(
                "<html><head><style>@page{margin:0}html,body{margin:0}"
                f"svg{{display:block;width:{win}in;height:{hin}in}}</style></head>"
                f"<body>{svg}</body></html>")
            with tempfile.TemporaryDirectory() as t:
                pdf = os.path.join(t, "r.pdf")
                self._page.pdf(path=pdf, width=f"{win:.5f}in", height=f"{hin:.5f}in",
                               print_background=True,
                               margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
                subprocess.run(["pdftocairo", "-png", "-singlefile", "-f", "1", "-l", "1",
                                "-scale-to-x", str(w), "-scale-to-y", str(h), pdf,
                                os.path.join(t, "r")], check=True)
                png = open(os.path.join(t, "r.png"), "rb").read()
        elif self.name == "cairosvg":
            import cairosvg
            png = cairosvg.svg2png(bytestring=svg.encode(), output_width=w,
                                   output_height=h, background_color="white")
        elif self.name == "rsvg-convert":
            png = subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h),
                                  "-b", "white"], input=svg.encode(),
                                 capture_output=True, check=True).stdout
        else:
            return None
        return np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(float)

    def close(self):
        if self._pw:
            self._b.close(); self._pw.stop()


def _page_png(src, pno, tmp):
    import numpy as np
    from PIL import Image
    out = os.path.join(tmp, f"src{pno}")
    subprocess.run(["pdftocairo", "-png", "-singlefile", "-r", str(GL_DPI),
                    "-f", str(pno), "-l", str(pno), src, out], check=True)
    return np.asarray(Image.open(out + ".png").convert("RGB")).astype(float)


def _page_svg(src, pno, tmp):
    out = os.path.join(tmp, f"p{pno}.svg")
    subprocess.run(["pdftocairo", "-svg", "-f", str(pno), "-l", str(pno), src, out],
                   check=True)
    return re.sub(r"<\?xml[^>]*\?>", "", open(out, encoding="utf-8").read())


# ---- transformations (each one answers a specific violation)

def t_namespace(svg, pno):
    """Answers G2 collisions: pages share one HTML document, so ids must not."""
    svg = re.sub(r'id="([^"]+)"', lambda m: f'id="p{pno}-{m.group(1)}"', svg)
    svg = re.sub(r'href="#([^"]+)"', lambda m: f'href="#p{pno}-{m.group(1)}"', svg)
    return re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#p{pno}-{m.group(1)})", svg)


def _b64img(tag):
    from PIL import Image
    data = re.search(r"base64,([A-Za-z0-9+/=]+)", tag).group(1)
    return Image.open(io.BytesIO(base64.b64decode(data)))


def t_flatten(svg):
    """Answers G3: bake luminance masks into RGBA images. Masked images are
    drawn through <use>, so images are first placed directly."""
    imgs = {m.group(1): m.group(0)
            for m in re.finditer(r'<image id="([^"]+)"[^>]*/>', svg)}
    masks = {m.group(1): m.group(2) for m in re.finditer(
        r'<mask id="([^"]+)">.*?<use xlink:href="#([^"]+)"', svg, re.S)}

    def bake(m):
        mid, img = m.group(1), m.group(2)
        if mid not in masks or masks[mid] not in imgs:
            return m.group(0)
        rgb = _b64img(img).convert("RGB")
        a = _b64img(imgs[masks[mid]]).convert("L")
        if a.size != rgb.size:
            a = a.resize(rgb.size)
        rgb.putalpha(a)
        buf = io.BytesIO(); rgb.save(buf, "PNG", optimize=True)
        return re.sub(r"base64,[A-Za-z0-9+/=]+",
                      "base64," + base64.b64encode(buf.getvalue()).decode(), img)

    def inline(m):
        src = imgs.get(m.group(1))
        if not src:
            return m.group(0)
        return re.sub(r'^<image id="[^"]+"', f'<image transform="{m.group(2)}"', src)

    svg = re.sub(r'<use xlink:href="#([^"]+)" transform="([^"]*)"\s*/>', inline, svg)
    svg = re.sub(r'<g mask="url\(#([^)]+)\)">\s*(<image[^>]*/>)\s*</g>', bake, svg)
    svg = re.sub(r'<mask id="[^"]+">.*?</mask>', "", svg, flags=re.S)

    for k, v in imgs.items():
        if f'#{k}"' not in svg:          # drop sources nothing points to any more
            svg = svg.replace(v, "", 1)
    return svg


def t_raster(svg, renderer, w, h):
    """Last resort: a picture of the graphics, drawn by the target renderer."""
    from PIL import Image
    arr = renderer.draw(svg, w, h)
    buf = io.BytesIO(); Image.fromarray(arr.astype("uint8")).save(buf, "PNG", optimize=True)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {w} {h}"><image width="{w}" height="{h}" xlink:href="data:image/png;base64,'
            f'{base64.b64encode(buf.getvalue()).decode()}"/></svg>')


def strip_text(svg):
    """The text layer already carries the words; keep only graphics."""
    svg = re.sub(r'<use xlink:href="#[^"]*glyph-[^"]*"[^>]*/>', "", svg)
    return re.sub(r'<g id="[^"]*glyph-[^"]*">.*?</g>', "", svg, flags=re.S)


def has_graphics(svg):
    body = re.sub(r"<defs>.*?</defs>", "", svg, flags=re.S)
    return bool(re.search(r"<(path|image|rect|circle|ellipse|line|polygon|polyline|use)\b", body))


# ---- invariants

def check_closure(svg, seen_ids):
    ids = re.findall(r'id="([^"]+)"', svg)
    refs = set(re.findall(r'href="#([^"]+)"', svg)) | set(re.findall(r"url\(#([^)]+)\)", svg))
    v = []
    dangling = sorted(refs - set(ids))
    if dangling:
        v.append(dict(cls="Representation", boundary="reference closure",
                      observation=f"{len(dangling)} references point nowhere, e.g. {dangling[:3]}",
                      assumption="every referenced definition is kept"))
    clash = sorted(set(ids) & seen_ids)
    if clash:
        v.append(dict(cls="Representation", boundary="one id space per document",
                      observation=f"{len(clash)} ids already used by an earlier page, e.g. {clash[:3]}",
                      assumption="each page's SVG is drawn on its own"))
    return v


def check_portable(svg):
    n_mask = len(re.findall(r"<mask\b", svg))
    if not n_mask:
        return []
    return [dict(cls="Representation", boundary="renderer agreement",
                 observation=f"{n_mask} luminance mask(s); Chromium's print path draws these wrong",
                 assumption="soft masks render the same everywhere")]


def text_mask(words, shape, pad=2):
    """Pixels covered by the text layer's words. Text fidelity is I1's job;
    G1 judges the graphics around and under it."""
    import numpy as np
    m = np.zeros(shape[:2], bool)
    k = GL_DPI / 72.0
    for w in words or []:
        y0 = int(w["top"] * k) - pad; y1 = int((w["top"] + w["size"]) * k) + pad
        x0 = int(w["x0"] * k) - pad; x1 = int(w["x1"] * k) + pad
        m[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = True
    return m


def check_fidelity(svg, ref, renderer, mask=None):
    import numpy as np
    if renderer.name is None:
        return [], None
    h, w = ref.shape[:2]
    got = renderer.draw(svg, w, h)
    hh, ww = min(h, got.shape[0]), min(w, got.shape[1])
    got, ref = got[:hh, :ww], ref[:hh, :ww]
    # renderers anti-alias edges at different sub-pixel phases: a pixel counts
    # as matching when its value lies inside the range the source shows within
    # one pixel of it. A dropped image or a wrong colour still falls outside.
    pad = np.pad(ref, ((1, 1), (1, 1), (0, 0)), mode="edge")
    win = [pad[dy:dy + hh, dx:dx + ww] for dy in (0, 1, 2) for dx in (0, 1, 2)]
    lo, hi = np.minimum.reduce(win), np.maximum.reduce(win)
    d = np.maximum(np.maximum(lo - got, got - hi), 0).max(2)
    keep = ~mask[:hh, :ww] if mask is not None else np.ones((hh, ww), bool)
    frac = float((d[keep] > GL_PX_TOL).mean()) if keep.any() else 0.0
    if frac <= GL_FRAC_MAX:
        return [], frac
    return [dict(cls="Precision", boundary="visual fidelity",
                 observation=f"{frac*100:.2f}% of pixels differ by >{GL_PX_TOL}/255 "
                             f"(allowed {GL_FRAC_MAX*100:.1f}%), renderer {renderer.name}",
                 assumption="this representation draws what the source draws")], frac


# ---- driver

def graphics_layer(src, pages=None):
    """Returns one SVG string (or None) per page, chosen by fewest violations."""
    if not _have("pdftocairo"):
        observe(**{"class": "Representation"}, boundary="graphics layer",
                observation="pdftocairo not found", assumption="poppler is installed",
                transformation="install poppler (pkg install poppler)", outcome="graphics skipped")
        return None
    renderer = Renderer()
    if renderer.name is None:
        observe(**{"class": "Representation"}, boundary="visual fidelity",
                observation="no SVG renderer found; G1 cannot be checked",
                assumption="a renderer is available to verify the graphics",
                transformation="pip install cairosvg, or playwright", outcome="G1 unchecked")
    elif renderer.name != "chromium":
        observe(**{"class": "Precision"}, boundary="visual fidelity",
                observation=f"G1 uses {renderer.name}, which shares cairo with poppler",
                assumption="the verifying renderer is independent of the producing one",
                transformation="G3 stands in for browser-specific failures", outcome="G1 weaker")
    out, seen = [], set()
    n = int(re.search(r"Pages:\s+(\d+)",
                      subprocess.run(["pdfinfo", src], capture_output=True, text=True).stdout).group(1)) \
        if _have("pdfinfo") else None
    with tempfile.TemporaryDirectory() as tmp:
        pno = 1
        while n is None or pno <= n:
            try:
                raw = _page_svg(src, pno, tmp)
            except subprocess.CalledProcessError:
                break
            ref = _page_png(src, pno, tmp) if renderer.name else None
            mask = (text_mask(pages[pno - 1]["words"], ref.shape)
                    if ref is not None and pages and pno <= len(pages) else None)
            h, w = (ref.shape[:2] if ref is not None else (0, 0))
            cands = [("raw svg", lambda: raw),
                     ("namespaced svg", lambda: t_namespace(raw, pno)),
                     ("flattened svg", lambda: t_flatten(t_namespace(raw, pno)))]
            if renderer.name:
                def raster():
                    flat = t_flatten(t_namespace(raw, pno))
                    return (t_namespace(t_raster(flat, renderer, w, h), pno),
                            t_namespace(t_raster(strip_text(flat), renderer, w, h), f"{pno}g"))
                cands.append(("raster", raster))
            attempts = []
            for name, make in cands:
                made = make()
                svg, emit = made if isinstance(made, tuple) else (made, None)
                viol = check_closure(svg, seen) + check_portable(svg)
                fv, frac = check_fidelity(svg, ref, renderer, mask) if ref is not None else ([], None)
                viol += fv
                attempts.append((len(viol), name, svg, frac, emit))
                for v in viol:
                    observe(**{"class": v["cls"]}, page=pno, boundary=v["boundary"],
                            observation=v["observation"], assumption=v["assumption"],
                            transformation=f"try a graphics representation after '{name}'",
                            outcome="next representation")
                if not viol:
                    break
            best = min(attempts, key=lambda a: a[0])
            seen |= set(re.findall(r'id="([^"]+)"', best[2]))
            g = best[4] if best[4] is not None else strip_text(best[2])
            fr = f", {best[3]*100:.3f}% px differ" if best[3] is not None else ""
            print(f"  graphics p{pno}: '{best[1]}', {best[0]} violation(s){fr}")
            out.append(g if has_graphics(g) else None)
            pno += 1
    renderer.close()
    return out


# ---------------------------------------------------------------------- html

CSS = ("body{margin:0;padding:24px 16px;background:#f2f3f5;font:13px/1.45 Arial,sans-serif;color:#1b1f29}"
       ".doc{max-width:900px;margin:auto;background:#fff;padding:28px}h1{font-size:18px}h2{font-size:15px}"
       "p{margin:3px 0}.tw{overflow-x:auto;margin:10px 0}table{border-collapse:collapse;width:100%}"
       "td{border:1px solid #d3d6dd;padding:4px 8px;vertical-align:top}.n{text-align:right;"
       "font-variant-numeric:tabular-nums;white-space:nowrap}.pg svg{display:block;width:100%;height:auto;margin:6px 0 14px}hr{border:0;border-top:2px dashed #d3d6dd;margin:22px 0}")


def render(pages_blocks, title, graphics=None):
    out = []
    for k, blocks in enumerate(pages_blocks):
        if graphics and k < len(graphics) and graphics[k]:
            out.append(f'<div class="pg">{graphics[k]}</div>')
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
    args = [a for a in sys.argv[1:] if a != "--no-graphics"]
    want_graphics = "--no-graphics" not in sys.argv
    sys.argv = [sys.argv[0]] + args
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else re.sub(r"\.pdf$", "", src, flags=re.I) + ".html"
    pages = words_of(src)
    # I0 coverage: every character drawn on the page is in some word. I1 cannot
    # see this, since it counts the source with the same extraction.
    short = [(k + 1, p["chars"], sum(len(w["text"]) for w in p["words"]))
             for k, p in enumerate(pages)
             if sum(len(w["text"]) for w in p["words"]) < p["chars"]]
    if short:
        observe(**{"class": "Representation"}, boundary="text coverage",
                observation=f"{len(short)} page(s) draw characters that no word holds, "
                            f"e.g. page {short[0][0]}: {short[0][1]} drawn, {short[0][2]} in words",
                assumption="all text sits in top-level text lines",
                transformation="re-extract grouping text inside figures (all_texts)",
                outcome="re-extracted")
        pages = words_of(src, all_texts=True)
        left = [k + 1 for k, p in enumerate(pages)
                if sum(len(w["text"]) for w in p["words"]) < p["chars"]]
        if left:
            observe(**{"class": "Representation"}, boundary="text coverage",
                    observation=f"pages {left[:10]} still draw characters no word holds",
                    assumption="text inside figures groups into lines",
                    transformation="none yet", outcome="reported")
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
        f.write(render(best[2], src, graphics_layer(src, pages) if want_graphics else None))
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
