#!/usr/bin/env python3
"""extract_votes.py — grammar-anchored motion + NAMED-vote extractor for Cache County
Council minutes -> legislative/all_votes.csv.

INDEX-DRIVEN (2026-07-29): the documents extracted are exactly the `md_path`s listed in
`legislative/minutes_index.csv` — the catalogue, not `os.walk(minutes/)`.  See
`index_docs()` for the defect this repairs (12 orphan `_2` duplicate files that were
double-counting 107 motions / 640 votes).  Indexed-but-missing and on-disk-but-unindexed
files are both PRINTED every run, never silently dropped.

TWO ERAS (recon.md), dispatched by the markdown front-matter `format:`:

  BORN-DIGITAL (format: text)  — the CENTERPIECE. Full named roll calls, unanimous included:
      Action: [timecode]? Motion made by <role> <mover> to <text>; seconded by <role> <seconder>
      Motion passes.                                  <- verbatim result (may be absent)
      Aye: N <name, name, ...>                         <- named, wraps across lines
      Nay: N <name...>   Absent: N <name...>   Abstain: N <name...>
    -> one CSV row per named member; names_recorded via the presence of member rows.

  SCANNED / OCR (format: ocr)  — TALLY-ONLY recording ceiling, LOW confidence:
      ACTION: Motion by <role> <mover> to <text>. <seconder> seconded the motion.
      The vote was unanimous, 5-0. <names> absent.
    -> one tally-only CSV row (blank member/vote); result verbatim; provenance citysite_ocr.
    Named individual votes appear only on a called division (captured where present).

Never fabricates: a motion with no parseable result keeps result="" ; a tally-only motion
carries no member rows (an honest recording ceiling). Verbatim result strings preserved.
Idempotent. Output schema matches the repo's all_votes.csv (13 cols + provenance).

    python3 extract_votes.py [--verify N]   # --verify prints N random blocks for spot-check
"""
import argparse, csv, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
MIN_DIR = os.path.join(HERE, "minutes")
INDEX = os.path.join(HERE, "minutes_index.csv")
OUT = os.path.join(HERE, "all_votes.csv")
COLS = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
        "result", "mover", "seconder", "member", "vote", "source", "provenance"]

ROLE = (r"(?:Council\s*member|Councilmember|Council\s*Member|Councilor|Vice\s*Chair|"
        r"Chair(?:man|person)?|Executive|Mayor|Mr\.?|Ms\.?|Mrs\.?|Dr\.?)")
NAME = r"[A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,3}"
LABELS = (r"(?:Aye|Nay|Absent|Abstain|Abstained|Recuse[d]?|Excused|Present|Total|"
          r"In Favor|Against|Motion|Action|Discussion|Present)")
# obvious non-name tokens that survive capitalization but must never be a member
BLACKLIST = {"review", "pending action", "public hearings", "rodeo", "rec center",
             "sports courts", "motion passes", "motion fails", "public hearing",
             "total", "present", "in favor", "against", "county"}
VMAP = {"aye": "Aye", "nay": "Nay", "absent": "Absent", "abstain": "Abstain",
        "abstained": "Abstain", "recuse": "Recuse", "recused": "Recuse", "excused": "Excused"}
# A name in OCR'd NARRATIVE prose: a surname, optionally preceded by a first name and/or a
# single-letter initial. Deliberately does NOT admit a multi-letter token ending in "." —
# that is a sentence end, not part of a name (see extract_ocr's seconder capture).
OCR_NAME = r"[A-Z][A-Za-z'\-]+(?:\s+(?:[A-Z]\.|[A-Z][A-Za-z'\-]+)){0,2}"

NON_NAME = re.compile(r"^\d+$|^\d[\d:;.,)Ql-]*$|^[ivxIVX]+$|p\.?m|a\.?m", re.I)


def read_front(text):
    fm = {}
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            mm = re.match(r"\s*([a-z_]+):\s*(.*)", line)
            if mm:
                fm[mm.group(1)] = mm.group(2).strip()
        body = text[m.end():]
    else:
        body = text
    return fm, body


LEADING_JUNK = re.compile(
    r"^(?:Vice[\s-]*Chair(?:man|person)?|Chair(?:man|person)?|Council\s*member|"
    r"Councilmember|Councilor|Council|Executive|County\s+Executive|Mayor|"
    r"Mr\.?|Ms\.?|Mrs\.?|Dr\.?|"
    # agenda-subject words that precede a narrative seconder with no sentence break
    r"Tax|Relief|Budget|Ordinance|Resolution|Agenda|Minutes|Public|Hearing|Consent)\s+",
    re.I)


