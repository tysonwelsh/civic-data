#!/usr/bin/env python3
"""Closing-pass step — resolve `ordinances/index.csv` -> the enacting County Council
motion, ONLY where the motion is uniquely identifiable and survives every guard.

WHY THIS EXISTS (audit 2026-07-25 F8, repaired 2026-07-29)
---------------------------------------------------------
The linkage used to be a one-off hand pass that wrote raw `motion_id` integers into
`index.csv`.  Two things broke it:

  1. **A clerk typo was linked as `high` confidence.**  At 2021-10-12 the Action line
     under agenda item (c) "Ordinance **2021-23** ... APPROVED" reads "approve Ordinance
     **2021-22**" -- a typo.  Item (b) on the same page reads "Ordinance 2021-22 ...
     TABLED FOR NEXT MEETING".  A bare ordinance-number match therefore pointed ORD
     2021-22 at the wrong ordinance's roll call, and the register's own
     `adoption_date` (2021-12-14) already contradicted it.

  2. **Every stored motion_id went stale.**  The 2026-07-26 OCR backfill of the
     2015-2020 era inserted 1,505 motions AHEAD of the born-digital era, renumbering
     `motion_id`.  All 10 surviving links then pointed at unrelated 2015-2017 motions
     ("approve the agenda as written", "adjourn from the Council meeting at ...").
     Hand-written ids cannot survive a rebuild -- so the linkage is now DERIVED and
     re-runnable.

RUN IT AFTER EVERY `python3 db/build_db.py`.  Idempotent; writes only `motion_id`,
`match_confidence`, and the trailing " | enacting Council roll call ..." clause of
`notes`.  Every other column is preserved verbatim (cardinal rule 2).

THE GUARDS (each one is a real defect this county's minutes actually produce)
----------------------------------------------------------------------------
  G1 canonical document -- the motion's `source_file` must be listed in
     `legislative/minutes_index.csv`.  12 un-indexed duplicate markdown files sit on
     disk (byte-identical second copies, e.g. 2021-12-14_council.md vs
     ..._council_2.md) and the vote extractor walks the directory, so every motion in
     them exists twice.  Only the catalogued document counts.
  G2 ordinance context -- "Ordinance <no>", not "Resolution <no>".  Cache reuses the
     same serial numbers for ordinances and resolutions in the same year.
  G3 adoption verb -- approve/adopt/enact, and NOT "set a public hearing", "deny",
     "table", "postpone", or "amend the meeting minutes".
  G4 the motion carried -- `outcome='Pass'` and the verbatim result does not say the
     motion died/failed.  (2022-06-28's "Motion dies" for ORD 2022-19 is stored with
     `outcome='Pass'` -- an upstream extractor defect, guarded here as well.)
  G5 agenda-item heading -- walk up from the Action line to the nearest agenda item
     heading naming an Ordinance/Resolution; if it names a DIFFERENT instrument the
     motion is a clerk typo and is rejected.  The heading outranks the number inside
     the motion text.  SKIPPED for bundled motions (below), which sit under the last
     item of the bundle by construction.
  G6 date consistency -- if the register printed an `adoption_date`, the motion's
     meeting date must equal it.
  G7 year consistency -- if the register printed NO date, the ordinance's own year
     prefix must equal the meeting year.  (ORD 2021-09's only surviving candidate is a
     2021-03-09 motion re-printed inside the 2022-11-22 packet as an attachment and
     therefore mis-dated to the host meeting -- G7 rejects it, honestly unlinked.)

BUNDLES: "approve Ordinance 2022-06, 07, 08, 09 and 10" enacts five ordinances in one
roll call.  The trailing bare numbers are expanded onto the leading year prefix, so each
member links to the same motion.  This is a printed, verbatim enumeration -- not an
inference.

UNIQUENESS: exactly one surviving candidate -> `match_confidence='high'`.  Zero or many
-> `motion_id` blank, `match_confidence='unlinked'`.  `motion_resolution='unique'` in
gov.db is the only linkage this repo quotes, so an ambiguous link is never written.
"""
import csv
import os
import re
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
DB = os.path.join(HERE, "cache_county.db")
IDX = os.path.join(COUNTY, "ordinances", "index.csv")
MIN_IDX = os.path.join(COUNTY, "legislative", "minutes_index.csv")

