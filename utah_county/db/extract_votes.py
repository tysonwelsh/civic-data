#!/usr/bin/env python3
"""Extract MOTIONS + VOTES from the Utah County minutes markdown into db/staging/.

Utah County has no machine vote API (recon.md) -> votes are prose-parsed from the minutes,
exactly like the non-Legistar cities. The vote grammar is ERA-SPLIT; this extractor anchors
on the RESULT line of each motion and searches backward for the mover / seconder / subject,
so one code path covers all four grammars:

  * 2015-2016 & born-digital 2017-18: "Commissioner Lee made the motion to X. The motion was
        seconded by Commissioner Graves and carried with the following vote: AYE: <names> /
        NAY: <names>"  -> NAMED roll  (names_recorded=1)
  * 2017-2019 scanned (caps):  "COMMISSIONER GRAVES: MOTION TO X / COMMISSIONER LEE: SECOND /
        ALL IN FAVOR: AYE"       -> tally-only (names_recorded=0)
  * 2020-2026 scanned:  "Motion to X: Commissioner Gordon / Seconded by: Commissioner Beltran /
        Vote: All in favor - Aye / Result: Motion passed 2/0"  -> tally-only
  * Consent agenda: numbered item + "Approved on Consent" / "Stricken on Consent" -> tally-only
  * HAUC: "April made a motion to X. Amelia seconded the motion. The motion passed unanimously."

NEVER fabricates: a tally-only motion stores mover/seconder + the verbatim result line but NO
per-member vote rows (names_recorded=0). Named votes come only from an explicit AYE:/NAY:
block. pypdf inserts stray mid-word spaces on born-digital PDFs ("seconde d", "ca rried"), so
anchors avoid mid-word matching. Writes staging/{persons,meetings,motions,votes}.csv.

DERIVED + idempotent. Run after fetch_legislative.py / fetch_agencies.py.
"""
import csv, os, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
STG = os.path.join(HERE, "staging")
CATALOGS = [
    os.path.join(COUNTY, "legislative", "minutes", "_catalog.csv"),
    os.path.join(COUNTY, "agencies", "housing_authority", "minutes", "_catalog.csv"),
]

# ---- anchors: a line that marks a decided motion ----------------------------------------
RESULT_RE = re.compile(
    r"(carried with the following vote"
    r"|all in favor"                                 # "ALL IN FAVOR: AYE" or "AYE: ALL IN FAVOR"
    r"|the motion (?:passed|failed|carried|did not (?:pass|carry))"
    r"|motion (?:passed|failed|carried)\b"
    r"|result\s*:\s*motion"
    r"|passed unanimously|carried unanimously"
    r"|approved on consent|adopted on consent|stricken on consent|approved by consent"
    r"|motion (?:to strike )?(?:passed|failed) \d"
    # 2026-07-25 (audit F3-ii): the 2019+ OCR era prints its own roll-call header —
    #   "VOTE: 3-0" / "AYE: COMMISSIONER LEE" / "COMMISSIONER AINGE" / …
    # None of the phrases above match it, so entire meetings anchored nothing
    # (2019-01-29 published a full named roll and yielded ZERO motions).
    r"|vote\s*:\s*\d+\s*[-/]\s*\d+"
    # bare verdict+tally line, e.g. "FAILED: 2-1" / "PASSED: 2/0". The pattern above
    # required the word "motion" adjacent, so a whole failed motion could vanish
    # (2018-08-28: "AYE: (COMMISSIONER LEE) / NAY: COMMISSIONER GRAVES AND COMMISSIONER
    # IVIE / FAILED: 2-1" was absent from the db entirely).
    r"|(?:passed|failed)\s*:\s*\d+\s*[-/]\s*\d+"
    r")", re.I)

# Caps-era voter line: "COMMISSIONER LEE" / "CHAIR AINGE" / "VICE-CHAIR IVIE".
CAPS_VOTER_RE = re.compile(
    r"^\s*(?:COMMISSIONER|VICE[\s-]*CHAIR|CHAIRMAN|CHAIR)\s+"
    r"([A-Z][A-Z'\-]+(?:\s+[A-Z][A-Z'\-]+){0,2})\s*$")
