# SLCo 2016–2021 campaign finance — portal probe, 2026-08-20

Probe agent, read-only. Nothing outside this directory was written. No federation run.

## VERDICT

**Channel (b) — the county disclosure portal — is BLOCKED, and the reason is NOT a WAF.
The application behind the load balancer is DEAD. A real browser does not help.**

**But the era is only PARTLY lost.** A second, freely-downloadable source for the same
window was found on the county's own CMS and is **NOT in this repo**: **130 paper-filed
county-office PDFs for 2015–2021**, sitting on the same clerk page the 547 legacy PDFs came
from, under a URL family (`/globalassets/…`) the 2026-08-01 harvest never matched.

| slice | filings | route | status |
|---|---|---|---|
| paper-filed 2015–2021 | **130** (2015 15 · 2016 29 · 2017 16 · 2018 34 · 2019 10 · 2020 23 · 2021 5 · 2014 2) | plain HTTPS GET, works today | **acquirable now — inventory in `globalassets_inventory.csv`** |
| online-filed 2015–2021 | **251** (2015 14 · 2016 27 · 2017 6 · 2018 75 · 2019 12 · 2020 98 · 2021 19) | `/Search/PublicSearch/Report/{id}` — dead host, never archived | **GRAMA only — inventory in `portal_online_reports_inventory.csv`** |

The two slices are **complementary, not duplicative** (see "Cross-check" below).

## Corrections to RECON.md § "Channel (b)" — the source disagrees with the record

1. **The itemized report URL is NOT `/Report/{id}`.** The archived folder pages call
   `openReport('/Search/PublicSearch/Report/{id}')`. The prior session probed `/Report/1069`,
   which is not an application route at all — that is why it got a bare redirect and why the
   Wayback playback 404'd. Correct pattern: `/Search/PublicSearch/Report/{id}`, ids **1069–2104**.
2. **"WAF-blocked … a real browser TLS/JS session may pass" is WRONG.** Tested and disproved.
3. **Wayback's folder capture is COMPLETE for this category, not partial.** The archived
   `Search/PublicSearch/Category/PCC` listing enumerates **54** County-and-Metro-Township
   folders (ids 129–263) and Wayback holds **all 54** folder pages (131 folder pages total,
   incl. 76 Local School Board + 1 PAC). So the online-filed inventory below is exhaustive,
   not a sample.
4. **The 2015–2021 paper PDFs exist and are free.** AVAILABILITY.md already knew the
   `/globalassets/…/financial_disclosure/` host — but only from the **metro-township** page,
   filed as a "BONUS … out of scope" lead. Nobody checked whether the **county-offices page
   itself** served that family. It does: 690 PDF links on that page, of which **135 anchors /
   130 unique files** are `globalassets`, and every one of the 547 already in
   `raw/clerk_legacy/_fetch_log.jsonl` is `slco.org/clerk/financialDisclosurePDF/…`. Zero overlap.

## Evidence — why the portal is dead, not defended

Probed 2026-08-20 from this machine, and independently from Anthropic infrastructure.

**(a) Deterministic, path-selective behaviour.** `Server: BigIP`, DNS `204.99.179.232`.

```
/                                        302 → /Search/PublicSearch   (HTTP/1.0, Server: BigIP)
/foobarbaz                               302 → /Search/PublicSearch
/favicon.ico                             302 → /Search/PublicSearch
/Home/Index          (×6, 2s apart)      302 → /Search/PublicSearch   ← deterministic
/Report/1069                             302 → /Search/PublicSearch   ← not an app route
/Content             (no slash)          302 → /Search/PublicSearch
/Search/PublicSearch (×6, 2s apart)      RST  curl(56) Recv failure   ← deterministic
/Search/PublicSearch/FolderDetails/1     RST
/Search/PublicSearch/Report/1069         RST
/Search/AdvancedSearch-family, /Registration/EntityDetails/196, /Scripts/x.js,
/Content/Site.css, /searchx              RST
```

