#!/usr/bin/env python3
"""Regenerate the land_use Planning-Commission vote layer from the minutes markdown.

DERIVED, idempotent, no network. Reads minutes/**/*.md, writes all_votes.csv,
motions_tally.csv and roster.csv. See VOTES_README.md for the recording ceiling
and method. Run: python3 build_votes.py   (prints a summary; add nothing else)."""
import os, re, csv, glob, sys

BASE = os.path.dirname(os.path.abspath(__file__))
MIN = os.path.join(BASE, "minutes")

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

BODY_MAP = {
    "Planning Commission": "PlanningCommission",
    "Mountainous Planning District Planning Commission": "MountainousPlanningCommission",
}

def clean(s):
    return re.sub(r"\s+", " ", s).strip()

def name_after(label_text):
    # strip label, remove role words, return remaining name
    t = re.sub(r"\s+", " ", label_text).strip(" .")
    t = re.sub(r"^(Commissioners|Commissioner|Vice Chair|Chair|Mr\.|Ms\.|Mrs\.)\s+", "", t).strip(" .")
    # bare role word left over (no actual name) -> blank (honest gap)
    if t in ("Commissioner", "Commissioners", "Chair", "Vice Chair", ""):
        return ""
    # keep only the leading name token(s) before any trailing prose
    t = re.split(r"\s+(said|asked|motioned|seconded|moved)\b", t)[0]
    return t.strip(" .")

# stop patterns for capturing vote continuation
STOP = re.compile(r"(Motion:|Motion by:|2nd by:|Speaker\s*#|PUBLIC PORTION|LEGISLATIVE|ADMINISTRATIVE|Hearings began|The Planning Commission|^Commissioners Public|^Business|^Planning Staff|Salt Lake County .* Meeting Summary|Mountainous Planning)", re.I)

def rejoin_split_second(lines):
    """Repair the pypdf artifact that splits a '2nd by:' label across two lines.

    Some PMN PDFs superscript the 'nd' in '2nd by:', and pypdf then emits the '2' on
    its own line with 'nd by: Commissioner X' on the next (observed: the approved
    2024-12-11 Planning Commission minutes, motion 3). Without this repair the label
    matches nothing and a seconder the source DOES print is silently lost. Purely a
    text-layout repair — no content is invented."""
    out = []
    i = 0
    while i < len(lines):
        if (lines[i].strip() == "2" and i + 1 < len(lines)
                and re.match(r"^\s*nd by:", lines[i + 1])):
            out.append("2" + lines[i + 1].lstrip())
            i += 2
            continue
        out.append(lines[i])
        i += 1
    return out

TABLE_START = re.compile(r"^(Commissioners\s+Public|Business|Mtg\b|Absent\b|Planning Staff|Planning and Development|Phone:|Fax:|\*?NOTE:|ATTENDANCE)", re.I)

def extract_voters(vote_text):
    """Return list of (member, vote) for NAMED dissenters/abstainers only.
    Ayes are never individually named (recording ceiling)."""
    rows = []
    vt = clean(vote_text)
    low = vt.lower()
    if "unanim" in low and "nay" not in low and "abstain" not in low:
        return rows  # pure tally
    # NAY clauses: "<names> voted nay"
    for m in re.finditer(r"(Commissioners?\s+[A-Za-z ,and]+?)\s+voted\s+nay", vt, re.I):
        for nm in re.findall(r"[A-Z][a-z]+", re.sub(r"\b(Commissioners?|and|All|other)\b", "", m.group(1))):
            rows.append((nm, "Nay"))
    # ABSTAIN clauses: "<names> abstained"
    for m in re.finditer(r"(Commissioners?\s+[A-Za-z ,and]+?)\s+[Aa]bstained", vt, re.I):
        for nm in re.findall(r"[A-Z][a-z]+", re.sub(r"\b(Commissioners?|and|All|other)\b", "", m.group(1))):
            rows.append((nm, "Abstain"))
    # de-dup while preserving
    seen = set(); out = []
    for r in rows:
        if r not in seen:
            seen.add(r); out.append(r)
    return out

vote_rows = []      # 13-col member rows
tally_rows = []     # motions with no named members
meeting_stats = {}  # (body)-> counts

files = sorted(glob.glob(os.path.join(MIN, "*", "*.md")))
per_meeting = []

