#!/usr/bin/env python3
"""
extract_votes.py — Copperton PLANNING COMMISSION vote extraction (PURE deterministic).

Reads planning_commission/minutes_index.csv, parses the structured PC minutes blocks, and
emits per-meeting JSON + all_votes.csv (13-col standard) + roster.csv. NO LLM, no network.
Resumable (skips existing JSON unless --force).

PC MINUTES GRAMMAR (born-digital, MSD-staffed; body 1560):
    1) <agenda item>. (Motion/Voting)
     Motion: <motion text>
     Motion by: Commissioner <Name>          (no seconder field is ever printed)
     Vote: Commissioners voted unanimous in favor [(of commissioners present)]
        or Vote: Commissioner <Name> abstained, all other commissioners voted ... in favor

PC votes are NARRATIVE-TALLY / collective ("Commissioners voted unanimous in favor") with NO
per-member Aye list -> every recorded vote is TALLY-ONLY (blank member). A named abstention
("Commissioner X abstained") IS recorded as a named Abstain row (the dissent signal); the
consensus majority is never fabricated as individual Ayes. There is NO mayor on the PC (max
tally = the seated commissioners). Mover is recorded where named; seconder is never printed.
Most scheduled PC meetings are CANCELLED — the corpus is deliberately thin, and honest.
"""
import os, re, csv, json, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(ROOT, "votes")
INDEX = os.path.join(ROOT, "minutes_index.csv")
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")
ROSTER = os.path.join(ROOT, "roster.csv")
FORCE = "--force" in sys.argv

# Observed PC commissioners (surname -> display). Roster is OBSERVED from Motion-by / named
# vote slots; add a full name where one was seen, else the title-cased surname.
CANON = {
    "taylor": "Taylor", "breinholt": "Breinholt", "alder": "Alder", "winkler": "Winkler",
    "pratt": "Pratt", "pazell": "Pazell", "green": "Green", "stone": "Stone",
}
ALIASES = {}


def canon(token):
    if not token:
        return None
    for w in reversed(re.findall(r"[A-Za-z’'\-]{2,}", token)):
        wl = re.sub(r"[^a-z]", "", w.lower())
        wl = ALIASES.get(wl, wl)
        if wl in CANON:
            return CANON[wl]
    return None


def classify_motion(text):
    t = text.lower()
    if re.search(r"(?:open|close|continue|recess)\w*\s+(?:the\s+)?(?:public\s+hearing|meeting)|"
                 r"continue\s+to\s+\w+\s+\d|continue\s+to\s+the", t):
        return "Procedural/Administrative"
    if re.search(r"\bminutes\b", t) and re.search(r"approv|accept|adopt", t):
        return "Procedural/Administrative"
    if re.search(r"elect|chair|vice\s+chair|appoint|nominat", t):
        return "Appointment"
    if re.search(r"rezon|zoning|zone change|\bzone\b|subdivision|\bplat\b|conditional use|"
                 r"special exception|variance|land use|general plan|site plan|setback|"
                 r"lot line|easement|annex|overlay|permit|ordinance|code amendment", t):
        return "Land-Use/Zoning"
    if re.search(r"recommend", t):
        return "Recommendation"
    return "Other"


MOTION_ANCHOR = re.compile(r"Motion:\s*", re.I)
MOVER_RE = re.compile(r"Motion\s+by:\s*(?:Commissioner\s+)?([A-Z][A-Za-z’'\-]+)", re.I)
MOTIONBY_ANCHOR = re.compile(r"Motion\s+by:", re.I)
VOTE_RE = re.compile(r"Vote:\s*(.+)", re.I | re.S)
ABSTAIN_RE = re.compile(r"Commissioner\s+([A-Z][A-Za-z’'\-]+)\s+(abstain\w*|recus\w*|opposed)", re.I)


def clean(s):
    s = re.sub(r"\s+", " ", s).strip(" .,;:—-")
    return s[:400]


def split_body(raw):
    parts = re.split(r"\n---\n", raw, maxsplit=1)
    return parts[1] if len(parts) > 1 else raw


