#!/usr/bin/env python3
"""bbox_lib.py — TRUE-COORDINATE page geometry for Washington County's born-digital PDF ledgers.

WHY THIS EXISTS (measured 2026-08-23, on the page, not from a backlog note). The county's
2010-2013 generation publishes its ledgers as born-digital PDFs, and the module read them
through `pdftotext -layout`, i.e. through a CHARACTER-CELL reconstruction. That reconstruction
is **not stable across pages of one document**: on
`raw/wayback_2010elections/Expenditures - Rob Tersigni.pdf` the Amount column lands at
character columns 40-47 on page 1 and 19-26 on page 2, while the header — printed ONCE, on
page 1 — pins the family's column territories to the page-1 geometry. Every row on pages 2+
then failed the completeness gate and was silently dropped: 23 of 77 expenditure rows emitted.

In TRUE PDF coordinates there is no drift at all. The same file's Amount values right-align to
x=305.0 on **every** page and `Recipient` starts at x=56.4 on every page. The drift was an
artifact of the text reconstruction, never a property of the document.

So this module hands the family what the document actually says: `pdftotext -bbox-layout` word
boxes, clustered into lines, with the page size. Two things follow:

  * the column model is built ONCE from the printed header and is valid on every page, so
    multi-page ledgers parse completely;
  * every emitted row can carry **`pct:` geometry** (SCHEMA.md 2a — percentages of the page,
    resolution-independent, IIIF-region-shaped), measured from the PDF's own text coordinates
    rather than inferred. No page is rendered and no pixel is guessed.

The shell-out lives HERE, in the county module, so the shared family stays a pure
text/structure -> rows function. Stdlib only; `pdftotext` (poppler) is already a hard
dependency of this module's `build_text.py`.
"""
import os
import re
import subprocess
import xml.etree.ElementTree as ET

# words on the same printed line never differ by more than a fraction of the line height;
# 4.0 pt is well inside the 26 pt line pitch these exports use and well outside intra-line jitter.
_Y_TOL = 4.0


def read_pdf_boxes(pdf_path):
    """-> [{'width': float, 'height': float, 'lines': [{'y0','y1','words':[(x0,x1,text)]}]}]

    Returns [] when the file is not a PDF, poppler is unavailable, or the document carries no
    text layer (a scan). The caller then falls back to the `-layout` sidecar reader — never to
    a guess.
    """
    if not pdf_path or not os.path.exists(pdf_path):
        return []
    if os.path.splitext(pdf_path)[1].lower() != ".pdf":
        return []
    try:
        proc = subprocess.run(["pdftotext", "-bbox-layout", pdf_path, "-"],
                              capture_output=True, text=True)
    except (OSError, ValueError):
        return []
    if proc.returncode != 0 or not proc.stdout.strip():
        return []
    xml = re.sub(r'\sxmlns="[^"]+"', "", proc.stdout)
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []
    pages = []
    for page in root.iter("page"):
        try:
            w = float(page.get("width") or 0)
            h = float(page.get("height") or 0)
        except ValueError:
            continue
        words = []
        for el in page.iter("word"):
            t = (el.text or "").strip()
            if not t:
                continue
            try:
                words.append((float(el.get("yMin")), float(el.get("yMax")),
                              float(el.get("xMin")), float(el.get("xMax")), t))
            except (TypeError, ValueError):
                continue
        words.sort(key=lambda t: (t[0], t[2]))
        lines, cur = [], []
        for y0, y1, x0, x1, t in words:
            if cur and abs(y0 - cur[0][0]) <= _Y_TOL:
                cur.append((y0, y1, x0, x1, t))
                continue
            if cur:
                lines.append(cur)
            cur = [(y0, y1, x0, x1, t)]
        if cur:
            lines.append(cur)
        out = []
        for ln in lines:
            ln.sort(key=lambda t: t[2])
            out.append({"y0": min(x[0] for x in ln), "y1": max(x[1] for x in ln),
                        "words": [(x[2], x[3], x[4]) for x in ln]})
        pages.append({"width": w or 612.0, "height": h or 792.0, "lines": out})
    return pages
