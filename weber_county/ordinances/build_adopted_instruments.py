#!/usr/bin/env python3
"""Build the Weber County adopted-instruments register — the adopted-ordinance /
resolution table the county itself never published — from the motion-anchored instrument
references (../db/staging/motion_refs.csv) joined to the enacting motions in
../db/weber_county.db.

Weber prints numbered instruments (Resolution NN-YYYY, Ordinance YYYY-N) inline with the
motion that acts on them, and names every commissioner's roll-call vote, so each adopted
instrument can be tied to the EXACT enacting motion + its named roll call, every row citing
its minutes. DERIVED + idempotent — regenerate after db/build_db.py; never hand-edit the
outputs.

Two outputs:
  adopted_instruments.csv  the FULL working register — one row per distinct instrument
                           (ordinances + resolutions), with the adopting motion, its
                           outcome, named-roll availability, reading stage, and any prior
                           readings.
  index.csv                the ORDINANCE-class subset in the schema the repo-root
                           federation loader (scripts/build_search_layer.py
                           load_ordinances, non-city path) consumes: a DIRECT county-db
                           motion_id (the loader applies the fed_index offset) so Weber's
                           ordinances federate into cities.db `ordinance` WITH vote linkage.
                           Resolutions stay register-only.

Selecting the adopting motion: an instrument may appear across several motions (readings).
The adopting motion is the one maximizing (passed, reading-stage rank, date, motion_no);
earlier appearances are listed in prior_readings. The link is marked 'unique' only when
that winner is not tied with another motion on the SAME date at the SAME (pass, stage) —
otherwise 'ambiguous' and the federated motion_id is left BLANK (never force an ambiguous
join). Rates are printed.
"""
import csv, os, re, sqlite3, collections

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
DB = os.path.join(COUNTY, "db", "weber_county.db")
REFS = os.path.join(COUNTY, "db", "staging", "motion_refs.csv")
MIDX = os.path.join(COUNTY, "legislative", "minutes_index.csv")

STAGE_RANK = {"final reading": 4, "third reading": 4, "second reading": 2,
              "first reading": 1, "": 0}

# A motion that only adjourns / recesses / reconvenes / convenes a session can never be
# the motion that ENACTS an instrument. Weber's section headers print the number in caps
# ("7.H.4-... - ORDINANCE 2019-13"), so a header-anchored reference lands on whichever
# motion follows the header — routinely the "moved to adjourn the public meeting and
# reconvene the public hearing" motion. Left in the candidate pool, that procedural row
# either WINS the tie-break (highest motion_no on the day) or manufactures a spurious
# tie that blanks an otherwise-unique link. Excluding it (found 2026-07-29) re-points
# ordinance 2019-13 to nothing (its adopting motion was never extracted — an honest gap)
# and recovers 50 ordinances whose own adopting motion cites their number verbatim.
PROCEDURAL_RE = re.compile(
    r"moved to (?:adjourn|recess|reconvene|convene|go into|enter)\b", re.I)