# Attendance line, same era: "PRESENT: COMMISSIONER BILL LEE, CHAIR".
# Anchored and length-bounded ON PURPOSE: an unanchored version matched ordinary prose
# ("COMMISSIONER LEE IS TALKING ABOUT…") and produced roster junk like
# {'ABOUT': 'Lee Is Talking About'}.
PRESENT_RE = re.compile(
    r"^\s*(?:PRESENT\s*:\s*)?(?:COMMISSIONER|VICE[\s-]*CHAIR|CHAIRMAN|CHAIR)\s+"
    r"([A-Z][A-Z'.\-]+(?:\s+[A-Z][A-Z'.\-]+){1,3})"
    r"\s*(?:,\s*(?:VICE[\s-]*CHAIR|CHAIRMAN|CHAIR))?\s*$")

def caps_roster(lines):
    """surname -> printed full name, harvested from THIS meeting's attendance block.

    The 2019+ roll calls name voters by surname only ("COMMISSIONER LEE") while the
    PRESENT block prints the full name ("COMMISSIONER BILL LEE, CHAIR"). Resolving
    per-file is the repo's proven pattern (alta, slc) and avoids inventing a surname-only
    person that would collide with the Title-Case era's "William C. Lee".
    """
    roster = {}
    # Scan the whole document, not just the head: multi-part meetings can begin mid-document
    # ("Page 18") with the attendance block in another part, or none at all.
    for line in lines:
        if len(line) > 70:                 # attendance lines are short; prose is not
            continue
        m = PRESENT_RE.match(line)
        if not m:
            continue
        toks = m.group(1).split()
        # "COMMISSIONER IVIE SECONDS MOTION." also fits the attendance shape — reject any
        # capture containing an action word, so the roster holds people, not sentences.
        if any(re.sub(r"\W", "", t).upper() in NON_NAME_TOKENS for t in toks):
            continue
        full = " ".join(w if w.endswith(".") else w.capitalize() for w in toks)
        roster.setdefault(toks[-1].upper(), full)
    return roster

NON_NAME_TOKENS = {
    "SECOND", "SECONDS", "SECONDED", "MOTION", "MOTIONS", "MAKES", "MAKE", "MADE",
    "MEETING", "BOARD", "ABSENT", "EXCUSED", "PRESENT", "AYE", "NAY", "VOTE", "VOTES",
    "APPROVED", "ASKED", "SAID", "STATED", "ANSWERED", "REPLIED", "IS", "TO", "THAT",
    "AND", "THE", "WHO", "ANOTHER", "ABOUT", "CONCERN", "CONCERNS", "QUESTION",
    "QUESTIONS", "INDICATED", "CLARIFY", "TALKING", "GIVING", "TERM", "PROJECT", "OKAY",
    "YES", "SO", "ADDITIONS", "BUILDINGS", "FEES", "REQUEST", "CONSCIOUS", "MOTIO",
}

# Corpus-wide surname fallback, for the meetings whose minutes carry no attendance block
# (multi-part documents that begin mid-meeting). Built lazily from every file that DOES
# have one, so it is derived from the source, never hand-authored.
_CORPUS_ROSTER = None
def corpus_roster():
    global _CORPUS_ROSTER
    if _CORPUS_ROSTER is not None:
        return _CORPUS_ROSTER
    import collections
    seen = collections.defaultdict(collections.Counter)
    for f in glob.glob(os.path.join(COUNTY, "legislative", "minutes", "*", "*.md")):
        try:
            _fm, body = read_front_matter(open(f, encoding="utf-8", errors="replace").read())
        except Exception:
            continue
        for sur, full in caps_roster(relineate(body).splitlines()).items():
            seen[sur][full] += 1
    # keep only surnames seen on >=3 attendance lines — enough to exclude one-off OCR noise
    _CORPUS_ROSTER = {s: c.most_common(1)[0][0] for s, c in seen.items()
                      if sum(c.values()) >= 3}
    return _CORPUS_ROSTER

FAIL_RE = re.compile(r"fail|denied|did not (pass|carry)|stricken", re.I)

