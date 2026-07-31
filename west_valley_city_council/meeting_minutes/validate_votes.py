#!/usr/bin/env python3
"""
validate_votes.py — shared council-vote validator (REMEDIATION_PLAN.md 3.1).

ONE template, installed per city as meeting_minutes/validate_votes.py with only the
CONFIG block below changed (never fork the logic; the canonical copy lives at
scripts/validate_votes_template.py). Validates THIS dataset's all_votes.csv (long
format, SCHEMA_SPEC.md §2) plus the normalization layer's motions_std.csv:

  1. schema + dates: 13 standard columns present; every date ISO-parses, is plausible,
     and matches the year column; vote values within the SCHEMA_SPEC §4 vocabulary
     (+ documented per-city extensions).
  2. names_recorded convention: each motion is EITHER >=1 named member rows and no
     placeholder, OR exactly one tally-only placeholder row (member and vote blank).
     We never guess voters, so mixed/malformed groups are defects.
  3. no member voting twice on one motion — UNLESS the pair is a documented exception:
     a row in ../db/vote_overrides.csv (cities whose db resolves source clerk
     contradictions) or in KNOWN_DOUBLE_VOTES below (cities without that file).
  4. voter names resolvable to roster.csv when one exists in this dataset (none of the
     council datasets currently ship one — the check then degrades to an OBSERVED
     per-year voter table in the report, with very-low-frequency names surfaced for
     review, informational only).
  5. result-tally vs counted member rows, using the normalization layer's parsed
     tallies (motions_std.csv tally_aye/tally_nay — covers exotic result strings).
     Mismatches are never auto-corrected; the report separates the documented
     dissent-only-naming undercount class (crosswalks/README.md) from real mismatches.

Output: votes/_validation_report.txt (or ./_validation_report.txt if no votes/ dir)
plus a one-line stdout summary. Exit code = number of HARD failures (schema/date/vocab
defects, malformed motion groups, undocumented double votes, off-roster voters).
Tally mismatches and observed-roster oddities are reported, not failed — they flag
source typos / documented source styles for hand review.
"""
import csv
import datetime
import os
import re
import sys
from collections import Counter, defaultdict

# --------------------------------------------------------------------------- CONFIG
CITY = "West Valley City"
# Minutes name ONLY dissenters/absentees on many motions (documented source style,
# crosswalks/README.md) -> counted Ayes < stated tally by design; such undercounts are
# reported as the documented class, not as mismatches.
DISSENT_ONLY_NAMING = False
# Documented vote-value extensions beyond Aye|Nay|Abstain|Recuse|Absent|Excused (§4).
VOTE_VALUE_EXTENSIONS = set()
# Documented same-member-twice pairs for cities WITHOUT a db/vote_overrides.csv that
# covers them: {(source_basename, motion_no, member): "reasoning"}.
KNOWN_DOUBLE_VOTES = {}
# Failed motions print the tally PREVAILING-SIDE-FIRST ("The motion failed 6:1 with
# [6 names] opposed, [1] in favor") -- accept the swapped orientation on fail outcomes
# (abstains may be folded into the prevailing side).
FAIL_TALLY_PREVAILING_FIRST = False
# Hand-verified tally mismatches (source clerk contradictions / logged extraction gaps):
# {(date, motion_no): "reasoning"} -- annotated and counted as KNOWN, not unexplained.
KNOWN_TALLY_MISMATCHES = {}
# Free-text, hand-verified notes appended to the report (known source typos etc.).
KNOWN_NOTES = []
# ---------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
ALL_VOTES = os.path.join(HERE, "all_votes.csv")
MOTIONS_STD = os.path.join(HERE, "motions_std.csv")
ROSTER = os.path.join(HERE, "roster.csv")
VOTE_OVERRIDES = os.path.join(os.path.dirname(HERE), "db", "vote_overrides.csv")
VOTES_DIR = os.path.join(HERE, "votes")
REPORT = os.path.join(VOTES_DIR if os.path.isdir(VOTES_DIR) else HERE,
                      "_validation_report.txt")

