#!/usr/bin/env python3
"""
validate_votes.py — sanity-check the extracted Holladay vote JSONs + all_votes.csv, and
(re)write roster.csv (OBSERVED). Writes votes/_validation_report.txt. Body-agnostic:
Council max roll = 6 (5 district members + the VOTING Mayor); PC roll = 6 (5 members +
Chair). Never mutates the minutes; corrections belong in override files.

Checks:
  1. Totals: meetings, motions, named vs tally-only, per-body counts, motion-type mix.
  2. all_votes.csv row count reconciles with the JSON vote rows.
  3. Per-year observed roster (member -> recorded votes).
  4. Mayor-vote rows (the Mayor is a real voter here) — count + sample.
  5. >MAX-VOTER flags (parse error signal: a named roll exceeding 6). Should be empty.
  6. Named-roll-size deviations (!=5 and !=6) — vacancy/absence/parse-miss, informational.
  7. Full contested list (any No/Nay/Abstain/Recuse) — the analytical signal.

Run:  python3 validate_votes.py
"""
import csv, json, os, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(ROOT, "votes")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")
ROSTER = os.path.join(ROOT, "roster.csv")
BODY = "PlanningCommission" if os.path.basename(ROOT) == "planning_commission" else "Council"
# Council roll tops out at 6 (5 district members + the VOTING Mayor). Holladay PC seats
# a 7-member commission (Chair + up to 6 commissioners); a recusal still prints 7 names.
MAX_ROLL = 7 if BODY == "PlanningCommission" else 6
EXPECTED_SIZES = {5, 6, 7} if BODY == "PlanningCommission" else {5, 6}
DISSENT = {"No", "Nay", "Abstain", "Recuse"}


def iter_jsons():
    for dp, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dp, fn)


def main():
    meetings = motions = named = tally_only = 0
    body_counts = Counter(); type_counts = Counter()
    per_year = defaultdict(Counter)
    member_span = {}  # member -> [first_date, last_date, n_vote_rows, is_mayor_ever, roles]
    mayor_rows = []; over_max = []; size_dev = []; contested = []
    json_vote_rows = 0

    for jp in iter_jsons():
        mtg = json.load(open(jp, encoding="utf-8"))
        meetings += 1
        date = mtg["date"]; year = date[:4]
        for mo in mtg["motions"]:
            motions += 1
            body_counts[mo["body"]] += 1
            type_counts[mo["motion_type"]] += 1
            vs = mo["votes"]
            if mo["names_recorded"]:
                named += 1
            else:
                tally_only += 1
            n = len(vs)
            json_vote_rows += max(n, 1)  # tally-only motions still emit 1 blank row
            if n > MAX_ROLL:
                over_max.append(f"{date} [{mo['body']}] m{mo['motion_no']} "
                                f"{n} voters :: {mo['motion'][:70]}")
            if mo["names_recorded"] and n not in EXPECTED_SIZES:
                size_dev.append(f"{date} [{mo['body']}] m{mo['motion_no']} roll={n} "
                                f"{[ (v['member'],v['vote']) for v in vs]} :: {mo['motion'][:55]}")
            if any(v["vote"] in DISSENT for v in vs):
                contested.append(f"{date} [{mo['body']}] m{mo['motion_no']} | {mo['result'][:45]} | "
                                 + " ".join(f"{v['member']}={v['vote']}" for v in vs)
                                 + f" :: {mo['motion'][:60]}")
            for v in vs:
                per_year[year][v["member"]] += 1
                ms = member_span.setdefault(v["member"], [date, date, 0, False])
                ms[0] = min(ms[0], date); ms[1] = max(ms[1], date)
                ms[2] += 1
                if v.get("is_mayor"):
                    ms[3] = True
                    mayor_rows.append(f"{date} {v['member']}={v['vote']} m{mo['motion_no']}")

    # reconcile with all_votes.csv
    csv_rows = list(csv.DictReader(open(ALL_VOTES))) if os.path.exists(ALL_VOTES) else []
    csv_ok = len(csv_rows) == json_vote_rows

    # write roster.csv (OBSERVED)
    with open(ROSTER, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["member", "role", "first_seen", "last_seen", "n_vote_rows", "mayor_rows_seen"])
        for m, (fs, ls, nn, mayor) in sorted(member_span.items()):
            role = "Mayor (voting) / Council Member" if (BODY == "Council" and mayor) else \
                   ("Council Member" if BODY == "Council" else "Commissioner/Chair")
            w.writerow([m, role, fs, ls, nn, "yes" if mayor else ""])

    passed = csv_ok and not over_max
    lines = []
    lines.append(f"HOLLADAY {BODY} — VOTE VALIDATION REPORT")
    lines.append("=" * 64)
    lines.append(f"Meetings (json):        {meetings}")
    lines.append(f"Motions:                {motions}  (named {named}, tally-only/consent {tally_only})")
    lines.append(f"JSON vote rows:         {json_vote_rows}")
    lines.append(f"all_votes.csv rows:     {len(csv_rows)}   reconcile: {'OK' if csv_ok else 'MISMATCH'}")
    lines.append(f"Per-body motions:       {dict(body_counts)}")
    lines.append(f"Motion types:           {dict(type_counts.most_common())}")
    lines.append(f"Mayor vote rows:        {len(mayor_rows)}")
    lines.append(f">{MAX_ROLL}-voter parse flags: {len(over_max)}")
    lines.append(f"Named-roll size !=5/6:  {len(size_dev)} (informational)")
    lines.append(f"Contested motions:      {len(contested)}")
    lines.append("")
    lines.append(f"RESULT: {'PASS' if passed else 'FAIL'}")
    lines.append("")
    lines.append("-- Observed roster (member: first..last, rows) --")
    for m, (fs, ls, nn, mayor) in sorted(member_span.items(), key=lambda x: -x[1][2]):
        lines.append(f"   {m:14s} {fs}..{ls}  rows={nn}{'  [MAYOR]' if mayor else ''}")
    lines.append("")
    lines.append("-- Per-year observed voters --")
    for y in sorted(per_year):
        lines.append(f"   {y}: " + ", ".join(f"{k}({v})" for k, v in per_year[y].most_common()))
    lines.append("")
    if over_max:
        lines.append("-- >MAX-VOTER FLAGS (investigate) --")
        lines.extend("   " + x for x in over_max)
        lines.append("")
    lines.append(f"-- Contested motions ({len(contested)}) --")
    lines.extend("   " + x for x in contested)
    lines.append("")
    lines.append(f"-- Named-roll size deviations ({len(size_dev)}) — first 40 --")
    lines.extend("   " + x for x in size_dev[:40])
    lines.append("")
    lines.append(f"-- Mayor vote rows (sample 20 of {len(mayor_rows)}) --")
    lines.extend("   " + x for x in mayor_rows[:20])

    os.makedirs(VOTES_DIR, exist_ok=True)
    open(REPORT, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines[:16]))
    print(f"... full report -> {REPORT}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