def clean_name(s):
    s = re.sub(r"\s+", " ", s.replace("’", "'")).strip(" .,;:-–—")
    # fix common born-digital split surnames ("Good lander" -> "Goodlander")
    s = re.sub(r"\bGood lander\b", "Goodlander", s)
    # 2026-07-26: strip leading ROLE words and agenda-subject words that the OCR-era
    # narrative capture drags in ("Vice Chairman Ward", "Tax Relief Potter",
    # "Council Potter"). Repeat because they stack ("County Executive David Zook").
    prev = None
    while prev != s:
        prev = s
        s = LEADING_JUNK.sub("", s).strip()
    # a bare agenda word left standing after the strip is not a person
    if s.lower().rstrip("s") in ("hearing", "tax", "relief", "budget", "ordinance",
                                 "resolution", "agenda", "minute", "consent", "council"):
        return ""
    return s


STOPWORDS = {"none", "the", "motion", "vote", "council", "action", "discussion",
             "aye", "nay", "absent", "abstain", "abstained", "recuse", "recused"}


def name_ok(nm):
    if not nm or NON_NAME.match(nm):
        return False
    if nm.lower() in STOPWORDS or nm.lower() in BLACKLIST:
        return False
    # strip a leaked leading role word ("Councilor Tidwell", "Chair Worthen", "Absent Paul")
    low = nm.lower()
    for w in ("councilor", "councilmember", "council member", "chair", "vice chair",
              "absent", "present", "excused"):
        if low.startswith(w + " "):
            return False   # role/label leaked in — reject (the clean row exists elsewhere)
    # a trailing vote-value word or a leaked single-letter lead is not part of a name
    if re.search(r"\b(Nay|Aye|Passes|Fails|Absent|Present)$", nm):
        return False
    if re.match(r"^[A-Z]\.?\s+[A-Z]", nm):   # stray single-letter lead ("I Kathryn Beus")
        return False
    toks = nm.split()
    if len(toks) > 4:            # a real name is <=4 tokens; longer = prose leak
        return False
    # every token must look like a name token (Capitalized, alpha-ish)
    for t in toks:
        core = t.strip(".'-")
        if not core or not core[0].isupper() or not core.replace("'", "").replace("-", "").isalpha():
            return False
    if len(toks) == 1 and len(nm) < 4:
        return False
    return True


def split_names(blob, limit=None):
    """Names from a label blob. `limit==0` (a printed 'Nay: 0') => no names — the key
    guard against prose leaking past a zero count. A positive count is NOT used to
    truncate (some born-digital 'Aye: N' lines copy-paste the full roster including the
    members the Absent line names — truncating kept the wrong ones; de-conflicting in
    extract_born fixes it). A generous hard cap of 9 still stops runaway prose."""
    if limit == 0:
        return []
    blob = blob.replace("\n", " ")
    out = []
    for part in re.split(r",|;|\band\b", blob):
        nm = clean_name(part)
        if not name_ok(nm):
            # a non-name token terminates the list (prose has begun)
            if out:
                break
            continue
        # a 4-token all-name blob is a missing-comma merge of two 2-token names
        # ("Sandi Goodlander Keegan Garrity") — no Cache councilmember has 4 name tokens.
        toks = nm.split()
        if len(toks) == 4:
            out.append(" ".join(toks[:2])); out.append(" ".join(toks[2:]))
        else:
            out.append(nm)
        if len(out) >= 9:        # safety cap (max roll is ~7-8) — stops prose runaway
            break
    return out


def grab_label(block, label):
    """Return (count, names_text) after `label:` up to the next label / new item.
    count is the printed integer ('Aye: 7' -> 7; 'Nay: O' -> 0) or None."""
    m = re.search(r"\b" + label + r"\s*:?\s*([0-9O]+)?\b", block)
    if not m:
        return None, None
    cnt = m.group(1)
    count = 0 if cnt in ("0", "O") else (int(cnt) if cnt and cnt.isdigit() else None)
    rest = block[m.end():]
    stop = re.search(r"\b" + LABELS + r"\s*:", rest)
    seg = rest[:stop.start()] if stop else rest
    # cut at a blank line, a numbered/lettered agenda item, or a discussion/timecode line
    seg = re.split(r"\n\s*\n|\n\s*[0-9a-z]{1,2}\.\s|\n\s*\d+:\d+|Discussion:", seg)[0]
    return count, seg


