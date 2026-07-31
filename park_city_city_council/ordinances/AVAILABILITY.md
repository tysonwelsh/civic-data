# ordinances/ — availability & coverage (built 2026-07-05; refreshed 2026-07-19)

Additive dataset built by the `expand-city-sources` skill (Source 3: zoning/land-use
ordinances). **Read-only** on every existing dataset — nothing here modifies
`meeting_minutes/`, `planning_commission/`, `db/`, etc.

## What this is
An index of **adopted Park City ordinances, 2020–2026** (262 rows), each linked to the
council **motion** that adopted it in `meeting_minutes/all_votes.csv`, with an honest
confidence tier. Emphasis is **zoning / land-use**: **160 of 262 (61%)** are land-use
(subdivision/plat 107, LMC text amendments 37, zone-map changes 7, annexations 4,
general-plan amendments 2, plus overlay/housing/area-plan singles).

**2026-07-19 Q3-refresh reconcile (+2 rows, 260 → 262).** The votes refresh extended
`all_votes.csv` to 2026-07-09, so the three formerly beyond-coverage signed ordinances
`2026-14/16/17` now link to their 2026-06-25 council motions → `high` (none 5 → 2), and the
06-25 meeting added two number-cited-but-not-yet-signed ordinances `2026-15`/`2026-18` →
`within_source` (93→96 high, 162→164 within_source). See **"Signed PDFs still owed"** below.

## Does an independent archive exist? YES.
Unlike most cities in this repo, Park City publishes **full signed ordinance PDFs** to a
public, list-able archive: the Municode **MunicipalCodeOnline** ordinance document store
(S3 bucket `municipalcodeonline.com-new/parkcity/ordinances/documents/`, surfaced by
`parkcity.municipalcodeonline.com`). The bucket held **371 ordinance PDFs** total
(2000–2026); **98 distinct in-window numbers (104 files)** were harvested to `raw/`
(83 MB, all born-digital text — 0 scanned, 0 OCR). Each signed PDF states its number, full
title, and a *"PASSED AND ADOPTED this <day> day of <Month>, <Year>"* clause — an
**independent adoption record**, not derived from the minutes. This is what makes 96 rows
`high` confidence.

## Do the minutes cite ordinance numbers? YES.
Park City council motions restate the adopted number in the motion text, in two spellings —
`Ordinance 2020-14` (2020) and `Ordinance No. 2020-14` (all years) — both normalized here to
`YYYY-NN`. This is the backbone for rows without a signed PDF. (Contrast Orem, which cites no
numbers.) Per-year number coverage is near-sequential (2020: 52 numbers, 2021: 50, 2022: 47,
2023: 55), i.e. the minutes capture essentially the full adopted sequence for 2020–2023;
2024–2026 cite fewer (22/22/12) and the signed archive fills the gaps.

## Confidence tiers (see CLAUDE.md for definitions)
| tier            | rows | meaning |
|-----------------|------|---------|
| `high`          | 96   | number in BOTH the signed PDF AND a council motion (cross-source). |
| `within_source` | 164  | number known ONLY from council motion text (no signed PDF in the S3 archive). Strong but **within-source** — the number/date/subject all come from the same audited minutes row, not corroborated independently. |
| `none`          | 2    | signed ordinance with no linkable vote row (see Gaps). Match fields left empty — never forced. |
| `medium`/`low`  | 0    | the date+subject fallback ladder is implemented but was not needed — every in-window signed ordinance either matched by number (→`high`) or fell to `none`. |

- **signed PDFs retained**: 98 numbers (rows with `has_signed_pdf=yes`); the other 164 are minutes-derived.

## Signed PDFs still owed (2 — honest acquisition gap, logged 2026-07-19)
Two 2026 ordinances have their **adopting motion captured** (`within_source`, number cited
in the 2026-06-25 council motion) but **no signed PDF** to lift them to `high`:

| ord | title | adopting motion | result |
|-----|-------|-----------------|--------|
| `2026-15` | adopting a revised budget for FY2026 and a final budget for FY2027 | 2026-06-25 m11 | 5-0 Pass |
| `2026-18` | establishing compensation for the Mayor, City Council, and Statutory Officers (FY27) | 2026-06-25 m10 | 3-2 Pass |

