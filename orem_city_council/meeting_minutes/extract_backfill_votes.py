#!/usr/bin/env python3
"""
extract_backfill_votes.py — integrate recovered standalone Orem RDA / MBA minutes
from ../pmn_backfill/ into meeting_minutes/all_votes.csv.

WHY
    Orem never publishes separate RDA/MBA meeting files — the audited extractor
    tags those bodies only via in-council "adjourn to a meeting of X" markers, so
    the structured RDA/MBA record is tiny (RDA 15, MBA 1). Utah Public Notice holds
    standalone RDA/MBA minutes; the parseable (born-digital, chars>0) ones are
    reused here. Because these are STANDALONE files (no in-file body marker), the
    parser defaults them to Council, so we FORCE the body from the pmn index.

SCOPE (deliberately bounded)
    - Only recovered docs with real extracted text (chars>0). The 2026-07-19 OCR pass
      (tesseract 300 DPI) recovered the previously image-only RDA/MBA scans, so those
      now parse here too. Parsing uses ev.extract_file(..., lenient=True): a scoped OCR/
      phrasing tolerance (bare "<Body> Minutes - date" footers injected mid name-list;
      "The vote was unanimous, motion passed"; "The motion <noise> passed") applied ONLY
      to this standalone-file path — the default audited council pipeline is unchanged.
    - Board of Adjustment (BoA) recovered minutes are NOT included: BoA is a body
      the schema/crosswalks don't yet model (OWNER-GATED — needs body plumbing).

PROVENANCE  minutes (audited) | pmn_minutes (recovered, this script)

RUN (after extract_votes.py):
    python3 meeting_minutes/extract_votes.py
    python3 meeting_minutes/extract_backfill_votes.py
Idempotent.
"""
import os
import csv
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PMN = os.path.join(REPO, "pmn_backfill")
ALL_VOTES = os.path.join(HERE, "all_votes.csv")
REPORT = os.path.join(HERE, "votes", "_backfill_extract_report.txt")

sys.path.insert(0, HERE)
import extract_votes as ev

CANON_PROVENANCE = "minutes"
BACKFILL_PROVENANCE = "pmn_minutes"
BODIES = {"rda": "RDA", "mba": "MBA"}            # BoA deferred (new body)
COLS = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
        "result", "mover", "seconder", "member", "vote", "source", "provenance"]


def main():
    if not os.path.exists(ALL_VOTES):
        sys.exit("run extract_votes.py first")
    canon_rows, structured = [], {}
    with open(ALL_VOTES, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("provenance", "") == BACKFILL_PROVENANCE:
                continue
            canon_rows.append(r)
            structured.setdefault(r["body"], set()).add(r["date"])

    recovered = []
    with open(os.path.join(PMN, "index.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            b = BODIES.get(r["body"])
            if not b:
                continue
            if int(r.get("chars") or 0) <= 0:            # image-only scan, unparseable
                continue
            if r["date"] in structured.get(b, set()):    # already council-embedded
                continue
            recovered.append((b, r))

    back_rows = []
    parsed = motions = 0
    for b, r in sorted(recovered, key=lambda x: (x[1]["date"], x[0])):
        tp = r.get("text_path", "")
        path = os.path.join(PMN, tp) if tp else ""
        if not path or not os.path.exists(path):
            g = glob.glob(os.path.join(PMN, "text", f"{r['body']}_{r['date']}_*.txt"))
            if not g:
                continue
            path = g[0]
        rel_source = f"pmn_backfill/{os.path.relpath(path, PMN)}"
        title = f"Orem {'Redevelopment Agency' if b == 'RDA' else 'Municipal Building Authority'}"
        res = ev.extract_file(path, {"date": r["date"], "title": title, "path": rel_source},
                              lenient=True)
        if not res["votes"]:
            continue
        parsed += 1
        for v in res["votes"]:
            motions += 1
            base = {
                "date": r["date"], "year": r["date"][:4], "title": title,
                "body": b,                                # FORCE body (standalone file)
                "motion_no": v["motion_no"], "motion": v["motion"],
                "motion_type": v["motion_type"], "result": v["result"],
                "mover": v["mover"], "seconder": v["seconder"],
                "source": rel_source, "provenance": BACKFILL_PROVENANCE,
            }
            for key, vote in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                              ("absent", "Absent"), ("recuse", "Recuse")):
                for member in v[key]:
                    back_rows.append(dict(base, member=member, vote=vote))

    out = []
    for r in canon_rows:
        r = dict(r)
        if not r.get("provenance"):
            r["provenance"] = CANON_PROVENANCE
        out.append(r)
    out += back_rows
    out.sort(key=lambda r: (r["date"], r["body"], int(r["motion_no"]), r.get("member", "")))
    with open(ALL_VOTES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in out:
            w.writerow({c: r.get(c, "") for c in COLS})

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("Orem RDA/MBA backfill (pmn_backfill -> meeting_minutes/all_votes.csv)\n")
        f.write(f"recovered meetings parsed : {parsed}\n")
        f.write(f"recovered motions         : {motions}\n")
        f.write(f"recovered member rows     : {len(back_rows)}\n")
        f.write(f"canonical rows            : {len(canon_rows)}\n")
        f.write(f"merged total rows         : {len(out)}\n")
        f.write("DEFERRED: chars=0 image scans (need OCR) + BoA (new body).\n")

    print(f"merged all_votes.csv: {len(canon_rows)} canonical + {len(back_rows)} recovered "
          f"(pmn_minutes) rows; {parsed} RDA/MBA meetings / {motions} motions")


if __name__ == "__main__":
    main()