def extract_meeting(path, rel_source, date, year, title):
    raw = open(path, encoding="utf-8").read()
    flat = re.sub(r"[ \t]+", " ", split_body(raw))
    # slice the text into "Motion:" spans; each recorded vote = a span containing a "Vote:".
    anchors = [m.start() for m in MOTION_ANCHOR.finditer(flat)]
    votes = []
    for i, a in enumerate(anchors):
        nxt = anchors[i + 1] if i + 1 < len(anchors) else len(flat)
        span = flat[a:nxt]
        vm = VOTE_RE.search(span)
        if not vm:
            continue                                   # motion with no recorded vote -> skip
        # motion text = between "Motion:" and "Motion by:"/"Vote:"
        head = span[len("Motion:"):]
        end = len(head)
        mb = MOTIONBY_ANCHOR.search(head)
        vb = VOTE_RE.search(head)
        for c in (mb, vb):
            if c:
                end = min(end, c.start())
        motion_text = clean(head[:end])
        if len(motion_text) < 3:
            continue
        mm = MOVER_RE.search(span)
        mover = canon(mm.group(1)) if mm else None
        vote_txt = vm.group(1)[:180].strip()
        if not vote_txt:
            continue
        vl = vote_txt.lower()
        # named dissent (abstain/recuse/opposed) -> named row; majority stays tally-only
        abst = {}
        for a in ABSTAIN_RE.finditer(vote_txt):
            person = canon(a.group(1))
            if person:
                w = a.group(2).lower()
                abst[person] = ("Recuse" if w.startswith("recus")
                                else "Nay" if w.startswith("oppos") else "Abstain")
        unanimous = "unanim" in vl
        failed = bool(re.search(r"fail|denied|did not (?:pass|carry)|motion\s+lost", vl))
        passed = not failed
        result = ("Fail" if failed else "Pass")
        if unanimous and not failed:
            result += " (unanimous)"
        of_present = "of commissioners present" in vl
        if of_present:
            result += " (of commissioners present)"
        nay = sorted(n for n, v in abst.items() if v == "Nay")
        abstain = sorted(n for n, v in abst.items() if v == "Abstain")
        recuse = sorted(n for n, v in abst.items() if v == "Recuse")
        if abst:
            result += " (w/ named " + ("dissent" if nay else "abstention") + ")"
        rec = {"motion": motion_text, "body": "PlanningCommission",
               "motion_type": classify_motion(motion_text), "result": result,
               "mover": mover or "", "seconder": "",
               "names_recorded": False,
               "aye": [], "nay": nay, "abstain": abstain, "recuse": recuse,
               "tally_only": {"unanimous": unanimous, "of_present": of_present}}
        votes.append(rec)
    for n, v in enumerate(votes, 1):
        vv = {"motion_no": n}; vv.update(v); votes[n - 1] = vv
    return {"date": date, "year": int(year), "title": title, "body": "PlanningCommission",
            "source": rel_source, "votes": votes}


def json_path_for(rel_path, year):
    parts = rel_path.split("/")
    return os.path.join(VOTES_DIR, str(year), parts[-2], parts[-1].replace(".md", ".json"))


def main():
    rows = list(csv.DictReader(open(INDEX, encoding="utf-8")))
    os.makedirs(VOTES_DIR, exist_ok=True)
    for r in rows:
        path = os.path.join(ROOT, r["path"])
        if not os.path.exists(path):
            print("MISSING", r["path"], file=sys.stderr); continue
        jp = json_path_for(r["path"], r["year"])
        if os.path.exists(jp) and not FORCE:
            continue
        try:
            meeting = extract_meeting(path, r["path"], r["date"], r["year"], r["title"])
        except Exception as e:
            print("PARSE ERROR", r["path"], e, file=sys.stderr); continue
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        json.dump(meeting, open(jp, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    rebuild_csv(rows); build_roster(rows); print("done")


def rebuild_csv(rows):
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source"]
    out = []
    for r in rows:
        jp = json_path_for(r["path"], r["year"])
        if not os.path.exists(jp):
            continue
        obj = json.load(open(jp, encoding="utf-8"))
        for v in obj["votes"]:
            base = dict(date=obj["date"], year=obj["year"], title=obj["title"],
                        body=v["body"], motion_no=v["motion_no"], motion=v["motion"],
                        motion_type=v["motion_type"], result=v["result"],
                        mover=v.get("mover", ""), seconder=v.get("seconder", ""),
                        source=obj["source"])
            emitted = False
            for key, lab in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                             ("recuse", "Recuse")):
                for mem in v.get(key, []):
                    row = dict(base); row["member"] = mem; row["vote"] = lab
                    out.append(row); emitted = True
            if not emitted:
                row = dict(base); row["member"] = ""; row["vote"] = ""
                out.append(row)
    with open(ALL_VOTES, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for row in out:
            w.writerow({k: row.get(k, "") for k in cols})
    return len(out)


def build_roster(rows):
    seen = {}
    for r in rows:
        jp = json_path_for(r["path"], r["year"])
        if not os.path.exists(jp):
            continue
        obj = json.load(open(jp, encoding="utf-8"))
        date = obj["date"]
        people = set()
        for v in obj["votes"]:
            if v.get("mover"):
                people.add(v["mover"])
            for k in ("nay", "abstain", "recuse"):
                people.update(v.get(k, []))
        for p in people:
            d = seen.setdefault(p, {"first": date, "last": date, "n": 0})
            d["first"] = min(d["first"], date); d["last"] = max(d["last"], date); d["n"] += 1
    with open(ROSTER, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["member", "role", "first_seen", "last_seen", "n_meetings"])
        for nm in sorted(seen, key=lambda n: (seen[n]["first"], n)):
            d = seen[nm]
            w.writerow([nm, "Commissioner", d["first"], d["last"], d["n"]])
    return len(seen)


if __name__ == "__main__":
    main()
