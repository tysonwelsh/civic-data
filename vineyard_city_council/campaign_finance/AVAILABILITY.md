# Vineyard campaign-finance disclosures — availability & provenance

*As of 2026-07-05. Additive dataset; completes the elections → members → votes chain by
recording who funded the candidates. Documents-plus-index only (no structured
contribution/expenditure tables — that is a separate planned layer, out of scope here).*

## Bottom line

**Vineyard self-hosts its municipal campaign-finance filings on the city website** — there
is no third-party portal. Filings were retrieved for **five cycles (2015, 2017, 2019, 2021,
2025)**; the **2023 cycle is a documented hole** (filed with the city but purged in a CMS
migration and never archived as bytes — see below). **59 filing PDFs, 71 MB**, one text
sidecar each.

| Cycle | Filings | Candidates | Where it came from | Notes |
|------:|--------:|-----------:|--------------------|-------|
| 2015 | 16 | 10 | Wayback (legacy DocumentCenter) | pre-2019 election floor — bonus pre-history |
| 2017 | 11 | 6 | Wayback (legacy DocumentCenter) | pre-floor; 2 final statements unrecoverable |
| 2019 | 13 | 7 | Wayback (legacy DocumentCenter) | all 7 council candidates; 3 PDFs truncated in the archive |
| 2021 | 16 | 7 | Wayback (legacy DocumentCenter) | **complete** (mayor + council); 1 PDF truncated |
| **2023** | **0** | — | — | **UNRECOVERABLE — filings purged pre-archival (see §2023)** |
| 2025 | 3 | 2 | Live city site (`vineyardutah.gov`) | only the 2 primary-losing council candidates posted a statement |

## Where the filings live (hosts tried, in order)

1. **City site — current CMS `www.vineyardutah.gov` (Revize).** This is where live filings
   live. Per-cycle candidate pages —
   `government/city_council_candidates.php` and `government/mayoral_candidates.php` — list
   each candidate's documents (Declaration of Candidacy, Pledge of Fair Campaign Practices,
   Conflict-of-Interest, Bio, **and campaign-finance "Financial Disclosure Statement(s)"**),
   linked as `government/docs/<name>.pdf?t=<ts>`. As of 2026-07-05 these pages carry the
   **2025** cycle only. Only **two** candidates (Steve Terry, Terry Ewing — the two who lost
   the Aug primary) posted a finance statement; the six general-election council candidates
   (Wood, McCumber, Lauret, Nair, Clawson, Rhoton) and both mayoral finalists (Stratton,
   Sifuentes) posted every *other* candidate document but **no campaign-finance statement**.
   That is a genuine city-publication gap, not an acquisition failure. (`elections.php`,
   `2023_election_information.php` etc. exist but carry no finance-doc links; the bare
   `elections.php`/`2025_election_information.php` slugs 404 — the working pages are the
   two `*_candidates.php` pages.)
2. **City site — legacy CMS `www.vineyardutah.org` (CivicPlus), Document Center.** This held
   the 2015/2017/2019/2021/2023 filings under `/DocumentCenter/View/<id>/<name>`. It is now
   **dead**: `vineyardutah.org` 301-redirects to `.gov`, and every `/DocumentCenter/View/*`
   URL 404s on the live site. **The old filings survive only in the Internet Archive.**
3. **Wayback Machine (`web.archive.org`).** First-class recovery tool here. Enumerated via
   CDX (`cdx/search/cdx?url=vineyardutah.org/DocumentCenter*`), filtered for
   finance/disclosure/statement/report, then fetched the born bytes with the `…/web/<ts>id_/<url>`
   replay form (WebFetch cannot reach web.archive.org; used `polite_fetch.py`/urllib, delay ≥2s).
   Filenames prefixed with the DocumentCenter **View id** (stable, collision-proof).