STD_COLS = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source"]
VOCAB = {"Aye", "Nay", "Abstain", "Recuse", "Absent", "Excused"} | set(
    VOTE_VALUE_EXTENSIONS)
DATE_MIN = datetime.date(2000, 1, 1)
DATE_MAX = datetime.date.today() + datetime.timedelta(days=60)


def main():
    if not os.path.exists(ALL_VOTES):
        print(f"{CITY}: no all_votes.csv — nothing to validate"); return 1
    with open(ALL_VOTES, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        header = rdr.fieldnames or []
        rows = list(rdr)

    hard = []          # hard failures (exit code)
    report = []
    w = report.append

    # ---- 1. schema + dates + vocabulary ------------------------------------
    missing_cols = [c for c in STD_COLS if c not in header]
    if missing_cols:
        hard.append(f"missing standard columns: {missing_cols}")
    bad_dates, bad_years, bad_vocab = [], [], []
    for i, r in enumerate(rows, 2):
        d = (r.get("date") or "").strip()
        try:
            dt = datetime.date.fromisoformat(d)
            if not (DATE_MIN <= dt <= DATE_MAX):
                bad_dates.append(f"line {i}: implausible date {d}")
            elif (r.get("year") or "").strip() != d[:4]:
                bad_years.append(f"line {i}: year={r.get('year')} vs date {d}")
        except ValueError:
            bad_dates.append(f"line {i}: unparseable date {d!r}")
        v = (r.get("vote") or "").strip()
        m = (r.get("member") or "").strip()
        if m and v not in VOCAB:
            bad_vocab.append(f"line {i}: vote={v!r} member={m!r}")
        if not m and v:
            bad_vocab.append(f"line {i}: vote={v!r} with blank member")
    hard += bad_dates + bad_years + bad_vocab

    # ---- group rows per motion ----------------------------------------------
    motions = defaultdict(list)            # (source, motion_no, date) -> rows
    for r in rows:
        motions[(r.get("source", ""), r.get("motion_no", ""), r.get("date", ""))].append(r)

    # ---- 2. names_recorded convention ---------------------------------------
    malformed = []
    n_named_motions = n_tallyonly = 0
    for key, grp in motions.items():
        named = [r for r in grp if (r.get("member") or "").strip()]
        blanks = [r for r in grp if not (r.get("member") or "").strip()]
        if named and not blanks:
            n_named_motions += 1
        elif not named and len(blanks) == 1:
            n_tallyonly += 1
        else:
            malformed.append(
                f"{key[2]} m{key[1]}: {len(named)} named + {len(blanks)} placeholder "
                f"rows :: {os.path.basename(key[0])}")
    hard += [f"malformed motion group: {m}" for m in malformed]

    # ---- 3. double votes (documented exceptions honored) --------------------
    overrides = set()
    if os.path.exists(VOTE_OVERRIDES):
        with open(VOTE_OVERRIDES, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                overrides.add((os.path.basename(r["source_file"]),
                               r["motion_no"].strip(), r["member"].strip()))
    doubles_documented, doubles_undocumented = [], []
    override_motions = set()               # motions whose contradiction is documented
    for key, grp in motions.items():
        counts = Counter((r["member"], ) for r in grp if (r.get("member") or "").strip())
        for (m, ), c in counts.items():
            if c <= 1:
                continue
            vals = "+".join(sorted(r["vote"] for r in grp if r["member"] == m))
            base = os.path.basename(key[0])
            line = f"{key[2]} m{key[1]} {m} x{c} ({vals}) :: {base}"
            if (base, key[1], m) in overrides:
                doubles_documented.append(line + "  [db/vote_overrides.csv]")
                override_motions.add(key)
            elif (base, key[1], m) in KNOWN_DOUBLE_VOTES:
                doubles_documented.append(
                    line + f"  [KNOWN: {KNOWN_DOUBLE_VOTES[(base, key[1], m)]}]")
                override_motions.add(key)
            else:
                doubles_undocumented.append(line)
    hard += [f"undocumented double vote: {d}" for d in doubles_undocumented]

    # ---- 4. roster resolvability --------------------------------------------
    roster_names = None
    off_roster = []
    if os.path.exists(ROSTER):
        with open(ROSTER, newline="", encoding="utf-8") as f:
            rr = list(csv.DictReader(f))
        name_col = next((c for c in ("member", "commissioner", "name") if rr and c in rr[0]),
                        None)
        if name_col:
            roster_names = {r[name_col].strip() for r in rr}
            seen = {r["member"].strip() for r in rows if (r.get("member") or "").strip()}
            off_roster = sorted(seen - roster_names)
            hard += [f"voter not on roster.csv: {n}" for n in off_roster]
    per_year = defaultdict(Counter)
    for r in rows:
        m = (r.get("member") or "").strip()
        if m:
            per_year[(r.get("date") or "????")[:4]][m] += 1
    total_by_name = Counter()
    for yr in per_year:
        total_by_name.update(per_year[yr])
    rare = [(n, c) for n, c in total_by_name.items() if c <= 2]

    # ---- 5. tally vs counted member rows (motions_std parsed tallies) -------
    tally_checked = tally_ok = 0
    undercounts, known_mm, contradiction_mm, mismatches = [], [], [], []
    if os.path.exists(MOTIONS_STD):
        std = {}
        with open(MOTIONS_STD, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                std[(r["source"], r["motion_no"], r["date"])] = r
        for key, grp in motions.items():
            named = [r for r in grp if (r.get("member") or "").strip()]
            if not named:
                continue
            s = std.get(key)
            if not s or not (s.get("tally_aye") or "").strip():
                continue
            try:
                t_aye = int(s["tally_aye"])
                t_nay = int(s["tally_nay"]) if (s.get("tally_nay") or "").strip() else 0
            except ValueError:
                continue
            n_aye = sum(1 for r in named if r["vote"] == "Aye")
            n_nay = sum(1 for r in named if r["vote"].startswith("Nay"))
            n_abst = sum(1 for r in named if r["vote"] == "Abstain")
            tally_checked += 1
            ok = (n_aye == t_aye and n_nay == t_nay) or \
                 (n_aye == t_aye and n_nay + n_abst == t_nay)
            if not ok and FAIL_TALLY_PREVAILING_FIRST and \
                    s.get("outcome") in ("fail", "died"):
                # failed motions state the tally prevailing-side-first
                ok = (n_aye == t_nay) and (n_nay == t_aye or n_nay + n_abst == t_aye)
            if ok:
                tally_ok += 1
            else:
                line = (f"{key[2]} m{key[1]}: stated {t_aye}:{t_nay} vs counted "
                        f"aye={n_aye} nay={n_nay} abstain={n_abst} :: "
                        f"result={s.get('result_raw', '')!r}")
                if key in override_motions:
                    contradiction_mm.append(
                        line + "  [explained by the documented source contradiction "
                               "for this motion]")
                elif (key[2], key[1]) in KNOWN_TALLY_MISMATCHES:
                    known_mm.append(
                        line + f"  [KNOWN: {KNOWN_TALLY_MISMATCHES[(key[2], key[1])]}]")
                elif DISSENT_ONLY_NAMING and n_aye < t_aye and n_nay <= t_nay:
                    undercounts.append(line)
                else:
                    mismatches.append(line)

    # ---- report --------------------------------------------------------------
    w(f"{CITY} — council vote validation report (shared validator, plan item 3.1)")
    w("=" * 76)
    w(f"rows: {len(rows)}   motions: {len(motions)}   "
      f"named-vote motions: {n_named_motions}   tally-only motions: {n_tallyonly}")
    w("")
    w(f"1. SCHEMA/DATES/VOCAB defects: "
      f"{len(missing_cols) + len(bad_dates) + len(bad_years) + len(bad_vocab)}")
    for ln in (bad_dates + bad_years + bad_vocab)[:50]:
        w("   " + ln)
    w("")
    w(f"2. MALFORMED MOTION GROUPS (mixed named+placeholder / multi-placeholder): "
      f"{len(malformed)}")
    for ln in malformed[:50]:
        w("   " + ln)
    w("")
    w(f"3. DOUBLE VOTES — documented exceptions: {len(doubles_documented)}, "
      f"undocumented (DEFECTS): {len(doubles_undocumented)}")
    for ln in doubles_documented:
        w("   OK  " + ln)
    for ln in doubles_undocumented:
        w("   BAD " + ln)
    w("")
    if roster_names is not None:
        w(f"4. ROSTER: roster.csv present ({len(roster_names)} names); "
          f"off-roster voters: {len(off_roster)}")
        for n in off_roster:
            w("   " + n)
    else:
        w("4. ROSTER: no roster.csv in this dataset — observed per-year voter table "
          "below (informational); names with <=2 total rows surfaced for review:")
        for n, c in sorted(rare):
            w(f"   rare voter ({c} row{'s' if c > 1 else ''}): {n}")
        for yr in sorted(per_year):
            names = ", ".join(f"{n}({c})" for n, c in per_year[yr].most_common())
            w(f"   {yr}: {names}")
    w("")
    w(f"5. TALLY vs COUNTED MEMBER ROWS (parsed tallies from motions_std.csv): "
      f"{tally_ok}/{tally_checked} match"
      + (f" ({100.0 * tally_ok / tally_checked:.1f}%)" if tally_checked else ""))
    if DISSENT_ONLY_NAMING:
        w(f"   documented dissent-only-naming undercounts (source style, not defects): "
          f"{len(undercounts)}")
        for ln in undercounts[:40]:
            w("      " + ln)
    if contradiction_mm:
        w(f"   explained by documented source contradictions: {len(contradiction_mm)}")
        for ln in contradiction_mm:
            w("      " + ln)
    if known_mm:
        w(f"   known, hand-verified source quirks: {len(known_mm)}")
        for ln in known_mm:
            w("      " + ln)
    w(f"   UNEXPLAINED mismatches (hand-review; never auto-corrected): "
      f"{len(mismatches)}")
    for ln in mismatches[:60]:
        w("      " + ln)
    if KNOWN_NOTES:
        w("")
        w("KNOWN, HAND-VERIFIED QUIRKS:")
        for n in KNOWN_NOTES:
            w("   - " + n)
    w("")
    w(f"HARD FAILURES: {len(hard)}")
    for h in hard[:80]:
        w("   " + h)

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")

    print(f"{CITY}: rows={len(rows)} motions={len(motions)} "
          f"(named {n_named_motions} / tally-only {n_tallyonly}) | "
          f"schema-defects={len(missing_cols) + len(bad_dates) + len(bad_years) + len(bad_vocab)} "
          f"malformed-groups={len(malformed)} "
          f"doubles: {len(doubles_documented)} documented / "
          f"{len(doubles_undocumented)} undocumented | "
          f"tally {tally_ok}/{tally_checked}"
          + (f" (+{len(undercounts)} documented dissent-only undercounts)"
             if DISSENT_ONLY_NAMING else "")
          + (f", {len(contradiction_mm)} explained-by-documented-contradiction"
             if contradiction_mm else "")
          + (f", {len(known_mm)} known-quirk" if known_mm else "")
          + f", unexplained mismatches {len(mismatches)} | HARD FAILURES {len(hard)}")
    print(f"report: {os.path.relpath(REPORT, HERE)}")
    return len(hard)


if __name__ == "__main__":
    sys.exit(main())
