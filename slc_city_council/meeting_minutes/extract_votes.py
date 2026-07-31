#!/usr/bin/env python3
"""
Analyze each meeting-minutes file and produce a supplemental votes document.

For every recorded vote in a meeting, Claude extracts the motion, a plain-English
description, a motion type, the result, mover/seconder, and exactly how each council
member voted (aye / nay / abstain / absent). Output sits beside each minutes file:

    minutes/<year>/<week>/<date>_<slug>.votes.json   structured per-meeting vote data
    all_votes.csv                                    combined long format, one row per
                                                     member-vote (rebuilt from the .votes.json;
                                                     the analysis file)

Runs over the PrimeGov Markdown minutes (clean, structured roll calls). The 2020
Laserfiche OCR (.txt) is skipped by default -- its vote formatting is messier;
pass --include-ocr to attempt it too.

Uses the Anthropic Batch API (cost-effective). The key auto-loads from .env via
config.py. Resumable: meetings whose .json already exists are skipped.

Usage:
    python3 extract_votes.py            # process all not-yet-done minutes
    python3 extract_votes.py --force    # reprocess everything
    python3 extract_votes.py --include-ocr
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import anthropic

from config import BASE_DIR, MINUTES_DIR, MODEL, MAX_TOKENS

ALL_CSV = BASE_DIR / "all_votes.csv"
CHUNK = 100   # meetings per batch

SYSTEM = """You extract EVERY recorded vote from Salt Lake City Council (and CRA/RDA/LBA board) meeting minutes.

A recorded vote is a motion that has a result -- typically an "AYE:/NAY:" roll call and a "Final Result". For each one, produce an object:
- motion: the action voted on, concise but faithful (what was moved/adopted).
- description: 1-2 plain-English sentences on what it does / its context.
- motion_type: ONE of [Resolution, Ordinance, Ceremonial Resolution, Budget Amendment, Appointment/Advice & Consent, Public Hearing Action, Interlocal/Agreement, Grant/Funding, Contract/Property, Procedural/Administrative, Legislative Intent, Other].
- mover, seconder: council member names (or "" if not stated).
- result: e.g. "6-1 Pass", "Unanimous Pass", "Fail".
- aye, nay, abstain, absent: arrays of council member names for each (use [] if none).

Only include motions with an actual recorded result. Preserve member names exactly.
Respond with ONLY valid JSON: {"votes":[ ... ]} -- no markdown fences, no commentary. If there are no recorded votes, return {"votes":[]}."""


def vote_json_path(src_file):
    """Vote data sits beside its minutes file: <date>_<slug>.votes.json."""
    return src_file.with_name(src_file.stem + ".votes.json")


def discover(force, include_ocr):
    exts = ["*.md"] + (["*.txt"] if include_ocr else [])
    files = sorted(f for ext in exts for f in MINUTES_DIR.rglob(ext))
    todo = [f for f in files if force or not vote_json_path(f).exists()]
    return files, todo


def parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # re-escape unescaped interior quotes (same failure mode as the comments pipeline)
        fixed = _fix_quotes(text)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            return None


def _fix_quotes(s):
    out, i, n, in_str = [], 0, len(s), False
    while i < n:
        c = s[i]
        if not in_str:
            out.append(c); in_str = c == '"'
        elif c == "\\" and i + 1 < n:
            out.append(c); out.append(s[i + 1]); i += 2; continue
        elif c == '"':
            j = i + 1
            while j < n and s[j] in " \t\r\n": j += 1
            if j >= n or s[j] in ",:}]":
                out.append('"'); in_str = False
            else:
                out.append('\\"')
        else:
            out.append(c)
        i += 1
    return "".join(out)


def meeting_meta(md_file):
    rel = md_file.relative_to(BASE_DIR)
    stem = md_file.stem
    return {"date": stem[:10], "slug": stem[11:],
            "title": stem[11:].replace("-", " ").title(),
            "year": md_file.parts[-3], "source": str(rel)}


def write_outputs(src_file, votes):
    meta = meeting_meta(src_file)
    vote_json_path(src_file).write_text(
        json.dumps({"meta": meta, "votes": votes}, indent=2), encoding="utf-8")


def _body_deriver():
    """
    body column (standard 13-col schema; retrofit 2026-07-02): each motion's body
    (Council/RDA/CRA/LBA — SLC's council adjourns/reconvenes in-session as the
    agencies) is recovered by walking the source markdown's section headers — the
    same derivation the db build uses, imported from ../db/build_db.py so there is
    exactly one implementation.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_slc_build_db", BASE_DIR.parent / "db" / "build_db.py")
    bdb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bdb)
    short = {"Council": "Council", "Redevelopment Agency": "RDA",
             "Community Reinvestment Agency": "CRA", "Local Building Authority": "LBA"}
    def derive(rows_one_source):
        bm = bdb._derive_bodies(rows_one_source, str(BASE_DIR))
        return {mno: short[b] for mno, b in bm.items()}
    return derive