for f in files:
    raw = open(f, encoding="utf-8").read()
    fm, body_text = parse_fm(raw)
    body_val = fm.get("body", "")
    body = BODY_MAP.get(body_val)
    date = fm.get("date", "")
    year = date[:4]
    title = body_val
    src = os.path.relpath(f, "/Users/tysonwelsh/civic-data/salt_lake_county")
    lines = rejoin_split_second(body_text.splitlines())
    n = len(lines)

    # label each line by type, ignoring interleaved attendance-table lines
    def label(ln):
        if re.search(r"^\s*Motion:", ln): return "M"
        if re.search(r"Motion by:", ln):  return "B"
        if re.search(r"2nd by:", ln):     return "S"
        if re.search(r"^\s*Vote:", ln):   return "V"
        return None
    events = [(i, label(lines[i])) for i in range(n)]
    events = [(i, t) for (i, t) in events if t]

    # group into motions: a motion starts at "M"; collect the first B,S,V
    # that appear before the next "M".
    motions = []
    cur = None
    for (i, t) in events:
        if t == "M":
            if cur is not None:
                motions.append(cur)
            cur = {"M": i, "B": None, "S": None, "V": None}
        elif cur is not None:
            if t in ("B", "S", "V") and cur[t] is None:
                cur[t] = i
    if cur is not None:
        motions.append(cur)
    # keep only real motions (must have a "Motion by:" line)
    motions = [mm for mm in motions if mm["B"] is not None]

    seq = 0
    m_named = 0; m_tally = 0
    for k, mm in enumerate(motions):
        seq += 1
        mi, bi, si, vi = mm["M"], mm["B"], mm["S"], mm["V"]
        # motion text: Motion: line -> Motion by: line, cut at table/stop
        mparts = [re.split(r"Motion:", lines[mi], 1)[1]]
        for j in range(mi+1, bi):
            ln = lines[j]
            if TABLE_START.search(ln.strip()) or STOP.search(ln):
                break
            mparts.append(ln)
        motion_text = clean(" ".join(mparts))
        mover = name_after(re.split(r"Motion by:", lines[bi], 1)[1])
        seconder = name_after(re.split(r"2nd by:", lines[si], 1)[1]) if si is not None else ""
        vote_text = ""
        if vi is not None:
            parts = [re.split(r"Vote:", lines[vi], 1)[1]]
            for j in range(vi+1, min(vi+6, n)):
                ln = lines[j]
                if ln.strip() == "" or STOP.search(ln) or TABLE_START.search(ln.strip()):
                    break
                parts.append(ln)
            vote_text = " ".join(parts)
        result = clean(vote_text)
        # trim trailing agenda-line bleed after the outcome phrase (verbatim up to it).
        # pypdf packs the next agenda line onto the Vote line when the source PDF has
        # no blank between them; cut at the earliest natural outcome boundary.
        end = 0
        for pat in (r"Motion (?:passed|carried|failed|denied)\.?",
                    r"\(of [Cc]ommissioner['’]?s? present\)\.?",
                    r"voted unanimous(?:ly)? in favor\.?"):
            m2 = re.search(pat, result, re.I)
            if m2:
                end = max(end, m2.end())
        if end:
            result = result[:end].strip()
        voters = extract_voters(vote_text)
        if voters:
            m_named += 1
            for (nm, vt) in voters:
                vote_rows.append([date, year, title, body, seq, motion_text,
                                  "", result, mover, seconder, nm, vt, src])
        else:
            m_tally += 1
            tally_rows.append([date, body, seq, motion_text, result, mover, seconder, "false"])
        per_meeting.append((date, body, seq, mover, seconder, voters))
    st = meeting_stats.setdefault(body, {"meetings":0,"motions":0,"named":0,"tally":0})
    st["meetings"] += 1
    st["motions"] += len(motions)
    st["named"] += m_named
    st["tally"] += m_tally

# ---------- write all_votes.csv ----------
HEADER = ["date","year","title","body","motion_no","motion","motion_type",
          "result","mover","seconder","member","vote","source"]
with open(os.path.join(BASE, "all_votes.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(HEADER)
    for r in vote_rows:
        w.writerow(r)

# ---------- write motions_tally.csv ----------
with open(os.path.join(BASE, "motions_tally.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["date","body","motion_no","motion","result","mover","seconder","names_recorded"])
    for r in tally_rows:
        w.writerow(r)

# ---------- roster.csv ----------
# Ayes are never individually named (recording ceiling), so per-member vote
# rows exist only for named dissenters/abstainers. The richest honest record of
# WHO the commissioners are comes from named participation as mover / seconder /
# named-voter. n_votes = count of motions in which the commissioner is named in
# any of those roles.
roster = {}
for (date, body, seq, mover, seconder, voters) in per_meeting:
    named = set()
    if mover: named.add(mover)
    if seconder: named.add(seconder)
    for (nm, vt) in voters: named.add(nm)
    for nm in named:
        d = roster.setdefault(nm, {"first":date,"last":date,"n":0})
        d["first"] = min(d["first"], date)
        d["last"] = max(d["last"], date)
        d["n"] += 1
with open(os.path.join(BASE, "roster.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["commissioner","first_seen","last_seen","n_votes"])
    for nm in sorted(roster, key=lambda x:(-roster[x]["n"], x)):
        d = roster[nm]
        w.writerow([nm, d["first"], d["last"], d["n"]])

tot_motions = sum(s['motions'] for s in meeting_stats.values())
print("wrote all_votes.csv (%d named rows) + motions_tally.csv (%d tally motions) + "
      "roster.csv (%d commissioners)" % (len(vote_rows), len(tally_rows), len(roster)))
print("meetings=%d  motions=%d  named-vote motions=%d  tally-only=%d"
      % (sum(s['meetings'] for s in meeting_stats.values()), tot_motions,
         tot_motions - len(tally_rows), len(tally_rows)))
for b, st in sorted(meeting_stats.items()):
    print("  %-30s meetings=%d motions=%d named=%d tally=%d"
          % (b, st['meetings'], st['motions'], st['named'], st['tally']))
