#!/usr/bin/env python3
"""Extract motions + NAMED roll-call votes from the Weber County Commission minutes
markdown (legislative/minutes/**/*.md) into db/staging/ CSVs for build_db.py.

Weber's roll-call grammar is highly regular and NAMED even on unanimous motions:

    Commissioner Harvey moved to approve Resolution 12-2026 ...; Commissioner Bolos seconded.
    [Roll Call Vote:] Chair Froerer – aye; Commissioner Harvey – aye; Commissioner Bolos – aye

So a motion is anchored by "<title Name> moved ... ; <title Name> seconded." and the roll
call is the next line of "<title> <Name> [–-] <value>;" pairs. result_raw is the roll-call
line VERBATIM; outcome is derived (aye vs nay). Resolution / ordinance / contract numbers
printed with the motion are captured in staging/motion_refs.csv for later ordinance linkage.

Never fabricates: a motion with no roll call gets names_recorded=0 (source printed no names).
"""
import csv, os, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
MIN = os.path.join(COUNTY, "legislative", "minutes")
STG = os.path.join(HERE, "staging")

TITLE = r"(?:Chair|Vice[ -]?Chair|Commissioner|Comm\.)"
NAME = r"([A-Z][A-Za-z'’.-]+)"
DASH = r"[–—-]"  # en/em dash or hyphen
VAL_WORDS = r"aye|nay|yes|no|abstain|abstained|absent|recuse|recused|excused|conflict|present"

# Visiting (non-Weber) officials whose votes appear in Weber minutes only because of a JOINT
# meeting with another county — their votes must NOT be attributed to Weber. Confirmed Davis
# County commissioners from the shared Weber/Davis boundary-adjustment meetings (2020-10-14,
# 2023-08-01, where the roll call intermixes both boards on one line). Keyed by last name.
# NOTE: "Elliott" is deliberately NOT excluded — it is ambiguous (Davis Comm. Randy Elliott vs
# Weber Surveyor Max Elliott) and Elliott was excused at 2020-10-14 (cast no vote anyway).
VISITING = {"kamalu", "stevenson"}

VMAP = {"aye": "Aye", "yes": "Aye", "nay": "Nay", "no": "Nay",
        "abstain": "Abstain", "abstained": "Abstain", "absent": "Absent",
        "recuse": "Recuse", "recused": "Recuse", "conflict": "Recuse",
        "excused": "Excused", "present": "Present"}

# a single roll-call vote pair, e.g. "Commissioner Harvey – aye"
PAIR_RE = re.compile(TITLE + r"\s+" + NAME + r"\s*" + DASH + r"\s*(" + VAL_WORDS + r")\b",
                     re.I)
# joint Weber+Davis boundary meetings print a SECOND roll call for the OTHER county
# ("Davis County: Commissioner Stevenson – aye; …") — never attribute those to Weber.
OTHER_COUNTY_RE = re.compile(r"^\s*(?!Weber\b)[A-Z][a-z]+\s+County\s*:", )
# the EARLY-ERA roll call (mostly 2015-2017): "Roll Call Vote:" header then ONE member per
# line, name-to-value joined by dot leaders — "Commissioner Bell .......... aye".
LEADER_RE = re.compile(
    r"^\s*(?:Chair|Vice[ -]?Chair|Commissioner|Comm\.)\s+([A-Z][A-Za-z'’-]+)[.\s]{2,}("
    + VAL_WORDS + r")\s*$", re.I)
# the motion anchor: "<title> <Name> moved ..."
MOVED_RE = re.compile(TITLE + r"\s+" + NAME + r"\s+(?:moved|move[sd]?)\b", re.I)
SECOND_RE = re.compile(TITLE + r"\s+" + NAME + r"\s+second", re.I)

# A motion that DIES FOR LACK OF A SECOND terminates right there — it never reaches a roll
# call. Weber's clerk prints the died motion, its terminator, and the SUBSTITUTE motion that
# follows inside ONE hard-wrapped paragraph, so before the 2026-07-31 fix the died motion
# swallowed the SUBSTITUTE's roll call and displayed as a PASS with named ayes
# (2018-07-03 #6, 2018-09-11 #6 and #7, 2018-12-18 #13).
DIED_RE = re.compile(
    r"motion\s+(?:died|dies|failed|lost)\s+for\s+(?:the\s+)?lack\s+of\s+a\s+second\.?", re.I)
