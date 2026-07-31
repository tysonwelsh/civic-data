# Nephi City — campaign-finance disclosures: availability & coverage

**As of 2026-07-05.** This records every host/URL tried, per-cycle coverage, and honest
gaps. An honest partial result is a valid, complete result.

## Where Nephi campaign-finance filings live

**Nephi City self-hosts every filing** on its own CivicPlus **DocumentCenter**
(`https://www.nephi.utah.gov/DocumentCenter/View/<id>/<slug>`), surfaced from three nav
pages:

- `https://www.nephi.utah.gov/680/Disclosures` — current-cycle candidate disclosures
- `https://www.nephi.utah.gov/618/Candidates` — per-candidate filing links
- `https://www.nephi.utah.gov/269/Elections` — election notices/results (older cycles)

Filings are **not** under a keyword page; each is an individually-named DocumentCenter
item (per candidate, or a per-cycle multi-candidate compilation). Saved-file names are
prefixed with the DocumentCenter **View id** (`cf_<viewid>_<slug>.pdf`).

Every filing is a **handwritten, scanned** "NEPHI CITY CAMPAIGN FINANCIAL REPORT" form
(one-page summary + optional Form A/B itemization). `format=scanned`; each has an OCR
text sidecar in `text/` (`ocr:tesseract --psm 6`, 200 dpi; 150 dpi for the large Canon
scans). **OCR of handwriting is noisy** — the printed form template reads cleanly, but
handwritten names/amounts/dates are approximate. Treat `text/` as a search aid, not an
authoritative transcription; the raw scan is authoritative.

## Hosts checked

| Host | Result |
|------|--------|
| `nephi.utah.gov` DocumentCenter (680/618/269) | **PRIMARY — all filings live here.** 27 filings retrieved. |
| Wayback CDX (`web.archive.org/cdx/search/cdx?url=nephi.utah.gov*`) | Used to locate **de-linked older cycles** (2019 View 1199–1202, 2021 View 2118). Those View ids no longer appear in live nav but the files still serve live, so they were fetched from the live host (no truncated/302 Wayback capture needed). |
| `disclosures.utah.gov` | Not the host for Nephi. State tree is a link-directory back to city sites; Nephi self-hosts. (Consistent with the 2026-07-05 recon note.) |
| Juab County | Runs elections/results, **not** municipal campaign-finance filings. |

## Per-cycle coverage

| Cycle | Filings | Form of publication | Notes |
|------:|:-------:|---------------------|-------|
| **2019** | 4 | 4 individual PDFs (View 1199–1202) | Memmott, Goode, Ostler, Seely (Council). De-linked from live nav; recovered via Wayback CDX discovery → fetched live. All 4 join election_results. |
| **2021** | 6 | 1 compilation PDF, 12 pp (View 2118) | Seely + Nielson (Mayor); Worwood, Parady, Robinson, Callaway (Council). Split into 6 per-candidate index rows (page_range). All 6 join. |
| **2023** | 6 general + interims | 2 compilation PDFs | View **2803** (11 pp, dated 11/14/23) = **final** reports for all 6 general candidates (Parady, Ostler, Bradley, Cowan, Miller, Worwood) — all join. View **2706** (20 pp) = pre-election **interim** filings; see flag below. |
| **2025** | 25 | 21 individual PDFs across 4 reporting rounds | Every 2025 candidate filed. 4 upload batches = 4 deadlines (pre-primary ~Aug 5; two pre-general ~Oct 6–7 and ~Oct 28; final/year-end ~Dec 8), anchored by date-stamped Canon scans of B.S. Miller's filings. |

**Totals:** 27 raw PDFs, 43 filing-level index rows, ~19 MB. Cycles 2019/2021/2023/2025
all represented — no cycle is missing.

## Flags & discrepancies (NOT edited — election_results is authoritative for elections)

1. **2023 primary field not in `election_results`.** The 2023 interim compilation
   (View 2706) contains **~9–10 filer forms** — more than the **6** candidates
   `nephi_results_by_candidate.csv` lists for the 2023 general — and includes at least
   two names not in that roster (OCR-read as **"Vanessa Goode"** and **"Carolyn
   Louise …"**). With a vote-for-3 council seat, a field of 7+ would trigger an Aug 2023
   primary. This suggests the elections dataset omits a 2023 primary / eliminated
   candidates. The two non-roster names are indexed with
   `candidate_match=ocr_uncertain;not_in_election_results`.
   **RESOLVED 2026-07-20 (independently, from the OFFICIAL county canvass — NOT from these
   filings).** A real **Sept 5 2023 Nephi City Council primary** DID happen (9 candidates,
   Vote-For-3, top-6 advanced); it is now in `election_results` (see
   `election_results/CLAUDE.md` + `ELECTION_VERIFICATION.md`). The two OCR-uncertain filer
   names resolve to **VANESSA GOATES** and **CAROLYN L. FORD**, both on the official primary
   ballot (eliminated: 160 and 200 votes). The CF flag correctly predicted the missing primary;
   the filer-count inference (7+) matched the 9-candidate reality. The two names now DO have an
   election_results counterpart (the 2023 primary `is_winner=False` rows), though their
   `candidate_match` in `index.csv` is left as-is (OCR-uncertain on the handwritten forms).

2. **Worwood name ambiguity — kept distinct.** Two different Worwoods filed:
   **SKIP F. WORWOOD** (Council candidate 2021, 2025) and **TRAVIS L WORWOOD** (Council
   candidate 2023). Resolved by surname + first token; never merged. (Mirrors the caveat
   in the parent `election_results/CLAUDE.md`.)

3. **Illegible pages recorded, not attributed.** ~3 pages of the 2706 compilation have
   handwritten candidate names too degraded to read; indexed as one honest
   `(unidentified filers)` row (`candidate_match=unreadable`) rather than guessed.

## Out of scope (present on the same pages, deliberately NOT included)

The `/680/Disclosures` and `/618/Candidates` pages also carry **conflict-of-interest /
municipal-ethics disclosure statements** and **declarations of candidacy** — a different
document class, not campaign finance. Two were fetched during recon and then removed from
`raw/` once their content was confirmed out of scope:
- View **3337** "Seely-Disclosure" = a CDBG conflict-of-interest certification.
- View **3338** "T-Worwood-Disclosure" = a Municipal Officers & Employees Ethics Act
  conflict-of-interest statement (Travis L. Worwood).

They remain in `raw/_fetch_log.jsonl` as provenance of what was checked. If a future
task wants an ethics/conflict-of-interest dataset, these plus the 3388/3404–3415/3643–3666
/3910–3915 series are the leads.

## Reproduce

```
# discovery: fetch the three nav pages, grep DocumentCenter/View/<id> links
# fetch (polite, GET-only, logged):
python3 ../../.claude/skills/expand-city-sources/scripts/polite_fetch.py \
    --out raw --batch <urls.csv> --referer https://www.nephi.utah.gov/680/Disclosures --delay 3
# OCR each PDF -> text/<base>.txt (pdftoppm -r 200 | tesseract --psm 6)
# rebuild index:
python3 build_index.py
# validate:
python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .
```
