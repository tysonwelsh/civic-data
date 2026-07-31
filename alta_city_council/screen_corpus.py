#!/usr/bin/env python3
"""Corpus screen for Town of Alta minutes PDFs.

Runs pdftotext -layout on every raw PDF for both bodies, measures extracted
character volume per page, and flags any doc that looks scanned/empty (a stub
needing OCR). Deterministic, no network. Writes screen_report.txt to each body dir.
"""
import subprocess, os, sys, glob

ROOT = "/Users/tysonwelsh/civic-data/alta_city_council"
BODIES = {"council": f"{ROOT}/meeting_minutes",
          "pc": f"{ROOT}/planning_commission"}
STUB_CHARS_PER_PAGE = 200  # below this avg -> likely scanned

def pages(pdf):
    try:
        out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True, timeout=60)
        for ln in out.stdout.splitlines():
            if ln.startswith("Pages:"):
                return int(ln.split()[1])
    except Exception:
        pass
    return 1

def main():
    all_stubs = []
    for tag, d in BODIES.items():
        raw = os.path.join(d, "raw")
        pdfs = sorted(glob.glob(os.path.join(raw, "*.pdf")))
        lines = [f"Corpus screen — {tag} ({len(pdfs)} PDFs)", "=" * 60]
        stubs = []
        for p in pdfs:
            txt = subprocess.run(["pdftotext", "-layout", p, "-"],
                                 capture_output=True, text=True, timeout=120).stdout
            n = len(txt.strip())
            pg = pages(p)
            cpp = n / max(pg, 1)
            flag = ""
            if cpp < STUB_CHARS_PER_PAGE:
                flag = "  <-- STUB / possibly scanned (OCR)"
                stubs.append(os.path.basename(p))
            lines.append(f"{os.path.basename(p):70s} pg={pg:2d} chars={n:6d} cpp={cpp:7.0f}{flag}")
        lines.append("")
        lines.append(f"STUBS needing OCR: {len(stubs)}")
        for s in stubs:
            lines.append(f"   {s}")
        open(os.path.join(d, "screen_report.txt"), "w").write("\n".join(lines) + "\n")
        print(f"{tag}: {len(pdfs)} pdfs, {len(stubs)} stubs")
        all_stubs += [(tag, s) for s in stubs]
    if all_stubs:
        print("STUBS:")
        for t, s in all_stubs:
            print(" ", t, s)
    else:
        print("SCREEN CLEAN: all born-digital text")

if __name__ == "__main__":
    main()
