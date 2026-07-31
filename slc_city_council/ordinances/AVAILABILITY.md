# SLC adopted ordinances — availability & coverage

*As of 2026-07-05 (2026 backfill 2026-07-19). Additive dataset. Window: 2020–2026.*

> **2026-07-19 backfill.** The 21 owed 2026 instruments — **Ordinances 19–25 + 27–40 of
> 2026** (26 was already indexed) — were added, completing the contiguous 2026 sequence
> **1–40** with no gaps. All 21 are minutes-attested `within_source` with a **unique**
> adopting-motion link (each maps to exactly one Council motion in
> `../meeting_minutes/all_votes.csv`; enacting votes recorded 2026-05-19 / 2026-06-02 /
> 2026-06-16, the last being the FY2026-27 budget formals). No independent numbered
> corroboration was reachable for these (see archive-access note below), so none reach
> `high`/`medium` — the honest minutes-attested tier. (TODO logged "22"; the true
> enumeration 19–25 + 27–40 is **21** numbers.)

## What this is

An index of **Salt Lake City adopted ordinances** (`Ordinance NN of YYYY`), keyed by
ordinance number → adoption date → subject → the adopting **Council** motion in
`../meeting_minutes/all_votes.csv`. SLC assigns an ordinance number *at adoption*, so a
number printed in the minutes is an adopted instrument. **Only the Council adopts
ordinances** — the RDA/CRA/LBA bodies that share SLC's minutes documents pass
*resolutions*, and none of the 2,777 ordinance-motion vote rows carry any body but
`Council`, so every row here is `body=Council`.

## Counts

- **464 adopted ordinances** total (2020–2026), all unique `NN of YYYY`.
- By year: **2020 · 48**, 2021 · 71, 2022 · 74, 2023 · 68, 2024 · 92, 2025 · 71, 2026 · 40.
- **Land-use ordinances: 151** (`land_use=yes` — rezones, zoning map/text amendments,
  Title 21A changes, general/master/station-area plans, subdivisions, annexations,
  street/alley closures, ADU/form-based/adaptive-reuse, historic-district).
- `format`: **416 text** (2021–2026 PrimeGov minutes) · **48 scanned** (2020 Laserfiche OCR).

## Confidence tiers (`match_confidence`)

| tier | n | meaning |
|------|---|---------|
| `high` | **9** | number printed in BOTH an independent retained doc AND a Council motion |
| `medium` | **49** | land-use ord whose adoption date+subject matches the independent SLC Planning *Adopted Zoning Amendments* list |
| `within_source` | **352** | reconstructed from Council motion text only — **NOT independently corroborated** (the dominant tier; see below) |
| `none` | **54** | no matched vote row (empty match fields — never forced): 48 are 2020 (pre-vote-floor), 6 are consent-folded 2021 budget ords |

`high` set = 14/17/19/23 of 2023 and 67/68 of 2022 (SLC Planning adopted-zoning list) +
48/54/56 of 2024 (PMN *Ordinance Synopsis* notices) — see `raw/`.

## Is there an independent adopted-ordinance archive? Yes — but not GET-enumerable

The dominant tier is `within_source` because **no machine-readable, publicly numbered
2020+ ordinance index is reachable under polite GET-only**:

- **American Legal** (`codelibrary.amlegal.com/codes/saltlakecityut`) — **403 bot-blocked**,
  and it publishes only current consolidated code text, no adoption history.
- **City Recorder Laserfiche archive** — `webdme.slcgov.com/OrdinancesResolutions/`
  (a.k.a. *tinyurl.com/SLCAdoptedLegislation*) **IS live and is the signed-ordinance
  archive of record**, but it is a JavaScript/cookie-gated WebLink SPA: `Browse`/`DocView`
  return only the app shell (≈2–3 KB), and there is no GET-reachable listing or document
  export. It exists; it is not harvestable here.
- **SLC Infobase chronological listing**
  (`slc.gov/slc-infobase/ordinances-by-chronological-listing/`) — retained in `raw/`;
  its per-number listings **stop at 2010–2019**. There is no public numbered 2020+ page.