RESULT_RE = re.compile(
    r"Motion\s+(?:passes|Passes|passed|Passed|fails|Fails|failed|Failed|carried|"
    r"did not pass|does not pass)\b[^\n.]*\.?", re.I)
TALLY_RES_RE = re.compile(
    r"(?:The\s+vote\s+was\s+unanimous[,\s]*\d+-\d+|"
    r"(?:motion|vote)\s+(?:was\s+)?(?:carried|passed|failed|approved|denied)[^.\n]*\d+-\d+|"
    r"unanimous[,\s]*\d+-\d+|\bvote[d]?\s+\d+-\d+)", re.I)


def extract_born(body):
    """Yield motion dicts for a born-digital doc."""
    txt = body.replace("–", "-")
    # normalize vote-count O -> 0 right after a label
    txt = re.sub(r"(\b(?:Aye|Nay|Absent|Abstain)\s*:)\s*O\b", r"\1 0", txt)
    # anchor on "Action:" lines (the motion marker). Add a "Motion made by" anchor ONLY
    # where no Action: sits within the preceding 80 chars (avoids double-anchoring one
    # motion into a fragment; catches the rare motion printed without an "Action:" line).
    act = [m.start() for m in re.finditer(r"(?m)^\s*Action\s*:", txt)]
    anchors = list(act)
    for m in re.finditer(r"Motion made by", txt):
        if not any(0 <= m.start() - a <= 80 for a in act):
            anchors.append(m.start())
    anchors = sorted(set(anchors))
    for i, a in enumerate(anchors):
        end = anchors[i + 1] if i + 1 < len(anchors) else len(txt)
        # cap the block so the LAST motion never swallows a distant ordinance signature
        # page ("PASSED BY THE COUNTY COUNCIL ... In Favor/Against" checkbox table) — the
        # vote is already captured from the motion's own Aye:/Nay: lines.
        end = min(end, a + 1400)
        block = txt[a:end]
        block = re.split(r"PASSED BY THE COUNTY COUNCIL", block)[0]
        has_vote = re.search(r"\bAye\s*:", block) or re.search(r"Motion made by", block)
        if not has_vote:
            continue
        # mover / motion / seconder
        mover = seconder = None
        motion_text = ""
        mm = re.search(r"Motion made by\s+(?:%s\s+)?(%s)\s+to\s+(.*?)(?:;\s*seconded by|"
                       r"\.\s*Motion|\n\s*Motion|\n\s*Aye)" % (ROLE, NAME), block, re.S)
        if mm:
            mover = clean_name(mm.group(1))
            motion_text = clean_name(mm.group(2))
        sm = re.search(r"seconded by\s+(?:%s\s+)?(None|%s)" % (ROLE, NAME), block)
        if sm:
            if sm.group(1) == "None":
                seconder = None
            else:
                # stop at the first non-name token ("Mark Hurd. Motion" -> "Mark Hurd")
                toks = []
                for t in sm.group(1).split():
                    if name_ok(t) or (toks and t[0:1].isupper()):
                        if t.lower().strip(".") in STOPWORDS:
                            break
                        toks.append(t.strip("."))
                    else:
                        break
                seconder = clean_name(" ".join(toks)) or None
        if not motion_text:
            # "Action: [tc] <text>" fallback (e.g. "Vote for X as Chair")
            am = re.match(r"\s*Action\s*:\s*(?:[\d:;.]+\s+)?(.*)", block)
            if am:
                motion_text = clean_name(am.group(1).split("\n")[0])
        rm = RESULT_RE.search(block)
        result = rm.group(0).strip() if rm else ""
        votes = []
        for lab, canon in (("Aye", "Aye"), ("Nay", "Nay"), ("Absent", "Absent"),
                           ("Abstain(?:ed)?", "Abstain"), ("Recuse[d]?", "Recuse"),
                           ("Excused", "Excused")):
            count, seg = grab_label(block, lab)
            if seg is None:
                continue
            for nm in split_names(seg, limit=count):
                votes.append((nm, canon))
        # DE-CONFLICT (source-template defect fix): a member named in Absent/Excused is
        # NOT a voter — some 'Aye: N' lines copy-paste the full roster, listing the very
        # members the Absent line names. The explicit Absent/Excused designation wins; a
        # name is never both present-voting and absent on the same motion. Also dedupe
        # any exact duplicate (person, value) pairs.
        away = {nm for nm, v in votes if v in ("Absent", "Excused")}
        seen = set(); deconf = []
        for nm, v in votes:
            if v in ("Aye", "Nay", "Abstain", "Recuse") and nm in away:
                continue
            if (nm, v) in seen:
                continue
            seen.add((nm, v)); deconf.append((nm, v))
        votes = deconf
        # drop empty fragments: a block with no votes, no mover, and no motion text is a
        # mis-anchor, not a motion (never emit a hollow row).
        if not votes and not mover and not motion_text:
            continue
        yield dict(motion=motion_text or "(motion text not captured)", result=result,
                   mover=mover, seconder=seconder, votes=votes)


