#!/usr/bin/env python3
"""Select the genuinely-missing council/PC-scope minutes from the PMN sweep and emit
_work/recover_manifest.csv (the fetch + index driver for Cottonwood Heights pmn_backfill).

Recover set = minutes-like PMN docs, 2020+, whose meeting date has NO repo doc within +/-4d:
  - body 2148 (Planning Commission), class pc                -> body=PlanningCommission
  - body 3287 (Administrative Hearings), class admin         -> body=PlanningCommission (slug=administrative-hearing)
Council (2147) has 0 genuine gaps (verified). ARC/BOA/AHO are separate bodies NOT in the
repo -> inventory only, never recovered here."""
import csv, re, os
from datetime import date, timedelta

HERE = os.path.dirname(__file__)
REPO = os.path.abspath(os.path.join(HERE, ".."))
import importlib.util
spec = importlib.util.spec_from_file_location("d", os.path.join(HERE, "chpmn_diff.py"))
D = importlib.util.module_from_spec(spec); spec.loader.exec_module(D)

def load(rel):
    ds = set()
    for r in csv.DictReader(open(os.path.join(REPO, rel))): ds.add(r["date"])
    return ds
PC = load("planning_commission/minutes_index.csv")

MONTHS = {}

def main():
    rows = [r for r in csv.DictReader(open(os.path.join(HERE, "_work/attachments_all.csv")))
            if r["minutes_like"] == "True"]
    for r in rows:
        r["cls"] = D.classify(r["filename"])
        r["mdate"] = D.parse_date(r["filename"]) or (
            r["event_date"] if re.match(r"\d{4}-\d{2}-\d{2}", r["event_date"]) else None)
    recover = []
    for r in rows:
        d = r["mdate"]
        if not d or d < "2020-01-01":
            continue
        # PC proper (body 2148, class pc) missing from repo PC
        if r["body"] == "2148" and r["cls"] == "pc" and D.within(d, PC) is None:
            r["slug"] = "planning-commission"; r["outbody"] = "PlanningCommission"
            recover.append(r)
        # Administrative hearings (body 3287, class admin) missing from repo PC
        elif r["body"] == "3287" and r["cls"] == "admin" and D.within(d, PC) is None:
            r["slug"] = "administrative-hearing"; r["outbody"] = "PlanningCommission"
            recover.append(r)
    recover.sort(key=lambda r: (r["mdate"], r["file_id"]))
    out = os.path.join(HERE, "_work/recover_manifest.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["mdate", "outbody", "slug", "body", "body_name",
                                          "notice_id", "file_id", "filename", "cls"])
        w.writeheader()
        for r in recover:
            w.writerow({k: r[k] for k in w.fieldnames})
    print(f"recover set: {len(recover)}")
    for r in recover:
        print(f"  {r['mdate']}  {r['slug']:<22} [{r['body_name']} #{r['file_id']}] {r['filename']}")
    print("wrote", out)

if __name__ == "__main__":
    main()