# mover patterns (return (name, motion_text_or_None))
MOVER_PATS = [
    re.compile(r"Commissioner\s+([A-Z][A-Za-z.'\-]+)\s+made\s+(?:a|the)\s+motion\s+to\s+(.+)", re.I),
    re.compile(r"Motion\s+to\s+(.+?)\s*:\s*Commissioner\s+([A-Z][A-Za-z.'\-]+)", re.I),  # (text, name) swapped below
    re.compile(r"COMMISSIONER\s+([A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,2})\s*:\s*MOTION\s+TO\s+(.+)"),  # caps, 1-3 name tokens
    re.compile(r"\b([A-Z][a-z]+)\s+made\s+a\s+motion\s+to\s+(.+)"),                       # HAUC first-name
]
SECOND_PATS = [
    # tolerant of pypdf mid-word spaces ("seconde d by") via second[a-z ]{0,4}by
    re.compile(r"second[a-z ]{0,4}by\s*:?\s*Commissioner\s+([A-Z][A-Za-z.'\-]+)", re.I),
    re.compile(r"COMMISSIONER\s+([A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,2})\s*:\s*SECOND"),  # caps, 1-3 name tokens

    re.compile(r"\b([A-Z][a-z]+)\s+seconded\b"),                                          # HAUC first-name
]
ITEM_RE = re.compile(r"^\s*(\d{1,2})[.)]\s+([A-Z].{6,})")          # numbered agenda item heading
VOTE_CAT_RE = re.compile(r"^\s*(AYE|NAY|ABSTAIN|ABSTAINED|ABSENT|EXCUSED|RECUSED|OPPOSED)\s*:\s*(.*)$", re.I)
# a voter name in these minutes is Title-Case First [M.] Last (never ALL-CAPS section labels)
NAME_LINE_RE = re.compile(r"^\s*([A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z'\-]+){1,2})\s*$")
# cut a captured motion clause at the point the sentence turns to the second/result
MTEXT_CUT_RE = re.compile(
    r"\.?\s*(?:the motion was second|seconded by|and (?:was )?(?:unanimously )?carried"
    r"|and (?:the motion )?(?:passed|failed)|:\s*Commissioner|Seconded by|COMMISSIONER|"
    r"the motion (?:passed|carried|failed)|\.\s+The motion)", re.I)
CAT_MAP = {"aye": "Aye", "nay": "Nay", "opposed": "Nay", "abstain": "Abstain",
           "abstained": "Abstain", "absent": "Absent", "excused": "Excused", "recused": "Recuse"}


def relineate(text):
    """Some OCR minutes (esp. 2024+) merge columns so many motions land on ONE long line
    ("...MOTION TO APPROVE COMMISSIONER GORDON: SECOND ALL IN FAVOR: AYE PASSED: 2/0 Agreement:
    2024-529 8. APPROVE AND..."). Insert line breaks at motion-cycle boundaries so the
    line-based anchor logic sees one motion per segment. Idempotent on already-lineated text."""
    t = text
    t = re.sub(r"\s+(\d{1,2}\.\s+[A-Z]{3,})", r"\n\1", t)                       # before numbered items
    t = re.sub(r"\s*(COMMISSIONER\s+[A-Z][A-Za-z. ]{2,30}?:\s*(?:MOTION|SECOND))", r"\n\1", t)
    t = re.sub(r"(APPROVED ON CONSENT|STRICKEN ON CONSENT|ADOPTED ON CONSENT)", r"\n\1\n", t, flags=re.I)
    # Split each AYE:/NAY: verdict onto its own line, KEEPING any trailing
    # "(COMMISSIONER X AND COMMISSIONER Y)" attached — that parenthetical is the only
    # named-voter list the 2020-2024 era prints, and the divided votes name BOTH sides:
    #   "AYE: THOSE IN FAVOR (…) NAY: THOSE OPPOSED (COMMISSIONER LEE) PASSED: 2/1"
    # OCR wraps a voter parenthetical across lines ("(COMMISSIONER POWERS GARDNER AND\n
    # COMMISSIONER SAKIEVICH)"), which defeats the same-line paren match below. Collapse
    # whitespace INSIDE parentheses first so each list stays on one line.
    t = re.sub(r"\(([^()]{0,240}?)\)",
               lambda m: "(" + re.sub(r"\s+", " ", m.group(1)).strip() + ")", t, flags=re.S)
    t = re.sub(r"(ALL IN FAVOR\s*:\s*AYE)", r"\n\1\n", t, flags=re.I)
    t = re.sub(r"((?:AYE|NAY)\s*:\s*(?:ALL|THOSE)\s+(?:IN FAVOR|OPPOSED)(?:\s*\([^)\n]*\))?)",
               r"\n\1\n", t, flags=re.I)
    t = re.sub(r"(PASSED\s*:\s*\d+\s*/\s*\d+|FAILED\s*:\s*\d+\s*/\s*\d+)", r"\n\1\n", t, flags=re.I)
    t = re.sub(r"\s+(Agreement|Ordinance|Resolution)\s*:\s*(20\d\d-\d+)", r"\n\1: \2", t)
    return t