# the linker owns only the trailing LINKAGE clause(s) of `notes` -- everything from the
# first such clause onward is regenerated.  (The 2026-07-26 hand pass used four different
# clause openers, all of them carrying now-stale motion ids; they are all recognised here.)
AUTO_CLAUSE_RE = re.compile(
    r"\s*\|\s*(enacting |LINK REMOVED|NOT LINKED|AMBIGUOUS enacting).*$", re.S | re.I)

LEGISLATIVE_BODIES = ("Council", "Workshop", "BoardOfCanvassers", "ServiceArea1")

HEADING_RE = re.compile(r"\b(Ordinance|Resolution)\s*(?:No\.?\s*)?(\d{2,4}-\d{1,2})\b", re.I)
NON_HEADING_RE = re.compile(r"^\s*(Action|Discussion|Aye|Nay|Absent|Abstain|Motion)\b", re.I)
APPROVE_RE = re.compile(r"\b(approv\w*|adopt\w*|enact\w*)\b", re.I)
NOT_ADOPTION_RE = re.compile(
    r"set (a |the )?public hearing|\bdeny\b|\bdenied\b|\btabl\w+\b|\bpostpon\w+\b"
    r"|meeting minutes|\bcontinu\w+\b", re.I)
FAILED_RE = re.compile(r"\b(dies|died|fail\w*)\b", re.I)


def bundle_members(text, year):
    """Expand 'Ordinance 2022-06, 07, 08, 09 and 10' -> {'2022-06',...,'2022-10'}."""
    out = set()
    for m in re.finditer(r"\bordinance[s]?\s*(?:no\.?|#)?\s*(\d{4})-(\d{1,2})"
                         r"((?:\s*,\s*\d{1,2})+(?:\s*(?:,\s*)?and\s+\d{1,2})?)", text, re.I):
        yr, first, tail = m.group(1), m.group(2), m.group(3)
        out.add("%s-%s" % (yr, first))
        for n in re.findall(r"\d{1,2}", tail):
            out.add("%s-%s" % (yr, n))
    return out


class Minutes(object):
    """Lazy markdown reader used only for the agenda-item heading guard."""

    def __init__(self, root):
        self.root = root
        self.cache = {}

    def norm_lines(self, rel):
        if rel not in self.cache:
            path = os.path.join(self.root, rel or "")
            if rel and os.path.exists(path):
                raw = open(path, encoding="utf-8", errors="replace").read().split("\n")
            else:
                raw = []
            self.cache[rel] = [re.sub(r"\s+", " ", ln).strip() for ln in raw]
        return self.cache[rel]

    def heading_for(self, rel, motion_text):
        """Return (instrument, number) of the agenda item the motion sits under, or None."""
        lines = self.norm_lines(rel)
        if not lines:
            return None
        key = re.sub(r"\s+", " ", motion_text or "").strip()[:45]
        if not key:
            return None
        joined = "\n".join(lines)
        pat = re.escape(key).replace(r"\ ", r"[\s\n]+")
        hit = re.search(pat, joined)
        if not hit:
            return None
        li = joined[:hit.start()].count("\n")
        for j in range(li - 1, max(-1, li - 30), -1):
            if NON_HEADING_RE.match(lines[j]):
                continue
            h = HEADING_RE.search(lines[j])
            if h:
                return (h.group(1).lower(), h.group(2))
        return None


