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


def is_vote_line(line):
    """A genuine roll call: >=2 member-value pairs, OR a single pair right after a motion."""
    pairs = PAIR_RE.findall(line)
    return len(pairs), pairs


def parse_meeting(path):
    body = strip_front(open(path, encoding="utf-8").read())
    lines = body.split("\n")
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
    while i < n:
        line = lines[i]
        mv = MOVED_RE.search(line)
        # only treat as a motion if a "second" appears within this + next ~4 lines
        if mv:
            window = " ".join(lines[i:i + 5])
            sec = SECOND_RE.search(window)
            # motion_text: from "moved" through the seconder clause (or end of window)
            start = mv.start()
            wtext = " ".join(l.strip() for l in lines[i:i + 6])
            wmv = MOVED_RE.search(wtext)
            mtext = wtext[wmv.start():] if wmv else window
            # trim at the seconder's "seconded." for a clean verbatim motion
            cut = re.search(r"second(?:ed)?\.?", mtext, re.I)
            if not sec:
                i += 1
                continue
            mno += 1
            mover = mv.group(1)
            secm = SECOND_RE.search(mtext) or SECOND_RE.search(window)
            seconder = secm.group(1) if secm else ""
            motion_text = re.sub(r"\s+", " ", mtext[: cut.end()] if cut else mtext).strip()

            # find the roll call after the motion — TWO grammars:
            #  (a) single line, semicolon-separated, dash-joined (modern)
            #  (b) "Roll Call Vote:" header + one dot-leader member line each (early era)
            # A motion can be followed by pages of discussion before its roll call
            # (2020-01-07 rezone: 12 lines down), so scan generously — but STOP at the next
            # motion so a genuinely-unvoted motion never steals the following one's roll call.
            vote_line, vpairs = "", []
            j = i
            scanned = 0
            while j < n and scanned < 60:
                cand = lines[j]
                if j != i and OTHER_COUNTY_RE.match(cand):
                    j += 1  # skip another county's roll call, keep scanning for Weber's
                    continue
                if j != i and MOVED_RE.search(cand) and SECOND_RE.search(
                        " ".join(lines[j:j + 5])):
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
            i = j + 1
            continue
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