**Why they are not yet in the independent archive** (verified 2026-07-19): the Municode
**MunicipalCodeOnline S3 bucket** — the dataset's canonical signed-PDF source — was re-listed
in full (371 keys, `IsTruncated=false`) and contains **no** `2026-15`/`2026-18` under any
key; it ingested the three *codified* 06-25 ordinances (`2026-14/16/17`) but not these two
**non-codified administrative** (budget / elected-official-compensation) ordinances, which it
historically does not carry. They are **not** published as standalone CivicClerk files either
(the 2026-06-25 event `3931` exposes only Agenda / Agenda-Packet / Minutes). Park City does
post adopted ordinances on its own site via the CivicPlus `parkcity.gov/home/showpublisheddocument`
CMS route, but that route did **not** resolve from this environment (the origin serves the
static `/Documents/` tree but returns IIS 404 for every `/home/showpublisheddocument/…` token).
Adoption itself is independently corroborated in the press (TownLift / KPCW / SL Tribune, June
2026). **Recorded as an honest gap — not fabricated to `high`, no packet exhibit mislabeled as
a signed copy.** To close: fetch each ordinance PDF from `parkcity.gov` (showpublisheddocument)
or await the next Municode S3 ingest, drop it in `raw/` (filename carrying `2026-15` / `2026-18`),
and re-run `build_index.py` — the number-match logic will promote both to `high` automatically.

### 2026-07-19 re-probe #2 — signed PDFs still not published; independent adoption NOTICE recovered (PMN)
A second full acquisition pass was run for the two owed signed ordinances. **The signed
ordinance PDFs remain unpublished on every channel; the rows stay `within_source`.** However,
an **independent City-published adoption record was recovered** and archived — it does not
replace the signed copy but it lifts adoption of both ordinances out of "within-source only."

Per-channel results (browser UA, ≥1 s throttle):

