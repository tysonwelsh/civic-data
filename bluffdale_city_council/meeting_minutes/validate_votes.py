#!/usr/bin/env python3
"""Bluffdale vote validator + OBSERVED roster builder (no network, no mutation of votes).

Dropped in BOTH meeting_minutes/ and planning_commission/; auto-detects the dataset.
Writes votes/_validation_report.txt and roster.csv (observed from the extracted votes).

Checks: motion/row/named/tally-only counts; body split; contested list; off-roster names
(must be 0 — the parser is roster-gated); printed-tally-vs-counted mismatches (surfaces OCR
digit slips, faithfully, never patched); max MEMBER (non-mayor) tally per body (Council/RDA/
LBA and PC must be <= 5 council-members; the Mayor votes only in RDA/LBA + rare Council
tie-breaks and is listed separately); per-year roster.
"""
import csv, glob, json
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATASET = "pc" if ROOT.name == "planning_commission" else "council"
VOTES_DIR = ROOT / "votes"
REPORT = VOTES_DIR / "_validation_report.txt"
ROSTER = ROOT / "roster.csv"
MAYORS = {"Natalie Hall", "Derk Timothy"}


def load():
    out = []
    for jp in sorted(VOTES_DIR.rglob("*.json")):
        out.append(json.loads(jp.read_text()))
    return out


def main():
    meetings = load()
    L = []
    p = L.append
    n_meet = len(meetings)
    n_motion = named = tally_only = contested = mayor_voted = 0
    rows = 0
    bodies = Counter()
    max_member_tally = Counter()
    off_roster = Counter()
    mismatches = []
    contested_list = []
    mayor_events = []
    # observed roster: name -> [role, first_date, last_date, n_motions, bodies]
    roster = {}

    known = set()
    # gather the canonical full names from the extractor's roster module
    import importlib.util
    spec = importlib.util.spec_from_file_location("ev", ROOT / "extract_votes.py")
    ev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ev)
    for full, _ in ev.ROSTER.values():
        known.add(full)

    for d in meetings:
        date = d["date"]
        for v in d["votes"]:
            n_motion += 1
            bodies[v["body"]] += 1
            if v["names_recorded"]:
                named += 1
            else:
                tally_only += 1
            if v["nay"] or v["abstain"] or v["recuse"]:
                contested += 1
                contested_list.append((date, v["body"], v["result"],
                                       ",".join(v["nay"]), v["motion_no"]))
            if v.get("mayor_voted"):
                mayor_voted += 1
                mayor_events.append((date, v["body"], v["result"], v["motion_no"]))
            members = [(x, k) for k in ("aye", "nay", "abstain", "absent", "recuse")
                       for x in v[k]]
            rows += max(1, len(members))
            non_mayor = [x for x, _ in members if x not in MAYORS]
            max_member_tally[v["body"]] = max(max_member_tally[v["body"]], len(non_mayor))
            for name, _ in members:
                if name not in known:
                    off_roster[name] += 1
                r = roster.get(name)
                role = "Mayor" if name in MAYORS else ("Commissioner" if DATASET == "pc"
                                                       else "Council Member")
                if r is None:
                    roster[name] = [role, date, date, 1, {v["body"]}]
                else:
                    r[1] = min(r[1], date)
                    r[2] = max(r[2], date)
                    r[3] += 1
                    r[4].add(v["body"])
            # printed-tally vs counted (named motions only). Bluffdale prints the PREVAILING
            # side first: on a PASS the ayes lead, on a FAIL the nays lead; a trailing
            # "with one abstention" is the second number. So compare (winning, other-named).
            if v["names_recorded"] and v.get("printed_tally"):
                a, b = v["printed_tally"]
                total = len(v["aye"]) + len(v["nay"]) + len(v["abstain"]) + len(v["recuse"])
                win = len(v["aye"]) if v["result"].lower().find("fail") < 0 else len(v["nay"])
                other = total - win
                if (a, b) != (win, other):
                    mismatches.append((date, v["body"], v["motion_no"],
                                       f"printed {a}-{b} vs counted {win}-{other}", v["result"]))

    p(f"BLUFFDALE {'PLANNING COMMISSION' if DATASET=='pc' else 'CITY COUNCIL'} — vote validation")
    p("=" * 70)
    p(f"meetings                 {n_meet}")
    p(f"motions                  {n_motion}")
    p(f"member-vote/placeholder  {rows}")
    p(f"named motions            {named}")
    p(f"tally-only (unnamed)     {tally_only}")
    p(f"contested (nay/abst/rec) {contested}")
    p(f"body split               {dict(bodies)}")
    p(f"max MEMBER tally / body  {dict(max_member_tally)}  (Council members = 5 max)")
    p(f"mayor votes (Council)    {mayor_voted}  (genuine faithful mayor votes: tie-break / recorded)")
    p(f"off-roster names         {sum(off_roster.values())}  {dict(off_roster) if off_roster else ''}")
    p(f"printed-vs-counted mism. {len(mismatches)}")
    p("")

    # ceiling check
    ceil_ok = all(x <= 5 for x in max_member_tally.values())
    p(f"CEILING CHECK (<=5 members/tally): {'PASS' if ceil_ok else 'FAIL'}")
    p(f"OFF-ROSTER CHECK (must be 0):      {'PASS' if not off_roster else 'FAIL'}")
    p("")

    p("MAYOR VOTES (Council body — non-voting mayor, so these are genuine events):")
    for e in mayor_events:
        p(f"  {e[0]}  {e[1]}  motion {e[3]}  {e[2]}")
    p("")

    p(f"PRINTED-TALLY vs COUNTED mismatches ({len(mismatches)}) — faithful, NOT patched:")
    for m in mismatches[:60]:
        p(f"  {m[0]}  {m[1]}  motion {m[2]}  {m[3]}  [{m[4]}]")
    p("")

    p(f"CONTESTED MOTIONS ({len(contested_list)}):")
    for c in contested_list:
        p(f"  {c[0]}  {c[1]}  motion {c[4]}  {c[2]}  nay=[{c[3]}]")
    p("")

    # per-year roster
    yr = defaultdict(set)
    for d in meetings:
        y = d["date"][:4]
        for v in d["votes"]:
            for k in ("aye", "nay", "abstain", "absent", "recuse"):
                for x in v[k]:
                    yr[y].add(x)
    p("PER-YEAR OBSERVED VOTERS:")
    for y in sorted(yr):
        p(f"  {y}: {', '.join(sorted(yr[y]))}")

    REPORT.write_text("\n".join(L) + "\n")
    print("\n".join(L[:16]))
    print(f"...\nwrote {REPORT}")

    # roster.csv (observed)
    with ROSTER.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "role", "bodies", "first_date", "last_date", "n_motions"])
        for name in sorted(roster, key=lambda n: (-roster[n][3])):
            role, first, last, cnt, bset = roster[name]
            w.writerow([name, role, "|".join(sorted(bset)), first, last, cnt])
    print(f"wrote {ROSTER} ({len(roster)} observed voters)")


if __name__ == "__main__":
    main()
