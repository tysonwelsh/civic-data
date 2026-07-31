#!/usr/bin/env python3
"""Regenerate the Cache County land_use Planning-Commission vote layer from the
minutes markdown. DERIVED, idempotent, no network. Reads minutes/**/*.md, writes
all_votes.csv, motions_tally.csv and roster.csv. See VOTES_README.md for the
recording ceiling and method. Run: python3 build_votes.py

Cache County PC minutes state motions inline in prose. TWO grammar eras:
  * TALLY era (2015-01 .. 2024-10): "<Mover> motioned to <text>; <Seconder>
    seconded; <Result> <aye>, <nay>." — only the numeric tally is recorded; NO
    voter is named (dissenters on split votes are NOT named — a source ceiling).
  * NAMED era (2024-11 onward): the same motion line is followed by
    "Ayes: <full names>" / "Nays: <full names or 0>" — every voter is named,
    even on unanimous motions (fuller than the tally era).
Margin line-numbers in the 2015-2016 scans bleed into tallies
("Passed 6, 35 \n0." == "Passed 6, 0"); the result regex takes the digit group
immediately before the terminating period.
"""
import os, re, csv, glob

BASE = os.path.dirname(os.path.abspath(__file__))
MIN = os.path.join(BASE, "minutes")
REPO = os.path.dirname(os.path.dirname(BASE))          # civic-data/
BODY = "PlanningCommission"
TITLE = "Cache County Planning Commission"
NAMED_ERA_START = "2024-11-07"

