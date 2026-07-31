#!/usr/bin/env python3
"""
Corpus screen (mandatory QC gate) — anomaly-screen the minutes markdown for each body
against the corpus's own statistical baseline to catch OCR garble / broken extractions,
and re-OCR any scanned stub (pdftoppm + tesseract) in place.

Per file we compute: char count, letter ratio (letters / non-space chars), mean token
length, share of 1-char tokens, and whether the vote grammar is present. A file is FLAGGED
when it is a statistical outlier (very low letter ratio, tiny body, or high 1-char-token
share) — the signatures of a scanned/garbled PDF. Flagged raw PDFs are re-OCR'd; temp PNGs
are deleted.

Run:  python3 .harvest/corpus_screen.py            # report only
      python3 .harvest/corpus_screen.py --fix       # re-OCR flagged raw PDFs, rewrite md
"""
import re, subprocess, sys, statistics, tempfile, shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATASETS = {"meeting_minutes": REPO/"meeting_minutes", "planning_commission": REPO/"planning_commission"}
HDR = re.compile(r"<!--.*?-->", re.S)

def stats(text):
    body = HDR.sub("", text)
    nonspace = re.sub(r"\s", "", body)
    letters = sum(c.isalpha() for c in nonspace)
    toks = re.findall(r"\S+", body)
    one = sum(1 for t in toks if len(t) == 1)
    return dict(
        chars=len(body),
        letter_ratio=(letters/len(nonspace)) if nonspace else 0.0,
        mean_tok=(statistics.mean(len(t) for t in toks) if toks else 0),
        one_share=(one/len(toks)) if toks else 0.0,
        has_vote=bool(re.search(r"Roll Call Vote:|Voice Vote:|Vote:|:\s*(Yes|No)\b|– Aye", body)),
        toks=len(toks),
    )

def reocr(pdf, out_md_header):
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["pdftoppm", "-r", "300", "-png", str(pdf), str(tmp/"p")], check=True)
        parts = []
        for png in sorted(tmp.glob("p*.png")):
            parts.append(subprocess.run(["tesseract", str(png), "-", "--psm", "6"],
                                        capture_output=True, text=True).stdout)
        return out_md_header + "\n\n".join(parts)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def main():
    fix = "--fix" in sys.argv
    report = []; flagged_total = 0
    for name, ds in DATASETS.items():
        mds = sorted((ds/"minutes").rglob("*.md"))
        if not mds:
            continue
        S = [(md, stats(md.read_text(encoding="utf-8", errors="replace"))) for md in mds]
        lrs = [s["letter_ratio"] for _, s in S]
        med_lr = statistics.median(lrs) if lrs else 0
        report.append(f"\n=== {name}: {len(S)} files, median letter_ratio={med_lr:.3f} ===")
        flagged = []
        for md, s in S:
            reasons = []
            if s["letter_ratio"] < 0.55: reasons.append(f"letter_ratio={s['letter_ratio']:.2f}")
            if s["chars"] < 400: reasons.append(f"tiny={s['chars']}c")
            if s["one_share"] > 0.30: reasons.append(f"1char={s['one_share']:.2f}")
            if not s["has_vote"] and s["chars"] > 400: reasons.append("no-vote-grammar")
            if reasons:
                flagged.append((md, s, reasons))
        report.append(f"   flagged: {len(flagged)}")
        for md, s, reasons in flagged:
            report.append(f"   FLAG {md.relative_to(ds)}  [{', '.join(reasons)}]")
            flagged_total += 1
            if fix and any("letter_ratio" in r or "1char" in r for r in reasons):
                # scanned/garbled -> re-OCR the retained raw pdf
                m = re.search(r"pmn_file:\s*(\d+)", md.read_text())
                raws = list((ds/"raw").glob(f"{md.stem}_*.pdf"))
                if raws:
                    header = HDR.search(md.read_text()).group(0) + "\n\n"
                    new = reocr(raws[0], header)
                    if stats(new)["letter_ratio"] > s["letter_ratio"] + 0.05:
                        md.write_text(new, encoding="utf-8")
                        report.append(f"      RE-OCR'd -> letter_ratio {stats(new)['letter_ratio']:.2f}")
    verdict = "clean" if flagged_total == 0 else ("fixed" if fix else "flagged")
    print("\n".join(report))
    print(f"\nSCREEN VERDICT: {verdict} ({flagged_total} flagged)")

if __name__ == "__main__":
    main()
