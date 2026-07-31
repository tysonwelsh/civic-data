#!/usr/bin/env python3
"""Link Utah County's adopted-ordinance catalog to the enacting Commission motion, and
regenerate the loader-facing ordinances/index.csv.

Utah County numbers ordinances "YYYY-NN" — but that pattern COLLIDES pervasively with the
county's ubiquitous "Agreement No. YYYY-NNN" / "Recommendation Letter No." / resolution
numbering, so a literal ordinance-number match in motion text produces false positives
(verified). The only HIGH-confidence signal is a strict 1:1 date match to an
ordinance-ADOPTION motion:

  ordinance O (adoption_date d) is linked to Board-of-Commissioners motion m  <=>
    * exactly ONE catalogued ordinance was adopted on d, AND
    * exactly ONE BoC motion on d is an ordinance-adoption ("adopt/approve an ordinance
      amending ..."), excluding agreements/resolutions/continuances.

Everything else stays blank (match_confidence empty) — honest. Utah's 2019+ motions are
OCR tally-only, so a modest link rate is expected and correct.

Writes:
  * adopted_ordinances.csv  <- matched_motion_date / matched_motion_no / match_confidence
    filled ONLY on the unique links (CITY-side convention; kept as the working catalog).
  * ordinances/index.csv    <- the loader-facing artifact: preserves the codified-code
    (code_snapshot) rows and merges all adopted rows carrying a DIRECT utah_county.db
    `motion_id` (blank where unlinked). The federated loader (build_search_layer.py)
    applies the entity offset itself.

DERIVED + idempotent: recompute from adopted_ordinances.csv + utah_county.db each run.
Runs AFTER build_db.py (the BoC motions must exist).
"""
import csv, os, re, sqlite3
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
DB = os.path.join(HERE, "utah_county.db")
ORD_DIR = os.path.join(COUNTY, "ordinances")
ADOPTED = os.path.join(ORD_DIR, "adopted_ordinances.csv")
INDEX = os.path.join(ORD_DIR, "index.csv")

ORD = re.compile(r"\bordinance\b", re.I)
ADOPT_SHAPE = re.compile(r"\badopt(?:s|ed|ing)?\b.*\bordinance\b|\bordinance\b.*\bamend", re.I)
NEG = re.compile(r"agreement|resolution|interlocal|deferred comp|purchase|\blease\b|"
                 r"compliance agreement|bond for", re.I)
CONT = re.compile(r"\bcontinue\b|\btable\b|\bpostpone\b", re.I)

# merged index.csv schema: codified-code columns preserved + ordinance/link columns added
INDEX_COLS = ["doc_type", "ordinance_no", "adoption_date", "title", "land_use",
              "book_type", "jurisdiction", "recodified_date", "recodified_ord",
              "n_sections", "latest_amendment", "source_book", "n_amendments",
              "motion_id", "match_confidence", "path", "text_path", "format",
              "source_url", "doc_class", "fetch_status", "sha256", "text_chars", "notes"]


def compute_links():
    db = sqlite3.connect(DB)
    by_date = defaultdict(list)
    for mid, d, tx, mno in db.execute(
            "SELECT m.motion_id, mt.meeting_date, m.motion_text, m.motion_no FROM motion m "
            "JOIN meeting mt ON mt.meeting_id=m.meeting_id JOIN body b ON b.body_id=m.body_id "
            "WHERE b.name='Board of Commissioners'"):
        by_date[d].append((mid, tx or "", mno))
    db.close()

    ords = list(csv.DictReader(open(ADOPTED, encoding="utf-8")))
    ord_by_date = defaultdict(list)
    for o in ords:
        if o.get("adoption_date"):
            ord_by_date[o["adoption_date"]].append(o)

    links = {}   # ordinance_no -> (motion_id, motion_no)
    for o in ords:
        d = o.get("adoption_date", "")
        if not d:
            continue
        cands = [c for c in by_date.get(d, [])
                 if ORD.search(c[1]) and ADOPT_SHAPE.search(c[1])
                 and not NEG.search(c[1]) and not CONT.search(c[1])]
        if len(cands) == 1 and len(ord_by_date[d]) == 1:
            links[o["ordinance_no"]] = (cands[0][0], cands[0][2])
    return ords, links


def main():
    ords, links = compute_links()

    # ---- 1. fill adopted_ordinances.csv matched_* (working catalog) ----
    afields = list(ords[0].keys())
    for o in ords:
        no = o["ordinance_no"]
        if no in links:
            mid, mno = links[no]
            o["matched_motion_date"] = o["adoption_date"]
            o["matched_motion_no"] = str(mno)
            o["match_confidence"] = "high"
        else:
            o["matched_motion_date"] = ""
            o["matched_motion_no"] = ""
            o["match_confidence"] = ""
    with open(ADOPTED, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=afields)
        w.writeheader()
        w.writerows(ords)

    # ---- 2. regenerate index.csv: keep codified-code rows, merge adopted rows ----
    kept = []
    for r in csv.DictReader(open(INDEX, encoding="utf-8")):
        if (r.get("doc_type") or "").startswith("codified") or r.get("doc_class") == "code_snapshot":
            kept.append({c: r.get(c, "") for c in INDEX_COLS})

    adopted_rows = []
    for o in ords:
        no = o["ordinance_no"]
        mid = str(links[no][0]) if no in links else ""
        adopted_rows.append({
            "doc_type": "adopted_ordinance",
            "ordinance_no": no,
            "adoption_date": o.get("adoption_date", ""),
            "title": o.get("title", ""),
            "land_use": o.get("land_use", ""),
            "book_type": "", "jurisdiction": "", "recodified_date": "",
            "recodified_ord": "", "n_sections": "", "latest_amendment": "",
            "source_book": o.get("source_book", ""),
            "n_amendments": o.get("n_amendments", ""),
            "motion_id": mid,
            "match_confidence": "high" if mid else "",
            "path": "", "text_path": "", "format": "html_codified",
            "source_url": o.get("source_url", ""),
            "doc_class": "adopted_ordinance", "fetch_status": "catalog",
            "sha256": "", "text_chars": "",
            "notes": o.get("notes", ""),
        })
    with open(INDEX, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=INDEX_COLS)
        w.writeheader()
        w.writerows(kept + adopted_rows)

    total = len(ords)
    linked = len(links)
    print("ordinance linkage (strict 1:1 date + ordinance-adoption motion):")
    print("  adopted_ordinances.csv: %d rows, %d uniquely linked (high), %d blank (ambiguous/none/pre-2015)"
          % (total, linked, total - linked))
    print("  index.csv regenerated: %d codified-code rows + %d adopted rows = %d"
          % (len(kept), len(adopted_rows), len(kept) + len(adopted_rows)))
    for no in sorted(links):
        print("    %-10s -> motion %d (%s)" % (no, links[no][0], links[no][1]))


if __name__ == "__main__":
    main()