def main():
    db = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    motions = db.execute(
        "SELECT m.motion_id, mt.meeting_date, m.motion_text, m.result_raw, m.outcome, "
        "       m.source_file "
        "FROM motion m JOIN meeting mt ON mt.meeting_id=m.meeting_id "
        "JOIN body b ON b.body_id=m.body_id "
        "WHERE b.name IN (%s)" % ",".join("?" * len(LEGISLATIVE_BODIES)),
        LEGISLATIVE_BODIES).fetchall()
    db.close()

    canonical = {r["md_path"] for r in csv.DictReader(open(MIN_IDX, encoding="utf-8"))}
    md = Minutes(COUNTY)

    rows = list(csv.DictReader(open(IDX, encoding="utf-8")))
    cols = list(rows[0].keys()) if rows else []

    linked = 0
    log = []
    for r in rows:
        ono = (r.get("ordinance_no") or "").strip()
        base_notes = AUTO_CLAUSE_RE.sub("", r.get("notes") or "")
        r["motion_id"] = ""
        r["match_confidence"] = ""
        r["notes"] = base_notes
        if not ono:
            continue

        direct = re.compile(r"\bordinance[s]?\s*(?:no\.?|#)?\s*" + re.escape(ono) + r"\b", re.I)
        year = ono.split("-")[0] if re.match(r"^\d{4}-\d{1,2}$", ono) else None

        survivors = []
        referencing = 0
        for mid, mdate, text, result_raw, outcome, src in motions:
            text = text or ""
            bundled = ono in bundle_members(text, year)
            if not (direct.search(text) or bundled):          # G2
                continue
            if src not in canonical:                          # G1
                continue
            referencing += 1
            if not APPROVE_RE.search(text) or NOT_ADOPTION_RE.search(text):   # G3
                continue
            if (outcome or "") != "Pass" or FAILED_RE.search(result_raw or ""):  # G4
                continue
            if not bundled:                                   # G5
                head = md.heading_for(src, text)
                if head and (head[0] != "ordinance" or head[1] != ono):
                    continue
            adoption = (r.get("adoption_date") or "").strip()
            if adoption:
                if mdate != adoption:                         # G6
                    continue
            elif year and (mdate or "")[:4] != year:          # G7
                continue
            survivors.append((mid, mdate, text, bundled))

        if len(survivors) == 1:
            mid, mdate, text, bundled = survivors[0]
            r["motion_id"] = str(mid)
            r["match_confidence"] = "high"
            r["notes"] = (base_notes + " | enacting Council roll call %s (motion_id %s, "
                          "unique%s; guards: number+agenda-item+date)"
                          % (mdate, mid, ", bundled roll call" if bundled else ""))
            linked += 1
            log.append("  Ord %-8s -> motion %-6s %s  %s%s"
                       % (ono, mid, mdate, text[:58].replace("\n", " "),
                          "  [BUNDLE]" if bundled else ""))
        elif len(survivors) > 1:
            r["match_confidence"] = "unlinked"
            r["notes"] = (base_notes + " | NOT LINKED: %d candidate adoption motions (%s) "
                          "- ambiguous, and only motion_resolution='unique' is quoted"
                          % (len(survivors), "; ".join(s[1] for s in survivors)))
        elif referencing:
            # the ordinance number IS spoken on the floor, but nothing survived the guards
            # (set-a-public-hearing only, a FAILED adoption motion, a clerk-typo heading
            # mismatch, or a date/year contradiction).  Honest gap, recorded not papered over.
            r["match_confidence"] = "unlinked"
            r["notes"] = (base_notes + " | NOT LINKED: %d Council motion(s) name this "
                          "ordinance but none is a verified enacting roll call (no passing "
                          "adoption motion under its own agenda item on a consistent date)"
                          % referencing)

    with open(IDX, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print("ordinances catalogued: %d | uniquely motion-linked: %d" % (len(rows), linked))
    for line in log:
        print(line)
    amb = [r["ordinance_no"] for r in rows if r["match_confidence"] == "unlinked"]
    if amb:
        print("named on the floor but NOT uniquely linkable (blank, honest): %s"
              % ", ".join(amb))


if __name__ == "__main__":
    main()
