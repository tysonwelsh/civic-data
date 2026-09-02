#!/usr/bin/env python3
"""fitgrid.py <pdf> <page> [--col x0,x1] — fit a REGULAR row grid to a page's detected rules.

PROMOTED 2026-08-18 from the summit/weber wave kits alongside `rowbands.py` (whose fixed
detection this inherits — coordinates are RAW-render-frame). Handwritten ledgers defeat
plain band detection: ink crossing a rule merges two bands, and a heavy pen stroke invents
one. But the underlying PRINTED grid is perfectly regular, so the honest recovery is to fit
`y = y0 + k*pitch` to the rules that WERE found and report the fit, its residual and how
many detected rules it explains. The frame is then declared in the record, and the fit
statistics are the evidence that it is a measurement of the page and not a guess.

Prints the fitted pitch, the anchor, the residual, and the implied y of each band.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rowbands as RB  # noqa: E402


def fit(ys, lo=None, hi=None, steps=2500):
    """Grid-search pitch; score = rules explained within 0.25 * pitch, tie-break residual.

    ⚠ THE SEARCH RANGE IS DERIVED FROM THE PAGE, not fixed. Any integer DIVISOR of the
    true pitch explains every rule too — a 4.05-pct printed grid is "explained 17/17" by a
    1.35-pct pitch — so an open search silently returns a sub-multiple and every band index
    is then 2x or 3x wrong. The printed pitch is the TYPICAL ADJACENT-RULE GAP, so the
    search is bounded to 0.7-1.4x the median gap and the sub-multiples fall outside it.
    """
    gaps = sorted(b - a for a, b in zip(ys, ys[1:]) if b > a)
    med = gaps[len(gaps) // 2] if gaps else 1.0
    lo = lo if lo is not None else max(0.3, 0.7 * med)
    hi = hi if hi is not None else max(lo + 0.1, 1.4 * med)
    best = None
    for i in range(steps):
        p = lo + (hi - lo) * i / (steps - 1)
        for anchor in ys:
            resid, hits = 0.0, 0
            for y in ys:
                k = round((y - anchor) / p)
                d = abs(y - (anchor + k * p))
                if d <= 0.25 * p:
                    hits += 1
                    resid += d
            score = (hits, -resid)
            if best is None or score > best[0]:
                best = (score, p, anchor)
    return best


def main():
    pdf, page = sys.argv[1], int(sys.argv[2])
    col = None
    if "--col" in sys.argv:
        col = tuple(float(v) for v in sys.argv[sys.argv.index("--col") + 1].split(","))
    img = RB.render(pdf, page, 200)
    hr, vr, W, H, ang = RB.rules(img, col=col)
    ys = [100.0 * y / H for y in hr]
    if len(ys) < 4:
        print("too few rules (%d) to fit" % len(ys))
        return
    (hits, negres), p, anchor = fit(ys)
    k0 = min(round((y - anchor) / p) for y in ys)
    y0 = anchor + k0 * p
    print("rules=%d  fit pitch=%.4f  y0=%.3f  explains %d/%d  mean_resid=%.4f  skew=%.1f"
          % (len(ys), p, y0, hits, len(ys), -negres / max(hits, 1), ang))
    cols = [round(100.0 * x / W, 2) for x in vr]
    print("cols=%s" % cols)
    n = max(1, int((99.0 - y0) / p) + 1)
    print("band tops: %s" % ", ".join("%d:%.2f" % (i + 1, y0 + i * p) for i in range(n)))


if __name__ == "__main__":
    main()
