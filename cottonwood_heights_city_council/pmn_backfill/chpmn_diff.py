#!/usr/bin/env python3
"""Classify every PMN minutes-like attachment by FILENAME (catches cross-filed docs),
parse its meeting date, and diff against the repo's audited council + PC indexes.

Mapping to repo datasets:
  council      -> meeting_minutes/minutes_index.csv  (City Council + in-session CDRA)
  pc / admin   -> planning_commission/minutes_index.csv (PC + admin-hearing-officer rows)
  arc/boa/aho  -> NOT in the repo (separate quasi-judicial/land-use bodies) -> inventory only
Filename date is authoritative; event_date is the fallback when the filename lacks one."""
import csv, re, os
from datetime import date, timedelta
from collections import defaultdict

HERE = os.path.dirname(__file__)
REPO = os.path.abspath(os.path.join(HERE, ".."))

def load(rel):
    ds, fmt = set(), {}
    for r in csv.DictReader(open(os.path.join(REPO, rel))):
        ds.add(r["date"]); fmt.setdefault(r["date"], set()).add(r["format"])
    return ds, fmt

COUNCIL, COUNCIL_FMT = load("meeting_minutes/minutes_index.csv")
PC, PC_FMT = load("planning_commission/minutes_index.csv")

def classify(fn):
    f = fn.lower()
    if re.search(r'\barc\b|architectural', f): return "arc"
    if re.search(r'\bboa\b|board of adjustment', f): return "boa"
    if re.search(r'\baho\b|appeal', f): return "aho"
    if re.search(r'\badm\b|admin', f): return "admin"
    if re.search(r'chpc|ch pc|\bpc\b|planning comm', f): return "pc"
    if re.search(r'chcc|ch cc|city council|\bccm\b|council meeting|\bcc\b', f): return "council"
    return "other"

def parse_date(fn):
    f = fn
    # 1) YYYY_MM_DD or YYYY-MM-DD
    m = re.search(r'\b(20\d{2})[_\-](\d{1,2})[_\-](\d{1,2})\b', f)
    if m:
        y, mo, dd = m.groups()
        if 1 <= int(mo) <= 12 and 1 <= int(dd) <= 31: return f"{y}-{int(mo):02d}-{int(dd):02d}"
    # 2) MM-DD-YYYY / M-D-YYYY (dash or dot, 4-digit year)
    m = re.search(r'\b(\d{1,2})[-.](\d{1,2})[-.](20\d{2})\b', f)
    if m:
        mo, dd, y = m.groups()
        if 1 <= int(mo) <= 12 and 1 <= int(dd) <= 31: return f"{y}-{int(mo):02d}-{int(dd):02d}"
    # 3) MM-DD-YY / M-D-YY / MM.DD.YY (dash or dot, 2-digit year)
    m = re.search(r'\b(\d{1,2})[-.](\d{1,2})[-.](\d{2})\b', f)
    if m:
        mo, dd, y = m.groups()
        if 1 <= int(mo) <= 12 and 1 <= int(dd) <= 31: return f"20{y}-{int(mo):02d}-{int(dd):02d}"
    # 4) MMDDYYYY (8 consecutive digits)
    m = re.search(r'(?<!\d)(\d{2})(\d{2})(20\d{2})(?!\d)', f)
    if m:
        mo, dd, y = m.groups()
        if 1 <= int(mo) <= 12 and 1 <= int(dd) <= 31: return f"{y}-{mo}-{dd}"
    # 5) MMDDYY (exactly 6 consecutive digits) — CH's dominant style
    m = re.search(r'(?<!\d)(\d{2})(\d{2})(\d{2})(?!\d)', f)
    if m:
        mo, dd, y = m.groups()
        if 1 <= int(mo) <= 12 and 1 <= int(dd) <= 31: return f"20{y}-{mo}-{dd}"
    return None

def within(d, dateset, tol=4):
    try: dd = date.fromisoformat(d)
    except Exception: return None
    for delta in range(0, tol + 1):
        for s in (dd + timedelta(days=delta), dd - timedelta(days=delta)):
            if s.isoformat() in dateset: return s.isoformat()
    return None

def main():
    rows = [r for r in csv.DictReader(open(os.path.join(HERE, "_work/attachments_all.csv")))
            if r["minutes_like"] == "True"]
    for r in rows:
        r["cls"] = classify(r["filename"])
        r["mdate"] = parse_date(r["filename"]) or (
            r["event_date"] if re.match(r"\d{4}-\d{2}-\d{2}", r["event_date"]) else None)

    nodate = [r for r in rows if not r["mdate"]]
    print(f"minutes-like attachments: {len(rows)}   no parseable date: {len(nodate)}")
    for r in nodate:
        print("   NODATE", r["body_name"], "|", r["filename"], "| event", r["event_date"])

    # cross-tab body x class
    print("\n== body x class (minutes-like) ==")
    ct = defaultdict(lambda: defaultdict(int))
    for r in rows: ct[r["body_name"]][r["cls"]] += 1
    classes = ["council", "pc", "admin", "arc", "boa", "aho", "other"]
    print(f"{'body':<38}" + "".join(f"{c:>8}" for c in classes))
    for b in sorted(ct):
        print(f"{b:<38}" + "".join(f"{ct[b][c]:>8}" for c in classes))

    def collect(clset):
        m = defaultdict(list)
        for r in rows:
            if r["cls"] in clset and r["mdate"]: m[r["mdate"]].append(r)
        return m

    def report(name, pmn_map, repo_dates, repo_fmt, floor="2020"):
        print(f"\n########## {name} ##########")
        print(f"repo dates: {len(repo_dates)}   PMN distinct meeting-dates: {len(pmn_map)}")
        missing = []
        for d in sorted(pmn_map):
            hit = within(d, repo_dates)
            files = pmn_map[d]
            fnames = sorted(set((f['body_name'], f['file_id'], f['filename']) for f in files))
            if hit is None and d >= f"{floor}-01-01":
                missing.append((d, fnames))
        print(f"-- GENUINELY MISSING (no repo doc +/-4d, {floor}+): {len(missing)} --")
        for d, fnames in missing:
            print(f"   {d}")
            for bn, fid, fn in fnames:
                print(f"        [{bn} #{fid}] {fn}")
        return missing

    cm = report("COUNCIL SESSION (2147, class=council)", collect({"council"}), COUNCIL, COUNCIL_FMT)
    pm = report("PLANNING COMMISSION (2148+3287, class=pc/admin)", collect({"pc", "admin"}), PC, PC_FMT)

    # inventory of separate bodies (not in repo)
    print("\n########## SEPARATE-BODY INVENTORY (not in repo) ##########")
    for cl in ("arc", "boa", "aho"):
        cm2 = collect({cl})
        yrs = defaultdict(int)
        for d in cm2: yrs[d[:4]] += 1
        print(f"  {cl}: {len(cm2)} distinct minutes dates; by year: {dict(sorted(yrs.items()))}")

if __name__ == "__main__":
    main()
