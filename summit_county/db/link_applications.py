#!/usr/bin/env python3
"""Closing-pass step 3 — load the development pipeline into summit_county.db and resolve
PC-motion links WHERE UNIQUE (never forced).

Reads development/applications.csv (built by development/build_applications.py from the same
land_use minutes) and the already-built summit_county.db (Council + PC). For every
application it inserts an `application` row (app_key, body_id). For the rows that carry an
OUTCOME it tries to bind the application to the exact enacting PC motion, restricted to the
SAME (body, meeting date) and scored on shared parcel/project/location/title tokens + the
dev-type keyword (the same signal development/build_applications.py used). A link is written
ONLY when a single motion is the unique top scorer at/above threshold — ties and no-match
stay blank (cardinal rule: honest gaps are data, never force a link).

Side effects (all idempotent, rerun after every build_db.py):
  - db: application table populated; motion.application_id / app_match_method / app_confidence
    set on the uniquely-linked PC motions.
  - development/applications.csv: rewritten with a trailing `motion_id` column (the per-county
    summit_county.db motion_id, which the repo-root federation loader offsets) and
    names_recorded normalized to 1/0 (federation-readable); all native columns preserved.

DERIVED — never hand-edit applications.csv or the db by hand.
"""
import csv, os, re, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
DB = os.path.join(HERE, "summit_county.db")
APP = os.path.join(COUNTY, "development", "applications.csv")

ACTION = re.compile(r"approv|den|recommend|continue|table|forward|adopt|reject|postpone", re.I)
# distinctive project NAME phrase — Summit PC motions identify a matter by its project name
# ("Coleman Acres Final Subdivision Plat") while the agenda item is keyed by parcel #, so the
# project name is the reliable join key. 1–4 Capitalized words in front of a land-use noun.
PNOUN = (r"(?:Subdivision|Final Plat|Plat Amendment|Preliminary Plat|Conditional Use Permit|"
         r"PUD|Planned Development|Ranch|Acres|Estates|Annexation|Rezone|Amendment)")
PHRASE = re.compile(r"((?:[A-Z][A-Za-z'\.]+ ){1,4})" + PNOUN)
PHRASE_STOP = {"based upon", "findings of fact", "the "}
TYPEWORDS = {"conditional_use_permit": "conditional use", "plat_amendment": "plat amendment",
             "subdivision": "subdivision", "rezone": "rezone",
             "master_planned_development": "master planned",
             "specially_planned_area": "specially planned", "low_impact_permit": "low impact",
             "general_plan_amendment": "general plan", "code_amendment": "code",
             "annexation": "annexation"}


def main():
    rows = list(csv.DictReader(open(APP, encoding="utf-8")))
    db = sqlite3.connect(DB)

    body_id = {name: bid for bid, name in db.execute("SELECT body_id, name FROM body")}
    # PC motions indexed by (body_id, date) → [(motion_id, motion_text)]
    from collections import defaultdict
    cand = defaultdict(list)
    for mid, bid, txt, mdate in db.execute(
            "SELECT m.motion_id, m.body_id, m.motion_text, mt.meeting_date "
            "FROM motion m JOIN meeting mt ON mt.meeting_id=m.meeting_id "
            "JOIN body b ON b.body_id=m.body_id WHERE b.kind='planning'"):
        cand[(bid, mdate)].append((mid, txt or ""))

    # (re)populate application table + clear prior motion links
    db.execute("DELETE FROM application")
    db.execute("UPDATE motion SET application_id=NULL, app_match_method='', app_confidence=''")

    seen = set()
    app_id = 0
    linked = 0
    method_ct = defaultdict(int)
    for r in rows:
        bid = body_id.get(r["body"])
        base = "%s|%s|%s|%s|%s" % (r["body_slug"], r["date"], r["item_no"], r["dev_type"],
                                   (r["project"] or r["parcel"] or r["title"][:40]))
        key = base
        n = 1
        while key in seen:
            n += 1
            key = "%s#%d" % (base, n)
        seen.add(key)
        app_id += 1
        db.execute("INSERT INTO application VALUES (?,?,?,?,?,?)",
                   ("summit_county", app_id, key, bid, r["title"][:200], ""))
        r["_app_id"] = app_id
        r["motion_id"] = ""

        if not r["outcome"]:
            continue
        # unique-motion resolution among same body+date candidates
        keys = [(r["parcel"], "parcel"), (r["project"], "project"),
                (r["location"].split(",")[0] if r["location"] else "", "location"),
                (r["title"][:40], "text")]
        tw = TYPEWORDS.get(r["dev_type"], "")
        scored = []
        for mid, txt in cand.get((bid, r["date"]), []):
            low = txt.lower()
            if not ACTION.search(low):
                continue
            score = 0
            hit_method = ""
            for k, meth in keys:
                if k and len(k) > 3 and k.lower() in low:
                    score += 3
                    if not hit_method:
                        hit_method = meth
            if tw and tw in low:
                score += 1
            if score:
                scored.append((score, mid, hit_method or "type"))
        mid = meth = None
        if scored:
            top = max(s[0] for s in scored)
            winners = [s for s in scored if s[0] == top]
            if top >= 3 and len(winners) == 1:
                _, mid, meth = winners[0]

        # second pass — unique project-NAME phrase match (only if token pass didn't resolve)
        if mid is None:
            text = " ".join([r["title"], r["location"], r["applicant"]])
            phrases = {m.group(1).strip() for m in PHRASE.finditer(text)}
            phrases = {p for p in phrases if len(p) > 4 and p.lower() not in PHRASE_STOP}
            if phrases:
                hits = set()
                for cid, txt in cand.get((bid, r["date"]), []):
                    low = txt.lower()
                    if not ACTION.search(low):
                        continue
                    if any(p.lower() in low for p in phrases):
                        hits.add(cid)
                if len(hits) == 1:  # unique — never force a tie
                    mid = hits.pop()
                    meth = "project_name"

        if mid is None:
            continue  # ambiguous or no match — honest gap
        conf = "high" if r["link_confidence"] == "motion_matched" else "medium"
        db.execute("UPDATE motion SET application_id=?, app_match_method=?, app_confidence=? "
                   "WHERE motion_id=?", (app_id, meth, conf, mid))
        r["motion_id"] = mid
        linked += 1
        method_ct[meth] += 1

    db.commit()

    # rewrite applications.csv with motion_id + normalized names_recorded
    cols = ["date", "body", "body_slug", "item_no", "dev_type", "title", "location", "parcel",
            "applicant", "owner", "project", "session", "pc_recommendation", "outcome",
            "tally", "names_recorded", "link_confidence", "minutes_path", "motion_id"]
    with open(APP, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            r["names_recorded"] = "1" if str(r["names_recorded"]).strip().lower() in ("1", "true") else "0"
            w.writerow({c: r.get(c, "") for c in cols})

    with_outcome = sum(1 for r in rows if r["outcome"])
    print("applications loaded: %d (application table)" % len(rows))
    print("with outcome: %d | uniquely motion-linked: %d (%s)"
          % (with_outcome, linked, dict(method_ct)))
    print("db motion.application_id set: %d"
          % db.execute("SELECT COUNT(*) FROM motion WHERE application_id IS NOT NULL").fetchone()[0])
    db.close()


if __name__ == "__main__":
    main()