# The substitute motion printed after a died motion is anchored more loosely than the
# ordinary "<Title> <Name> moved", because the clerk writes it several ways: "made a
# substitute motion", "made a motion", "<Name> felt … and moved to …". Applied ONLY to the
# line immediately following a died motion (and allowed to span that line's wrap onto the
# next), so the corpus-wide motion anchor is unchanged.
SUBST_RE = re.compile(
    TITLE + r"\s+" + NAME + r"(?:[^;]{0,220}?\s+and)?\s+"
    r"(?:moved|move[sd]?|made\s+an?\s+(?:substitute\s+|amended\s+|friendly\s+)?motion)\b",
    re.I)

RES_RE = re.compile(r"\bRESOLUTION\s+(?:NO\.?\s*)?(\d{1,3}-\d{4}|\d{4}-\d{1,4})", re.I)
ORD_RE = re.compile(r"\bORDINANCE\s+(?:NO\.?\s*)?(\d{1,3}-\d{4}|\d{4}-\d{1,4}|CO?-?\d+-\d+)", re.I)
CONTRACT_RE = re.compile(r"\b([A-Z]{1,3}-\d{4}-\d{2,5})\b")
READING_RE = re.compile(r"\b(First|Second|Final|Third)\s+Reading\b", re.I)


def strip_front(txt):
    if txt.startswith("---"):
        parts = txt.split("---", 2)
        if len(parts) == 3:
            return parts[2]
    return txt


def norm(v):
    return VMAP.get(v.strip().lower(), "")


def split_at_died(lines):
    """Put every "motion died for lack of a second" phrase at the END of its own line.

    The minutes are PDF text with hard wraps, so a died motion, its terminator and the
    substitute motion that follows routinely share one physical line ("… Motion died for
    lack of a second. Chair" / "Harvey moved to adopt …"), and a line-at-a-time motion
    anchor cannot see the substitute at all. Normalising the phrase onto one line and
    breaking after it makes BOTH motions addressable. Whitespace only — no text added,
    removed or reworded; motion_text stays verbatim.
    """
    text = "\n".join(lines)
    text = DIED_RE.sub(lambda m: re.sub(r"\s+", " ", m.group(0)) + "\n", text)
    return text.split("\n")


def is_vote_line(line):
    """A genuine roll call: >=2 member-value pairs, OR a single pair right after a motion."""
    pairs = PAIR_RE.findall(line)
    return len(pairs), pairs


