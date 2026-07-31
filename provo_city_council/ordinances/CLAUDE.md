# ordinances/ — build method, linkage logic, caveats

Adopted Provo ordinances (esp. zoning/land-use), keyed to `ordinance_no`, each linked back
to a council vote in `../meeting_minutes/all_votes.csv`. **Additive / read-only** on all
existing datasets. As-of **2026-07-03**.

```
raw/    31 PMN "Notice of Ordinances Approved" .docx (verbatim) + _fetch_log.jsonl
text/   31 text sidecars extracted from the .docx (word/document.xml → text)
index.csv                one row per distinct adopted ordinance (213 rows)
adopted_not_in_votes.csv audit list: PMN-adopted ordinances with no matching motion
AVAILABILITY.md          what exists / what doesn't / how verified
```

## Sources (two, deliberately kept distinct)
1. **PMN Notice-of-Ordinances (INDEPENDENT of the minutes).** Utah Public Notice Website,
   *Provo Municipal Council* body **1600**. Discovered via the cumulative GET list
   `https://www.utah.gov/pmn/list/notices.html?id=1600&page=300` (single high page number =
   full history; the 6-month list view and POST search were avoided). Rows whose title matches
   `Notice of Ordinance(s)` carry a Recorder-certified `.docx` (`/pmn/files/<id>.docx`) that
   lists each ordinance's **number, adoption date, and full title/summary**. 31 docs,
   2024-05-14 → 2026-06-23, 87 distinct ordinances. Fetched with `polite_fetch.py`
   (`--referer https://www.utah.gov/pmn/ --now 2026-07-03T00:00:00Z`); `_fetch_log.jsonl` has
   the sha256/bytes provenance.
2. **Minutes-as-backbone (`../meeting_minutes/all_votes.csv`).** Council motions cite
   `Ordinance YYYY-NN` in their text for 2020–2022 and 2024–2026. This is the ONLY source
   covering 2020–2023 (the code hosts are 403; PMN starts mid-2024), so it is the backbone for
   the early window.

`.docx` text was extracted by unzipping `word/document.xml` and stripping tags (no LLM
cleanup; source wording preserved). `screen_corpus.py`: 31/31 clean — no cid/mojibake/PUA/
split-word outliers (the 6 "short<500B" files are single-ordinance notices, expected).

## Ordinance number normalization
Provo zero-pads inconsistently (`2020-03`, `2020-5`, `2020-09`, `2025-1`). The join key is
`(year, int(sequence))`; `ordinance_no` is written canonical-unpadded (`2025-34`). Match by
this key, not string equality.

## Linkage logic → `match_confidence`
Join PMN ordinances to `all_votes.csv` motions. **Never forced** — an ordinance with no
motion match keeps empty `matched_motion_*` and `match_confidence=none`.

| confidence | meaning | n |
|---|---|---|
| **high** | Ordinance number cited **in a motion's text**, on the PMN adoption date. Independent number cross-match. (All 34 have motion date == adoption date.) | 34 |
| **medium** | Number NOT in the motion, but the **land-use application code** (`PLRZ…`/`PLOTA…`/`PLGPA…`/item id) matches a motion on the same date + subject agreement. (All 20 have a 0-day gap.) | 20 |
| **within_source** | Number cited in a motion but **no independent PMN notice** exists (chiefly 2020–2022, + early-2024 / PMN-omitted numbers). Linkage is **high *by construction* — derived FROM the minutes, NOT corroborated by a second source.** Kept a distinct value so it is never read as cross-verified. | 126 |
| **none** | PMN-adopted, no motion match. See `adopted_not_in_votes.csv`: 30 = adoption date not yet in the vote layer (OnBase minutes lag), 3 = extracted meeting but bundled/amended item with no clean match. | 33 |

`low` is defined (date-only / fuzzy) but was not needed — every non-`none` match resolved to
number (high), same-date app-code (medium), or within-source. **213 total rows.**

## Coverage & composition
- By adoption year: 2020=57, 2021=38, 2022=9, **2023=0 (number gap — see AVAILABILITY)**,
  2024=22, 2025=65, 2026=22.
- **Zoning/land-use: 135 of 213** rows (title matches zone-map / Title 14 / general-plan /
  annexation / `PL…` application code).
- Independent PMN-doc-backed: 87 rows (high 34 + medium 20 + none 33). Minutes-only: 126.

## Caveats
- `format=text` + `path=raw/<docx>` on PMN-backed rows (the retained artifact is the notice,
  a **summary**, not the full ordinance text — full text lives behind
  `documents.provo.org/onbaseagendaonline`, the `packets/` source). `within_source` rows have
  `format=na`, empty `path`, and `source_url` = the repo-relative minutes markdown that cites
  the number.
- One PMN `.docx` covers a *range* of ordinances (e.g. `2026-18..23`); those rows share one
  `path`/`source_url` by design.
- `adoption_date` is parsed from each notice's "approved … on <date>" header (authoritative);
  for `within_source` rows it is the citing motion's meeting date.
- Re-run: re-crawl body 1600, re-parse `all_votes.csv`; as new late minutes land in the vote
  layer, several `none` rows will upgrade to high/medium.