- **Utah Public Notice (PMN) body-1788 "Notice/Synopsis of Ordinance"** — the independent
  corroborator, but its search is JS/opaque (same limitation logged for other cities in
  the repo). Individual notice pages *are* GET-fetchable once their URL is known.

So corroboration is a **retrieved sample** (7 independent raw docs), which anchors the 9
`high` + 49 `medium` rows. Everything else is honestly labeled minutes-derived, matching
the established repo convention (nephi/logan/orem ordinance datasets).

**Re-probe 2026-07-19 (for the 19–40 of 2026 backfill).** The JS gate is unchanged:
`webdme.slcgov.com/OrdinancesResolutions/` now returns an explicit Laserfiche WebLink
"Cookies are not enabled… must be enabled to sign in" wall + `Login.aspx` redirect — a
cookie/login SPA, still not GET-harvestable. The SLC Planning *Adopted Zoning Amendments*
list (GET-reachable) carries **no ordinance numbers** and does not yet enumerate the
May/June 2026 address-based rezones (19/20/22/23/24), so it can't lift them to `medium`.
PMN body-1788 synopsis **search** remains JS-opaque; individual notice URLs are fetchable
only once known, and none were discoverable for these 21 by title. Net: no independent
numbered source reachable → all 21 stay `within_source` (minutes-attested). A future
headless/cookie-capable fetch of `webdme.slcgov.com` remains the only path to signed-PDF
text (still deferred; see repo `TODO.md`).

### Raw independent docs retained (`raw/`, provenance in `raw/_fetch_log.jsonl`)

- `slc_planning_adopted_zoning_amendments.html` — SLC Planning *Adopted Zoning
  Amendments* (land-use corroboration; explicit numbers 14/17/19/23 of 2023, 67/68 of 2022).
- `slc_pmn_ord_48_of_2024_consolidated_fee.html`, `..._54_of_2024_zma.html`,
  `..._56_of_2024_adaptive_reuse.html` — PMN *Ordinance Synopsis* notices (independent, numbered).
- `slc_pmn_notice_811219_zma_130N2100W.html` — PMN ZMA hearing notice (petition PLNPCM2022-00833).
- `slc_ord_mu8_ballpark_subdistrict_signed.pdf` — a signed SLC ordinance PDF from slcdocs.com (398 KB).
- `slc_infobase_ord_chronological_listing.html` — proves the public numbered index stops at 2019.

## The 2021+ vote floor

Council roll-call votes exist **2021+ only** (2020 minutes are Laserfiche OCR; no votes
were extracted). The **48 · 2020 ordinances therefore cannot link** to a vote row — they
are `match_confidence=none`, `format=scanned`, adoption date/subject taken from the OCR
minutes snippet. This is a coverage floor, not a gap in this dataset.

## Audit signal — adopted ordinances missing from `all_votes.csv`

Among **2021–2026** (the vote-era), only **6** ordinance numbers appear in the minutes
with **no per-number vote row**: **26–31 of 2021**, the FY2021-22 budget appropriation
ordinances (A–F). They are **consent/omnibus-folded** — adopted together under the single
omnibus budget motion of 2021-06-15, which the vote layer records as the budget motion,
not six per-number motions. No land-use adoption is missing. In other words, **essentially
every standalone-numbered adopted ordinance in the vote era carries a matching vote row.**
These 6 rows are flagged in `index.csv.note`.

## Gaps / caveats

- `within_source` (331 rows) is the honest dominant tier — treat these as
  minutes-attested, not independently verified.
- 2020 titles are mid-sentence OCR snippets (clean, readable; no junk detected) rather
  than formal ordinance titles.
- The signed-PDF text of individual ordinances is **not** stored (Laserfiche is JS-gated);
  only the sampled independent docs above are retained. A full signed-PDF backfill would
  require a headless/cookie-capable fetch of `webdme.slcgov.com` — deferred (see repo `TODO.md`).
