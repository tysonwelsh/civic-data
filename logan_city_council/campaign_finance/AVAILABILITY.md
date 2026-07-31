# Campaign-finance disclosures — availability & sources checked

**As-of: 2026-07-05.** Dataset for **Logan City** (Cache County, Utah) municipal
candidates — **Mayor + City Council (5 at-large seats, no districts)** — for the
**2019, 2021, 2023, 2025** cycles (including primaries).

**Result: PARTIAL.** Logan self-hosts its municipal campaign-finance statements on the
**city recorder's election page**, but only the **2025** cycle is fully published and
live; **2021** survives only in the Internet Archive (7 of 8 filings recovered); the
**2023** cycle is archived only as dead redirects (0 of 21 recoverable); and the **2019**
cycle was never published online at all. **45 filings retrieved** (38 × 2025, 7 × 2021),
**69 MB**. Every retrieved filer joins to `election_results/` (**45/45 rows, 18/18
distinct (year,candidate) — 100%**). All filings are **scanned handwritten forms**
(Utah "Financial Disclosure Report"); OCR text sidecars in `text/`.

---

## Where Logan candidate financial statements actually live

Logan runs its **own** municipal disclosure — the Lieutenant Governor's state site
(`disclosures.utah.gov`) does not host Logan candidate PDFs, and Cache County runs the
election mechanics (canvass/results), not the filings. The statements are posted by the
**city recorder** on the election page:

- **Current / live:** `https://www.loganutah.gov/government/mayor_s_office/election.php`
  — a Revize-CMS page with a **"Campaign Finance Statements"** accordion. As of 2026-07-05
  it lists **only the 2025 cycle**, one PDF per candidate per statutory deadline
  (Aug 5, Sep 11, Oct 7, Oct 28, Dec 4 2025). PDFs live under
  `/departments/admin/council/<Name> <Month D, YYYY>.pdf`. Downloaded directly.
- **Legacy domain (dead):** `https://www.loganutah.org/departments/admin/council/`
  hosted the 2021 & 2023 statements as `<Name> <YYYYMonthD>.pdf`. **`loganutah.org` now
  404s entirely** (migrated to `loganutah.gov`, then to the `cms9files.revize.com/loganut`
  CDN). Those cycles were sought in the **Wayback Machine**.

The **election.php page itself is only archived from 2024-05 onward**, and the earliest
snapshot has **no** campaign-finance section — so there is no archived index page listing
the 2021/2023 filings. They were found instead by **enumerating the legacy council
directory via the Wayback CDX API** and pattern-matching candidate-name + report-date
filenames.

---

## Per-cycle coverage

| Cycle | Published online? | Retrieved | Source | Notes |
|---|---|---|---|---|
| **2025** | Yes (live) | **38 / 38** | live `loganutah.gov` | Complete. 13 filers (5 Mayor, 8 Council) across 5 deadlines. |
| **2021** | Yes (legacy, now dead) | **7 / 8** | Wayback (`loganutah.org` captures) | Keegan Garrity's Oct-26 filing archived only as a redirect (unrecoverable). Ernesto Lopez (council winner) **never had a finance statement posted** — only a Declaration of Candidacy. |
| **2023** | Yes (legacy, now dead) | **0 / 21** | — | All 21 statements exist in the CDX index but Wayback holds **only 302 redirects** to the `cms9files.revize.com` CDN; the CDN target 404s live and was never captured as bytes. **Unrecoverable** (see `unrecovered.csv`). |
| **2019** | **No** | **0** | — | Logan published no campaign-finance statements online for 2019 (only candidate declarations/bios survive). Pre-dates the online-posting practice. |

**24 known-missing filings are logged in `unrecovered.csv`** (21×2023, Garrity 2021, Lopez
2021 never-posted, and the 2019 whole-cycle note).

---

## Sources checked (each host/query, and what it had)