PLACEHOLDER_RE = re.compile(
    r"\[SCANNED\b|OCR\s*\+?\s*vote extraction DEFERRED|OCR pending", re.I)


def extract_ocr(body):
    """Yield tally-only motion dicts for a scanned/OCR doc (recording ceiling)."""
    txt = body
    anchors = [m.start() for m in re.finditer(r"(?mi)^\s*ACTION\s*:|Motion by\s", txt)]
    anchors = sorted(set(anchors))
    for i, a in enumerate(anchors):
        end = anchors[i + 1] if i + 1 < len(anchors) else min(len(txt), a + 900)
        block = txt[a:end]
        mm = re.search(r"Motion by\s+(?:%s\s+)?(%s)\s+to\s+(.*?)(?:\.\s|\n)" % (ROLE, NAME),
                       block, re.S)
        if not mm:
            continue
        mover = clean_name(mm.group(1))
        motion_text = clean_name(mm.group(2))
        # 2026-07-26: NAME admits tokens ending in "." so it crossed the SENTENCE boundary —
        # "…approve the Permit Limits. Ward seconded the motion." captured "Permit Limits.
        # Ward" as the seconder, and the OCR'd 2015-2020 era alone minted ~430 phantom
        # persons that way. OCR_NAME allows a single-letter initial ("Karl B. Ward") but
        # never a multi-letter word ending in a period.
        sm = re.search(r"(%s)\s+seconded the motion" % OCR_NAME, block)
        seconder = clean_name(sm.group(1)) if sm else None
        rm = TALLY_RES_RE.search(block)
        result = rm.group(0).strip() if rm else ""
        # a called division may still name members via "voting aye:" — capture if present
        votes = []
        for lab, canon in (("Aye", "Aye"), ("Nay", "Nay")):
            count, seg = grab_label(block, "voting %s" % lab)
            if seg:
                for nm in split_names(seg, limit=count):
                    votes.append((nm, canon))
        yield dict(motion=motion_text or "(motion text not captured)", result=result,
                   mover=mover, seconder=seconder, votes=votes)


