# Salt Lake County — Ordinances module: SOURCES & provenance

Adopted **Salt Lake County ordinances** as a searchable plain-text corpus, each linked to
the **County Council motion that enacted it** (the vote linkage). Built 2026-07-11.

## Where these come from

Salt Lake County is a **Legistar** body (client `slco`, `webapi.legistar.com/v1/slco`;
public site `slco.legistar.com`, file host `slco.legistar1.com`). Every ordinance moves
through the Council as a **matter** (`MatterId`). The ordinance document itself is a
**matter attachment** — the "approved as to form / ready for adoption" ordinance drafted
by the District Attorney, presented for the adopting vote.

Two joins tie an ordinance to its enacting vote, both from `db/salt_lake_county.db`
(READ-ONLY here — nothing in this module writes to the db):

1. `motion` → the enacting Council motion. Candidate set:
   `outcome='Pass' AND motion_text LIKE '%ordinance%'` (115 motions / 114 matters).
2. `application.app_key = 'matter:<MatterId>'` → the Legistar `MatterId`;
   `meeting.meeting_date` → the adoption date.

For each `MatterId` we fetched
`https://webapi.legistar.com/v1/slco/matters/<MatterId>/attachments`, downloaded the PDF
attachment that is the ordinance (confirmed by ordinance language in the extracted text —
`ORDINANCE NO.`, `AN ORDINANCE …`, `… ordains as follows`), and extracted text with
`pypdf`. `source_url` in `index.csv` is the exact attachment URL for every row.

## Retrieval method

- Candidate motions exported from `salt_lake_county.db` (see query above).
- Attachments listed per matter via the Legistar API; API calls throttled ~0.12s apart
  with 4-try retry (the `slco` endpoint drops connections under load).
- Ordinance PDF chosen per matter by ranking attachment names (`…ordinance…` /
  `…RAFL/RATF/final…` first, `staff report`/`map`/`notice` last) and confirming
  **ordinance language anywhere in the full extracted text** (not just the head — several
  ordinances sit behind a multi-page cover letter / staff report inside the same PDF,
  e.g. matter 5396).
- Text extracted with `pypdf` (`PdfReader`, per-page `extract_text()`) → `text/<stem>.txt`.
- **All 67 PDFs are born-digital** (clean extractable text, largest ~1.2 MB). No scan/OCR
  floor was hit; **no PDF exceeded 50 MB**, so every ordinance is stored in `raw/`
  (nothing is link-only).

## Regenerate a text file

    python3 -c "from pypdf import PdfReader; \
    open('text/<stem>.txt','w').write('\n'.join((p.extract_text() or '') \
    for p in PdfReader('raw/<stem>.pdf').pages))"

## Inventory

- **67 distinct adopted ordinances**, 2020-01-07 → 2025-05-06, each with a raw PDF +
  extracted text + a unique enacting Council motion.
- **Enacting-vote linkage:** 64 `high`, 3 `medium`, 0 `low`. Every row links to one
  `motion_id` in `salt_lake_county.db` (join `motion_id` → the roll call in
  `motion`/`vote`, or gov.db `city='salt_lake_county'`).
- **Land use:** 23 land-use (rezones, Title 19 zoning, Title 18 subdivisions, ADUs,
  FCOZ/foothill, hydrology studies, MIH plan, Olympia Hills MDA), 44 non-land-use
  (governance, procurement, ethics, health, holidays, tax, RDA project-area dissolutions).

## HONEST GAPS

### 1. Ordinance numbers are NOT recoverable from Legistar → `ordinance_no` is blank for all 67
The Legistar attachment is the **pre-signature draft**. Its number line literally reads
`ORDINANCE NO. ______________` — the sequential number is assigned only on the **signed,
recorded** copy, which Salt Lake County does **not** publish as a Legistar attachment.
Per the repo's cardinal rule, a number is **never fabricated**: every `ordinance_no` is
left blank. Recovering the assigned numbers would require the County Clerk/Recorder's
signed-ordinance register (or a Municode/American Legal codified cross-reference) — logged
as a follow-up, not invented here.

### 2. Matters with no ordinance PDF (in `gaps.csv`, 24 matters) — correctly NOT ordinances
The candidate query (`motion_text LIKE '%ordinance%'`) also catches motions that merely
*mention* "ordinance." None of these produced a signed ordinance PDF, and on inspection
none is an adopted ordinance:
- **Resolutions** (budget / ad-valorem tax rate / Consolidated recognition / constable
  appointment): 5221, 5763, 6521, 7130, 8413, 9470, 9715, 10383, 10930, 11451 — a
  resolution is not an ordinance. Two **fee-waiver resolutions** (6472, 7497) that matched
  only on the phrase "County Ordinance 3.42.073" are logged `not_an_ordinance`.
- **Legislative intents / informational briefings**: 5918, 7007, 10222, 10372.
- **Set-/hold-public-hearing procedural motions** whose adoption is elsewhere or not
  separately adopted: 7521, 7565, 7714, 9795, 9815; and 3 **Olympia Hills** public-hearing
  matters (4700, 4707, 4709) that carry no PDF (or no) attachment at all.

### 3. Procedural / duplicate lifecycle stages (in `gaps.csv`, 23 matters) — deduplicated
SLCo files **separate matters** for "Set Public Hearing," "Public Hearing," and "Adoption"
of the *same* ordinance, each re-attaching the same draft. To avoid double-counting, the
catalog holds **one row per adopted ordinance, keyed to the enacting adoption vote**;
the set-hearing / public-hearing / first-reading / initiation stages are moved to
`gaps.csv` (`gap_type='procedural_or_duplicate_stage'`) with a pointer to the adopting
matter where one exists (e.g. the ADU set-hearing/public-hearing matters 6981/7012 point
to the adoption at matter 7035). A few reading/initiation-stage ordinances whose adoption
was not separately captured in the motion set (mineral-extraction 7175, changing-facilities
9713, FR/FA animal-uses 9876) are logged here rather than asserted as adopted.

### 4. Word-document ordinances (3 rows) — text captured from the accompanying PDF
For matters 7036 and 7695 the signed ordinance was attached as a **Word document** (not a
PDF); for 9287 no standalone ordinance PDF was attached. In these cases the ordinance text
was captured from the accompanying **staff-report PDF** (which embeds the full ordinance);
this is noted per-row in `index.csv`.

## Verify a source link

    curl -sSI "<source_url>" | grep -i "http/\|content-type\|content-length"

Expect `200` and `application/pdf`.
