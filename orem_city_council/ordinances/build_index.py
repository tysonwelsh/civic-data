#!/usr/bin/env python3
"""Build orem_city_council/ordinances/index.csv (additive; read-only on all other datasets).

Three provenance streams, kept honestly distinct:
  A. MINUTES-DERIVED backbone (within_source) — Orem council minutes never print an
     ordinance number, but every ordinance ADOPTION is a roll-call motion in
     meeting_minutes/all_votes.csv ("approve, by ordinance, to amend ..."). Those motions
     carry the adoption date + full subject + the vote. This is the number-less backbone:
     match_confidence = within_source (derived from the motion text itself, NOT an
     independent cross-match), ordinance_no left EMPTY (the city assigns one but does not
     restate it in minutes).
  B. INDEPENDENT source (orem.gov WordPress "City Council Ordinance"/"Resolutions and
     Ordinances" posts) — a practice begun mid-2026 — publish the full adopted-ordinance
     text WITH its O-YYYY-NNNN number. Retained in raw/ + text/.
  C. CROSS-MATCH (medium) — where an independent post's ordinance uniquely matches a council
     adoption motion ON THE POST'S MEETING DATE by distinctive code-section / subject tokens,
     the two are joined into ONE row: number+full caption from the independent post, roll-call
     from the minutes. This is a genuine CROSS-SOURCE corroboration → match_confidence=medium
     (the dataset's first corroborated tier; see ordinances/CLAUDE.md). The duplicate
     number-less within_source row for that same motion is SUPPRESSED (no double count).
     Independent ordinances with NO unique token match on their meeting date fall to `none`
     (audit signal): either adopted on the consent agenda (blanket motion, not individually
     rolled) or beyond the current vote coverage (link on the next minutes refresh). Nothing
     is ever forced; the vote layer is never edited.

Re-run: python3 build_index.py   (idempotent; regenerates index.csv + text/).
"""
import csv, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
CC = os.path.dirname(HERE)  # orem_city_council/
VOTES = os.path.join(CC, "meeting_minutes", "all_votes.csv")
MIDX = os.path.join(CC, "meeting_minutes", "minutes_index.csv")
RETRIEVED = "2026-07-19"

# ---- land-use classifier (Orem City Code Title 22 = the Development/Land-Use code) ----
LU_RE = re.compile(r"""(?ix)
    rezon | zoning\s+map | zone\s+change | standard\s+land\s+use | \bslu\b |
    general\s+plan | \b22-\d | article\s+22 | chapter\s+22 | land\s+use |
    moratorium | planned\s+development | \bpd-?\d | vacat | subdivision | annex |
    concept\s+plan | appendix
""")

def is_land_use(motion_type, text):
    if motion_type.strip().lower() == "land-use/zoning":
        return True
    if LU_RE.search(text):
        return True
    return False

def lead_verb(m):
    m = m.lower().strip().lstrip('"').replace("dény", "deny").replace("énact", "enact")
    return re.split(r"[ ,]", m)[0]

# non-adopting leading verbs -> NOT an ordinance adoption (deny/continue/table/withdraw)
NON_ADOPT = {"deny", "continue", "table", "withdraw", "refer", "postpone"}

# ---------------- load minutes + votes ----------------
fmt_by_date = {}
for r in csv.DictReader(open(MIDX)):
    fmt_by_date[r["date"]] = "scanned" if r["format"].lower() == "ocr" else "text"

votes = list(csv.DictReader(open(VOTES)))
motions = {}
for r in votes:
    motions.setdefault((r["date"], r["motion_no"]), r)
MAX_VOTE_DATE = max(r["date"] for r in votes)
dates_with_motions = set(d for (d, _mno) in motions)