Every path the load balancer forwards to the application pool resets; everything else gets a
clean catch-all redirect. An anti-bot control discriminates by *client*; this discriminates by
*path*, at a flat ~0.23 s (LB-local, no backend latency). Port 80 resets identically.
`disclosure.slco.org` resets identically. The TLS cert is current (Sectigo, valid to
2026-11-18) — the VIP is maintained, the pool behind it is not.

**(b) A real browser gets the same reset.** Google Chrome 151 (local app binary, headless=new,
full TLS + JS, Chrome UA via `Network.setUserAgentOverride`, driven over CDP) navigating to
`https://disclosure.saltlakecounty.gov/Search/PublicSearch`:

```
URL: chrome-error://chromewebdata/
"This site can't be reached — The connection was reset. ERR_CONNECTION_RESET"
```

**(c) Not an IP block on this machine.** The same URL fetched from Anthropic's infrastructure
(WebFetch tool, unrelated source IP) returns `read ECONNRESET`.

**(d) The archive dates the shutdown.** Wayback's captures of `/Search/PublicSearch` are
HTTP 200 through **2026-01-15**; there is no successful capture after that, and no capture at
all after 2026-03. The portal went dark between 2026-01-15 and the 2026-08-01 recon.

**Conclusion: no browser session, and no client-side technique of any kind, reaches this
application. There is nothing to defeat — there is nothing listening.** Per the brief's
constraint, this is where a client-side route stops and GRAMA begins.

**c11 note:** the `c11` app is running but its control socket refuses this process
(`ERROR: Access denied — only processes started inside c11 can connect`; ancestry here is
tmux → claude → zsh, no c11 in the chain). Moot — a genuine browser was used instead, via
Chrome + CDP, and it reproduces the reset exactly.

## Wayback — what it does and does not hold

- `FolderDetails/{id}` for **all 54** County/Metro-Township filers, plus 76 Local School Board
  and 1 PAC (131 pages, ids 129–264, 5 ids absent because they do not exist).
- Category listings (`Category/PCC`, `Category/LSB`, `?type=PCC`, `?type=LSB`) — these are what
  make the folder inventory provably complete.
- **Zero** `/Search/PublicSearch/Report/*` captures. Confirmed by CDX (`…/Report*` → empty).
  The dollar figures were never crawled.

A folder page gives: filer name, cycle-year + office label, per-year "Paper Filed Reports and
Organizational Documents" and "Online Filed Reports" lists, and each online report's numeric id.
That is the whole of what survives of the online-filed slice.

## Cross-check — the two slices barely overlap

Matching the 54 portal filers against the 37 clerk-page candidates that carry globalassets PDFs:

- 34 of 54 portal filers have **no** clerk-page PDF at all (they filed electronically only) —
  e.g. Bradshaw 8 online / 0 PDFs, Swensen 8/0, Rivera 8/0, Newton 8/0, Winder 8/0.
- The filers with rich clerk-page PDF sets have **zero** online reports — Bradley 0 online /
  12 PDFs, Evershed 0/8, Dekeyzer 0/4.
- By year the mismatch is starkest where the portal was busiest: 2020 = 98 online vs 23 PDFs;
  2018 = 75 vs 34; 2016 = 27 vs 29.

So acquiring the 130 PDFs closes a real and distinct part of the hole; it does not make the
GRAMA unnecessary.

## Data shape — proof-of-route captures (`samples/`)

Four PDFs pulled by plain GET (browser UA), one per era. All `200 application/pdf`.
**All are image-only scans — `pdftotext` yields 1–10 characters.** Vision is the only channel,
exactly as for `raw/clerk_legacy/`.

| file | era | pages | what it is |
|---|---|---|---|
| `max-burdick--council-6_redacted.pdf` | 2016 June interim | 4 | cover + Summary Page + schedules |
| `bradley-jim--council-at-large-c1.pdf` | 2018 Sept 15 interim | 6 | cover + Schedule A (page 2 of 5) |
| `evershed-amendment-09-2018.pdf` | 2018 (filed under a 2016 folder) | 10 | amendment |
| `burdick-fin-report-3.pdf` | 2020 Sept 15 | 1 | Schedule B only — a filing split across files |

**It is the SAME FORM the repo already transcribes.** Verified on the page images:

- Cover: `Salt Lake County Clerk / <YEAR> Financial Disclosure Report For a Candidate` —
  Name, Office, Political Party, address (county-redacted to a black bar), Office Sought,
  District Number, Type-of-Report checkboxes (April 5 / seven days before primary /
  September 15 / seven days before general / Year-End / Final-Dissolution), amendment
  yes-no, printed name, signature, date, clerk RECEIVED stamp.
- **Summary Page** (`burdick 2016` p2): Column A "Total this Period" / Column B "Aggregate
  Total", lines 1–7 exactly as documented in `campaign_finance/CLAUDE.md`. Slashed-zero
  glyphs present → the repo-wide zero-glyph ruling applies unchanged.
- **Schedule A — Itemized Contributions Received** (`bradley 2018` p3):
  `Date Received | Name of Contributor | Complete Mailing Address | Occupation/Employer |
  Amount $`, then `SUBTOTAL FOR THIS PAGE` and `TOTAL CONTRIBUTIONS RECEIVED (Sum of subtotals
  from all Schedule A pages)`. Page-numbering box top-right (`Page 2 of 5`, last name, date).
- **Schedule B — Itemized Expenditures Made** (`burdick 2020`):
  `Date of Expenditure | Name of Recipient | Purpose | Amount of Expenditure`, same two totals.

⚠ **One field is NEW relative to the 2006-era corpus: `Occupation/Employer` on Schedule A.**
The wave-B2 contribution rows have no home for it (`scripts/campaign_finance/SCHEMA.md` carries
donor name / city / state / district, not occupation). Values observed: "RETIRED", "PAC",
"BUSINESS OWNER", "LEGISLATOR", "INVESTMENT COMPANY". A schema decision for the coordinator —
it is genuinely useful donor-classification signal and it is printed on the form.

⚠ **Mailing Address is redacted at source** (solid black bar) on the `_redacted` files, so the
existing privacy contract (`donor_city`/`donor_state` only) is satisfied trivially here; note
that "redacted by the county" and "left blank by the filer" must stay distinguishable, per the
wave-B2 contract.

⚠ **Folder year lies.** `2016_disclosures/september/evershed-amendment-09-2018.pdf` and
`…/bradley-september-amendment-2018.pdf` are 2018 documents parked in a 2016 folder. Same
GOTCHAS rule as everywhere: the form governs, the listing label does not.

⚠ **Filings are split across files** in this era (`burdick-fin-report-3.pdf` is a bare Schedule
B page). Do not assume one PDF = one complete filing; page-1-is-the-cover does not hold.

## Volume estimate for an acquisition wave

**Plain-GET slice (do this first — no permission needed, it is already public):**
130 unique PDFs, 37 candidates, 2015–2021. Page count in the 4 sampled files is 1–10, so
expect ~400–700 page renders total — roughly **one-quarter the size of the wave-B2 legacy
tranche** (496 filings). The existing pipeline applies unchanged: `build_index.py` fetch-log
convention → vision totals tranche → `make_itemized_caches.py` itemization, same per-row
contract in `_backups/2026-08-02-tranche3/slco-b2/AGENT_BRIEF.md`. Estimate **1 harvest agent +
4–5 transcription agents**.

**GRAMA slice:** 251 online-filed reports, 54 filers, 2015–2021, report ids 1069–2104. Because
the county's own system rendered these, they should exist as database rows or as generated
report files — ask for the export, not for 251 printouts.

**Out of scope but adjacent** (already logged in AVAILABILITY.md, and the same globalassets
host): metro-township councils 297 PDFs, local school board 76 portal folders + a clerk page.

## Files in this directory

- `NOTES.md` — this file.
- `globalassets_inventory.csv` — 135 anchors / 130 unique URLs, candidate + office + listing
  label + folder year/period + direct URL. Ready to drive a fetch wave.
- `portal_online_reports_inventory.csv` — 251 rows: folder id, filer label, reporting year,
  report id, the dead URL, and the Wayback URL of the folder page that proves the filing exists.
- `GRAMA_EMAIL_2026-08-20.txt` — DRAFT ONLY, not sent.
- `samples/` — the 4 proof-of-route PDFs + `samples/png/` page renders.