def clean(s):
    return re.sub(r"\s+", " ", (s or "")).strip().strip(".").strip()


def clean_name(s):
    """Sanitize a captured mover/seconder name. In caps OCR the capture can bridge a sentence
    into the next speaker ("AINGE-NO. COMMISSIONER SAKIEVICH"); keep only the trailing name
    after any embedded 'COMMISSIONER' or sentence period, capped to <=3 tokens."""
    s = re.sub(r"\s+", " ", (s or "")).strip()
    if not s:
        return ""
    if re.search(r"COMMISSIONER", s, re.I):
        s = re.split(r"COMMISSIONER", s, flags=re.I)[-1]
    s = s.split(".")[-1] if "." in s and not re.match(r"^[A-Z]\.$", s.strip()) else s
    toks = [t for t in s.replace(".", " ").split() if t]
    return " ".join(toks[-3:]).strip()


def clean_mtext(s):
    s = re.sub(r"\s+", " ", (s or "")).strip()
    m = MTEXT_CUT_RE.search(s)
    if m:
        s = s[:m.start()]
    return s.strip().strip(".").strip()


def read_front_matter(md_text):
    m = re.match(r"---\n(.*?)\n---\n", md_text, re.S)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1); fm[k.strip()] = v.strip()
        md_text = md_text[m.end():]
    return fm, md_text


def find_mover(window):
    """window = lines from just after the previous motion up to the result line. Return the
    mover CLOSEST to the result (last match), as (name, text)."""
    flat = re.sub(r"\s+", " ", " ".join(window))
    best = None; best_pos = -1
    for i, pat in enumerate(MOVER_PATS):
        for m in pat.finditer(flat):
            if m.start() >= best_pos:
                best_pos = m.start()
                best = (clean_name(m.group(2)), clean_mtext(m.group(1))) if i == 1 \
                    else (clean_name(m.group(1)), clean_mtext(m.group(2)))
    return best if best else (None, None)


def find_seconder(window):
    flat = re.sub(r"\s+", " ", " ".join(window))
    best = None; best_pos = -1
    for pat in SECOND_PATS:
        for m in pat.finditer(flat):
            if m.start() >= best_pos:
                best_pos = m.start(); best = clean_name(m.group(1))
    return best


def nearest_item(lines, anchor_idx):
    for j in range(anchor_idx, max(anchor_idx - 40, -1), -1):
        m = ITEM_RE.match(lines[j])
        if m:
            return clean(m.group(2))[:240]
    return None