4. **EasyVote (`<sub>.easyvotecampaignfinance.com`).** Tried `vineyard`, `vineyardut`,
   `vineyardcity` — **all fail DNS resolution** (the base domain resolves; no Vineyard
   tenant exists). Vineyard does **not** use EasyVote.
5. **`disclosures.utah.gov`.** The state municipal store returns a filesystem error
   (`Path \\…\Municipal\… does not exist`) — the state does **not** host Vineyard municipal
   filings. Confirms the city self-hosts. (Utah County runs Vineyard's *elections*, not its
   campaign-finance *filings*.)

## The 2023 hole (flagged, not filled)

The 2023 council candidates (Holdaway, Cameron, Welsh, Rhoton, Harbin, Teemsma, Hendrix)
**did file** — the archived Sept-2023 candidate page (`/1553/2023-City-Council-Candidates`)
lists "General Election Financial Disclosure #1 / Financial Statement 2 / 3 / Final" rows for
each, and CivicPlus assigned them DocumentCenter ids 3370–3417. But:
- At the Sept-2023 capture the finance rows were **text placeholders with no working links
  yet** (statements are filed later in the cycle).
- The only Wayback captures of View 3370–3417 are from **2024-03-04, all HTTP 404** — by then
  Vineyard had migrated off CivicPlus and the PDFs were gone. Wayback **never captured the
  bytes**. The live `.gov` site does not republish them.

So 2023 finance content is **lost at every reachable source**. This is *not* an
election-record gap — `election_results/` has the 2023 winners — only the finance documents
are missing. If Vineyard or a candidate re-publishes them, drop them in `raw/2023/` and
rerun `build_index.py`.

## Partial gaps within recovered cycles

- **4 PDFs are truncated in the Internet Archive** to exactly 1 MiB (crawler size cap) and
  are unreadable — re-fetching returns the same truncated bytes, and no alternate capture
  exists. They are retained verbatim (the archive artifact) and labelled
  `extraction_method=unreadable:archive_capture_truncated` with an empty text sidecar:
  2019 Flake interim **and** final (View 1870, 1919 — Flake's 2019 content is fully lost),
  2019 Lauret interim (1876 — his final 1921 is readable), 2021 Cane interim (2486 — her
  redacted duplicate 2491 and final 2556 are readable). Filing *existence* is confirmed;
  only these scans' content is unreadable.
- **3 filings are revisit-only in Wayback** (a dedup pointer whose payload never resolves) —
  not recovered, no bytes available: 2015 Fernandez primary (View 244), 2017 Judd final
  (1038), 2017 Farnworth final (1055). All pre-2019-floor.

## Join to `election_results/`

Every candidate is joined to `election_results/vineyard_results_by_candidate.csv` on
(year, surname) — see `index.csv` columns `matched_election_candidate` / `join_confidence`.
- **2019/2021/2025 (in the election dataset): 32/32 filings joined = 100%.** The finance
  candidate rosters match the election rosters exactly (no unexplained candidates).
- **2015 & 2017 (27 filings): `pre_floor`** — these cycles predate the repo's 2019 election
  floor, so there is no `election_results` row to join. This is expected. Finance data thus
  **extends named-candidate coverage two cycles below the election floor** (e.g. Julie
  Fullmer's 2015 council and 2017 mayor filings, Randy Farnworth as 2015 mayor). Flagged
  here as a coverage note; `election_results/` is **not** edited.

No election-record *discrepancy* was found: no filing implies a candidate or contest that
`election_results/` omits within its 2019+ scope. (`office` for the pre-floor 2015/2017
rows is inferred from public record and marked `office_confidence=inferred`; 2019/2021/2025
offices are `verified` against `election_results` + repo notes.)

## Reproduce

`python3 build_index.py` (idempotent; re-OCRs only missing text sidecars; `--force` re-OCRs
all). Raw provenance: `raw/<cycle>/_fetch_log.jsonl` (url, status, bytes, sha256 per fetch).
Discovery artifacts (CDX enumerations, fetch plan): `discovery/`.
