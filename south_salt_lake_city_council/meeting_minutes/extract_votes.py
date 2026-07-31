#!/usr/bin/env python3
"""
South Salt Lake vote extractor  (PURE deterministic — no LLM, no network).

Walks the minutes markdown under <dataset>/minutes/<year>/<week-monday>/*.md (each file
carries a provenance header naming date/body/kind/pmn_file), parses every recorded motion,
and emits one JSON per meeting under <dataset>/votes/<year>/<week>/<slug>.json plus the
13-column standard <dataset>/all_votes.csv (one row per member-vote).

SSL vote grammar (named per-member roll call — verified against council 2026-06-10 and the
2020 corpus):

    Council Member <X> made a motion to <action>.
    MOTION: <Full Name>
    SECOND: <Full Name>
    Roll Call Vote:                (or  "Voice Vote:")
    Glad:            Yes
    Thomas:          Yes
    Bynum:           Yes
    Mitchell:        Not Present
    Jones:           Yes
    Williams:        Yes
    deWolfe:         Yes

Every voter is named (names_recorded always True). The source prints NO "motion passed"
string, so `result` is the synthesized tally "<aye>-<nay> Pass|Fail" (there is no verbatim
result string to preserve). Vote mode (Roll Call / Voice) is retained. The Mayor is an
executive who does NOT vote and never appears in a roll call (max tally = 7 council
members); the roster is OBSERVED from each doc's "MEMBERS PRESENT" header (it evolves over
2020-2026), never hardcoded. `body` comes from the provenance header
(Council / RDA / PlanningCommission).

Run:  python3 extract_votes.py            # this dataset (script's parent dir)
      python3 extract_votes.py --force    # re-extract all
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MINUTES_DIR = ROOT / "minutes"
VOTES_DIR = ROOT / "votes"
ALL_VOTES = ROOT / "all_votes.csv"

HEADER_RE = re.compile(r"<!--\s*(.*?)\s*-->", re.S)

VOTE_WORD = r"(Yes|No|Not\s+Present|Absent|Abstain(?:ed)?|Recuse[d]?|Aye|Nay|Excused|Present|None)"
_ROLE = r"(?:Commissioner|Council\s*Member|Board\s*Member|Vice[- ]?Chair|Chair|" \
        r"Mayor\s*Pro\s*Tem(?:pore)?|Director|Mr\.|Ms\.|Mrs\.)"
# Handles BOTH grammars:
#   council   "Glad:            Yes"            (surname, colon, value)
#   PlanningC "Commissioner Carter – Aye;"    (role prefix, name, en-dash, value, semicolon)
# 2026-07-16 promotion (T-SSL minutes-promotion) grammar extensions, all verified against
# source PDFs before adoption:
#   (a) separator may be WHITESPACE-ONLY (>=2 spaces): the 2023-2024 RDA clerk and the
#       2020-09-17 council SM print "Bynum          Yes" with no colon. Bare "Present"
#       is excluded on that path so roster headers ("OTHERS   PRESENT") can never read
#       as a vote; "Not Present" still passes.
#   (b) a trailing comma is as legal as ;/. ("Commissioner Ewell-Aye,").
#   (c) "None" as a printed value (e.g. 2025-12-10 "Mitchell: None") MATCHES the line so
#       the roll does not truncate, but maps to NO bucket - the member cast no recorded
#       vote and no vote is fabricated.
MEMBER_VOTE = re.compile(
    r"^\s*" + _ROLE + r"?\.?\s*([A-Za-z][A-Za-z'’.\-]{1,30}?)"
    r"(?:\s*(?::|[–\-—])\s*|\s{2,}(?!Present\b))"
    + VOTE_WORD + r"\s*[;.,]?\s*$", re.I)
VOTE_HEADER = re.compile(r"^\s*(Roll\s+Call\s+Vote|Voice\s+Vote|Vote)\s*:", re.I)
# 2026-07-16: a clerk-typo vote line ("Huff:   Ye", "Huff:   Y/es") must not END the
# roll mid-block (it truncated two promoted rolls to 1-0). A short single-token value
# after "Name:" inside an active roll is SKIPPED - the member's vote stays unrecorded
# (never guessed; the verbatim typo remains in the minutes markdown), the rest of the
# roll is captured. Corrections, if ever made, go through db/vote_overrides.csv.
MANGLED_VOTE = re.compile(
    r"^\s*" + _ROLE + r"?\.?\s*([A-Za-z][A-Za-z'’.\-]{1,30}?)\s*:\s*[A-Za-z/]{1,6}\s*$")
MOTION_LINE = re.compile(r"^\s*MOTION\s*:\s*(.+?)\s*$", re.I)
SECOND_LINE = re.compile(r"^\s*SECOND\s*:\s*(.+?)\s*$", re.I)
MADE_MOTION = re.compile(r"(?:Council\s*Member|Commissioner|Board\s*Member|Member|Chair|Vice\s*Chair)?\s*"
                         r"([A-Z][A-Za-z'’.\-]+)\s+made\s+a\s+motion\s+(.*)", re.I)
# FALLBACK-ONLY (2026-07-16): the RDA clerk writes "Director X moved to approve these
# minutes." with no "made a motion" sentence, no "Motion to X:" label and no numbered
# heading — those motions previously carved as "(motion — description not captured)".
# Used strictly LAST so no previously-captured audited motion text changes form.
MOVED_TO = re.compile(r"(?:Council\s*Member|Commissioner|Board\s*Member|Member|Chair|Vice\s*Chair|Director)?\s*"
                      r"([A-Z][A-Za-z'’.\-]+)\s+moved\s+(to\s+.*)", re.I)
# agenda headings sit at the left margin; deeply-indented "N." lines are findings /
# conclusions / conditions lists inside a motion, never the item heading
ITEM_HEADING = re.compile(r"^\s{0,4}\d+\.\s+(.*[A-Za-z].*)$")

VOTE_MAP = {
    "yes": "aye", "aye": "aye", "present": "aye",
    "no": "nay", "nay": "nay",
    "not present": "absent", "absent": "absent", "excused": "absent",
    "abstain": "abstain", "abstained": "abstain",
    "recuse": "recuse", "recused": "recuse",
}
# a captured "member name" that is itself a vote word is a table header, not a voter
# (2022-10-26 consent items print a blank "YES        NO" ballot-table header that the
# whitespace-separated grammar would otherwise read as member YES voting No)
_NAME_IS_VOTE = {"yes", "no", "aye", "nay", "absent", "abstain", "abstained",
                 "recuse", "recused", "excused", "present", "none", "vote"}

# running-footer / repeated-header lines that interrupt roll-call blocks -> stripped.
# T3.1(d) 2026-07-12: (a) the PC running footer prints "South Salt Lake City Planning
# Commission [Regular ]Meeting <page>" with NO dash — it survived and broke ~19 vote
# blocks mid-roll (sub-quorum "1-0/2-0" tallies for true 7-0 votes); (b) the bare
# page-number alternative had a `.*` tail, so EVERY line starting with a number —
# including all agenda-item headings and findings lists — was silently stripped
# (the 83 "(motion — description not captured)" rows). Page numbers now match only
# a WHOLE line; the PC footer is its own end-anchored family.
FOOTER_RE = re.compile(
    r"^\s*(?:"
    r"(?:South Salt Lake\s*[–\-—].*Meeting|"
    r"City of South Salt Lake City Council.*Meeting|"
    r"CITY OF SOUTH SALT LAKE|CITY COUNCIL MEETING|COUNCIL MEETING|"
    r"City of South Salt Lake Planning Commission.*|Planning Commission.*Meeting|"
    r"Page\s+\d+).*"
    r"|South Salt Lake City Planning Commission\b.*Meeting(?:\s+\d{1,3})?\s*"
    r"|\d{1,3}\s*"
    r")$", re.I)
FOOTER_DATE = re.compile(
    r"^\s*(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{1,2},?\s+\d{4}\s*(?:Page\s*\d+)?\s*$", re.I)

# 2026-07-16: several PC minutes PDFs (both PMN "_Final" copies and the AgendaCenter
# ArchivedMinutes recoveries) carry a vertical DRAFT watermark that pdftotext scatters
# as stray single letters/fragments (D / R / AF / T ...) - on their own lines, as a
# line-leading prefix, or wedged after a "Vote:" header. Unhandled, a mid-roll fragment
# line ends the vote block and silently truncates the roll (same failure family as the
# T3.1(d) footer bleed). Stripping is deliberately narrow:
#   - a whole line consisting ONLY of watermark letters/fragments (uppercase);
#   - a fragment prefix immediately followed by a role word (Commissioner/Chair/...);
#   - a fragment wedged between "...Vote:" and the first member.
# Attachment-page fragments mixed with real drawing text (e.g. "A    MD   HOUSE") do
# NOT match and are left verbatim.
WATERMARK_LINE = re.compile(r"^(?:(?:DRAFT|DRAF|RAFT|DRA|RAF|AFT|DR|RA|AF|FT|[DRAFT])\s*)+$")
WATERMARK_PREFIX = re.compile(
    r"^(\s*)(?:DRA|RAF|AFT|DR|RA|AF|FT|[DRAFT])\s{2,}"
    r"(?=(?:Commissioner|Chair|Vice|Council|Director|Mayor)\b)")
VOTE_HDR_FRAG = re.compile(
    r"^(\s*(?:Roll\s+Call\s+Vote|Voice\s+Vote|Vote)\s*:\s*)(?:DRA|RAF|AFT|DR|RA|AF|FT|[DRAFT])\s{2,}(?=\S)",
    re.I)


def parse_header(text):
    m = HEADER_RE.search(text[:600])
    meta = {}
    if m:
        for part in m.group(1).split("|"):
            if ":" in part:
                k, v = part.split(":", 1)
                meta[k.strip()] = v.strip()
    return meta


def build_roster(lines):
    """surname(lower) -> full name, parsed from the MEMBERS PRESENT / NOT PRESENT header."""
    roster = {}
    grab = False
    for ln in lines[:120]:
        if re.search(r"MEMBERS\s+PRESENT", ln, re.I):
            grab = True
            after = re.sub(r".*MEMBERS\s+(?:NOT\s+)?PRESENT\s*:?", "", ln, flags=re.I)
            _absorb(after, roster)
            continue
        if grab:
            if re.match(r"\s*(STAFF|OTHERS|PRESIDING|CONDUCTING|SERGEANT|PLEDGE|SERIOUS|"
                        r"MOMENT|CITIZEN|COUNCIL MEMBERS NOT)", ln, re.I) and "MEMBER" not in ln.upper().replace("COUNCIL MEMBERS NOT",""):
                # a NOT PRESENT header continues the roster; other section headers stop it
                if re.search(r"MEMBERS\s+NOT\s+PRESENT", ln, re.I):
                    _absorb(re.sub(r".*NOT\s+PRESENT\s*:?", "", ln, flags=re.I), roster)
                    continue
                grab = False
                continue
            if ln.strip() == "" and roster:
                # blank after names — keep grabbing one blank, stop on section header
                continue
            _absorb(ln, roster)
    return roster


def _absorb(text, roster):
    text = re.sub(r"\((?:Zoom|via Zoom|Electronic(?:ally)?|remote|phone)\)", " ", text, flags=re.I)
    text = re.sub(r"\b(and|None)\b", ",", text, flags=re.I)
    for chunk in text.split(","):
        name = chunk.strip(" .;")
        if not name or not re.search(r"[A-Za-z]", name):
            continue
        toks = re.findall(r"[A-Za-z'’.\-]+", name)
        if len(toks) < 2 or len(toks) > 4:
            continue
        if not toks[0][0].isupper():
            continue
        surname = toks[-1].lower()
        roster.setdefault(surname, " ".join(toks))


def _titlecase(toks):
    out = []
    for t in toks:
        # preserve internal caps (deWolfe, McGuire); else capitalize
        out.append(t if any(c.isupper() for c in t[1:]) else t.capitalize())
    return " ".join(out)


def resolve(raw, roster, groster=None):
    """Map a printed name/surname to a full roster name (per-doc roster, then the
    dataset-global roster, then a titlecased fallback). Fuzzy on surname for typos."""
    toks = re.findall(r"[A-Za-z'’.\-]+", raw)
    if not toks:
        return None
    sur = toks[-1].lower()
    for r in (roster, groster or {}):
        if sur in r:
            return r[sur]
        cands = [full for s, full in r.items()
                 if s[:4] == sur[:4] and abs(len(s) - len(sur)) <= 2]
        if len(set(cands)) == 1:
            return cands[0]
    return _titlecase(toks)


def classify_motion(text):
    t = text.lower()
    if re.search(r"rezon|zoning|zone change|\bzone\b|annex|subdivision|\bplat\b|"
                 r"conditional use|\bcup\b|land use|general plan|master plan|"
                 r"development agreement|overlay|site plan|variance|design review|"
                 r"redevelopment|project area|planned (?:unit )?development|\bpud\b|"
                 r"street vacation|vacat|preliminary|final plat", t):
        return "Land-Use/Zoning"
    if re.search(r"budget amendment|amend.*budget|tentative budget|final budget|"
                 r"adopt.*budget|budget for|appropriat", t):
        return "Budget Amendment"
    if re.search(r"interlocal|inter-local|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t) and "grant the" not in t:
        return "Grant-Funding"
    if re.search(r"appoint|reappoint|advice and consent|liaison|ratify|confirm.*appoint", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|procurement|award the bid|award the contract|"
                 r"professional services|franchise|agreement with|services agreement|"
                 r"enter into an agreement|task order|change order", t):
        return "Contract/Purchase"
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"public hearing", t):
        return "Public Hearing Action"
    if re.search(r"\b(proclamation|recognition|recognize|honou?r|commend|ceremonial|"
                 r"tribute|congratulat)\b", t):
        return "Ceremonial"
    if re.search(r"recess|adjourn|convene|reconvene|closed session|executive session|"
                 r"approve the (?:consent|agenda|minutes|order)|approve.*minutes|"
                 r"\btable\b|continue|postpone|move this item|amend the agenda|"
                 r"unfinished business", t):
        return "Procedural/Administrative"
    return "Other"


def clean_lines(text):
    out = []
    for ln in text.split("\n"):
        s = ln.strip()
        if FOOTER_RE.match(s) or FOOTER_DATE.match(s):
            continue
        if s and WATERMARK_LINE.match(s):
            continue
        ln = VOTE_HDR_FRAG.sub(r"\1", ln)
        ln = WATERMARK_PREFIX.sub(r"\1", ln)
        out.append(ln)
    return out


MOTION_TO = re.compile(r"^\s*Motion\s+to\s+(.+?):?\s*$", re.I)

def find_motion_text(lines, motion_idx):
    """Best motion description: council 'made a motion to X' action, PC 'Motion to X:'
    label, and/or the nearest preceding numbered agenda-item heading."""
    action = ""; label = ""; heading = ""; moved = ""
    # scan up to 140 lines back (a PC "Motion to X:" label can sit 90+ lines above its
    # "Motion:" anchor, across Findings/Conclusions/Conditions lists) but never into
    # the PREVIOUS motion's territory (its vote block / anchor is a hard boundary)
    for j in range(motion_idx - 1, max(0, motion_idx - 140), -1):
        ln = lines[j]
        if MOTION_LINE.match(ln) or VOTE_HEADER.match(ln) or MEMBER_VOTE.match(ln):
            break
        if not moved:
            mv = MOVED_TO.search(ln)
            if mv:
                frag = re.sub(r"^to\s+", "", mv.group(2), flags=re.I)
                moved = re.split(r"\.\s", frag)[0].strip(" .;,")
        if not action:
            m = MADE_MOTION.search(ln)
            if m:
                frag = m.group(2)
                k = j + 1
                while k < motion_idx and lines[k].strip() and not MOTION_LINE.match(lines[k]):
                    frag += " " + lines[k].strip(); k += 1
                action = re.split(r"\.\s", frag)[0].strip(" .;,")
                action = re.sub(r"^to\s+", "", action, flags=re.I)
        if not label:
            lm = MOTION_TO.match(ln)
            if lm and 4 < len(lm.group(1)) < 200 and not SECOND_LINE.match(ln):
                frag = lm.group(1).strip()
                # the PC label sentence often wraps across lines until the "Motion:" line
                k = j + 1
                while k < motion_idx and lines[k].strip() and not MOTION_LINE.match(lines[k]) \
                        and not SECOND_LINE.match(lines[k]) and not VOTE_HEADER.match(lines[k]):
                    frag += " " + lines[k].strip(); k += 1
                label = re.sub(r"\s+", " ", frag).strip(" .:;")
        if not heading:
            hm = ITEM_HEADING.match(ln)
            if hm and len(hm.group(1)) > 8:
                heading = hm.group(1).strip()
        if action and heading:
            break
    if heading and action:
        return f"{heading} — motion to {action}"
    if action:
        return f"motion to {action}"
    if label and heading:
        return f"{heading} — Motion to {label}"
    if label:
        return f"Motion to {label}"
    if heading:
        return heading
    if moved:                       # fallback only — see MOVED_TO
        return f"motion to {moved}"
    return "(motion — description not captured)"


def parse_meeting(text, body, groster=None):
    lines = clean_lines(text)
    roster = build_roster(lines)
    n = len(lines)
    votes = []
    i = 0
    while i < n:
        mm = MOTION_LINE.match(lines[i])
        if not mm:
            i += 1
            continue
        mover_raw = mm.group(1)
        seconder_raw = None
        vote_mode = None
        buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
        # scan forward for SECOND, vote header, and member-vote lines
        j = i + 1
        seen_votes = 0
        blanks = 0
        while j < n and j < i + 40:
            ln = lines[j]
            if MOTION_LINE.match(ln):
                break        # a new MOTION anchor always ends this block: a no-vote
                             # motion (acclamation/consent) must never absorb the NEXT
                             # motion's roll call, and the next anchor must be rescanned
            if ln.strip():
                blanks = 0   # count only CONSECUTIVE blanks (a stripped footer can
                             # leave 2 blank lines mid-roll; preamble blanks must not
                             # accumulate into the block's end-of-roll counter)
            sm = SECOND_LINE.match(ln)
            if sm and seconder_raw is None and vote_mode is None:
                seconder_raw = sm.group(1)
                j += 1
                continue
            vh = VOTE_HEADER.match(ln)
            if vh:
                vote_mode = ("Roll Call" if re.search(r"roll", ln, re.I)
                             else "Voice" if re.search(r"voice", ln, re.I) else "Vote")
                # PC puts the first member vote on the header line: "Vote: Commissioner X – Aye;"
                rest = ln[vh.end():].strip()
                if rest:
                    vm0 = MEMBER_VOTE.match(rest) or MEMBER_VOTE.match("x " + rest)
                    if vm0 and vm0.group(1).lower() not in _NAME_IS_VOTE:
                        sur0, val0 = vm0.group(1), re.sub(r"\s+", " ", vm0.group(2).lower())
                        b0 = VOTE_MAP.get(val0)
                        if b0:
                            full0 = resolve(sur0, roster, groster)
                            if full0 and full0 not in sum(buckets.values(), []):
                                buckets[b0].append(full0); seen_votes += 1
                j += 1
                continue
            vm = MEMBER_VOTE.match(ln)
            if vm and vm.group(1).lower() in _NAME_IS_VOTE:
                vm = None      # "YES    NO" ballot-table header, not a voter
            if vm:
                sur, val = vm.group(1), re.sub(r"\s+", " ", vm.group(2).lower())
                bucket = VOTE_MAP.get(val)
                if bucket:
                    full = resolve(sur, roster, groster)
                    if full and full not in sum(buckets.values(), []):
                        buckets[bucket].append(full)
                        seen_votes += 1
                j += 1
                blanks = 0
                continue
            if ln.strip() == "":
                blanks += 1
                if seen_votes and blanks >= 3:
                    # 2026-07-16: a stripped watermark fragment / page seam can leave a
                    # 3+-blank gap MID-roll (2022-11-17 PC m6 truncated to 1-0 without
                    # this). Break only if the roll does not visibly continue: look
                    # ahead to the next non-blank line and keep going when it is
                    # another member-vote line (never a new MOTION anchor).
                    k = j + 1
                    while k < n and k < i + 40 and lines[k].strip() == "":
                        k += 1
                    nxt = lines[k] if k < n and k < i + 40 else ""
                    if MOTION_LINE.match(nxt) or not MEMBER_VOTE.match(nxt):
                        break
                j += 1
                continue
            # a clerk-typo vote line mid-roll: skip it, do not end the block
            if seen_votes and MANGLED_VOTE.match(ln):
                j += 1
                blanks = 0
                continue
            # a content line after we've started collecting votes -> block ended
            if seen_votes:
                break
            # header seen but no named members yet: a narrative outcome line ends a
            # tally-only vote ("The motion passed with the unanimous consent ...")
            if vote_mode is not None and seen_votes == 0:
                if re.search(r"unanimous|passed|carried|approved|failed|denied|tabled|"
                             r"continued|withdrawn|motion|"
                             r"all\s+(?:present\s+|were\s+)?in\s+favor", ln, re.I):
                    j += 1
                    break
                j += 1
                continue
            j += 1
        if seen_votes >= 1:
            motion_text = find_motion_text(lines, i)
            aye, nay = len(buckets["aye"]), len(buckets["nay"])
            outcome = "Pass" if aye > nay else "Fail"
            votes.append({
                "body": body,
                "motion": motion_text[:600],
                "motion_type": classify_motion(motion_text),
                "result": f"{aye}-{nay} {outcome}",
                "vote_mode": vote_mode or "Roll Call",
                "mover": resolve(mover_raw, roster, groster) if mover_raw else None,
                "seconder": resolve(seconder_raw, roster, groster) if seconder_raw else None,
                "aye": buckets["aye"], "nay": buckets["nay"],
                "abstain": buckets["abstain"], "absent": buckets["absent"],
                "recuse": buckets["recuse"],
                "names_recorded": True,
                "printed_tally": None,
            })
            i = j
        elif vote_mode is not None:
            # a vote header with NO named members -> tally-only (e.g. PC "Vote: The motion
            # passed with the unanimous consent of the Commission."). Capture honestly with
            # names_recorded False and one placeholder row; no fabricated members.
            blob = " ".join(l.strip() for l in lines[i:min(j + 1, n)])
            if re.search(r"unanimous|passed|carried|approved|failed|denied|tabled|"
                         r"continued|withdrawn|all\s+(?:present\s+|were\s+)?in\s+favor",
                         blob, re.I):
                motion_text = find_motion_text(lines, i)
                outcome = ("Fail" if re.search(r"\bfailed\b|\bdenied\b", blob, re.I) else "Pass")
                res = ("Unanimous " + outcome) if re.search(r"unanimous", blob, re.I) else outcome
                votes.append({
                    "body": body, "motion": motion_text[:600],
                    "motion_type": classify_motion(motion_text), "result": res,
                    "vote_mode": vote_mode,
                    "mover": resolve(mover_raw, roster, groster) if mover_raw else None,
                    "seconder": resolve(seconder_raw, roster, groster) if seconder_raw else None,
                    "aye": [], "nay": [], "abstain": [], "absent": [], "recuse": [],
                    "names_recorded": False, "printed_tally": None,
                })
            i = j
        else:
            i += 1
    return votes


def iter_markdown():
    for p in sorted(MINUTES_DIR.rglob("*.md")):
        yield p


def build_global_roster():
    g = {}
    for md in iter_markdown():
        for sur, full in build_roster(clean_lines(md.read_text(encoding="utf-8", errors="replace"))).items():
            g.setdefault(sur, full)
    return g


_MONTHS = {m: i for i, m in enumerate(
    "january february march april may june july august september october "
    "november december".split(), 1)}
EMBED_HDR = re.compile(r"^\s*Planning Commission Meeting Minutes\s*$", re.I)
EMBED_DATE = re.compile(
    r"^\s*(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+"
    r"(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+(\d{1,2}),?\s+(\d{4})", re.I)


def strip_embedded_drafts(text, own_date):
    """A PC minutes PDF can embed the DRAFT minutes it approves as attachments
    (2026-05-07 embeds the 2026-02-19 + 2026-03-05 drafts, watermarked): cut at the
    first embedded full minutes header whose date differs from this file's own date,
    so attached drafts are never carved as this meeting's motions (T3.1(d))."""
    lines = text.split("\n")
    for i in range(5, len(lines)):
        if EMBED_HDR.match(lines[i]):
            for la in lines[i + 1:i + 4]:
                dm = EMBED_DATE.match(la)
                if dm:
                    iso = (f"{int(dm.group(3)):04d}-{_MONTHS[dm.group(1).lower()]:02d}-"
                           f"{int(dm.group(2)):02d}")
                    if own_date and iso != own_date:
                        return "\n".join(lines[:i])
    return text