def index_docs():
    """The set of documents to extract is `minutes_index.csv`, NOT the directory.

    2026-07-29 (audit F17). This used to `os.walk(minutes/)`.  The catalogue is the
    canonical statement of what documents exist; the directory is a working area that
    can also hold superseded artefacts.  It did: `fetch_minutes.py`'s collision guard
    compared a re-fetched document's stored `source_url` with `re.search(r"source_url:
    \\s*(\\S+)")` -- and every Cache source_url contains SPACES ("... 12-14-21 APPROVED
    sm.pdf"), so `\\S+` truncated it, the equality never held, and a re-fetch wrote a
    `_2.md` SECOND COPY instead of overwriting in place.  12 such orphans accumulated
    (byte-identical apart from front-matter added later to the indexed twin only); the
    index lists the `_2` form.  Walking the directory therefore extracted 9 of the 12
    meetings twice -- 107 duplicate motions / 640 duplicate votes in the db (~3% / ~5%).

    Returns (paths, missing, unindexed): absolute paths in index order (sorted by
    md_path, which preserves the previous directory-walk ordering and hence motion_id
    stability), indexed paths absent from disk, and on-disk markdown absent from the
    index.  Both gap lists are REPORTED, never silently swallowed.
    """
    indexed = []
    with open(INDEX, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rel = (r.get("md_path") or "").strip()
            if rel:
                indexed.append(rel)
    indexed = sorted(set(indexed))
    paths, missing = [], []
    for rel in indexed:
        p = os.path.join(COUNTY, rel)
        (paths if os.path.exists(p) else missing).append(p if os.path.exists(p) else rel)
    ondisk = set()
    for root, _, files in os.walk(MIN_DIR):
        for fn in files:
            if fn.endswith(".md"):
                ondisk.add(os.path.relpath(os.path.join(root, fn), COUNTY))
    unindexed = sorted(ondisk - set(indexed))
    return paths, missing, unindexed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", type=int, default=0)
    args = ap.parse_args()
    rows = []
    docs, missing, unindexed = index_docs()
    if missing:
        print("!! %d indexed md_path(s) MISSING on disk (not extracted, honest gap):" % len(missing))
        for p in missing:
            print("     ", p)
    if unindexed:
        print("   %d markdown file(s) on disk are NOT in minutes_index.csv and are "
              "DELIBERATELY SKIPPED (see index_docs docstring):" % len(unindexed))
        for p in unindexed:
            print("     ", p)
    n_named = n_tally = n_docs_named = n_docs_pending = 0
    per_doc_blocks = []
    for path in docs:
        text = open(path, encoding="utf-8").read()
        fm, body = read_front(text)
        fmt = fm.get("format", "text")
        prov = fm.get("provenance", "citysite_minutes")
        date = fm.get("meeting_date", "")
        bod = fm.get("body", "Council")
        src = fm.get("md_path") or os.path.relpath(path, COUNTY)
        title = "Cache County Council %s Meeting" % bod
        # 2026-07-26 (audit F1): route on CONTENT, not on the `format` label.
        # `format: scanned` describes the SOURCE, not whether text exists. Skipping every
        # scanned row meant that once a document was OCR'd its text was still never read —
        # 160 of 307 documents contributed zero motions, including 15 inside the named-roll
        # era. Skip only a genuine placeholder body; then pick the grammar by what is
        # actually in the text, because the OCR'd print-to-PDF rasters carry the SAME
        # named form as the born-digital era ("Action: Motion made by …" / "Aye: 6 <names>"),
        # not the tally-only caps form.
        if PLACEHOLDER_RE.search(body) or len(body.strip()) < 400:
            n_docs_pending += 1
            continue
        # The discriminator is the NAMED "Aye: N <names>" roll — and ONLY that. Both eras
        # open a motion with "Action: Motion by …", so testing the Action line routed every
        # OCR'd 2015-2020 document into extract_born, which found no named roll and yielded
        # zero motions for the whole era.
        named_form = re.search(r"(?mi)^\s*Aye\s*:\s*\d+\s+[A-Z]", body)
        gen = extract_born(body) if named_form else extract_ocr(body)
        motions = list(gen)
        doc_named = False
        for mno, mo in enumerate(motions, start=1):
            per_doc_blocks.append((src, mno, mo))
            if mo["votes"]:
                doc_named = True
                for nm, vv in mo["votes"]:
                    rows.append(dict(date=date, year=date[:4], title=title, body=bod,
                                     motion_no=mno, motion=mo["motion"], motion_type="",
                                     result=mo["result"], mover=mo["mover"] or "",
                                     seconder=mo["seconder"] or "", member=nm, vote=vv,
                                     source=src, provenance=prov))
                n_named += 1
            else:
                rows.append(dict(date=date, year=date[:4], title=title, body=bod,
                                 motion_no=mno, motion=mo["motion"], motion_type="",
                                 result=mo["result"], mover=mo["mover"] or "",
                                 seconder=mo["seconder"] or "", member="", vote="",
                                 source=src, provenance=prov))
                n_tally += 1
        if doc_named:
            n_docs_named += 1
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)
    total_motions = n_named + n_tally
    print("== extract_votes: %d docs, %d motions (%d named-roll, %d tally-only), %d vote rows ==" % (
        len(docs), total_motions, n_named, n_tally, sum(1 for r in rows if r["member"])))
    print("   docs with >=1 named roll: %d ; scanned/OCR-pending docs skipped: %d" % (
        n_docs_named, n_docs_pending))
    if args.verify and per_doc_blocks:
        print("\n-- VERIFY sample (%d blocks) --" % args.verify)
        for src, mno, mo in random.sample(per_doc_blocks, min(args.verify, len(per_doc_blocks))):
            print("\n[%s #%d] mover=%r sec=%r result=%r" % (src, mno, mo["mover"],
                  mo["seconder"], mo["result"]))
            print("   motion:", mo["motion"][:120])
            print("   votes :", mo["votes"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
