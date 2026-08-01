#!/usr/bin/env python3
"""
Midvale vote extractor (PURE deterministic — no LLM, no network; resumable).

Works for BOTH bodies from a single self-contained file: the governing body is inferred
from the parent directory (meeting_minutes -> City Council; planning_commission -> Planning
& Zoning Commission). An identical copy lives in each dataset dir.

Midvale prints a NAMED tabular roll call:

    MOTION: <Role> <Name> MOVED to <desc>. [The motion was ]SECONDED by <Role> <Name>.
    <Chair/Mayor> ... called for a roll call vote. The voting was as follows:
          <Role> <Name>            <Aye|Nay|Yes|No|Absent|Abstain|Excused|Recuse>
          ...
    The motion passed unanimously.            (or "... failed", or a tally)

Voice-vote fallback (no names recorded):
    MOTION: ... called for a[ voice] vote. The motion passed unanimously[ with all voting
    in favor].

NAMES ARE CAPTURED AS PRINTED — Midvale's roster changes across 2020-2026 (e.g. Dustin
Gettel is a Council Member 2020-21 then becomes Mayor in 2022; Quinn Sperry serves early,
Bonnie Billings / Denece Mikolash later). There is NO hard-coded roster: whoever the minutes
name in a roll call is recorded. A canonical map (built in pass 1 from the corpus) only
repairs whitespace jams ("BryantBrown" -> "Bryant Brown") and OCR typos within edit-distance
2 ("Paut Glover" -> "Paul Glover", "Gette" -> "Dustin Gettel"). Council roll calls print
FULL names; the Planning Commission prints SURNAMES (Chair/Vice Chair/Commissioner <Surname>).

MAYOR (council): six-member form — the Mayor PRESIDES but does NOT vote on ordinary motions
(max ordinary tally = 5 district members). The Mayor is absent from the roll block on ordinary
motions. A literal "Mayor <Name>  <vote>" line in the roll block is a genuine tie-break ->
mayor_voted=True (the only way the Mayor enters a tally). "Mayor Pro-Tem <Name>" is a
councilmember acting as chair (they appear as "Council Member <Name>" in the roll) and is
never treated as a mayor vote.
"""
import csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BODY = "pc" if ROOT.name == "planning_commission" else "council"
BODY_LABEL = "PlanningCommission" if BODY == "pc" else "Council"
MINUTES_DIR = ROOT / "minutes"
VOTES_DIR = ROOT / "votes"
INDEX = ROOT / "minutes_index.csv"
ALL_VOTES = ROOT / "all_votes.csv"
ROSTER_CSV = ROOT / "roster.csv"

# ---------------------------------------------------------------------------
VOTE_MAP = {
    "aye": "aye", "yes": "aye", "yea": "aye", "yay": "aye",
    "nay": "nay", "no": "nay",
    "abstain": "abstain", "abstained": "abstain", "abstaining": "abstain",
    "absent": "absent", "excused": "absent",
    "recuse": "recuse", "recused": "recuse", "recusal": "recuse",
}
VOTE_WORDS = (r"(?:Aye|Nay|Yea|Yay|Yes|No|Abstain(?:ed|ing)?|Absent|Excused|"
              r"Recuse[d]?|Recusal)")
CFG = {
    "council": {
        # [CG]ounci[l!] tolerates the 2020-23 OCR garbles of "Council" — "Gouncil
        # Member" (101 lines), "Counci! Member" (36), "Gounci! Member" (1) — whose
        # roll cells (incl. 4 named Nays) were silently dropped before (T3.1(c),
        # 2026-07-12). The NAME is still captured as printed; only the role token
        # is tolerant.
        "roles": r"(?:[CG]ounci[l!]\s*Member|Councilmember|Mayor\s*Pro[-\s]?Tem(?:pore)?|"
                 r"Mayor|[CG]ounci[l!]\s*President)",
        "default_body": "Council",
    },
    "pc": {
        "roles": r"(?:Commissioner|Vice[-\s]?Chair|Chair(?:man|person)?)",
        "default_body": "PlanningCommission",
    },
}[BODY]


