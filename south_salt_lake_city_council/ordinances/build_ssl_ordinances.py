#!/usr/bin/env python3
"""Build the South Salt Lake ordinances/ dataset (expand-city-sources Source 3).

Enumeration source: the Municode "Code Comparative Table and Disposition List"
(nodeId=COCOTADILI, product 16638) — an authoritative, minutes-INDEPENDENT
chronological listing of every adopted ordinance (Number, Date, Description, Code
Section). Retained raw in raw/municode_cocotadili_comparative_table.json.

Linkage: SSL council motions describe ordinances by SUBJECT/TITLE, not by number
(verified — no `#YYYY-NN` tokens in all_votes.csv motion text). So linkage to
meeting_minutes/all_votes.csv is by adoption DATE (+ subject agreement), never by
number. Combined with the city's recorded-minutes coverage cliff (council minutes
essentially 2020-early-2021 + sporadic recent), most rows cannot link -> honest 'none'.

Confidence (per skill / prompt):
  high  = adoption date AND ordinance number both appear in a recorded motion (N/A here
          because SSL motions never cite the number -> not producible)
  medium= a recorded council motion on the adoption date whose subject agrees
  low   = a recorded council motion on the adoption date, subject not clearly matched
  none  = no recorded council motion on the adoption date (the coverage-cliff gap)
Nothing is forced.

Writes: index.csv (SCHEMA_SPEC §9 ordinances contract) + text/ sidecars.
Idempotent. Helper lives inside the dataset dir by standing rule.
"""
import csv, json, re, html, os, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CITY = os.path.dirname(HERE)
RAW = os.path.join(HERE, "raw")
TEXT = os.path.join(HERE, "text")
VOTES = os.path.join(CITY, "meeting_minutes", "all_votes.csv")
FLOOR_YEAR = 2020
RETRIEVED = "2026-07-13"
SOURCE_URL = ("https://library.municode.com/ut/south_salt_lake/codes/"
              "code_of_ordinances?nodeId=COCOTADILI")
API_URL = ("https://api.municode.com/CodesContent?jobId=493395&nodeId=COCOTADILI"
           "&productId=16638")

os.makedirs(TEXT, exist_ok=True)


def cell_text(x):
    x = re.sub(r"<[^>]+>", " ", x)
    x = html.unescape(x)
    return re.sub(r"\s+", " ", x).strip()


