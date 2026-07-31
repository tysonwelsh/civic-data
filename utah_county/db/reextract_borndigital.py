#!/usr/bin/env python3
"""Re-extract the BORN-DIGITAL legislative minutes with poppler instead of pypdf.

WHY (2026-07-25 audit, _audits/2026-07-25/report.md F3(i)):
pypdf inserts stray mid-word spaces on this county's PDFs — "carried with the f ollowing
vote", "the mot ion was seconde d by". That corruption broke `extract_votes.py`'s literal
anchor, so whole meetings collapsed: 2016-08-30 holds 26 `AYE:` roll-call blocks but the
markdown carried only 5 usable anchors and the db recorded 5 motions. Measured across a
random sample of the 228 born-digital files, poppler's `pdftotext -layout` drops the
split-word rate from ~13 per 1,000 tokens to ~0 — better on 10 of 10.

WHAT IT DOES
Rewrites ONLY the body of each born-digital minutes markdown from its retained raw PDF,
preserving the provenance front-matter verbatim except `extraction:`, which is restamped
so the change is self-documenting. Scanned/OCR files are never touched. Idempotent.

The raw PDFs are canonical and untouched; the markdown is a derived text layer, so this is
re-derivation, not a hand-edit (SCHEMA_SPEC cardinal rule 3).

Usage:  python3 db/reextract_borndigital.py [--dry-run]
"""
import csv, glob, os, re, subprocess, sys

ROOT = "/Users/tysonwelsh/civic-data/utah_county"
IDX = os.path.join(ROOT, "legislative", "minutes_index.csv")
DRY = "--dry-run" in sys.argv

def raws_for(date, front):
    """All raw parts for a meeting, IN THE ORIGINAL PART ORDER.

    30 meetings are multi-part (n_parts 2..7). The fetcher joined their texts with
    '----PART BREAK----' and recorded the source URLs, in order, in the front-matter's
    `source_url: a | b | c`. Ordering by that list reproduces the original sequence;
    falling back to sorted filenames would silently reorder a meeting's parts.
    """
    hits = glob.glob(os.path.join(ROOT, "legislative", "raw", f"{date}_*.pdf"))
    m = re.search(r"^source_url:\s*(.+)$", front, re.M)
    if m:
        order, used = [], set()
        for u in [x.strip() for x in m.group(1).split("|")]:
            base = os.path.basename(u)
            for h in hits:
                if h not in used and h.endswith("_" + base):
                    order.append(h); used.add(h); break
        order += [h for h in sorted(hits) if h not in used]   # any unmatched, deterministic
        if order:
            return order
    return sorted(hits)

def split_front(text):
    m = re.match(r"---\n(.*?\n)---\n", text, re.S)
    return (m.group(1), text[m.end():]) if m else (None, text)

def main():
    rows = list(csv.DictReader(open(IDX)))
    done = skipped = nochange = norawx = 0
    for r in rows:
        if not (r.get("md_path") or "").strip():
            continue                           # unrecovered rows carry no markdown
        p = r["md_path"] if os.path.isabs(r["md_path"]) else os.path.join(ROOT, r["md_path"])
        if not os.path.isfile(p):
            continue
        text = open(p, encoding="utf-8", errors="replace").read()
        front, body = split_front(text)
        if not front or "pypdf" not in front:
            skipped += 1                       # OCR/scanned — leave alone
            continue
        parts = raws_for(r["date"], front)
        if not parts:
            norawx += 1
            continue
        texts = [subprocess.run(["pdftotext", "-layout", p, "-"],
                                capture_output=True, text=True).stdout for p in parts]
        out = "\n\n----PART BREAK----\n\n".join(texts)   # the fetcher's own join
        if len(out.strip()) < 200:             # refuse to replace good text with nothing
            norawx += 1
            continue
        # never silently shrink a document: poppler should match or beat pypdf's coverage
        if len(out.strip()) < 0.5 * len(body.strip()):
            print(f"  SKIP {r['date']}: poppler text {len(out.strip())} < half of existing "
                  f"{len(body.strip())} — left as-is for inspection")
            norawx += 1
            continue
        newfront = front.replace("extraction: pypdf text (born-digital)",
                                 "extraction: poppler pdftotext -layout (born-digital; "
                                 "re-extracted 2026-07-25, was pypdf — see db/reextract_borndigital.py)")
        new = "---\n" + newfront + "---\n\n" + out.lstrip("\n")
        if new == text:
            nochange += 1
            continue
        if not DRY:
            open(p, "w", encoding="utf-8").write(new)
        done += 1
    print(f"born-digital re-extracted: {done}  (unchanged {nochange}, "
          f"skipped-OCR {skipped}, no-usable-raw {norawx}){' [DRY RUN]' if DRY else ''}")

if __name__ == "__main__":
    main()