def parse_meeting(path):
    body = strip_front(open(path, encoding="utf-8").read())
    lines = split_at_died(body.split("\n"))
    iso = os.path.basename(path)[:10]

    # commissioners header → lastname:fullname (improves person names)
    fullnames = {}
    m = re.search(r"COMMISSIONERS?:\s*(.+)", body)
    if m:
        seg = m.group(1).split("STAFF")[0]
        for full in re.split(r",|\band\b", seg):
            full = re.sub(r"\s+", " ", full).strip(" .")
            full = re.sub(r'["“”].*?["“”]', "", full).strip()  # drop nicknames
            if full and " " in full:
                fullnames[full.split()[-1].lower()] = full

    motions, votes, refs = [], [], []
    mno = 0
    i = 0
    n = len(lines)
    # Non-blank lines still eligible for the loose SUBSTITUTE-motion anchor. Opened by a
    # died-for-lack-of-a-second motion and closed by the next motion registered; the clerk
    # usually prints the substitute in the very next clause, but can put a sentence of
    # staff advice in between (2020-06-23 Taylor Landing).
    died_window = 0
    while i < n:
        line = lines[i]
        relaxed = died_window > 0
        if relaxed:
            # substitute motion: allow the looser anchor, and let it span this line's wrap
            two = line + " " + (lines[i + 1] if i + 1 < n else "")
            mv = SUBST_RE.search(two)
            if mv and mv.start() > len(line):
                mv = None  # the anchor must BEGIN on this line
            anchor_re = SUBST_RE
        else:
            mv = MOVED_RE.search(line)
            anchor_re = MOVED_RE
        # only treat as a motion if a "second" appears within this + next ~4 lines
        # (or the motion explicitly DIED for lack of a second — those never get one)
        if mv:
            window = " ".join(lines[i:i + 5])
            sec = SECOND_RE.search(window)
            # motion_text: from "moved" through the seconder clause (or end of window)
            start = mv.start()
            wtext = " ".join(l.strip() for l in lines[i:i + 6])
            wmv = anchor_re.search(wtext)
            mtext = wtext[wmv.start():] if wmv else window
            # trim at the seconder's "seconded." for a clean verbatim motion
            cut = re.search(r"second(?:ed)?\.?", mtext, re.I)
            # DIED = the terminator is printed before any seconder clause in this motion
            dm = DIED_RE.search(mtext)
            secm_in = SECOND_RE.search(mtext)
            died = bool(dm) and (secm_in is None or secm_in.start() > dm.start())
            if not sec and not died:
                if relaxed and line.strip():
                    died_window -= 1
                i += 1
                continue
            died_window = 8 if died else 0
            mno += 1
            mover = mv.group(1)
            secm = SECOND_RE.search(mtext) or SECOND_RE.search(window)
            seconder = "" if died else (secm.group(1) if secm else "")
            motion_text = re.sub(
                r"\s+", " ", mtext[: dm.end()] if died
                else (mtext[: cut.end()] if cut else mtext)).strip()

            vote_line, vpairs, hit_next_motion = "", [], False
            j = i
            if died:
                # No roll call is scanned for at all: a motion that died for lack of a
                # second never reached a vote. Resume on the line AFTER the one the
                # terminator ends, which is where the substitute motion begins.
                for t in range(i, min(n, i + 6)):
                    d2 = DIED_RE.search(lines[t])
                    if d2 and d2.end() >= len(lines[t].rstrip()):
                        j = t
                        break

            # find the roll call after the motion — TWO grammars:
            #  (a) single line, semicolon-separated, dash-joined (modern)
            #  (b) "Roll Call Vote:" header + one dot-leader member line each (early era)
            # A motion can be followed by pages of discussion before its roll call
            # (2020-01-07 rezone: 12 lines down), so scan generously — but STOP at the next
            # motion so a genuinely-unvoted motion never steals the following one's roll call.
            scanned = 0
            while not died and j < n and scanned < 60:
                cand = lines[j]
                if j != i and OTHER_COUNTY_RE.match(cand):
                    j += 1  # skip another county's roll call, keep scanning for Weber's
                    continue
                if j != i and MOVED_RE.search(cand) and (
                        SECOND_RE.search(" ".join(lines[j:j + 5]))
                        or DIED_RE.search(" ".join(lines[j:j + 5]))):
                    hit_next_motion = True
                    break  # reached the NEXT motion — this one had no roll call
                if j != i:
                    lm = LEADER_RE.match(cand)
                    if lm:  # (b) collect the consecutive dot-leader member lines
                        block, parts, k = [], [], j
                        while k < n:
                            lm2 = LEADER_RE.match(lines[k])
                            if lm2:
                                block.append((lm2.group(1), lm2.group(2)))
                                parts.append(re.sub(r"[.\s]{2,}", " – ",
                                                    lines[k].strip()))
                                k += 1
                            else:
                                break
                        vpairs = block
                        vote_line = "; ".join(parts)
                        break
                    cnt, pairs = is_vote_line(cand)  # (a) single-line
                    if cnt >= 2:
                        vote_line = cand.strip()
                        vpairs = pairs
                        break
                if cand.strip():
                    scanned += 1
                j += 1

            weber_pairs = [(nm, v) for nm, v in vpairs
                           if re.sub(r"[^a-z]", "", nm.lower()) not in VISITING]
            ayes = sum(1 for _, v in weber_pairs if norm(v) == "Aye")
            nays = sum(1 for _, v in weber_pairs if norm(v) == "Nay")
            names_recorded = 1 if weber_pairs else 0
            if not vpairs:
                outcome = ""
            elif ayes > nays:
                outcome = "Pass"
            else:
                outcome = "Fail"

            # refs: the motion almost always names its own instrument ("adopt Resolution
            # 2-2015"), so search motion_text FIRST; fall back to the nearest header only.
            ctx = "\n".join(lines[max(0, i - 8):i])
            hay = motion_text + " \n " + ctx
            resn = RES_RE.search(hay)
            ordn = ORD_RE.search(hay)
            cont = CONTRACT_RE.search(hay)
            reading = READING_RE.search(hay)
            stage = reading.group(0).title() if reading else ""

            # trim any leading discussion prose so result_raw begins at the roll call itself
            fp = PAIR_RE.search(vote_line)
            result_raw = re.sub(r"\s+", " ", vote_line[fp.start():] if fp else vote_line).strip()
            motions.append({
                "meeting_date": iso, "motion_no": mno,
                "motion_text": motion_text[:1200],
                "mover": mover, "seconder": seconder,
                "result_raw": result_raw, "outcome": outcome, "stage": stage,
                "names_recorded": names_recorded, "n_aye": ayes, "n_nay": nays,
                "source_file": os.path.relpath(path, COUNTY),
                "provenance": "county_portal",
            })
            for tnm, v in vpairs:
                vv = norm(v)
                if not vv:
                    continue
                if re.sub(r"[^a-z]", "", tnm.lower()) in VISITING:
                    continue  # visiting official from a joint meeting — not a Weber vote
                votes.append({"meeting_date": iso, "motion_no": mno,
                              "person": tnm, "vote_value": vv})
            for kind, mm in (("resolution", resn), ("ordinance", ordn), ("contract", cont)):
                if mm:
                    refs.append({"meeting_date": iso, "motion_no": mno,
                                 "ref_type": kind, "ref_number": mm.group(1),
                                 "verbatim": re.sub(r"\s+", " ", mm.group(0)).strip()})
            # Resume AT the next motion's own line when the roll-call scan stopped there —
            # `j + 1` would step OVER it and lose that motion entirely (2026-07-31 fix: the
            # 2019-07-30 Ordinance 2019-13 Solar Overlay adoption was swallowed this way by
            # the retracted adjourn motion printed just above it).
            i = j + 1
            if hit_next_motion:
                i = j
            elif died:
                # land on the substitute motion's first line (skip the blank the died-phrase
                # split can leave behind) so SUBST_RE gets its one shot at it
                while i < n and not lines[i].strip():
                    i += 1
            continue
        if relaxed and line.strip():
            died_window -= 1
        i += 1
    return motions, votes, refs, fullnames