| Source | URL / query | Result |
|---|---|---|
| City election page (live) | `loganutah.gov/government/mayor_s_office/election.php` | **HIT** — "Campaign Finance Statements" accordion, 38 × 2025 PDFs (+ a blank fillable form + candidate guide, excluded). |
| City site (live) | `loganutah.gov/departments/admin/council/<2021/2023 filing>.pdf` | 404 — prior cycles not re-hosted on the live site. |
| Revize CDN (live) | `cms9files.revize.com/loganut/departments/admin/council/<filing>.pdf` | 404 for 2021/2023 candidate statements. |
| Legacy domain (live) | `loganutah.org/...` | 404 — whole domain retired. |
| Wayback CDX | `cdx/search/cdx?url=loganutah.gov*&filter=original:.*[Dd]isclosure.*` / `.*[Cc]ampaign.*` / `.*[Ff]inancial.*` | Surfaced only a conflict-of-interest page + budget docs — the filings are not keyword-named. |
| Wayback CDX | `cdx/search/cdx?url=loganutah.org/departments/admin/council*` (1,309 rows) | **HIT** — enumerated the legacy council dir; 8×2021 + 21×2023 candidate finance filenames found. |
| Wayback captures | `web/<ts>id_/https://www.loganutah.org/.../<Name> 2021...pdf` | 2021: real 200 PDF bytes (7 of 8). 2023: **302 redirect → CDN**, and `web/<ts>id_/…cms9files.revize.com/…` = 404 (no byte capture). |
| Wayback CDX | `cdx/search/cdx?url=cms9files.revize.com/loganut/departments/admin/council*` (1,625 rows) | 200 captures for the 2021 files (same bytes as `.org`); **no** capture of any 2023 finance PDF. |
| Wayback (election.php) | `cdx/search/cdx?url=loganutah.gov/government/mayor_s_office/election.php` | 7 snapshots, all **2024-05 or later**; earliest has **no** finance section → no archived index for 2019/2021/2023. |
| EasyVote | `ecf-api.easyvoteapp.com/api/getwebsiteuser/{logan,loganut,logancity}` | 404 — Logan does **not** use EasyVote. |
| `disclosures.utah.gov` | state municipal tree | Not a byte host for Logan candidates (link directory back to the city; enumerable only via JS/POST). Logan self-hosts. |

---

## Discrepancies flagged (NOT edited — additive dataset)

1. **Ernesto Lopez, 2021 council winner — no finance statement published.** Only his
   Declaration of Candidacy is online. This is a **city publishing gap**, not an
   archival loss. `election_results/` correctly lists him as the 2021 general winner.
2. **Keegan Garrity, 2021 Oct-26 statement — exists but unrecoverable** (Wayback holds
   only a redirect; CDN 404). His Aug filing was never required (council had no 2021
   primary). Garrity is in `election_results/` (2021 general, did not win).
3. **2023 cycle — 21 statements provably existed** (their filenames are in the Wayback
   CDX index for `loganutah.org`) **but none are byte-recoverable.** Every 2023 candidate
   (Anderson, Johnson, Simmonds, Needham, Lee-Koven, Bennett, Molitor, M. Fatuesi, Taylor)
   is in `election_results/`; none has a finance filing here.
4. **2019 cycle — no online campaign-finance publication.** No conflict with
   `election_results/` (which has 2019 results); simply nothing to fetch.

No new election-record errors were found: every retrieved filer matches an existing
`election_results/logan_results_by_candidate.csv` row (100% join). The 2021 council race
had **no primary** (3 candidates), consistent with the election dataset.

---

## Method notes / caveats

- **All 45 filings are scanned handwritten forms** (`format=scanned`). `text/` holds a
  `tesseract` OCR sidecar for **every** filing, but OCR of handwriting is **lossy** — the
  **raw PDF is authoritative**. No dollar amounts are transcribed or asserted anywhere in
  this dataset; open the raw PDF to read a filing.
- **Dates are the statutory report deadline** parsed from the filename, not the exact
  moment of filing. `filing_type`: pre-primary/pre-general deadlines = `interim`;
  post-primary "eliminated" and year-end deadlines = `summary`.
- **Filenames prefixed `YYYYMMDD_`** (report deadline) to prevent cross-period collision.
- Source URLs are the **original** city URLs (`loganutah.gov` for 2025, `loganutah.org`
  for 2021), not the Wayback wrapper; provenance (Wayback URL, HTTP status, sha256) is in
  the per-year `raw/<year>/_fetch_log.jsonl`.
