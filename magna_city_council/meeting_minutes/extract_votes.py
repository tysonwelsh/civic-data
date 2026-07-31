#!/usr/bin/env python3
"""
Magna City / Metro Township vote extractor  (PURE deterministic — no LLM, no network).

Reads council-meeting markdown listed in minutes_index.csv, parses every recorded motion,
tags the governing `body`, normalizes member names across the form-of-government seam, and
emits one JSON per meeting under votes/<year>/<slug>.json plus the flat all_votes.csv
(13-col standard). Resumable (skips meetings whose JSON already exists unless --force).

THE FORM-OF-GOVERNMENT SEAM (keyed off MEETING DATE):
  * 2017-2025 (Metro Township, and 2024-05 cityhood through 2025): a 5-member council whose
    members are styled "Council Member" and which elects one of its own as **Chair, titled
    "Mayor"** (Dan Peay 2017-2023, then Eric Barney 2024-2025). That chair-"Mayor" is one of
    the five and **VOTES** — e.g. an AYE block reads "... Mayor Barney, Council Member Pierce".
    Max council tally = 5 INCLUDING the chair-Mayor.
  * 2026+ (City): a directly-elected executive **Mayor (Mick Sudbury)** who PRESIDES but does
    NOT vote (confirmed by 4-0 tallies that exclude him); 5 DISTRICT Council Members vote.
    Max council tally = 5 EXCLUDING Mayor Sudbury.
  Net: the noun is "Council Member" in BOTH eras (the recon's "Trustee" styling was not borne
  out by the documents); the ONLY thing that flips is whether the person titled "Mayor" votes.
  => A member referred to as "Mayor <X>" is a VOTER when the meeting date < 2026-01-01 and
     NON-VOTING (Sudbury) when date >= 2026-01-01. Mick Sudbury was himself a *voting* Council
     Member in 2024-2025 before becoming the non-voting Mayor in 2026 — handled by date.

VOTE GRAMMAR (narrative-tally; MSD clerk shop, same as Taylorsville/South Jordan family):
  mover + seconder are named in two orders —
     "Council Member X, seconded by Council Member Y, moved to ..."   (older)
     "Council Member X moved ... Council Member Y seconded the motion" (newer)
  outcome is recorded as, in decreasing richness:
     - NAMED ROLL BLOCK: "AYE: <names> NAY: <names> ABSTAIN: <names> EXCUSED/ABSENT: <names>
       FINAL RESULT: A-B Motion Passes/Fails"                              (2024 template)
     - NUMERIC TALLY: "vote was A-B, unanimous in favor with Council Member X absent from the
       vote" / "vote was A-B, motion passed/failed" / "passed with a A-B vote, with ..." /
       "passed N to M, showing that Council Member X voted in opposition"  (2024-2026)
     - UNANIMOUS, NO TALLY: "The motion passed unanimously."              (2017-2023, the norm)
     - DIED: "died for lack of a second."
  Named dissent/absent/abstain are captured; on a unanimous-no-tally or a bare numeric tally
  the winning MAJORITY is honestly UNNAMED (names_recorded stays False) rather than guessed.
  Text carries mild born-digital garble (Gouncil/waa/Hult) + OCR on 15 scan-only 2024-25 docs
  — normalized here.
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "minutes_index.csv"
VOTES_DIR = ROOT / "votes"
ALL_VOTES = ROOT / "all_votes.csv"

# ---------------------------------------------------------------------------
# Roster / name normalization  (surname OR first-name -> canonical full name)
# Only Magna council members ever map; county/other officials named in narrative never do.
# ---------------------------------------------------------------------------
ROSTER_MAP = {
    "hull": "Trish Hull", "trish": "Trish Hull",
    "prokopis": "Steve Prokopis", "steve": "Steve Prokopis",
    "peel": "Brint Peel", "brint": "Brint Peel",
    "barney": "Eric Barney",
    "pierce": "Audrey Pierce", "audrey": "Audrey Pierce",
    "sudbury": "Mick Sudbury", "mick": "Mick Sudbury",
    "ferguson": "Eric Ferguson",
    "peay": "Dan Peay",
    "jensen": "Michael Jensen", "michael": "Michael Jensen", "mike": "Michael Jensen",
    "olsen": "Megan Olsen", "megan": "Megan Olsen",
    "george": "Terry George", "terry": "Terry George",
}
# The person titled "Mayor" is the elected voting Chair BEFORE 2026 (Peay/Barney) and the
# non-voting executive Mayor FROM 2026 (Sudbury). Non-voting only in the city era.
CITY_ERA = "2026-01-01"

ROLE = r"(?:Council\s*Members?|Gouncil\s*Members?|Board\s*Members?|Trustees?|Mayor(?:\s*Pro\s*Tem(?:pore)?)?)"


def find_member(phrase):
    """Return canonical name for the first roster token in `phrase`, else None."""
    for t in re.findall(r"[A-Za-z']+", phrase.lower()):
        if t in ROSTER_MAP:
            return ROSTER_MAP[t]
    return None


def names_in(group):
    """All distinct roster members named in a (possibly comma/and-joined) clause."""
    out = []
    for chunk in re.split(r"(?:Council|Gouncil|Board)\s*Members?|Trustees?|Mayor(?:\s*Pro\s*Tem\w*)?|,|\band\b",
                          group, flags=re.I):
        nm = find_member(chunk)
        if nm and nm not in out:
            out.append(nm)
    return out


# ---------------------------------------------------------------------------
# Text normalization (born-digital garble + common OCR slips)
# ---------------------------------------------------------------------------
GARBLE = [("Gouncil", "Council"), ("gouncil", "council"), ("Hoffrnan", "Hoffman"),
          ("quonrm", "quorum"), ("maiority", "majority"), (" waa ", " was "),
          ("jvote", "vote"), ("Masna", "Magna"), ("Hult", "Hull"), ("Silvestriui", "Silvestrini"),
          ("Paerce", "Pierce")]  # 2025-05-13 CRA sidecar OCR (pmn_backfill promotion)


def normalize(t):
    for a, b in GARBLE:
        t = t.replace(a, b)
    return t


# ---------------------------------------------------------------------------
# Motion-type taxonomy (fixed categories; land-use checked first)
# ---------------------------------------------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"\brez\d|rezon|zoning|zone change|\bzone\b|annex|subdivision|\bplat\b|"
                 r"conditional use|land use|general plan|master plan|development agreement|"
                 r"overlay|site plan|community reinvestment|redevelopment|project area|"
                 r"planned development|code amendment", t):
        return "Land-Use/Zoning"
    if re.search(r"budget amendment|amend(?:ing)? the (?:fiscal|fy)?\s*.*budget|tentative budget|"
                 r"final budget|adopt.*budget|budget for|certified tax rate", t):
        return "Budget/Finance"
    if re.search(r"interlocal|inter-local|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t) and "grant the" not in t:
        return "Grant-Funding"
    if re.search(r"appoint|mayor pro tem|liaison|ratify the (?:results|canvass)|reappoint|"
                 r"oath of office|elect.*chair", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|procurement|award the bid|award the contract|"
                 r"professional services|franchise|agreement with|services agreement|"
                 r"enter into an agreement|interlocal", t):
        return "Contract/Purchase"
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"public hearing", t):
        return "Public Hearing Action"
    if re.search(r"proclamation|recognition|recognize|honor|commend|ceremonial", t):
        return "Ceremonial"
    if re.search(r"recess|adjourn|convene|reconvene|closed session|executive session|"
                 r"close the (?:public|staff) meeting|open the public meeting|"
                 r"approve the (?:consent|agenda|minutes|order)|approve the .*minutes|"
                 r"\btable\b|continue|postpone|amend the agenda|move to", t):
        return "Procedural/Administrative"
    return "Other"


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------
NAME = r"([A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,2}?)"
# mover, with optional inline "seconded by <Y>," before the verb
MOVER = re.compile(ROLE + r"\.?\s+" + NAME +
                   r"(?:\s*,?\s*seconded by\s+" + ROLE + r"\.?\s+" + NAME + r"\s*,?)?\s+"
                   r"(?:moved|motioned|made\s+a\s+motion)\b", re.I)
SECOND_AFTER = re.compile(ROLE + r"\.?\s+" + NAME + r"\s+seconded\b", re.I)
SECOND_BY = re.compile(r"seconded by\s+" + ROLE + r"\.?\s+" + NAME, re.I)

# NAMED roll block: AYE: ... [NAY: ...] [ABSTAIN: ...] [EXCUSED/ABSENT: ...] FINAL RESULT: A-B Motion Passes/Fails
ROLLBLOCK = re.compile(
    r"\bAYES?\s*[:\-]?\s*(?P<aye>.*?)"
    r"(?:\bNAYS?\s*[:\-]?\s*(?P<nay>.*?))?"
    r"(?:\bABSTAIN(?:ED)?\s*[:\-]?\s*(?P<abstain>.*?))?"
    r"(?:\b(?:EXCUSED|ABSENT)\s*[:\-]?\s*(?P<absent>.*?))?"
    r"\bFINAL\s+RESULT\s*[:\-]?\s*(?P<a>\d+)\s*[-–]\s*(?P<b>\d+)\s*Motion\s+(?P<out>Passe?s?|Fail\w*)",
    re.I | re.S)

# numeric tally bound to a vote phrase
TALLY = re.compile(
    r"(?:vote (?:was|of|to be)|by a vote of|with a vote of|passed with a|failed with a|"
    r"motion (?:passed|failed|carried) (?:with )?(?:a )?)\s*(\d)\s*[-–]\s*(\d)"
    r"|(\d)\s*[-–]\s*(\d)\s*(?:vote|,?\s*(?:unanimous|majority|motion (?:passed|failed|carried)))"
    r"|(?:motion )?(?:passed|failed|carried)\s+(\d)\s+to\s+(\d)"
    r"|vote to be\s+(\d)\s+to\s+(\d)", re.I)
# "passed BY A unanimous vote" is the early-2024 clerk phrasing (also one 2022-12-13
# motion) — its absence silently DROPPED motions whose next mover sat >45 lines away
# and mis-nulled others (found promoting the pmn_backfill docs, 2026-07-16)
UNANIMOUS = re.compile(r"\b(?:passed|carried|approved)\s+(?:by\s+a\s+)?unanimous(?:ly)?|unanimous(?:ly)?\s+(?:in favor|approved)|"
                       r"\bvote\s+was\s+unanimous\b|"  # bare "vote was unanimous." (2024-11-12 CRA)
                       r"\ball\s+voted\s+aye\b|\bthe\s+motion\s+carried\b", re.I)
FAIL = re.compile(r"motion\s+(?:failed|did not (?:pass|carry)|was denied)|\bfail(?:ed|s)\b|denied", re.I)
# a bare "no second" is NOT death — it matches ordinary prose in a scanned-forward
# window ("no second access", the next item's discussion) and fabricated m632's
# 'Died (no second)' (T3.1(e) 2026-07-12). Death needs the full parliamentary phrase.
DEATH = re.compile(r"(?:died|failed)\s+(?:for|due to)\s+(?:the\s+)?lack of a?\s*second|"
                   r"there (?:was|being) no second|motion (?:received|got) no second", re.I)

# named dissent / absent / abstain (narrative). Magna's dominant split-vote frame is
# "The motion passed 3 to 2, with Council Members X and Y votING in opposition" —
# the gerund + quoted variants were missing, which is why 33/41 split-tally motions
# carried 0 vote rows (T3.1(e) 2026-07-12).
NAY_CLAUSE = re.compile(
    r"((?:" + ROLE + r"\s+)?[A-Z][A-Za-z.'\-]+(?:\s*(?:,|and)\s*(?:" + ROLE + r"\s+)?[A-Za-z.'\-]+)*)"
    r"\s*(?:vot(?:ed|ing)\s+(?:in\s+opposition|[\"“”',]*(?:no|nay)\b[\"“”',]*|against)|"
    r"(?:were|was)\s+(?:the\s+)?(?:no|dissenting)|"
    r"(?:being|had|cast(?:ing)?)\s+(?:the|a)\s+[,\"“”']*(?:no|nay)[,\"“”']*\s+vote|"
    r"opposed the motion)", re.I)
# reversed frame: "motion passes with (a) nay/NO vote(s) from Council Member X [and Y]"
NAY_FROM = re.compile(
    r"(?:nay|no)\s+votes?\s+(?:from|by|cast by)\s+"
    r"((?:" + ROLE + r"\s+)?[A-Z][A-Za-z.'\-]+(?:\s*(?:,|and)\s*(?:" + ROLE + r"\s+)?[A-Za-z.'\-]+)*)",
    re.I)
# full quoted per-member roll (rare): 'Council Member Pierce voting "Aye," Council
# Member Hull voting "Nay," ...' (2024-06-25 form-of-government vote) — >=2 hits = roll
QUOTED_ROLL = re.compile(
    r"(" + ROLE + r"\s+[A-Z][A-Za-z.'\-]+)\s+voting\s+[\"“”']\s*"
    r"(Aye|Yes|Nay|No|Abstain\w*)\b", re.I)
ABSTAIN_CLAUSE = re.compile(
    r"((?:" + ROLE + r"\s+)?[A-Z][A-Za-z.'\-]+(?:\s*(?:,|and)\s*(?:" + ROLE + r"\s+)?[A-Za-z.'\-]+)*)"
    r"\s*abstain(?:ed)?", re.I)
ABSENT_CLAUSE = re.compile(
    r"((?:" + ROLE + r"\s+)[A-Z][A-Za-z.'\-]+(?:\s*(?:,|and)\s*(?:" + ROLE + r"\s+)?[A-Za-z.'\-]+)*)"
    r"\s*(?:was\s+)?(?:absent(?:\s+from\s+the\s+vote)?|excused(?:\s+from\s+the\s+vote)?)", re.I)

# in-doc CRA / RDA section brackets (a council doc can recess into the CRA)
CRA_OPEN = re.compile(r"(?:convene|recess.*(?:to|into)).{0,40}(?:community reinvestment agency|\bCRA\b)|"
                      r"community reinvestment agency (?:meeting|board)", re.I)
CRA_CLOSE = re.compile(r"(?:adjourn|reconvene|return).{0,40}(?:council|city council) meeting|"
                       r"adjourn.*(?:CRA|reinvestment)", re.I)


# ---------------------------------------------------------------------------
# One meeting
# ---------------------------------------------------------------------------
def load_lines(path):
    text = normalize(path.read_text(encoding="utf-8", errors="replace"))
    # drop the provenance header block
    if "\n---\n" in text:
        text = text.split("\n---\n", 1)[1]
    out = []
    for ln in text.split("\n"):
        s = ln.strip()
        if re.match(r"^\s*\d{1,3}\s*$", s):        # bare page number
            continue
        if re.match(r"^\s*(?:Magna (?:City|Metro Township)|City Council|Planning Commission)"
                    r"[\w /&-]*(?:Meeting|Minutes)\s*$", s, re.I):  # running header/footer
            continue
        out.append(ln)
    return out


def cra_state(lines, doc_body):
    """line index -> body. doc_body seeds it (a CRA/Canvassers doc stays that body)."""
    if doc_body != "Council":
        return {i: doc_body for i in range(len(lines))}
    state, at = "Council", {}
    for i, ln in enumerate(lines):
        probe = ln + " " + (lines[i + 1] if i + 1 < len(lines) else "")
        if state == "Council" and CRA_OPEN.search(probe):
            state = "CRA"
        elif state == "CRA" and CRA_CLOSE.search(probe):
            state = "Council"
        at[i] = state
    return at


def result_of(window, date):
    """Parse a joined text window into a result dict, or None. `date` is meeting date."""
    # 1) named roll block (richest)
    m = ROLLBLOCK.search(window)
    if m:
        a, b = int(m.group("a")), int(m.group("b"))
        out = "Fail" if re.match(r"fail", m.group("out"), re.I) else "Pass"
        buckets = {"aye": names_in(m.group("aye") or ""),
                   "nay": names_in(m.group("nay") or ""),
                   "abstain": names_in(m.group("abstain") or ""),
                   "absent": names_in(m.group("absent") or "")}
        return {"kind": "roll", "outcome": out, "a": a, "b": b, "buckets": buckets,
                "result_str": f"{a}-{b} {out}"}
    # 2) death
    if DEATH.search(window):
        return {"kind": "death", "outcome": "Fail", "result_str": "Died (no second)"}
    # 3) numeric tally
    m = TALLY.search(window)
    if m:
        nums = [g for g in m.groups() if g is not None]
        a, b = int(nums[0]), int(nums[1])
        out = "Fail" if (FAIL.search(window) and "unanimous" not in window.lower()) else "Pass"
        return {"kind": "tally", "outcome": out, "a": a, "b": b, "result_str": f"{a}-{b} {out}"}
    # 4) unanimous, no number
    if UNANIMOUS.search(window):
        return {"kind": "unanimous", "outcome": "Pass", "result_str": "Unanimous Pass"}
    # 5) bare fail (no tally)
    if re.search(r"\bmotion\s+(?:failed|was denied|did not (?:pass|carry))\b", window, re.I):
        return {"kind": "fail", "outcome": "Fail", "result_str": "Failed"}
    return None


def parse_meeting(lines, date, doc_body):
    at = cra_state(lines, doc_body)
    n = len(lines)
    votes = []
    i = 0
    while i < n:
        line = lines[i]
        mv = MOVER.search(line)
        if not mv:
            i += 1
            continue
        mover = find_member(mv.group(1) or "")
        seconder = find_member(mv.group(2) or "") if mv.group(2) else None
        start = i
        # search a forward window for the result; a NEW mover line before any result
        # ends this motion UNRESOLVED (the old code fell through and bound the NEXT
        # item's result/prose to this motion — m632's fabricated Died; T3.1(e))
        ri = None
        end = i
        unresolved_at = None
        for span in range(0, 45):
            j = i + span
            if j >= n:
                break
            if span and MOVER.search(lines[j]):
                unresolved_at = j
                break
            # the ♦♦♦ section divider ends an agenda item — a result sentence never
            # sits on the far side of it; scanning past bound the next section's
            # prose to this motion (m632's fabricated result; T3.1(e))
            if span and re.match(r"^\s*(?:♦+\s*){2,}$", lines[j]):
                unresolved_at = j
                break
            window = re.sub(r"\s+", " ", " ".join(lines[i:j + 3]))
            cand = result_of(window, date)
            if cand:
                ri, end = cand, min(j + 2, n - 1)
                if cand["kind"] == "tally":
                    # the carriage word can trail the tally by a wrapped roll
                    # ("vote to be 3 to 2, with ... voting "Aye." The motion FAILED
                    # due to not having a two-thirds majority", 2024-06-25) — look a
                    # few lines past the tally before trusting the Pass default
                    tail = re.sub(r"\s+", " ", " ".join(lines[i:min(j + 6, n)]))
                    if FAIL.search(tail) and "unanimous" not in tail.lower():
                        ri = dict(ri, outcome="Fail",
                                  result_str=f"{ri['a']}-{ri['b']} Fail")
                        end = min(j + 5, n - 1)
                break
        if ri is None:
            if unresolved_at is not None:
                # a real, seconded motion whose minutes print NO result sentence —
                # record honestly with an unknown outcome, never bind a later result
                ri, end = ({"kind": "none", "outcome": None,
                            "result_str": "No result recorded"},
                           max(i, unresolved_at - 1))
            else:
                i += 1
                continue
        # seconder fallback (scan the motion window for a seconded-by / X seconded clause)
        if not seconder:
            wtxt = " ".join(lines[start:end + 1])
            sm = SECOND_BY.search(wtxt) or SECOND_AFTER.search(wtxt)
            if sm:
                seconder = find_member(sm.group(1))
        # motion text = the FULL span up to the result line (the old per-span collector
        # missed the window's 2-line lookahead, truncating ~338 texts at the first
        # line wrap — "moved to"; T3.1(e)), then cut at the result/roll phrases
        motion_text = re.sub(r"\s+", " ", " ".join([line[mv.start():]] + lines[i + 1:end + 1])).strip(" .;,")
        motion_text = re.split(r"\.\s+(?:AYES?\b|The motion\b|Roll was called|The vote was\b|"
                               r"Council Member \S+ seconded|seconded by)",
                               motion_text, flags=re.I)[0].strip(" .;,")
        body = at.get(start, doc_body)
        buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
        names_recorded = False
        printed_tally = None
        mayor_voted = False

        # dissent clauses wrap past the result line ("...4 to 1, with Council Member
        # Pierce voting in / opposition") — scan a couple of lines beyond `end`
        win = re.sub(r"\s+", " ", " ".join(lines[start:min(end + 3, n)]))

        if ri["kind"] == "roll":
            for k in ("aye", "nay", "abstain", "absent"):
                buckets[k] = list(ri["buckets"][k])
            names_recorded = True
            printed_tally = (ri["a"], ri["b"])
        elif ri["kind"] in ("tally", "unanimous", "fail", "death"):
            if ri["kind"] == "tally":
                printed_tally = (ri["a"], ri["b"])
            # full quoted per-member roll first ('X voting "Aye," Y voting "Nay"')
            qroll = list(QUOTED_ROLL.finditer(win))
            if len(qroll) >= 2:
                for qm in qroll:
                    nm = find_member(qm.group(1))
                    if not nm:
                        continue
                    w = qm.group(2).lower()
                    key = ("aye" if w in ("aye", "yes")
                           else "abstain" if w.startswith("abstain") else "nay")
                    if nm not in sum(buckets.values(), []):
                        buckets[key].append(nm)
                names_recorded = True
            # named dissent / abstain / absent sit on/near the result line
            for mm in NAY_CLAUSE.finditer(win):
                for nm in names_in(mm.group(1)):
                    if nm not in buckets["nay"] and nm not in buckets["aye"]:
                        buckets["nay"].append(nm)
            for mm in NAY_FROM.finditer(win):
                for nm in names_in(mm.group(1)):
                    if nm not in buckets["nay"] and nm not in buckets["aye"]:
                        buckets["nay"].append(nm)
            for mm in ABSTAIN_CLAUSE.finditer(win):
                for nm in names_in(mm.group(1)):
                    if nm not in buckets["nay"] and nm not in buckets["abstain"]:
                        buckets["abstain"].append(nm)
            for mm in ABSENT_CLAUSE.finditer(win):
                for nm in names_in(mm.group(1)):
                    if nm not in buckets["absent"] and nm not in buckets["nay"] \
                            and nm not in buckets["abstain"] and nm not in buckets["aye"]:
                        buckets["absent"].append(nm)
            if any(buckets.values()):
                names_recorded = True

        # city-era Mayor (Sudbury) is non-voting: flag if the source recorded him voting
        if date >= CITY_ERA:
            for k in ("aye", "nay", "abstain"):
                if "Mick Sudbury" in buckets[k]:
                    mayor_voted = True

        votes.append({
            "body": body,
            "motion": motion_text[:600],
            "motion_type": classify_motion(motion_text),
            "result": ri["result_str"],
            "mover": mover, "seconder": seconder,
            "aye": buckets["aye"], "nay": buckets["nay"], "abstain": buckets["abstain"],
            "absent": buckets["absent"], "recuse": buckets["recuse"],
            "names_recorded": names_recorded,
            "printed_tally": list(printed_tally) if printed_tally else None,
            "mayor_voted": mayor_voted,
        })
        i = end + 1
    return votes


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def main():
    force = "--force" in sys.argv
    rows = list(csv.DictReader(INDEX.open()))
    processed = skipped = 0
    for r in rows:
        rel = r["path"]
        path = ROOT / rel
        if not path.exists():
            print(f"MISSING: {rel}", file=sys.stderr)
            continue
        year = r["year"]
        slug = Path(rel).stem
        out_dir = VOTES_DIR / year
        out_json = out_dir / f"{slug}.json"
        if out_json.exists() and not force:
            skipped += 1
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        votes = parse_meeting(load_lines(path), r["date"], r["body"])
        for k, v in enumerate(votes, start=1):
            v["motion_no"] = k
        out_json.write_text(json.dumps(
            {"date": r["date"], "year": int(year), "title": r["title"], "body": r["body"],
             "source": rel, "votes": votes}, indent=1, ensure_ascii=False))
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