| channel | result |
|---------|--------|
| Municode **MunicipalCodeOnline S3** bucket, full re-list (`?list-type=2&prefix=parkcity/ordinances/documents/`) | **absent** — `IsTruncated=false`, carries `2026-14/16/17` (codified) but no `2026-15`/`2026-18` under any key (unchanged from re-probe #1) |
| MCO **Ordinance-Log** app (`/book?type=orddoc`) + its data route `/book/expand?type=orddoc` | **auth-gated** — HTTP 500 "Unauthorized Access"; the log's docs are the same S3 store (absent) |
| **parkcity.gov** `showpublisheddocument/<id>/<ver>` route | route is **valid** (returns real PDFs for known ids) but **not enumerable** — no id for `2026-15`/`2026-18` is exposed anywhere; the site's "Ordinances" nav link just points back to the auth-gated MCO log |
| parkcity.gov is **Revize**, not CivicPlus | so CivicPlus `/Search/Results?searchPhrase=…` and `/DocumentCenter/View/<id>` **404** here (those patterns are CivicPlus-only; they worked on Ogden because Ogden is CivicPlus) |
| Revize **site search** (`/search.php?q=…`) | it is a **Google CSE** (`cx=8904da87583c6b2eb`, client-side); approximated via `site:parkcity.gov` web search — **no** signed `2026-15`/`2026-18` PDF indexed |
| Revize **`/Documents/` tree** — budget, budget-archive, city-council pages | link **budget documents only** (e.g. `FY27 Budget Complete June 23 Version.pdf` — a budget doc, **not** the signed budget ordinance) and route all ordinances to MCO; no signed-ordinance PDFs |
| **Wayback** CDX (parkcity.gov + MCO ordinance pages, from 2026-05) | **0 captures** |
| **PMN** (Utah Public Notice), Park City entity 233 / City Council body 653 | **HIT** — see below |

**PMN find (archived).** The City Recorder's statutory **Notice of Adopted Ordinances** for the
2026-06-25 Council meeting (PMN notice `1090107`, "Park City City Council Regular Meeting",
event date **June 25, 2026**) attaches a document *"Approved Ordinances 2026-15 16 17 18.pdf"*
(`https://www.utah.gov/pmn/files/1455761.pdf`, sha256 `3a7fce0b…`). Its in-body text
independently states, for each number, *"the City Council of Park City, Utah, at its meeting held
on June 25, 2026, adopted Ordinance No. 2026-15, an ordinance adopting a revised budget for
Fiscal Year 2026 and a final budget for Fiscal Year 2027 …"* and *"… adopted Ordinance No.
2026-18, an ordinance establishing compensation for the Mayor, City Council, and Statutory
Officers for Fiscal Year 2026–2027 …"* — a genuine **independent** corroboration of number +
adoption date + exact title for both owed ordinances, published by the City on the State PMN
system separately from the audited minutes.

**Why this does NOT flip the tiers to `high`, and was NOT dropped into `raw/`.** This PMN document
is a **summary adoption notice**, *not* the full signed ordinance (no *"PASSED AND ADOPTED this __
day"* signature clause; the text itself says the full ordinance *"can be obtained at the City
Recorder's Office"*). The `high` tier and the `has_signed_pdf=yes` flag both mean **we hold the
full signed ordinance PDF from the Municode S3 archive**; `build_index.py` also labels every
`raw/` file as a *"Municode MunicipalCodeOnline signed ordinance PDF"* and points `source_url` at
S3. Placing this notice in `raw/` would therefore **mislabel a PMN summary notice as a held
Municode signed ordinance and falsify its source_url** — a fabrication of artifact type, barred by
the cardinal rules. So `2026-15` and `2026-18` **remain `within_source`** and `has_signed_pdf=no`
(honest), but their **adoption is now independently corroborated** by the archived PMN notice.

**Archived at** `independent_notices/pmn_notice_of_adoption_2026-15_16_17_18.pdf` (+ `.txt`,
+ `_fetch_log.jsonl` provenance) — a NEW, clearly-labeled sibling of `raw/` that
`build_index.py` does **not** scan, so `index.csv` is unaffected. **To still close the gap to
`high`:** obtain the full **signed** `2026-15`/`2026-18` ordinance PDF (next Municode S3 ingest,
or a City Recorder's Office request / GRAMA), drop it in `raw/`, and re-run `build_index.py`.

## Gaps & audit signals (adopted ordinances with NO vote row) — 2 rows, all `none`
Both are **consent-agenda / not individually itemized** (true audit signal, in-coverage):
**2024-08** (Special Events, Title 4A; adopted 2024-05-16) and **2026-08** (Property Disposal
review; adopted 2026-05-07). The council met on those dates and the signed ordinance exists,
but the vote layer records only a blanket *"moved to approve the Consent Agenda"* — the number
is not rolled individually, so there is no itemized vote row to link. Genuine coverage nuance,
not a fabrication. (The former beyond-coverage trio **2026-14/16/17** was resolved by the
2026-07-19 votes refresh — they now link to their 2026-06-25 motions → `high`.)

**2026-07-20 — TODO item (b) resolved (verified against the primary minutes).** Both are
**genuinely consent-folded, no separable motion** — NOT an extractor grammar gap. Each ordinance
is an unnumbered line item under the meeting's `CONSENT AGENDA` header (2024-08 = item VI-3 on
2024-05-16; 2026-08 = item IV-1 on 2026-05-07) and was adopted **en bloc** by the single
consent-agenda approval motion, which IS already captured in `meeting_minutes/all_votes.csv`:
**2024-05-16 motion 5** (Parigian moved to approve the Consent Agenda, 5-0 Pass) and
**2026-05-07 motion 4** (Miller moved to approve the Consent Agenda, 5-0 Pass). No per-ordinance
roll call exists to extract, so `all_votes.csv` is unchanged (adding one would fabricate an
itemized vote). The two `none` rows stay `none` with match fields empty (never forced); their
`linkage_note` now cites the specific en-bloc consent motion rather than saying "no vote row."

Also note: 5 `within_source` rows link to a **continue/deny** motion rather than a clean
adoption (2022-05 an ordinance *denying* an application, 2023-06/2023-17/2025-19 continued,
2024-04 a deny motion) — the ordinance number was cited but that specific motion was not the
final adoption; `result` is retained verbatim so these are visible. Spot-check before quoting
an adoption date for these.

## raw/ and text/
- `raw/` — 105 files (104 signed PDFs + 1 `.docx` original of 2020-17, both formats published;
  the index uses the PDF). `raw/_fetch_log.jsonl` = one JSONL line per fetch
  (url, status, bytes, sha256, retrieved_utc) via `polite_fetch.py` (GET-only, browser UA,
  1 s throttle). Every fetch returned HTTP 200.
- `text/` — `pdftotext -layout` of each PDF (104 `.txt`). `screen_corpus.py`: **0** cid /
  PUA-garble / mojibake / replacement-char / stub / read-error flags; advisory flags
  (repeated header lines, mid-page ends, one lower dict-ratio on 2023-09 which carries map
  attachments) are normal for signed legal PDFs with exhibits.

## Rebuild
`python3 park_city_city_council/ordinances/build_index.py` (idempotent; reads `raw/`,
`text/`, and `meeting_minutes/all_votes.csv`). To refresh the archive, re-list the S3 bucket
(`?list-type=2&prefix=parkcity/ordinances/documents/`) and re-run `polite_fetch.py` on any
new keys, then rebuild.
