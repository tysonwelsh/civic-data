#!/usr/bin/env python3
"""
Shared validator for Cottonwood Heights vote JSONs. Writes votes/_validation_report.txt
and (re)generates roster.csv from OBSERVED votes. Imported by each body's
validate_votes.py with its roster config.
"""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


def iter_jsons(votes_dir):
    for jp in sorted(Path(votes_dir).rglob("*.json")):
        if not jp.name.startswith("_"):
            yield jp


def run(ds_dir, roster_names, mayor_names, seat_max, seat_label):
    ds_dir = Path(ds_dir)
    votes_dir = ds_dir / "votes"
    report = votes_dir / "_validation_report.txt"

    meetings = motions = 0
    body_counts = Counter()
    type_counts = Counter()
    per_year = defaultdict(Counter)             # year -> voter -> rows
    first_seen = {}
    last_seen = {}
    mtgs_present = defaultdict(set)
    vote_rows = Counter()
    mayor_votes = []
    oversize = []
    tally_mismatch = []
    outcome_issue = []
    contested = []
    offroster = Counter()

    for jp in iter_jsons(votes_dir):
        mtg = json.load(jp.open())
        meetings += 1
        date = mtg["date"]
        year = str(mtg["year"])
        for v in mtg["votes"]:
            motions += 1
            body_counts[v["body"]] += 1
            type_counts[v["motion_type"]] += 1
            seated = []
            for key, lab in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                             ("recuse", "Recuse"), ("absent", "Absent")):
                for nm in v.get(key, []):
                    if nm not in roster_names and nm not in mayor_names:
                        offroster[nm] += 1
                    per_year[year][nm] += 1
                    vote_rows[nm] += 1
                    mtgs_present[nm].add(date)
                    first_seen[nm] = min(first_seen.get(nm, date), date)
                    last_seen[nm] = max(last_seen.get(nm, date), date)
                    if lab != "Absent":
                        seated.append((nm, lab))
            # mayor-vote flag
            for nm in mayor_names:
                if nm in v.get("aye", []) + v.get("nay", []) + v.get("abstain", []) + v.get("recuse", []):
                    mayor_votes.append((date, v["motion_no"], nm, v["result"]))
            # oversize roll
            n_seated = len(seated)
            if n_seated > seat_max:
                oversize.append((date, v["motion_no"], n_seated, v["result"]))
            # tally-vs-named mismatch
            pt = v.get("printed_tally")
            if pt and v.get("names_recorded"):
                na = len(v.get("aye", []))
                nn = len(v.get("nay", []))
                # CH prints the PREVAILING side first: "passed A-to-B" A=ayes; but
                # "failed A-to-B" A=nays (the winning no-side). Compare in that order.
                expect = [na, nn] if v["result"].lower().startswith("passed") else [nn, na]
                if expect != pt:
                    tally_mismatch.append((date, v["motion_no"], pt, [na, nn], v["result"]))
            # outcome consistency
            if v.get("names_recorded"):
                na, nn = len(v.get("aye", [])), len(v.get("nay", []))
                passed = v["result"].lower().startswith("passed")
                if passed and na <= nn and (na + nn) > 0:
                    outcome_issue.append((date, v["motion_no"], v["result"], na, nn))
                if (not passed) and na > nn:
                    outcome_issue.append((date, v["motion_no"], v["result"], na, nn))
            # contested
            if v.get("nay") or v.get("abstain") or v.get("recuse"):
                contested.append((date, v["body"], v["motion_no"], v["result"],
                                  v.get("nay"), v.get("abstain"), v.get("recuse"),
                                  v["motion"][:70]))

    named = sum(1 for _ in ())  # placeholder
    lines = []
    lines.append(f"COTTONWOOD HEIGHTS — {seat_label} vote validation")
    lines.append("=" * 64)
    lines.append(f"meetings: {meetings}   motions: {motions}")
    lines.append(f"body split: {dict(body_counts)}")
    lines.append(f"motion types: {dict(type_counts.most_common())}")
    lines.append("")
    lines.append(f"OFF-ROSTER names (should be 0): {sum(offroster.values())}  {dict(offroster)}")
    lines.append(f"OVERSIZE rolls (> {seat_max} seated): {len(oversize)}")
    for o in oversize[:40]:
        lines.append(f"   {o}")
    lines.append("")
    lines.append(f"MAYOR-vote rows (a real, counted vote here): {len(mayor_votes)}")
    lines.append(f"tally-vs-named mismatches: {len(tally_mismatch)}")
    for t in tally_mismatch[:60]:
        lines.append(f"   {t}")
    lines.append(f"outcome-vs-count issues: {len(outcome_issue)}")
    for t in outcome_issue[:40]:
        lines.append(f"   {t}")
    lines.append("")
    lines.append("PER-YEAR observed roster (voter -> rows):")
    for y in sorted(per_year):
        lines.append(f"  {y}: " + ", ".join(f"{n}({c})" for n, c in per_year[y].most_common()))
    lines.append("")
    lines.append(f"CONTESTED motions (Nay/Abstain/Recuse present): {len(contested)}")
    for c in contested:
        lines.append(f"   {c[0]} [{c[1]}] m{c[2]} {c[3]} nay={c[4]} abst={c[5]} rec={c[6]} :: {c[7]}")
    report.write_text("\n".join(lines) + "\n")
    print(f"Wrote {report}")
    print(f"  meetings={meetings} motions={motions} offroster={sum(offroster.values())} "
          f"oversize={len(oversize)} mayor_votes={len(mayor_votes)} "
          f"tally_mismatch={len(tally_mismatch)} outcome_issue={len(outcome_issue)} "
          f"contested={len(contested)}")

    # ---- roster.csv (OBSERVED) ----
    roster_path = ds_dir / "roster.csv"
    with roster_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "role", "first_seen", "last_seen", "meetings_present", "n_vote_rows"])
        for nm in sorted(vote_rows, key=lambda n: (-len(mtgs_present[n]), n)):
            role = "Mayor (voting)" if nm in mayor_names else seat_label
            w.writerow([nm, role, first_seen[nm], last_seen[nm],
                        len(mtgs_present[nm]), vote_rows[nm]])
    print(f"Wrote {roster_path} ({len(vote_rows)} observed members)")
    return {"meetings": meetings, "motions": motions, "offroster": sum(offroster.values()),
            "oversize": len(oversize), "mayor_votes": len(mayor_votes),
            "tally_mismatch": len(tally_mismatch), "outcome_issue": len(outcome_issue),
            "contested": len(contested)}