def parse_named_votes(lines, anchor_idx, roster=None):
    """From an 'AYE:'/'NAY:' block starting at/after anchor. Returns {name: value} or {}.

    `roster` is this meeting's caps-era surname->full-name map (see caps_roster). When
    supplied, ALL-CAPS "COMMISSIONER LEE" voter lines resolve through it; without it the
    2019+ era yields nothing, because ok_name() rejects every ALL-CAPS line as a label.
    """
    votes = {}
    roster = roster or {}
    # Locate the AYE: line near the anchor. Usually it IS the anchor or follows it, but
    # when the verdict line itself anchors ("FAILED: 2-1") the roll sits ABOVE it —
    # 2018-08-28 prints "AYE: (COMMISSIONER LEE)" / "NAY: COMMISSIONER GRAVES AND
    # COMMISSIONER IVIE" / "FAILED: 2-1" — so search backward as well.
    start = None
    for j in range(anchor_idx, min(anchor_idx + 4, len(lines))):
        if re.search(r"^\s*AYE\s*:", lines[j], re.I):
            start = j; break
    if start is None:
        for j in range(anchor_idx - 1, max(-1, anchor_idx - 7), -1):
            if re.search(r"^\s*AYE\s*:", lines[j], re.I):
                start = j; break
    if start is None:
        return {}
    cat = None
    def caps_name(s):
        """Resolve an ALL-CAPS 'COMMISSIONER <SURNAME>' voter line, or None."""
        s = s.strip().rstrip(".,;")
        m = CAPS_VOTER_RE.match(s)
        if not m:
            # inside a parenthetical list the token may lack the title ("… AND SAKIEVICH")
            if roster and re.fullmatch(r"[A-Z][A-Z'\-]{2,}", s) and s.upper() in roster:
                return roster[s.upper()]
            return None
        printed = m.group(1).strip()
        return roster.get(printed.split()[-1].upper()) or printed.title()

    def ok_name(s):
        s = s.strip()
        if not s or s.lower() == "none":
            return False
        if s.isupper():                      # ALL-CAPS = section/disposition label, not a voter
            return False                     # (caps VOTERS are handled by caps_name above)
        if re.search(r"^commissioner\b|page|minutes|ordinance|agreement|resolution"
                     r"|continued|utah county|regular agenda|work session|public comment"
                     r"|all in favor|unanimous|^aye$|^nay$|consent|motion", s, re.I):
            return False
        return bool(NAME_LINE_RE.match(s))
    for j in range(start, min(start + 16, len(lines))):
        line = lines[j]
        mc = VOTE_CAT_RE.match(line)
        if mc:
            cat = CAT_MAP.get(mc.group(1).lower(), None)
            rest = clean(mc.group(2))
            if rest:
                # 2020-2024 parenthetical form: "AYE: ALL IN FAVOR (COMMISSIONER LEE AND
                # COMMISSIONER SAKIEVICH)". TRAP: the clerk also writes
                # "AYE: THOSE OPPOSED (COMMISSIONER LEE)" — the AYE: prefix is a fixed
                # label and the real direction is in the PHRASE, so read the phrase and
                # only fall back to the prefix when it says neither.
                par = re.search(r"\(([^)]*COMMISSION[^)]*)\)", rest, re.I)
                if par:
                    if re.search(r"\bopposed\b|\bagainst\b", rest, re.I):
                        pcat = "Nay"
                    elif re.search(r"\bin\s+favor\b", rest, re.I):
                        pcat = "Aye"
                    else:
                        pcat = cat
                    for chunk in re.split(r",|\band\b|&", par.group(1), flags=re.I):
                        cn = caps_name(chunk.strip())
                        if cn:
                            votes[cn] = pcat
                    continue
                # "NAY: COMMISSIONER GRAVES AND COMMISSIONER IVIE" — several voters on the
                # category line itself, no parentheses.
                if len(re.findall(r"COMMISSIONER|CHAIR", rest, re.I)) > 1:
                    for chunk in re.split(r",|\band\b|&", rest, flags=re.I):
                        cn = caps_name(chunk.strip())
                        if cn:
                            votes[cn] = cat
                    continue
                cn = caps_name(rest)
                if cn:
                    votes[cn] = cat
                elif ok_name(rest):
                    votes[rest] = cat
            continue
        if cat is None:
            continue
        if not line.strip():
            # blank lines occur INSIDE a caps-era block ("AYE:" / "" / "COMMISSIONER LEE"),
            # so a blank must not terminate it — only a non-name with content does.
            continue
        cn = caps_name(line)
        if cn:
            votes[cn] = cat
        elif ok_name(line):
            votes[clean(line)] = cat
        else:
            if j > start:                    # first non-name after a category ends the block
                break
    return votes