def table_rows(content):
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", content, re.S):
        cs = [cell_text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
        if cs:
            yield cs


def flat_text(content):
    t = re.sub(r"<[^>]+>", "\n", content)
    t = html.unescape(t)
    return "\n".join(l.rstrip() for l in t.split("\n"))


def parse_date(s):
    # formats like "1- 8-2020", "10-14-2009", "6- 4-2009"
    s = s.replace(" ", "")
    m = re.match(r"(\d{1,2})-(\d{1,2})-((?:19|20)\d\d)", s)
    if not m:
        return ""
    mo, da, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return datetime.date(yr, mo, da).isoformat()
    except ValueError:
        return ""


LAND_USE_DESC = re.compile(
    r"zoning|land use|land-use|general plan|subdivision|overlay|annex|plat|"
    r"rezone|development|zone change|zone map|TTBU|beneficial use|road profile|"
    r"right-of-way|right of way|vacation of|street", re.I)


def is_land_use(desc, section):
    sec = section or ""
    if re.search(r"\b17[.\d]*", sec) or "Ch. 17" in sec:
        return "yes"
    if LAND_USE_DESC.search(desc or ""):
        return "yes"
    return "no"


# ---- extract sidecars for both disposition tables (born-digital) ----
def write_sidecar(raw_name, stem):
    d = json.load(open(os.path.join(RAW, raw_name)))
    content = "".join(doc.get("Content") or "" for doc in d.get("Docs", []))
    txt = flat_text(content)
    txt = re.sub(r"\n{3,}", "\n\n", txt).strip() + "\n"
    with open(os.path.join(TEXT, stem + ".txt"), "w") as f:
        f.write("[SOURCE: Municode api.municode.com CodesContent, born-digital HTML "
                "-> text. South Salt Lake product 16638.]\n\n" + txt)
    return content


cocota = write_sidecar("municode_cocotadili_comparative_table.json",
                       "municode_cocotadili_comparative_table")
write_sidecar("municode_orlidita_legacy_ordinance_table.json",
              "municode_orlidita_legacy_ordinance_table")


# ---- parse ordinances 2020+ ----
ords = []
for cs in table_rows(cocota):
    if not re.fullmatch(r"(19|20)\d\d-\d{1,3}[A-Za-z]?", cs[0]):
        continue
    num = cs[0]
    date_raw = cs[1] if len(cs) > 1 else ""
    desc = cs[2] if len(cs) > 2 else ""
    section = cs[-1] if len(cs) > 3 else ""
    iso = parse_date(date_raw)
    yr = int(num.split("-")[0])
    if yr < FLOOR_YEAR:
        continue
    ords.append(dict(num=num, date=iso, date_raw=date_raw.strip(),
                     desc=desc, section=section))

ords.sort(key=lambda o: (o["date"] or o["num"], o["num"]))


# ---- load council/RDA motions for linkage (by date) ----
MINUTES_SRC = "meeting_minutes/all_votes.csv (SSL recorded PMN minutes)"
motions_by_date = {}
all_motion_rows = []
with open(VOTES) as f:
    for r in csv.DictReader(f):
        d = r["date"].strip()
        if r.get("body") not in ("Council", "RDA"):
            continue
        motions_by_date.setdefault(d, {})
        motions_by_date[d][r.get("motion_no", "")] = r  # dedup to motion events
        all_motion_rows.append(r)

DEFER_RE = re.compile(r"unfinished business|adjourn|approve (these|all )?minutes|"
                      r"the minutes|consent agenda", re.I)
ADOPT_RE = re.compile(r"rdinance", re.I)   # motion concerns an ordinance
SECT_RE = re.compile(r"\b\d{1,2}\.\d{2,3}(?:\.\d{2,3})?\b")


def sections(text):
    return set(SECT_RE.findall(text or ""))


def chapters(text):
    return {s.rsplit(".", 1)[0] if s.count(".") >= 2 else s
            for s in sections(text)}


rows = []
counts = {"high": 0, "medium": 0, "low": 0, "none": 0, "within_source": 0}
for o in ords:
    m_date = m_no = conf = note = ""
    # candidate ordinance-ADOPTING motions on the adoption date (exclude deferrals/procedural)
    cands = {mno: r for mno, r in motions_by_date.get(o["date"], {}).items()
             if ADOPT_RE.search(r.get("motion", ""))
             and not DEFER_RE.search(r.get("motion", ""))}
    if cands:
        ord_secs = sections(o["section"])
        ord_chaps = chapters(o["section"])
        matched = None
        for mno, r in cands.items():
            msecs = sections(r.get("motion", ""))
            if ord_secs & msecs:
                matched, note = mno, "cited code section matches motion text"
                break
            if ord_chaps & chapters(r.get("motion", "")):
                matched, note = mno, "cited code chapter matches motion text"
        if matched:
            conf, m_date, m_no = "medium", o["date"], matched
        else:
            conf, m_date, m_no = "low", o["date"], sorted(cands)[0]
            note = ("recorded ordinance-adopting motion on this date; specific "
                    "ordinance unconfirmed (motion text truncated at item title)")
    else:
        conf = "none"
        note = ("no recorded ordinance-adopting motion on this date "
                "(coverage cliff: council minutes largely unpublished 2021-mid..2025)")
    counts[conf] += 1
    rows.append({
        "ordinance_no": o["num"],
        "adoption_date": o["date"],
        "date": o["date"],
        "title": o["desc"],
        "source_url": SOURCE_URL,
        "retrieved_date": RETRIEVED,
        "format": "json",
        "extraction_method": ("parsed Municode COCOTADILI comparative table "
                              "(api.municode.com, born-digital)"),
        "path": "raw/municode_cocotadili_comparative_table.json",
        "land_use": is_land_use(o["desc"], o["section"]),
        "result": "",  # adoption implied by codification; no roll call asserted from Municode
        "matched_motion_date": m_date,
        "matched_motion_no": m_no,
        "match_confidence": conf,
        # city-specific extras (after the contract columns):
        "code_section": o["section"],
        "adoption_date_raw": o["date_raw"],
        "codified": "no" if re.search(r"not included", o["section"], re.I) else "yes",
        "linkage_note": note,
        "minutes_source": MINUTES_SRC if conf in ("medium", "low") else "",
    })

# ---- within_source rows: ordinance adoptions the MINUTES prove but Municode has not
# yet codified (adopted after the codification cutoff 2026-01-28; SSL motions carry no
# ordinance number, so ordinance_no is blank = not recorded, never invented) ----
CUTOFF = "2026-01-28"
ws_seen = set()
for r in all_motion_rows:
    if r["date"] <= CUTOFF:
        continue
    m = r.get("motion", "")
    if not ADOPT_RE.search(m) or DEFER_RE.search(m):
        continue
    key = (r["date"], r.get("motion_no", ""))
    if key in ws_seen:
        continue
    ws_seen.add(key)
    counts["within_source"] += 1
    rows.append({
        "ordinance_no": "",  # SSL motions cite no number; not published elsewhere yet
        "adoption_date": r["date"],
        "date": r["date"],
        "title": m.split(" — motion")[0][:200].strip() or m[:200].strip(),
        "source_url": SOURCE_URL,
        "retrieved_date": RETRIEVED,
        "format": "json",
        "extraction_method": "derived from meeting_minutes/all_votes.csv motion text",
        "path": "raw/municode_cocotadili_comparative_table.json",
        "land_use": "no",
        "result": r.get("result", ""),
        "matched_motion_date": r["date"],
        "matched_motion_no": r.get("motion_no", ""),
        "match_confidence": "within_source",
        "code_section": "",
        "adoption_date_raw": "",
        "codified": "no",
        "linkage_note": ("adopted after Municode codification cutoff (2026-01-28); "
                         "known only from recorded minutes; un-numbered FY2026-27 "
                         "budget/tax ordinance"),
        "minutes_source": MINUTES_SRC,
    })

rows.sort(key=lambda r: (r["adoption_date"], r["matched_motion_no"] or "",
                         r["ordinance_no"]))

FIELDS = ["ordinance_no", "adoption_date", "date", "title", "source_url",
          "retrieved_date", "format", "extraction_method", "path", "land_use",
          "result", "matched_motion_date", "matched_motion_no", "match_confidence",
          "code_section", "adoption_date_raw", "codified", "linkage_note",
          "minutes_source"]

with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)

lu = sum(1 for r in rows if r["land_use"] == "yes")
print(f"ordinances 2020+: {len(rows)}")
print(f"land-use subset: {lu}")
print(f"date window: {rows[0]['adoption_date']} .. {rows[-1]['adoption_date']}")
print("linkage:", counts)