# ---------------- B. independent orem.gov ordinance posts ----------------
def strip_html(path):
    h = open(path, encoding="utf-8", errors="replace").read()
    h = re.sub(r"<script.*?</script>", " ", h, flags=re.S)
    h = re.sub(r"<style.*?</style>", " ", h, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", " ", h))
    return re.sub(r"\s+", " ", t).strip()

RAW = os.path.join(HERE, "raw")
TEXTDIR = os.path.join(HERE, "text")
os.makedirs(TEXTDIR, exist_ok=True)

# (raw filename, post URL, meeting/adoption date). The post slug date is the Orem council
# meeting date the ordinances were adopted at (Orem meets Tuesdays).
POSTS = [
    ("2026-06-23_city-council-ordinance_O-2026-0012.html",
     "https://orem.gov/06-23-2026-city-council-ordinance/", "2026-06-23"),
    ("2026-06-23_city-council-resolutions-and-ordinances.html",
     "https://orem.gov/06-23-2026-city-council-resolutions-and-ordinances/", "2026-06-23"),
    ("2026-07-14_city-council-ordinances_O-2026-0018.html",
     "https://orem.gov/07-14-2026-city-council-ordinances/", "2026-07-14"),
]
# Number token tolerates the OCR 'zero-for-O' variant seen on the 07-14 post ("0-2026-0018").
NUM_RE = re.compile(r"([O0]-20\d{2}-\d{4})\s+(AN?\s+ORDINANCE.*?)(?=(?:[OR0]-20\d{2}-\d{4})|Prev Previous|Next |$)", re.S)

def norm_num(n):
    return "O" + n[1:] if n[0] == "0" else n  # normalize OCR 0-2026-.... -> O-2026-....

# ---- CROSS-MATCH RULES (hand-verified 2026-07-19 against full motion text + WP caption) ----
# ordinance_no -> lowercase tokens that must ALL appear in EXACTLY ONE council motion on the
# ordinance's meeting (post) date. A unique hit -> medium cross-source row; otherwise `none`.
# Only ordinances individually rolled as a distinct motion qualify; the flood (O-2026-0012)
# and the 355 W University Pkwy rezone (O-2026-0013) were adopted on the 2026-06-23 CONSENT
# agenda (blanket motion "approve the consent items", no section tokens) -> they stay `none`.
MATCH_TOKENS = {
    "O-2026-0014": ["fiscal year 2025-2026", "budget"],   # -> 2026-06-23 budget amendment (motion omits the word "ordinance"; backbone misses it)
    "O-2026-0015": ["22-11-17", "7424"],                  # -> 2026-06-23 SLU #7424 Recreation Centers, PD-5
    "O-2026-0016": ["appendix a", "6231"],                # -> 2026-06-23 Appendix A #6231 Beauty/Barber + tattoo, M2
    "O-2026-0017": ["22-14-20", "22-1-5"],                # -> 2026-06-23 neighborhood-meeting requirements
}

def unique_motion_on_date(date, tokens):
    hits = [(d, mno) for (d, mno), r in motions.items()
            if d == date and all(t in r["motion"].lower() for t in tokens)]
    return hits[0] if len(hits) == 1 else None

indep = []   # list of dicts: {num,title,url,fname,adate}
seen_nums = set()
for fname, url, adate in POSTS:
    full = strip_html(os.path.join(RAW, fname))
    with open(os.path.join(TEXTDIR, fname.replace(".html", ".txt")), "w") as fo:
        fo.write(f"# source_url: {url}\n# adoption_date: {adate}\n# extracted: {RETRIEVED}\n\n")
        fo.write(full + "\n")
    for m in NUM_RE.finditer(full):
        num = norm_num(m.group(1))
        if num in seen_nums:
            continue
        seen_nums.add(num)
        title = re.sub(r"\s+", " ", m.group(2)).strip()
        title = re.sub(r"\s+(Prev Previous|Next).*$", "", title).strip()
        indep.append({"num": num, "title": title[:600], "url": url,
                      "fname": fname, "adate": adate})

# ---------------- build cross-matched (medium) + none rows ----------------
consumed = set()   # (date, motion_no) motions consumed by a medium match -> suppress in backbone
indep_rows = []
for it in indep:
    num, adate = it["num"], it["adate"]
    match = unique_motion_on_date(adate, MATCH_TOKENS[num]) if num in MATCH_TOKENS else None
    if match:
        d, mno = match
        r = motions[(d, mno)]
        consumed.add((d, mno))
        indep_rows.append({
            "ordinance_no": num,
            "adoption_date": d,
            "date": d,
            "title": it["title"],  # authoritative full caption from the independent post
            "source_url": it["url"],
            "retrieved_date": RETRIEVED,
            "format": "html",
            "extraction_method": "orem.gov WordPress ordinance post (independent, number-bearing) cross-matched to the council adoption motion by meeting date + distinctive code-section/subject tokens",
            "path": "raw/" + it["fname"],
            "result": r["result"],
            "land_use": "yes" if is_land_use(r["motion_type"], it["title"]) else "no",
            "matched_motion_date": d,
            "matched_motion_no": mno,
            "match_confidence": "medium",
            "linkage_note": "CROSS-SOURCE: ordinance number + full caption from the independent orem.gov post, roll-call adoption from meeting_minutes/all_votes.csv (unique distinctive-token match on the meeting date)",
            "minutes_source": r["source"],
        })
    else:
        # no unique token match on the meeting date -> honest audit signal
        if adate > MAX_VOTE_DATE:
            note = (f"independently-published adopted ordinance; all_votes.csv ends {MAX_VOTE_DATE} "
                    f"so NO vote row exists yet (meeting {adate} beyond current coverage) -> AUDIT "
                    f"SIGNAL, link on the next minutes refresh (not forced, vote layer not edited)")
        elif adate in dates_with_motions:
            note = (f"council met {adate} and this ordinance is listed, but it was adopted on the "
                    f"CONSENT agenda (blanket 'approve the consent items' motion, not individually "
                    f"rolled) -> no distinct vote row to link. AUDIT SIGNAL (not forced)")
        else:
            note = ("independently-published adopted ordinance with no matching vote row -> AUDIT "
                    "SIGNAL (not forced, vote layer not edited)")
        indep_rows.append({
            "ordinance_no": num,
            "adoption_date": adate,
            "date": adate,
            "title": it["title"],
            "source_url": it["url"],
            "retrieved_date": RETRIEVED,
            "format": "html",
            "extraction_method": "extracted from orem.gov WordPress 'City Council Ordinance' post (born-digital HTML)",
            "path": "raw/" + it["fname"],
            "result": "",
            "land_use": "yes" if is_land_use("", it["title"]) else "no",
            "matched_motion_date": "",
            "matched_motion_no": "",
            "match_confidence": "none",
            "linkage_note": note,
            "minutes_source": "",
        })

# ---------------- A. minutes-derived backbone (within_source) ----------------
minutes_rows = []
excluded = []
for (date, mno), r in sorted(motions.items()):
    if (date, mno) in consumed:
        continue  # already carried as a numbered medium cross-match
    mt = r["motion"]
    if "ordinance" not in mt.lower():
        continue
    verb = lead_verb(mt)
    if verb in NON_ADOPT:
        excluded.append((date, mno, verb, r["result"], mt[:70]))
        continue
    minutes_rows.append({
        "ordinance_no": "",
        "adoption_date": date,
        "date": date,
        "title": mt,
        "source_url": r["source"],          # repo-relative minutes markdown (city prints no per-ordinance URL)
        "retrieved_date": RETRIEVED,
        "format": fmt_by_date.get(date, "text"),
        "extraction_method": "reconstructed from meeting_minutes/all_votes.csv motion text (Orem minutes assign no ordinance number)",
        "path": "",
        "result": r["result"],
        "land_use": "yes" if is_land_use(r["motion_type"], mt) else "no",
        "matched_motion_date": date,
        "matched_motion_no": mno,
        "match_confidence": "within_source",
        "linkage_note": "backbone derived FROM this motion; number-less, not an independent cross-match",
        "minutes_source": r["source"],
    })

# ---------------- write ----------------
# SCHEMA_SPEC §9 ordinances contract header first, city extras after
COLS = ["ordinance_no", "adoption_date", "date", "title", "source_url", "retrieved_date",
        "format", "extraction_method", "path", "land_use", "result",
        "matched_motion_date", "matched_motion_no", "match_confidence",
        "linkage_note", "minutes_source"]
all_rows = indep_rows + minutes_rows
all_rows.sort(key=lambda r: (r["date"], r["ordinance_no"] or "zzz", r["matched_motion_no"] or ""))
with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(all_rows)

from collections import Counter
print("minutes-derived (within_source):", len(minutes_rows))
print("independent posts parsed:", len(indep), "numbers:", sorted(seen_nums))
print("cross-matched (medium):", sum(1 for r in indep_rows if r["match_confidence"] == "medium"),
      [r["ordinance_no"] for r in indep_rows if r["match_confidence"] == "medium"])
print("independent unmatched (none):", sum(1 for r in indep_rows if r["match_confidence"] == "none"),
      [r["ordinance_no"] for r in indep_rows if r["match_confidence"] == "none"])
print("excluded non-adopting motions:", len(excluded))
for e in excluded:
    print("   excl", e)
print("land_use yes:", sum(1 for r in all_rows if r["land_use"] == "yes"), "/", len(all_rows))
print("confidence:", Counter(r["match_confidence"] for r in all_rows))
print("TOTAL rows:", len(all_rows))