def main():
    os.makedirs(STG, exist_ok=True)
    catalog = []
    for cp in CATALOGS:
        if os.path.exists(cp):
            catalog += list(csv.DictReader(open(cp, encoding="utf-8")))
    print("catalog rows:", len(catalog))

    meetings = []; motions = []; votes = []
    mtg_id = mot_id = vote_id = 0
    for row in sorted(catalog, key=lambda r: (r["date"], r["body"])):
        md_path = os.path.join(COUNTY, row["md_path"])
        if not row["md_path"] or not os.path.exists(md_path):
            continue
        fm, text = read_front_matter(open(md_path, encoding="utf-8").read())
        lines = relineate(text).splitlines()
        roster = dict(corpus_roster()); roster.update(caps_roster(lines))
        #  ^ this meeting's own attendance block wins; corpus map fills documents that lack one
        mtg_id += 1
        meetings.append({"meeting_id": mtg_id, "date": row["date"], "body": row["body"],
                         "md_path": row["md_path"], "provenance": row["provenance"],
                         "kind": row.get("kind", ""), "source_url": row.get("source_url", "")})
        mno = 0
        prev_anchor = -99
        last_motion = None
        for i, line in enumerate(lines):
            if not RESULT_RE.search(line):
                continue
            # adjacent anchors (<=2 lines) belong to ONE motion — e.g. the 2020-era pair
            # "Vote: All in favor - Aye" then "Result: Motion passed 2/0". Merge: prefer the
            # numeric "Result:" line for result_raw/outcome; never emit a second motion.
            # 2026-07-25: measure adjacency in NON-BLANK lines and allow the whole vote
            # block to sit between the two anchors. relineate() puts "AYE: …", the voter
            # names and "PASSED: 2/0" on separate lines with blanks between, so a fixed
            # 2-line window treated the verdict line as a NEW motion — adding the bare
            # "PASSED:/FAILED: n-m" anchor inflated the corpus by ~1,670 phantom motions.
            gap = [x for x in lines[prev_anchor + 1: i] if x.strip()]
            block_only = all(
                re.match(r"^\s*(AYE|NAY|ABSTAIN|ABSENT|EXCUSED|RECUSED|OPPOSED)\s*:", x, re.I)
                or CAPS_VOTER_RE.match(x.strip()) or NAME_LINE_RE.match(x.strip())
                or re.match(r"^\s*\(?\s*COMMISSIONER", x, re.I)
                for x in gap)
            if last_motion is not None and (i - prev_anchor <= 2 or (len(gap) <= 6 and block_only)):
                prev_anchor = i
                if re.search(r"result\s*:\s*motion|passed\s*:?\s*\d|failed\s*:?\s*\d", line, re.I):
                    last_motion["result_raw"] = clean(line)[:300]
                    if re.search(r"fail|denied|did not", line, re.I):
                        last_motion["outcome"] = "Fail"
                continue
            result_raw = clean(line)[:300]
            consent = bool(re.search(r"consent", line, re.I))
            # bound the backward window so a previous motion's mover/seconder never bleeds in
            win_start = max(prev_anchor + 1, i - 14)
            window = lines[win_start: i + 1]
            prev_anchor = i
            mover, mtext = (None, None) if consent else find_mover(window)
            seconder = None if consent else find_seconder(window)
            subject = nearest_item(lines, i)
            motion_text = clean(mtext) if mtext else (subject or "")
            # a bare-verb motion clause ("APPROVE", "STRIKE", "ADJOURN") is uninformative — prefer
            # the numbered agenda-item subject as the motion text where we have it
            if subject and len(motion_text) < 12 and not consent:
                motion_text = "%s — %s" % (motion_text, subject) if motion_text else subject
            if not motion_text:
                motion_text = result_raw
            named = parse_named_votes(lines, i, roster) if not consent else {}
            outcome = "Fail" if FAIL_RE.search(line) and not re.search(r"strike|stricken", line, re.I) else "Pass"
            if re.search(r"stricken|strike", line, re.I):
                outcome = "Pass"      # a motion to strike that carried
            mno += 1; mot_id += 1
            last_motion = {
                "motion_id": mot_id, "meeting_id": mtg_id, "body": row["body"],
                "motion_no": mno, "motion_text": motion_text[:400],
                "subject": subject or "", "result_raw": result_raw,
                "outcome": outcome, "mover": mover or "", "seconder": seconder or "",
                "names_recorded": 1 if named else 0,
                "provenance": row["provenance"], "source_file": row["md_path"],
                "kind": "consent" if consent else "motion"}
            motions.append(last_motion)
            for nm, val in named.items():
                if not val:
                    continue
                vote_id += 1
                votes.append({"vote_id": vote_id, "motion_id": mot_id,
                              "person": nm, "vote_value": val})

    # write staging
    def w(name, rows, cols):
        with open(os.path.join(STG, name), "w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=cols); wr.writeheader()
            for r in rows:
                wr.writerow(r)
    w("meetings.csv", meetings, ["meeting_id", "date", "body", "md_path", "provenance", "kind", "source_url"])
    w("motions.csv", motions, ["motion_id", "meeting_id", "body", "motion_no", "motion_text",
      "subject", "result_raw", "outcome", "mover", "seconder", "names_recorded",
      "provenance", "source_file", "kind"])
    w("votes.csv", votes, ["vote_id", "motion_id", "person", "vote_value"])

    named_m = sum(1 for m in motions if m["names_recorded"])
    print("meetings=%d  motions=%d (named=%d tally=%d)  votes=%d"
          % (len(meetings), len(motions), named_m, len(motions) - named_m, len(votes)))


if __name__ == "__main__":
    main()