def _provenance_map():
    """
    provenance trailing column (repo standard, 2026-07-17): 'minutes' = audited
    portal-scraped primary (PrimeGov/Laserfiche); 'pmn_minutes' = Utah Public Notice
    recoveries (the 4 minutes promoted 2026-07-17). Derived from minutes_index.csv's
    `source` column, never guessed.
    """
    m = {}
    idx = BASE_DIR / "minutes_index.csv"
    if idx.exists():
        for r in csv.DictReader(open(idx, encoding="utf-8")):
            m[r["path"]] = "pmn_minutes" if r.get("source") == "pmn" else "minutes"
    return m


def rebuild_csv():
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source", "provenance"]
    derive_bodies = _body_deriver()
    prov = _provenance_map()
    rows = []
    for jf in sorted(MINUTES_DIR.rglob("*.votes.json")):
        d = json.loads(jf.read_text(encoding="utf-8"))
        meta = d["meta"]
        frows = []
        for i, v in enumerate(d["votes"], 1):
            base = {"date": meta["date"], "year": meta["year"], "title": meta["title"],
                    "motion_no": i, "motion": v.get("motion", ""),
                    "motion_type": v.get("motion_type", ""), "result": v.get("result", ""),
                    "mover": v.get("mover", ""), "seconder": v.get("seconder", ""),
                    "source": meta["source"],
                    "provenance": prov.get(meta["source"], "minutes")}
            for vote, members in (("Aye", v.get("aye", [])), ("Nay", v.get("nay", [])),
                                  ("Abstain", v.get("abstain", [])), ("Absent", v.get("absent", []))):
                for m in members:
                    frows.append({**base, "member": m, "vote": vote})
        if frows:
            bm = derive_bodies(frows)
            for r in frows:
                r["body"] = bm[r["motion_no"]]
        rows.extend(frows)
    rows.sort(key=lambda r: (r["date"], r["motion_no"], r["member"]))
    with open(ALL_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader(); w.writerows(rows)
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description="Extract per-meeting vote tables from minutes")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--include-ocr", action="store_true", help="also process 2020 .txt (messier)")
    args = ap.parse_args()

    files, todo = discover(args.force, args.include_ocr)
    print(f"{len(files)} minutes files, {len(todo)} to analyze "
          f"({len(files)-len(todo)} already done).")
    if not todo:
        print("Nothing to do."); rebuild_csv(); return

    client = anthropic.Anthropic()
    done = failed = 0
    for start in range(0, len(todo), CHUNK):
        chunk = todo[start:start + CHUNK]
        reqs = [{"custom_id": str(start + i),
                 "params": {"model": MODEL, "max_tokens": MAX_TOKENS, "system": SYSTEM,
                            "messages": [{"role": "user",
                              "content": "Extract all recorded votes from these minutes:\n\n"
                                         + f.read_text(encoding="utf-8")}]}}
                for i, f in enumerate(chunk)]
        idx = {str(start + i): f for i, f in enumerate(chunk)}
        print(f"\nBatch {start//CHUNK+1}: submitting {len(reqs)} meetings...")
        batch = client.messages.batches.create(requests=reqs)
        while True:
            b = client.messages.batches.retrieve(batch.id)
            c = b.request_counts
            print(f"  {c.succeeded+c.errored}/{len(reqs)} done", end="\r")
            if b.processing_status == "ended":
                break
            time.sleep(30)
        print()
        for res in client.messages.batches.results(batch.id):
            f = idx[res.custom_id]
            if res.result.type != "succeeded":
                print(f"  ERROR {f.name}: {res.result.type}"); failed += 1; continue
            data = parse_json(res.result.message.content[0].text)
            if data is None:
                print(f"  PARSE FAIL {f.name}"); failed += 1; continue
            write_outputs(f, data.get("votes", []))
            done += 1

    total = rebuild_csv()
    print(f"\nDone. Analyzed {done}, failed {failed}.")
    print(f"Per-meeting *.votes.json beside each minutes file ; "
          f"combined {ALL_CSV.name} has {total} member-vote rows.")


if __name__ == "__main__":
    main()
