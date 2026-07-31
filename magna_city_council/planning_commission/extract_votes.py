#!/usr/bin/env python3
"""
Magna Planning Commission vote extractor  (PURE deterministic — no LLM, no network).

The Magna PC is the MSD-staffed county land-use body that recommends on Magna rezones
(REZ####), conditional-use permits (CUP####-######), ordinance/code amendments
(OAM####-######) and subdivisions to the Magna Council. Records live on Utah PMN body 1559.

MINUTES FORMAT (uniform 2019->2026): a structured motion block —
    Motion:     To recommend application #30878 for approval to the Magna Council ...
    Motion by:  Commissioner Richards
    2nd by:     Commissioner Lockwood
    Vote:       Commissioners voted unanimous in favor (of commissioners present)
                -- or -- Commissioner Sudbury voted nay, all others voted in favor ...
                -- or -- Commissioner X abstained, all other commissioners voted in favor
    Motion passed.
Narrative "Commissioner X motioned to open/close the public hearing, Commissioner Y
seconded that motion" lines are PROCEDURAL hearing gavels with NO recorded Vote: line and
are intentionally NOT emitted; only the substantive Motion:/Vote: blocks are.

OUTCOME is a TALLY-ONLY 'unanimous in favor (of commissioners present)' on the vast
majority of motions — the assenting majority is honestly UNNAMED (names_recorded stays
False); only named dissenters/abstainers are attributed. body is always PlanningCommission.
Commissioner surnames are the published identifiers (PC minutes rarely print first names);
staff/presenters tagged "(Motion/Voting)" or "Mr./Ms." never map to a vote.
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "minutes_index.csv"
VOTES_DIR = ROOT / "votes"
ALL_VOTES = ROOT / "all_votes.csv"

# Observed Magna PC commissioners (whitelist; staff/public never map).
ROSTER = {
    "richards": "Richards", "weight": "Weight", "cripps": "Cripps", "elieson": "Elieson",
    "vanroosendaal": "VanRoosendaal", "roosendaal": "VanRoosendaal", "lockwood": "Lockwood",
    "collard": "Collard", "taylor": "Taylor", "larson": "Larson", "white": "White",
    "alder": "Alder", "shaw": "Shaw", "everett": "Everett", "sudbury": "Sudbury",
}


def find_member(phrase):
    toks = re.findall(r"[A-Za-z']+", phrase.lower())
    # try a joined VanRoosendaal first
    joined = "".join(toks)
    for t in toks:
        if t in ROSTER:
            return ROSTER[t]
    if "vanroosendaal" in joined:
        return "VanRoosendaal"
    return None


def names_in(clause):
    out = []
    for chunk in re.split(r"Commissioners?|,|\band\b", clause, flags=re.I):
        nm = find_member(chunk)
        if nm and nm not in out:
            out.append(nm)
    return out


GARBLE = [("Gommissioner", "Commissioner"), ("Masna", "Magna"), (" waa ", " was ")]
def normalize(t):
    for a, b in GARBLE:
        t = t.replace(a, b)
    return t


def classify_motion(text):
    t = text.lower()
    if re.search(r"#?\b(?:rez|cup|oam|sub|pud|gpz|con|var)\d|rezon|zoning|zone change|"
                 r"\bzone\b|conditional use|subdivision|\bplat\b|code amendment|land use|"
                 r"general plan|annex|overlay|site plan|development agreement", t):
        return "Land-Use/Zoning"
    if re.search(r"public hearing", t):
        return "Public Hearing Action"
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"minutes|agenda|elect|appoint|training|bylaws|rules of order|"
                 r"recess|adjourn|open the (?:public|business)|close the", t):
        return "Procedural/Administrative"
    return "Other"


# structured block: Motion: <text> Motion by: <X> 2nd by: <Y> Vote: <votetext>
BLOCK = re.compile(
    r"Motion:\s*(?P<text>.+?)\s*"
    r"Motion by:\s*(?:Commissioner\s+)?(?P<mover>[A-Za-z][A-Za-z '\-]*?)\s*"
    r"2nd by:\s*(?:Commissioner\s+)?(?P<sec>[A-Za-z][A-Za-z '\-]*?)\s*"
    r"Vote:\s*(?P<vote>.+?)(?=(?:\bMotion:\s)|(?:\n\s*\n)|$)",
    re.I | re.S)

FAILRE = re.compile(r"motion (?:failed|denied|did not (?:pass|carry))|failed|denied", re.I)


def parse_meeting(text):
    text = normalize(text)
    if "\n---\n" in text:
        text = text.split("\n---\n", 1)[1]
    votes = []
    for m in BLOCK.finditer(text):
        motion_text = re.sub(r"\s+", " ", m.group("text")).strip(" .;,")
        mover = find_member(m.group("mover") or "")
        seconder = find_member(m.group("sec") or "")
        vote = re.sub(r"\s+", " ", m.group("vote")).strip()
        buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
        names_recorded = False
        # dissent / abstain in the Vote clause
        for mm in re.finditer(r"((?:Commissioners?\s+)?[A-Z][A-Za-z'\-]+(?:\s+(?:and|,)\s+"
                              r"(?:Commissioner\s+)?[A-Z][A-Za-z'\-]+)*)\s*(?:voted\s+)?"
                              r"(nay|no|in opposition|opposed|abstain(?:ed)?)", vote, re.I):
            kind = "abstain" if re.match(r"abstain", mm.group(2), re.I) else "nay"
            for nm in names_in(mm.group(1)):
                if nm not in buckets[kind]:
                    buckets[kind].append(nm)
        outcome = "Fail" if (FAILRE.search(vote) and "in favor" not in vote.lower()) else "Pass"
        # numeric tally if printed
        tally = re.search(r"(\d+)\s*[-–]\s*(\d+)", vote)
        if buckets["nay"] or buckets["abstain"]:
            result = f"Pass (dissent: {', '.join(buckets['nay'] + buckets['abstain'])})" \
                     if outcome == "Pass" else "Failed"
        elif re.search(r"unanimous", vote, re.I):
            result = "Unanimous Pass"
        elif tally:
            result = f"{tally.group(1)}-{tally.group(2)} {outcome}"
        else:
            result = outcome
        votes.append({
            "body": "PlanningCommission",
            "motion": motion_text[:600],
            "motion_type": classify_motion(motion_text),
            "result": result,
            "mover": mover, "seconder": seconder,
            "aye": buckets["aye"], "nay": buckets["nay"], "abstain": buckets["abstain"],
            "absent": buckets["absent"], "recuse": buckets["recuse"],
            "names_recorded": names_recorded,
            "printed_tally": [int(tally.group(1)), int(tally.group(2))] if tally else None,
            "mayor_voted": False,
        })
    return votes


def main():
    force = "--force" in sys.argv
    rows = list(csv.DictReader(INDEX.open()))
    processed = skipped = 0
    for r in rows:
        path = ROOT / r["path"]
        if not path.exists():
            print(f"MISSING: {r['path']}", file=sys.stderr)
            continue
        year = r["year"]
        slug = Path(r["path"]).stem
        out_dir = VOTES_DIR / year
        out_json = out_dir / f"{slug}.json"
        if out_json.exists() and not force:
            skipped += 1
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        votes = parse_meeting(path.read_text(encoding="utf-8", errors="replace"))
        for k, v in enumerate(votes, start=1):
            v["motion_no"] = k
        out_json.write_text(json.dumps(
            {"date": r["date"], "year": int(year), "title": r["title"],
             "body": "PlanningCommission", "source": r["path"], "votes": votes},
            indent=1, ensure_ascii=False))
        processed += 1
    print(f"Processed {processed} meetings -> JSON  (skipped {skipped} existing)")
    build_all_votes()


def build_all_votes():
    fields = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
              "result", "mover", "seconder", "member", "vote", "source"]
    n = 0
    with ALL_VOTES.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for jp in sorted(VOTES_DIR.rglob("*.json")):
            if jp.name.startswith("_"):
                continue
            data = json.loads(jp.read_text())
            for v in data["votes"]:
                base = [data["date"], data["year"], data["title"], v["body"], v["motion_no"],
                        v["motion"], v["motion_type"], v["result"], v.get("mover") or "",
                        v.get("seconder") or ""]
                emitted = False
                for key, label in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                                   ("absent", "Absent"), ("recuse", "Recuse")):
                    for member in v.get(key, []):
                        w.writerow(base + [member, label, data["source"]])
                        n += 1
                        emitted = True
                if not emitted:
                    w.writerow(base + ["", "", data["source"]])
                    n += 1
    print(f"Wrote {ALL_VOTES} with {n} data rows")


if __name__ == "__main__":
    main()