def parse_fm(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, m.group(2)

def clean(s):
    return re.sub(r"\s+", " ", s).strip()

VERB = r"(Passed|Approved|Failed|Denied|Carried|Tabled|Continued)"
# Anchor each motion at "<Mover> motioned"; a motion runs to the NEXT such anchor.
# This avoids a single greedy match merging two motions when margin line-numbers
# bleed between the seconder clause and the outcome ("...seconded; 141 Passed 5, 0").
ANCHOR_RE = re.compile(r"([A-Z][A-Za-z’'\-]+)\s+motioned\s+")
SECOND_RE = re.compile(r"([A-Z][A-Za-z’'\-]+)\s+seconded")
# outcome verb, tolerating bled-in margin line-numbers before it and in the tally
# ("Passed 6, 35 \n0." == "Passed 6, 0"); nay = digit group before the period.
# Tally separator is comma OR hyphen ("Passed 6-0"); some minutes drop the verb
# and print only "seconded; 7, 0." (handled by BARE_TALLY_RE fallback).
# A verb IMMEDIATELY followed by a tally is the reliable outcome. Case-insensitive
# (a few minutes lowercase "passed 5, 0"); tolerates margin line-numbers bled into
# the tally ("Passed 6, 35 \n0." == "Passed 6, 0") and comma OR hyphen separators.
# optional leading margin line-number can sit between the verb and the real tally
# ("Passed 28 6, 0" == "Passed 6, 0"): a number followed by whitespace then the
# aye digit (only consumed when a "<n>, <n>" tally actually follows it).
TALLIED_RE = re.compile(VERB + r"\b\s*[,:]?\s*(?:\d+\s+)?(?:(\d+)\s*[,\-][\s\d\n]*?(\d+)\s*\.|(\d+)\s*[,\-]\s*(\d+))", re.I)
# a standalone capitalized outcome verb (no tally printed) — case-SENSITIVE so
# incidental lowercase verbs in prose ("approved the concept") are not mistaken
# for an outcome.
VERB_ONLY_RE = re.compile(VERB + r"\b")
# verb dropped, only "seconded; 7, 0." printed.
BARE_TALLY_RE = re.compile(r"seconded\s*[;,]\s*(\d+)\s*[,\-]\s*(\d+)\s*\.")
# a motion that never reached a vote (no second / withdrawn) — an honest outcome,
# not a missing tally. "dies"/"died", present or past tense.
DIED_RE = re.compile(r"[Mm]otion (?:die[ds]|failed)\s+(?:due to|for)\s+(?:a )?(?:lack|want)\s+of\s+(?:a\s+)?second"
                     r"|withdr(?:ew|awn)\s+the\s+motion|motion\s+was\s+withdrawn", re.I)

def parse_result(window):
    """Return (result, aye, nay, start). start = char offset of the outcome in
    the window (len(window) if none), used to bound the motion text.
    result='' (honest: no printed outcome) when nothing is found."""
    m = TALLIED_RE.search(window)
    if m:
        verb = m.group(1).title()
        if m.group(2) is not None:
            aye, nay = int(m.group(2)), int(m.group(3))
        else:
            aye, nay = int(m.group(4)), int(m.group(5))
        return f"{verb} {aye}, {nay}", aye, nay, m.start()
    b = BARE_TALLY_RE.search(window)
    if b:
        return f"Passed {int(b.group(1))}, {int(b.group(2))}", int(b.group(1)), int(b.group(2)), b.start()
    d = DIED_RE.search(window)
    if d:
        return clean(d.group(0)), None, None, d.start()
    v = VERB_ONLY_RE.search(window)
    if v:
        return v.group(1).title(), None, None, v.start()
    return "", None, None, len(window)

NAME_TOKEN = r"[A-Z][a-zA-Z’'\-]+(?:\s+[A-Z][a-zA-Z’'\-]+)*"

def parse_named_block(block):
    """From the text between a motion's result and the next motion, pull
    Ayes:/Nays: full-name lists. Returns list of (member, vote)."""
    rows = []
    for label, val in (("Aye", "Ayes?"), ("Nay", "Nays?"),
                       ("Abstain", "Abstain(?:ed|ing|s)?"),
                       ("Absent", "Absent")):
        m = re.search(rf"\b{val}\s*:\s*(.+)", block)
        if not m:
            continue
        seg = m.group(1)
        # cut at the next label or a newline that starts a non-name line
        seg = re.split(r"\b(?:Ayes?|Nays?|Abstain|Absent)\s*:", seg)[0]
        seg = seg.split("\n")[0]
        seg = seg.strip()
        if seg in ("0", "", "None", "none"):
            continue
        for nm in re.split(r",|\band\b", seg):
            # ";" too: the common form is "…, Chris Sands; Nays: 0." and the label-split
            # leaves the semicolon attached to the LAST name, failing the name test.
            nm = nm.strip(" .;\t")
            nm = re.sub(r"^(Commissioners?|Chair|Vice Chair|Mr\.|Ms\.|Mrs\.)\s+", "", nm)
            # 2026-07-26 (audit F12): these minutes are a NUMBERED legal transcript, so the
            # line number can fuse onto the last name — "…, Nate Daugs, Chris Sands 13".
            # The trailing digits made the token fail the name test and Chris Sands was
            # dropped from 7 motions on 2024-11-07. (Where a semicolon happened to follow
            # the name the row survived, which is why only some rolls lost him.)
            nm = re.sub(r"\s+\d{1,3}$", "", nm).strip()
            if re.match(rf"^{NAME_TOKEN}$", nm) and len(nm) > 2:
                rows.append((nm, label))
    return rows

def main():
    files = sorted(glob.glob(os.path.join(MIN, "*", "*.md")))
    vote_rows = []    # 13-col named-member rows
    tally_rows = []   # tally-only motions
    per_meeting = []  # (date, seq, mover, seconder, voters)
    stats = {"meetings": 0, "motions": 0, "named": 0, "tally": 0}

    for f in files:
        raw = open(f, encoding="utf-8").read()
        fm, text = parse_fm(raw)
        # strip verbatim "(check)" editorial margin notes (a clerk QA marker,
        # not content) so they never surface as a seconder/mover name.
        text = re.sub(r"\(\s*check\s*\)", "", text, flags=re.I)
        date = fm.get("date", "")
        year = date[:4]
        src = os.path.relpath(f, REPO)
        named_era = date >= NAMED_ERA_START
        stats["meetings"] += 1

        anchors = list(ANCHOR_RE.finditer(text))
        seq = 0
        for k, am in enumerate(anchors):
            seq += 1
            mover = am.group(1)
            nxt = anchors[k+1].start() if k+1 < len(anchors) else len(text)
            window = text[am.end():nxt]
            result, aye, nay, rstart = parse_result(window)
            # motion text = from anchor to the seconder / outcome / first ';'
            sm = SECOND_RE.search(window)
            cut = min(rstart, sm.start() if sm else len(window))
            semi = window.find(";")
            if semi != -1:
                cut = min(cut, semi)
            motion_text = clean(window[:cut])
            # seconder: named token before the outcome verb
            seconder = ""
            if sm and sm.start() < rstart:
                seconder = sm.group(1)
            stats["motions"] += 1

            voters = []
            if named_era:
                voters = parse_named_block(window[:900])

            if voters:
                stats["named"] += 1
                for (nm, vt) in voters:
                    vote_rows.append([date, year, TITLE, BODY, seq, motion_text,
                                      "", result, mover, seconder, nm, vt, src])
            else:
                stats["tally"] += 1
                tally_rows.append([date, BODY, seq, motion_text, result,
                                   mover, seconder, "false"])
            per_meeting.append((date, seq, mover, seconder, voters))

    HEADER = ["date","year","title","body","motion_no","motion","motion_type",
              "result","mover","seconder","member","vote","source"]
    with open(os.path.join(BASE, "all_votes.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(HEADER); w.writerows(vote_rows)
    with open(os.path.join(BASE, "motions_tally.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date","body","motion_no","motion","result","mover","seconder","names_recorded"])
        w.writerows(tally_rows)

    # roster: honest record of WHO commissioners are, from named roles
    roster = {}
    for (date, seq, mover, seconder, voters) in per_meeting:
        named = set()
        if mover: named.add(mover)
        if seconder: named.add(seconder)
        for (nm, vt) in voters:
            named.add(nm)
        for nm in named:
            d = roster.setdefault(nm, {"first": date, "last": date, "n": 0})
            d["first"] = min(d["first"], date); d["last"] = max(d["last"], date); d["n"] += 1
    with open(os.path.join(BASE, "roster.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["commissioner","first_seen","last_seen","n_votes"])
        for nm in sorted(roster, key=lambda x: (-roster[x]["n"], x)):
            d = roster[nm]; w.writerow([nm, d["first"], d["last"], d["n"]])

    print("wrote all_votes.csv (%d named-member rows) + motions_tally.csv (%d tally motions)"
          " + roster.csv (%d names)" % (len(vote_rows), len(tally_rows), len(roster)))
    print("meetings=%d motions=%d named-vote motions=%d tally-only=%d"
          % (stats["meetings"], stats["motions"], stats["named"], stats["tally"]))

if __name__ == "__main__":
    main()
