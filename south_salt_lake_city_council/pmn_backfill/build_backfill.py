#!/usr/bin/env python3
"""Build the South Salt Lake pmn_backfill dataset from the AgendaCenter independent-source sweep.

Source of the recovery: NOT PMN. The core build harvested recorded minutes from Utah Public
Notice (PMN bodies 1295/1296/1297) and logged the 2021-mid..2025 cliff as agenda-only. The
CITY's own CivicPlus AgendaCenter, however, exposes genuine recorded roll-call minutes through
its hidden 'ArchivedMinutes' slot (reached via each doc's PreviousVersions page) and, for many
2022-23 Planning-Commission dates, directly in the visible 'Minutes' slot. work/ssl_agendacenter_sweep.py
enumerated + content-detected every candidate; this script consolidates the genuine-minutes hits,
classifies body + meeting_kind, dedups to one file per (date,body,meeting_kind), keeps only the
rows the core MISSED (net-new vs meeting_minutes/ + planning_commission/ indexes), copies the raw
PDF into raw/<year>/, writes a trimmed text sidecar into text/, and emits index.csv (SCHEMA_SPEC
§9 pmn_backfill contract + recovery_source).
"""
import csv, json, os, re, shutil, subprocess, datetime
from pathlib import Path
from collections import defaultdict

DS = Path(__file__).resolve().parent
REPO = DS.parent
WORK = DS / "work"
TMP = WORK / "ac_tmp"
TODAY = "2026-07-13"
BODY = {"4": "Council", "3": "PlanningCommission", "5": "RDA"}
BSLUG = {"Council": "council", "PlanningCommission": "pc", "RDA": "rda"}
MIN = {"vote_grammar", "minutes_title", "header+motion"}

def load_core():
    core = set()
    for idx in [REPO/"meeting_minutes"/"minutes_index.csv", REPO/"planning_commission"/"minutes_index.csv"]:
        for r in csv.DictReader(open(idx)):
            core.add((r["date"], r["body"], r["meeting_kind"]))
    return core

def read_txt(d):
    stem = f"{d['date']}_{BODY[d['cat']]}_{d['slot']}{d['view_id']}"
    p = TMP / f"{stem}.txt"
    return p.read_text() if p.exists() else ""

def classify(d, txt):
    head = txt[:1800]
    body = BODY[d["cat"]]
    # content can override body (a council-listing doc that is actually the RDA convened)
    if re.search(r"REDEVELOPMENT AGENCY", head, re.I) and body == "Council":
        body = "RDA"
    if body == "PlanningCommission":
        kind = "WM" if re.search(r"WORK\s+MEETING|WORK\s+SESSION|STUDY MEETING", head, re.I) else "PC"
    else:
        if re.search(r"CANVASS|BOARD OF CANVASS", head, re.I): kind = "BoC"
        elif re.search(r"WORK\s+MEETING|WORK\s+SESSION|STUDY MEETING", head, re.I): kind = "WM"
        elif re.search(r"SPECIAL\s+(?:CITY\s+)?(?:COUNCIL\s+)?MEETING", head, re.I): kind = "SM"
        else: kind = "RC"
    return body, kind

def named_votes(txt):
    return len(re.findall(r"Commissioner\s+\w+\s*[–\-]\s*(?:Aye|Nay|Yes|No)", txt))

def minutes_start(text):
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if re.match(r"\s*CITY OF SOUTH SALT LAKE\s*$", ln, re.I):
            window = "\n".join(lines[i:i+25])
            if re.search(r"MEETING", window, re.I): return i
    for i, ln in enumerate(lines):
        if re.match(r"\s*MINUTES OF (?:THE )?MEETING", ln, re.I): return max(0, i)
        if re.match(r"\s*PRESIDING", ln, re.I): return max(0, i-4)
    return 0

def main():
    hits = [d for d in json.load(open(WORK/"ac_results_dedup.json")) if d["result"] in MIN]
    core = load_core()
    # group by (date, body, kind)
    groups = defaultdict(list)
    for d in hits:
        txt = read_txt(d)
        if len(txt) < 400: continue
        body, kind = classify(d, txt)
        d = dict(d); d["_body"], d["_kind"], d["_txt_len"] = body, kind, len(txt)
        d["_rc"], d["_named"] = d.get("rc_blocks", 0), named_votes(txt)
        groups[(d["date"], body, kind)].append(d)

    kept = []
    for (date, body, kind), cands in sorted(groups.items()):
        # best file: max recorded-vote content, then prefer ArchivedMinutes (pure minutes), then larger text
        cands.sort(key=lambda x: (x["_rc"] + x["_named"], x["slot"] == "ArchivedMinutes", x["_txt_len"]), reverse=True)
        best = cands[0]
        net_new = (date, body, kind) not in core
        best["_net_new"] = net_new
        best["_dupe_of_core"] = not net_new
        if net_new:
            kept.append((date, body, kind, best))

    # write raw + text + index (net-new only)
    raw_dir = DS / "raw"; txt_dir = DS / "text"
    raw_dir.mkdir(exist_ok=True); txt_dir.mkdir(exist_ok=True)
    rows = []
    for date, body, kind, d in sorted(kept):
        year = date[:4]
        slug = f"{date}_{BSLUG[body]}_{kind}"
        stem = f"{d['date']}_{BODY[d['cat']]}_{d['slot']}{d['view_id']}"
        src_pdf = TMP / f"{stem}.pdf"
        (raw_dir / year).mkdir(exist_ok=True)
        rel_pdf = f"raw/{year}/{slug}_{d['view_id'].strip('_')}.pdf"
        shutil.copyfile(src_pdf, DS / rel_pdf)
        # trimmed text sidecar
        full = (TMP / f"{stem}.txt").read_text()
        trimmed = "\n".join(full.split("\n")[minutes_start(full):]).strip()
        (txt_dir / f"{slug}.txt").write_text(trimmed, encoding="utf-8")
        title = f"{body} {kind} Meeting {date}"
        source_url = f"https://sslc.gov/AgendaCenter/ViewFile/{d['slot']}/{d['view_id']}"
        rec_src = "agendacenter_archivedminutes" if d["slot"] == "ArchivedMinutes" else "agendacenter_minutes"
        rows.append(dict(date=date, year=year, title=title, slug=slug, body=body, path=rel_pdf,
                         source="agendacenter", source_url=source_url, notice_url="",
                         pmn_body_id="", pmn_file_id="", retrieved_date=TODAY,
                         format="text", extraction_method="pdftotext -layout", recovery_source=rec_src))
    cols = ["date","year","title","slug","body","path","source","source_url","notice_url",
            "pmn_body_id","pmn_file_id","retrieved_date","format","extraction_method","recovery_source"]
    with open(DS/"index.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    # summary
    from collections import Counter
    print("net-new recovered rows:", len(rows))
    print("by body:", dict(Counter(r["body"] for r in rows)))
    print("by year:", dict(Counter(r["year"] for r in rows)))
    print("by recovery_source:", dict(Counter(r["recovery_source"] for r in rows)))

if __name__ == "__main__":
    main()