def main():
    force = "--force" in sys.argv
    groster = build_global_roster()
    processed = skipped = 0
    for md in iter_markdown():
        text = md.read_text(encoding="utf-8", errors="replace")
        meta = parse_header(text)
        date = meta.get("date", "")
        body = meta.get("body", "Council")
        year = date[:4] if date else md.parts[-3]
        week = md.parent.name
        slug = md.stem
        out_dir = VOTES_DIR / year / week
        out_json = out_dir / f"{slug}.json"
        if out_json.exists() and not force:
            skipped += 1
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        votes = parse_meeting(strip_embedded_drafts(text, date), body, groster)
        for k, v in enumerate(votes, 1):
            v["motion_no"] = k
        # provenance (documented trailing 14th all_votes column, repo convention):
        #   'minutes'              = audited primary (the PMN-harvested minutes layer)
        #   'agendacenter_minutes' = recorded minutes recovered 2026-07-13/16 from the
        #                            CivicPlus AgendaCenter ArchivedMinutes slot and
        #                            promoted into this layer (fully audited thereafter)
        doc_source = meta.get("source", "pmn")
        provenance = "minutes" if doc_source == "pmn" else f"{doc_source}_minutes"
        payload = {
            "date": date, "year": int(year) if year.isdigit() else year,
            "body": body, "kind": meta.get("meeting_kind", ""),
            "pmn_file": meta.get("pmn_file", ""),
            "source": str(md.relative_to(ROOT)),
            "source_url": meta.get("source_url", ""),
            "provenance": provenance,
            "votes": votes,
        }
        out_json.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
        processed += 1
    print(f"Processed {processed} meetings -> JSON (skipped {skipped} existing)")
    build_all_votes()


def build_all_votes():
    # 13-column standard + the documented trailing `provenance` column (see main()).
    fields = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
              "result", "mover", "seconder", "member", "vote", "source", "provenance"]
    n = 0
    with ALL_VOTES.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for jp in sorted(VOTES_DIR.rglob("*.json")):
            if jp.name.startswith("_"):
                continue
            data = json.loads(jp.read_text())
            prov = data.get("provenance", "minutes")
            title = f"{data.get('body','')} {data.get('kind','')} Meeting {data['date']}".strip()
            for v in data["votes"]:
                base = [data["date"], data["year"], title, v["body"], v["motion_no"],
                        v["motion"], v["motion_type"], v["result"],
                        v.get("mover") or "", v.get("seconder") or ""]
                emitted = False
                for key, label in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                                   ("absent", "Absent"), ("recuse", "Recuse")):
                    for member in v.get(key, []):
                        w.writerow(base + [member, label, data["source"], prov])
                        n += 1
                        emitted = True
                if not emitted:
                    w.writerow(base + ["", "", data["source"], prov])
                    n += 1
    print(f"Wrote {ALL_VOTES} with {n} data rows")


if __name__ == "__main__":
    main()