def clean_ws(s):
    return re.sub(r"\s+", " ", s).strip()

def despace(s):
    return re.sub(r"[^a-z]", "", s.lower())


# ---------------------------------------------------------------------------
# Motion-type taxonomy (fixed 12 categories) — land-use checked FIRST.
# ---------------------------------------------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"rezon|zoning ordinance|zone change|\bzone\b|annex|subdivision|"
                 r"\bplat\b|conditional use|\bcup\b|land use|general plan|master plan|"
                 r"development agreement|overlay|site plan|preliminary|final plat|"
                 r"future land use|redevelopment|project area|planned (?:unit )?develop|"
                 r"text amendment|form[-\s]?based|density|setback|variance", t):
        return "Land-Use/Zoning"
    if re.search(r"budget amendment|amend(?:ing)? the (?:fiscal|fy)?\s*.*budget|"
                 r"tentative budget|final budget|adopt.*budget|budget for|\bcip\b", t):
        return "Budget Amendment"
    if re.search(r"interlocal|inter-local|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t) and "grant the" not in t and "granting" not in t:
        return "Grant-Funding"
    if re.search(r"appoint|liaison|ratify the (?:results|canvass)|reappoint|"
                 r"nominee|nomination|elect.*(?:chair|vice)", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|procurement|award the bid|award the contract|"
                 r"professional services|franchise agreement|agreement with|"
                 r"services agreement|enter into an agreement|\blease\b", t):
        return "Contract/Purchase"
    if re.search(r"zoning ordinance|\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"public hearing", t):
        return "Public Hearing Action"
    if re.search(r"proclamation|recognition|recognize|honor|commend|ceremonial", t):
        return "Ceremonial"
    if re.search(r"recess|adjourn|convene|reconvene|closed session|executive session|"
                 r"approve the (?:consent|agenda|minutes|order)|approve the .*minutes|"
                 r"\btable\b|continue|postpone|amend the agenda|\bmove to\b|"
                 r"open .*public (?:comment|hearing)|close .*public (?:comment|hearing)|"
                 r"suspend .*rules|voice vote", t):
        return "Procedural/Administrative"
    return "Other"


# A motion that DIED for want of a second never reached a vote. Midvale's minutes print it
# as a result sentence inside the MOTION block ("The motion died for a lack of a second." —
# council 2020-06-30; "The motion failed for lack of a second." — PC 2020-09-09). Before
# 2026-07-31 neither phrasing was recognised: the council form left `outcome` None and
# result_string fell through to the "(voice vote)" default, asserting a voice vote that never
# happened and letting db_build_lib.outcome_of default it to **Pass** — the exact inverse of
# what the minutes say. Role-independent (module level) so the backfill extractor's
# agency-roles RX variant inherits it unchanged.
NO_SECOND_RX = re.compile(
    r"\bmotion\s+(?:was\s+)?(?:died|dies|failed|fails)\s+for\s+(?:a\s+)?lack\s+of\s+a\s+second|"
    r"\bmotion\s+died\b|"
    r"\b(?:received|receives)\s+no\s+second\b|"
    r"\bdid\s+not\s+receive\s+a\s+second\b", re.I)


def make_rx():
    roles = CFG["roles"]
    return {
        "motion_split": re.compile(r"(?=\bMOTION\b\s*[:\-])", re.I),
        "mover": re.compile(
            r"\b(" + roles + r")\.?\s+([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-!|]+){0,2}?)"
            r"\s+(?:MOVED|MOVES|MOVEO|MADE\s+A\s+MOTION)\b", re.I),
        "seconder": re.compile(
            r"\bSECONDED\s+BY\s+(" + roles + r")\.?\s+"
            r"([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-!|]+){0,2})", re.I),
        "asfollows": re.compile(r"(?:voting|vote)\s+was\s+as\s+follows", re.I),
        "tabline": re.compile(
            r"^\s*(" + roles + r")\.?\s+(.+?)\s+(" + VOTE_WORDS + r")\s*\.?\s*$", re.I),
        # TWO-COLUMN roll calls (2020-2023): two "<role> <name> <vote>" cells can sit
        # side-by-side on ONE physical line, e.g.
        #   Council Member Sperry   Aye        Council Member Glover   Aye
        # This finds EVERY such cell on a line (finditer), so a single-column line yields
        # one pair and a two-column line yields both — no merge, no dropped voter. The
        # name is captured as-printed (OCR garbles like "Pau! Glover" survive to canon()),
        # non-greedily bounded so it stops at the vote word before the next cell. The
        # trailing lookahead requires the vote word to END its column cell (EOL, a
        # multi-space column gap, a following role, or a period) so a vote word buried in
        # post-vote discussion prose ("Council Member Glover No longer supports ...") is
        # NOT mistaken for a roll cell when the block is scanned to its result line.
        "tabpair": re.compile(
            r"(" + roles + r")\.?\s+"
            r"([A-Z][A-Za-z'\-!|]+(?:\s+[A-Z][A-Za-z'\-!|]+){0,2}?)\s+"
            r"(" + VOTE_WORDS + r")(?=\s*$|\s{2,}|\s+" + roles + r"\b|\s*[.;])", re.I),
        "unanimous": re.compile(r"passed\s+unanimously|unanimous", re.I),
        # outcome is read from the result CLAUSE anchored on "(the) motion <verb>", so a
        # stray "failed"/"denied" in post-vote discussion can't flip the result.
        "motion_result": re.compile(
            r"(?:the\s+)?motion\s+(?:was\s+)?(passed|carried|approved|adopted|"
            r"failed|denied|defeated|did\s+not\s+(?:pass|carry))", re.I),
    }

RX = make_rx()


def parse_motions(text):
    """Return list of raw motion dicts (names NOT yet canonicalized)."""
    chunks = RX["motion_split"].split(text)
    out = []
    for ch in chunks:
        if not re.match(r"\s*MOTION\b\s*[:\-]", ch, re.I):
            continue
        lines = ch.split("\n")
        flat = clean_ws(ch)
        mv = RX["mover"].search(flat)
        mover = clean_ws(mv.group(2)).strip(" .!|,-") if mv else None
        sd = RX["seconder"].search(flat)
        sec = clean_ws(sd.group(2)).strip(" .!|,-") if sd else None
        dm = re.search(r"(?:MOVED|MOVEO|MOVES)\s+(.+?)(?:\.\s*(?:The\s+motion\s+was\s+)?"
                       r"SECONDED|\.\s*[A-Z][a-z]+\s+(?:Pro[-\s]?Tem\s+)?\w+\s+called\s+for|"
                       r"$)", flat, re.I)
        if dm:
            desc = clean_ws(dm.group(1))
        elif mv:
            desc = clean_ws(flat[mv.end():])[:400]
        else:
            desc = clean_ws(flat)[:400]
        desc = desc[:600]

        buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
        mayor_voted = False
        af = RX["asfollows"].search(ch)
        if af:
            # Scan the roll block from the text AFTER the "voting was as follows" marker.
            # (Starting from the marker's LINE would re-scan the motion preamble, whose
            # "The motion was SECONDED ..." falsely trips the result-line break when the
            # whole preamble + marker sit on one physical line — the common single-line
            # layout that silently dropped ~half of the 2020-2021 rolls to voice-votes.)
            # Non-roll interior lines (OCR page-break headers, form-feeds) are skipped, not
            # treated as end-of-block, so a roll split across a page boundary stays intact;
            # the tabpair lookahead keeps prose from leaking in before the result line.
            for ln in ch[af.end():].split("\n"):
                if re.search(r"\bthe\s+motion\s+(?:passed|failed|carried|was)", ln, re.I) \
                   and not RX["tabpair"].search(ln):
                    break
                # Split the physical line into ALL its "<role> <name> <vote>" cells so a
                # two-column line contributes BOTH voters (previously one was merged into
                # the other's name / dropped, undercounting an Aye and flipping outcomes).
                for m in RX["tabpair"].finditer(ln):
                    role, namephrase, vword = m.group(1), clean_ws(m.group(2)), m.group(3).lower()
                    bucket = VOTE_MAP.get(vword.rstrip("."))
                    if bucket is None:
                        continue
                    is_mayor = bool(re.match(r"mayor\b", role.strip(), re.I)) and \
                               "pro" not in role.lower()
                    name = namephrase.strip(" .!|,-")
                    if is_mayor:
                        mayor_voted = True
                    buckets[bucket].append({"name": name, "mayor": is_mayor})
        names_recorded = any(buckets[b] for b in buckets)

        outcome = None
        mr = RX["motion_result"].search(flat)
        if mr:
            verb = mr.group(1).lower()
            outcome = "Fail" if re.search(r"fail|den|defeat|did", verb) else "Pass"
        elif RX["unanimous"].search(flat):
            outcome = "Pass"
        unanimous = bool(RX["unanimous"].search(flat)) and not names_recorded
        # died-for-lack-of-a-second: only meaningful when NO roll was recorded (a motion with
        # a roll block plainly got its second); a stray phrase in post-vote discussion can
        # therefore never overwrite a real tally.
        no_second = bool(NO_SECOND_RX.search(flat)) and not names_recorded

        if not (mover or names_recorded or unanimous):
            continue
        out.append({"mover": mover, "seconder": sec, "desc": desc, "buckets": buckets,
                    "names_recorded": names_recorded, "unanimous": unanimous,
                    "mayor_voted": mayor_voted, "outcome": outcome,
                    "no_second": no_second})
    return out


# ---------------------------------------------------------------------------
# Explicit OCR name-alias map (council). The frequency-anchored fuzzy canon below
# cannot repair two classes of OCR garble: (a) a wrong spelling that itself recurs
# >=3x becomes its OWN anchor ("Dustin Geftel"/"Dustin Gette"), and (b) a first-letter
# substitution ("Oustin Gettel") is skipped by the same-initial fuzzy guard. These are
# folded to the canonical roster name here, keyed on the despaced form. A DROP value
# blanks a capture that is genuinely not a resolvable member (an OCR fragment the
# mover/seconder regex latched onto) — never guessed. This is normalization ALONGSIDE
# the as-printed roll (SCHEMA_SPEC §2): the source markdown is untouched; only the
# canonical member label is repaired. (PC's Erikson/Erickson variants live in the
# separate planning_commission copy of this file and are out of scope here.)
DROP = "\x00DROP"
NAME_ALIASES = {
    # OCR spelling garbles of Dustin Gettel (D5 councilmember 2020-2024)
    "dustingette":  "Dustin Gettel",
    "dustinget":    "Dustin Gettel",   # truncated OCR capture ("Dustin Get")
    "dustingeftel": "Dustin Gettel",
    "oustingettel": "Dustin Gettel",
    # OCR garble of Paul Glover ("Pau! Glover" -> despaced "pauglover")
    "pauglover":    "Paul Glover",
    # bare first names captured as mover/seconder (each unique in the roster)
    "bryant": "Bryant Brown",
    "paul":   "Paul Glover",
    "heidi":  "Heidi Robinson",
    "quinn":  "Quinn Sperry",
    "bonnie": "Bonnie Billings",   # page-break split "Bonnie / Billings" (2025-06-03 pmn doc)
    # OCR garbles found in the 2026-07-16 PMN-promoted docs (mover/seconder only):
    # capital-I-for-l and Gl-for-Q substitutions the fuzzy canon can't reach
    "paulgiover":  "Paul Glover",   # "Paul GIover" (2022-12-06 RDA doc)
    "gluinnsperry": "Quinn Sperry", # "Gluinn Sperry" (2023-06-20 CC doc)
    # mover/seconder fragments with trailing OCR / role bleed -> resolved member
    "quinnsperrymayor":  "Quinn Sperry",       # "Quinn Sperry' Mayor"
    "heidiproceedingsof": "Heidi Robinson",     # page-header bled into the name
    # non-members the mover/seconder regex latched onto -> blank (do not guess)
    "paulgettel":     DROP,   # ambiguous OCR cross of two surnames
    "mayorhalecalled": DROP,  # presiding mayor, not a mover
}


# ---------------------------------------------------------------------------
# Canonical-name map (pass 1)
# ---------------------------------------------------------------------------
def lev(a, b):
    if a == b:
        return 0
    if not a or not b:
        return len(a) + len(b)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def build_canon(all_names):
    freq = Counter(n for n in all_names if n)
    # anchors: names seen >= 3 times (robust true spellings)
    anchors = {n: c for n, c in freq.items() if c >= 3}
    if not anchors:  # tiny corpus fallback
        anchors = dict(freq)
    key2canon = {}
    for n, c in sorted(anchors.items(), key=lambda x: -x[1]):
        k = despace(n)
        # prefer the most frequent spelling; among ties prefer one containing a space
        if k not in key2canon:
            key2canon[k] = n
    # surname index from multi-token anchors (last token -> canonical, if unique)
    sur = defaultdict(set)
    for n in key2canon.values():
        toks = n.split()
        if len(toks) >= 2:
            sur[despace(toks[-1])].add(n)
    surname_index = {k: next(iter(v)) for k, v in sur.items() if len(v) == 1}
    keys = list(key2canon.keys())

    cache = {}
    def canon(name):
        if not name:
            return None
        clean = clean_ws(name).strip(" .!|,-")
        if not clean:
            return None
        if clean in cache:
            return cache[clean]
        k = despace(clean)
        res = None
        if k in NAME_ALIASES:                       # explicit OCR-garble repair (first)
            a = NAME_ALIASES[k]
            res = None if a == DROP else a
            cache[clean] = res
            return res
        if k in key2canon:
            res = key2canon[k]
        else:
            best, bd = None, 99
            for kk in keys:
                if kk and k and kk[0] == k[0] and abs(len(kk) - len(k)) <= 2:
                    d = lev(kk, k)
                    if d < bd:
                        bd, best = d, key2canon[kk]
            if best and bd <= 2:
                res = best
            elif " " not in clean and k in surname_index:
                res = surname_index[k]
            else:
                res = clean
        cache[clean] = res
        return res
    return canon


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def load_body_text(md_path):
    txt = md_path.read_text(encoding="utf-8", errors="replace")
    # strip provenance header (everything through the first '---' line)
    parts = txt.split("\n---\n", 1)
    return parts[1] if len(parts) == 2 else txt


def result_string(m):
    na, nn = len(m["buckets"]["aye"]), len(m["buckets"]["nay"])
    if m["names_recorded"]:
        # NAMED roll call: the outcome IS the tally — majority carries (a mayoral tie-break
        # already shows in the counts). The printed "motion passed/failed" phrase is not
        # trusted here because post-vote discussion routinely repeats "failed/denied".
        outcome = "Pass" if na > nn else "Fail"
        return f"{na}-{nn} {outcome}"
    # A motion that died for want of a second — no vote of any kind was taken. "Died (no
    # second)" is the collection-wide string for this (white_city/riverton/sandy/taylorsville/
    # magna/st_george emit it); db_build_lib.outcome_of maps it to outcome='Died' and
    # normalize_motions.py to outcome='died' (rule died-no-second).
    if m.get("no_second"):
        return "Died (no second)"
    if m["unanimous"]:
        return "Unanimous Pass"
    return (m["outcome"] or "Recorded") + " (voice vote)"


def detect_body(desc):
    if BODY == "pc":
        return "PlanningCommission"
    if re.search(r"redevelopment agency|\brda\b|community development.*agency|\bcda\b",
                 desc, re.I):
        return "RDA"
    return "Council"


def main():
    force = "--force" in sys.argv
    rows = list(csv.DictReader(INDEX.open()))

    # ---- pass 1: collect names for the canonical map ----
    all_names = []
    parsed = {}
    for r in rows:
        md = ROOT / r["path"]
        if not md.exists():
            print(f"MISSING: {r['path']}", file=sys.stderr)
            continue
        ms = parse_motions(load_body_text(md))
        parsed[r["path"]] = ms
        for m in ms:
            all_names += [m["mover"], m["seconder"]]
            for b in m["buckets"].values():
                all_names += [x["name"] for x in b]
    canon = build_canon(all_names)

    # ---- pass 2: canonicalize + write per-meeting JSON ----
    VOTES_DIR.mkdir(exist_ok=True)
    processed = skipped = 0
    for r in rows:
        if r["path"] not in parsed:
            continue
        year = r["year"]
        week = Path(r["path"]).parent.name
        slug = Path(r["path"]).stem
        out_dir = VOTES_DIR / year / week
        out_json = out_dir / f"{slug}.json"
        if out_json.exists() and not force:
            skipped += 1
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        votes = []
        for k, m in enumerate(parsed[r["path"]], start=1):
            def cbucket(key):
                seen, out = set(), []
                for x in m["buckets"][key]:
                    nm = canon(x["name"])
                    if nm and nm not in seen:
                        seen.add(nm)
                        out.append(nm)
                return out
            mayor = None
            for x in (m["buckets"]["aye"] + m["buckets"]["nay"]):
                if x["mayor"]:
                    mayor = canon(x["name"])
            votes.append({
                "body": detect_body(m["desc"]),
                "motion": m["desc"][:600],
                "motion_type": classify_motion(m["desc"]),
                "result": result_string(m),
                "mover": canon(m["mover"]),
                "seconder": canon(m["seconder"]),
                "aye": cbucket("aye"), "nay": cbucket("nay"),
                "abstain": cbucket("abstain"), "absent": cbucket("absent"),
                "recuse": cbucket("recuse"),
                "names_recorded": m["names_recorded"],
                "mayor_voted": m["mayor_voted"], "mayor": mayor,
                "motion_no": k,
            })
        payload = {"date": r["date"], "year": int(year), "title": r["title"],
                   "source": r["path"], "votes": votes}
        out_json.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
        processed += 1
    print(f"Processed {processed} meetings -> JSON  (skipped {skipped} existing)")
    build_all_votes()
    build_roster()


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
                base = [data["date"], data["year"], data["title"], v["body"],
                        v["motion_no"], v["motion"], v["motion_type"], v["result"],
                        v.get("mover") or "", v.get("seconder") or ""]
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


def build_roster():
    """Observed roster: every name that cast a recorded vote, with tenure + counts."""
    seen = defaultdict(lambda: {"n": 0, "dates": [], "votes": Counter()})
    for jp in sorted(VOTES_DIR.rglob("*.json")):
        if jp.name.startswith("_"):
            continue
        data = json.loads(jp.read_text())
        for v in data["votes"]:
            for key, label in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                               ("absent", "Absent"), ("recuse", "Recuse")):
                for member in v.get(key, []):
                    s = seen[member]
                    s["n"] += 1
                    s["dates"].append(data["date"])
                    s["votes"][label] += 1
    with ROSTER_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["body", "member", "n_vote_rows", "first_date", "last_date",
                    "aye", "nay", "abstain", "absent", "recuse"])
        for m in sorted(seen, key=lambda x: -seen[x]["n"]):
            s = seen[m]
            w.writerow([BODY_LABEL, m, s["n"], min(s["dates"]), max(s["dates"]),
                        s["votes"]["Aye"], s["votes"]["Nay"], s["votes"]["Abstain"],
                        s["votes"]["Absent"], s["votes"]["Recuse"]])
    print(f"Wrote {ROSTER_CSV} with {len(seen)} observed members")


if __name__ == "__main__":
    main()