def main():
    os.makedirs(STG, exist_ok=True)
    paths = sorted(glob.glob(os.path.join(MIN, "*", "*.md")))
    all_m, all_v, all_r, meetings = [], [], [], []
    fullmap = {}
    for p in paths:
        iso = os.path.basename(p)[:10]
        # meeting_type from front-matter
        head = open(p, encoding="utf-8").read(600)
        mt = re.search(r"meeting_type:\s*(\w+)", head)
        meetings.append({"meeting_date": iso, "body": "Board of Commissioners",
                         "meeting_type": mt.group(1) if mt else "regular",
                         "source_file": os.path.relpath(p, COUNTY),
                         "provenance": "county_portal"})
        m, v, r, fn = parse_meeting(p)
        all_m += m
        all_v += v
        all_r += r
        for k, val in fn.items():
            fullmap.setdefault(k, val)

    def dump(name, rows, cols):
        with open(os.path.join(STG, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)

    dump("meetings.csv", meetings,
         ["meeting_date", "body", "meeting_type", "source_file", "provenance"])
    dump("motions.csv", all_m,
         ["meeting_date", "motion_no", "motion_text", "mover", "seconder", "result_raw",
          "outcome", "stage", "names_recorded", "n_aye", "n_nay", "source_file", "provenance"])
    dump("votes.csv", all_v, ["meeting_date", "motion_no", "person", "vote_value"])
    dump("motion_refs.csv", all_r,
         ["meeting_date", "motion_no", "ref_type", "ref_number", "verbatim"])
    with open(os.path.join(STG, "person_fullnames.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["lastname_key", "full_name"])
        for k, val in sorted(fullmap.items()):
            w.writerow([k, val])

    named = sum(1 for m in all_m if m["names_recorded"])
    print("meetings:", len(meetings))
    print("motions :", len(all_m), " named:", named,
          "(%.1f%%)" % (100 * named / max(1, len(all_m))))
    print("votes   :", len(all_v))
    print("refs    :", len(all_r),
          "(res %d / ord %d / contract %d)" % (
              sum(1 for r in all_r if r["ref_type"] == "resolution"),
              sum(1 for r in all_r if r["ref_type"] == "ordinance"),
              sum(1 for r in all_r if r["ref_type"] == "contract")))


if __name__ == "__main__":
    main()