def clean(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def stage_rank(stage):
    return STAGE_RANK.get(clean(stage).lower(), 0)


def main():
    db = sqlite3.connect(DB)
    # (meeting_date, motion_no) -> motion facts. motion_no is unique within a meeting.
    mrows = {}
    for r in db.execute(
            "SELECT mt.meeting_date, m.motion_no, m.motion_id, m.outcome, m.stage, "
            "m.names_recorded, m.result_raw, m.source_file, m.motion_text "
            "FROM motion m JOIN meeting mt ON mt.meeting_id = m.meeting_id"):
        mrows[(r[0], str(r[1]))] = {
            "date": r[0], "motion_no": str(r[1]), "motion_id": r[2],
            "outcome": r[3] or "", "stage": clean(r[4]), "names_recorded": int(r[5] or 0),
            "result_raw": r[6] or "", "source_file": r[7] or "",
            "motion_text": clean(r[8])}

    # source_url per meeting date (from the minutes index) — the citation for each row
    src_url = {}
    with open(MIDX, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            src_url[r["meeting_date"]] = r.get("source_url", "")

    # group instrument references by (ref_type, ref_number)
    groups = collections.defaultdict(list)
    with open(REFS, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            groups[(r["ref_type"], r["ref_number"])].append(r)

    register = []
    for (rtype, rnum), rlist in groups.items():
        # distinct enacting motions that reference this instrument
        cands, procedural = {}, {}
        for r in rlist:
            key = (r["meeting_date"], r["motion_no"])
            mo = mrows.get(key)
            if not mo:
                continue
            (procedural if PROCEDURAL_RE.search(mo["motion_text"]) else cands)[key] = mo
        if not cands:
            if not procedural:
                continue  # (does not occur — all refs join — kept for safety)
            # EVERY reference to this instrument landed on a procedural motion: the
            # number was read off a section header and its real adopting motion is not
            # in the vote layer. The instrument is real, so keep the row (dated + cited
            # from the meeting the header sits in) but leave it honestly UNLINKED —
            # never point it at the adjourn/recess motion.
            anchor = sorted(procedural.values(), key=lambda m: (m["date"], int(m["motion_no"])))[0]
            register.append({
                "instrument_type": rtype, "instrument_number": rnum,
                "adoption_date": anchor["date"], "adopting_motion_no": "",
                "motion_id": "", "outcome": "", "names_recorded": "",
                "reading_stage": "", "n_readings": 0, "prior_readings": "",
                "match_confidence": "unlinked", "motion_resolution": "unlinked",
                "title": "", "source_file": anchor["source_file"],
                "source_url": src_url.get(anchor["date"], ""),
            })
            continue
        ordered = sorted(
            cands.values(),
            key=lambda m: (1 if m["outcome"] == "Pass" else 0, stage_rank(m["stage"]),
                           m["date"], int(m["motion_no"])),
            reverse=True)
        adopting = ordered[0]
        # unique unless another candidate ties the winner on (pass, stage, date)
        top = (1 if adopting["outcome"] == "Pass" else 0, stage_rank(adopting["stage"]),
               adopting["date"])
        ties = sum(1 for m in cands.values()
                   if (1 if m["outcome"] == "Pass" else 0, stage_rank(m["stage"]),
                       m["date"]) == top)
        resolution = "unique" if ties == 1 else "ambiguous"
        priors = [m for m in ordered[1:]]
        prior_str = "; ".join(
            "%s#%s%s" % (m["date"], m["motion_no"],
                         "(%s)" % m["stage"] if m["stage"] else "")
            for m in priors)
        register.append({
            "instrument_type": rtype,
            "instrument_number": rnum,
            "adoption_date": adopting["date"],
            "adopting_motion_no": adopting["motion_no"],
            "motion_id": adopting["motion_id"] if resolution == "unique" else "",
            "outcome": adopting["outcome"],
            "names_recorded": adopting["names_recorded"],
            "reading_stage": adopting["stage"],
            "n_readings": len(cands),
            "prior_readings": prior_str,
            "match_confidence": "high" if resolution == "unique" else "ambiguous",
            "motion_resolution": resolution,
            "title": adopting["motion_text"][:300],
            "source_file": adopting["source_file"],
            "source_url": src_url.get(adopting["date"], ""),
        })

    # sort: type then number (year-major where the number is year-first)
    def numkey(row):
        n = row["instrument_number"]
        m = re.findall(r"\d+", n)
        return (row["instrument_type"], [int(x) for x in m], n)
    register.sort(key=numkey)

    reg_cols = ["instrument_type", "instrument_number", "adoption_date",
                "adopting_motion_no", "motion_id", "outcome", "names_recorded",
                "reading_stage", "n_readings", "prior_readings", "match_confidence",
                "motion_resolution", "title", "source_file", "source_url"]
    with open(os.path.join(HERE, "adopted_instruments.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=reg_cols)
        w.writeheader()
        w.writerows(register)

    # index.csv — ordinance-class subset, in the federation loader's schema (direct
    # county-db motion_id; blank where the enacting motion is not unique).
    idx_cols = ["ordinance_no", "adoption_date", "title", "land_use_type", "result",
                "source_url", "format", "path", "text_path", "motion_id",
                "match_confidence", "reading_stage", "prior_readings", "source_file"]
    ords = [r for r in register if r["instrument_type"] == "ordinance"]
    with open(os.path.join(HERE, "index.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=idx_cols)
        w.writeheader()
        for r in ords:
            w.writerow({
                "ordinance_no": r["instrument_number"],
                "adoption_date": r["adoption_date"],
                "title": r["title"],
                "land_use_type": "",
                "result": "adopted" if r["outcome"] == "Pass" else r["outcome"],
                "source_url": r["source_url"],
                "format": "pdf",
                "path": "",           # no per-ordinance PDF — the minutes are the source
                "text_path": "",
                "motion_id": r["motion_id"],
                "match_confidence": r["match_confidence"],
                "reading_stage": r["reading_stage"],
                "prior_readings": r["prior_readings"],
                "source_file": r["source_file"],
            })

    n_ord = len(ords)
    n_res = sum(1 for r in register if r["instrument_type"] == "resolution")
    ord_linked = sum(1 for r in ords if r["motion_id"] != "")
    reg_linked = sum(1 for r in register if r["motion_id"] != "")
    print("adopted_instruments.csv: %d rows (%d ordinance / %d resolution)"
          % (len(register), n_ord, n_res))
    print("  register unique-link rate: %d/%d (%.1f%%)"
          % (reg_linked, len(register), 100 * reg_linked / len(register)))
    print("index.csv (ordinances): %d rows, unique motion_id link: %d/%d (%.1f%%), "
          "ambiguous (blank): %d"
          % (n_ord, ord_linked, n_ord, 100 * ord_linked / max(1, n_ord),
             n_ord - ord_linked))
    print("  named-roll available on adopting motion: %d/%d ordinances"
          % (sum(1 for r in ords if r["names_recorded"]), n_ord))


if __name__ == "__main__":
    main()
