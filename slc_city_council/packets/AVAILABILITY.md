# packets/ — availability & gap log (as-of 2026-07-05)

What was checked, what SLC publishes, and what it doesn't. Built by `expand-city-sources`
Source 1. Two sources because SLC splits the two bodies across two systems.

## Method (what was checked)
**Council (PrimeGov `slc.primegov.com`).** For every year **2020–2026** the archive API
`GET /api/v2/PublicPortal/ListArchivedMeetings?year=YYYY` was pulled (7 JSON files frozen
at `raw/api/council_YYYY.json`). Every `committeeId==5` meeting (the Council family —
Council/RDA/CRA/LBA interleaved) was classified and its `documentList` inspected for a
packet: `templateName=="Meeting Materials"` (the compiled whole-meeting PDF) or, failing
that, `"Agenda"`. `HTML Minutes`/`Minutes` were excluded (already in `../meeting_minutes/`).
Because the packets are huge, **a per-year sample (~6/year, 43 total) was stream-probed for
Content-Length** (headers only, body never downloaded) via
`/Public/CompiledDocument?meetingTemplateId=<templateId>` on 2026-07-05 — all sampled
probes returned HTTP 200 `application/pdf`. `raw/_fetch_log.jsonl` records every probe.

**Planning Commission (slcdocs.com).** The SLC Planning Commission is **not present in the
PrimeGov archive** (`committeeId` 5 = Council, 30 = Redistricting; no PC committee exists).
Its documents live on `slcdocs.com`. The index page
`https://www.slc.gov/planning/planning-commission-agendas-minutes/` (frozen at
`raw/pc/agendas_minutes_page.html`) was harvested; every linked `.pdf` classified by
filename into `staff_report` / `motion_sheet` / `agenda` (minutes + public-comment PDFs
skipped — they belong to `../planning_commission/` and `../public_comments/`). Each was
size-probed; files ≤ 10 MB were downloaded to `raw/pc/`.

## What exists

### Council — 530 rows, INDEX-ONLY, 2020–2026
| Year | full_packet | agenda_only |
|------|------------:|------------:|
| 2020 | 81 | 4 |
| 2021 | 73 | 7 |
| 2022 | 80 | 5 |
| 2023 | 83 | 2 |
| 2024 | 69 | 2 |
| 2025 | 74 | 2 |
| 2026 | 44 | 4 |
| **Total** | **504** | **26** |

Sampled sizes (n=43): **median 31 MB, mean 62 MB, min 0.2 MB, max 438 MB** → full
504-packet corpus ≈ **15–30 GB**. Per the disk-constrained mode, **no Council PDF is
stored**; each row is a live pointer (`source_url` re-mints a fresh Azure SAS). Note SLC
publishes **Meeting Materials back to 2020** — a year *earlier* than SLC's own PrimeGov
*minutes* (2021+) and earlier than West Jordan's packet start (2022). This makes 2020 the
one year where a packet exists but no extracted council vote does (SLC council votes are
2021+; 2020 minutes are OCR — see `../meeting_minutes/CLAUDE.md`).

### Planning Commission — 52 rows, 2026 only (39 STORED)
11 meeting dates, Jan–Jul 2026: `staff_report` 24 · `motion_sheet` 18 · `agenda` 10.
**39 files ≤ 10 MB stored** (`raw/pc/`, 47.8 MB, 38 `text` / 1 `scanned` by `pdftotext`);
**13 large exhibits >10 MB index-only** (up to 221 MB — image/plat-heavy site-plan staff
reports). A text screen of the 39 stored files (`audit-city-data/screen_corpus.py`) showed
a clean born-digital corpus (dict_ratio median 0.78, split-word ≈ 0, 0 read errors; the
`ends_mid` flags are benign agenda/signature endings).

## Coverage vs recorded votes (the join)
Packet `date` = meeting date; it matches the vote date exactly.
- **Council** (`../meeting_minutes/all_votes.csv`, vote-dates with a `full_packet`):
  2020 n/a (no 2020 council votes extracted) · **2021 31/33 · 2022 32/32 · 2023 32/32 ·
  2024 30/30 · 2025 30/30** · 2026 14/15. → **2022–2025 = 100% packet coverage.**
- **Planning Commission** (`../planning_commission/all_votes.csv`): 2020–2025 **0**
  (no packets published/discoverable — see gaps) · **2026 9/11**.

## Gaps (verified, with cause)
1. **Planning Commission 2020–2025: no packets in this dataset.** SLC PC is not in
   PrimeGov, and the only machine-discoverable PC packet index (the slc.gov agendas-minutes
   page) lists **current year only**. Spot checks of the slcdocs Planning directory for
   older meetings (e.g. `2020/PC01.08.2020…`) found **minutes only** — no sibling agenda or
   staff-report PDF — so pre-2026 SLC PC was largely published minutes-only under a flat
   year folder, and the per-meeting staff-report subfolder (`PC <M.DD.YYYY>/`) is a recent
   (≈2024+) practice with **no crawlable index**. Recorded here as a real acquisition gap.
   (The `../planning_commission/` minutes/votes for 2020–2026 are unaffected — this gap is
   only about the *packet/staff-report* layer.)
2. **4 Council meetings have no fetchable packet or agenda doc** (dropped from `index.csv`,
   listed here): 2021-03-02 & 2021-03-16 (Council Formal), 2021-04-13 (Special Limited
   Formal), 2023-01-16 (non-legislative "Open House / Tour for Legislators"). Their
   `documentList` carried only HTML Minutes/HTML Agenda, no `Meeting Materials`/`Agenda` PDF.
3. **26 Council `agenda_only` rows** carry the thin **HTML** agenda (no compiled Meeting
   Materials was published for that meeting) — `format=html`, index-only. Mostly
   oath/ceremonial/limited meetings plus early-2021 formal meetings.
4. **13 large PC exhibits (>10 MB) index-only** — stored would breach the small-file cap;
   fetch on demand from `source_url`.

## Not applicable / not done
- **Council per-item staff-report downloads:** not possible — PrimeGov bundles the whole
  Council meeting into one compiled `Meeting Materials` PDF; there is no per-agenda-item PDF.
- **RDA/CRA/LBA** are not separate rows — they are the Council sitting as those bodies in the
  same meeting/packet (`body=Council`; the 4-body split is in the minutes).
- **Redistricting Advisory Commission** (committeeId 30, 6 meetings) — minor board, skipped.

## Primary-document TEXT layer — what is separable (PRIMARY_DOCS_ROLLOUT, 2026-07-16)

SLC was triaged **A-lite (PC 2026 slice) + B-no (Council)** in `PRIMARY_DOCS_ROLLOUT.md`.
`classify_attachments.py` was run over the PC slice; the Council side was ruled not
separable.

### PC 2026 slice — the classified slice (A-lite, DONE)
The 24 PC `staff_report`-kind rows are the only per-item, on-disk primary documents SLC
exposes. **11 are stored** (`format=text`, ≤10 MB, with `raw/pc/` + `text/` sidecars) and
were classified `doc_class=staff_report` — **whole-class verified (n=11, 100%)** against
their own sidecar text (each is an SLC Planning Division land-use staff report: rezone /
zoning-map & text amendment / alley-vacation / planned-development extension /
petition-initiation). **0 misclassifications, 0 content-gate failures; none is a GP/
master-plan amendment exhibit** (`plan_amendment` stays empty here). The remaining **13
PC staff_report rows are the >10 MB map/plat-heavy exhibits** — never fetched (store-cap,
`format=na`, index-only, no on-disk text to verify and no stored binary to hash), so they
stay `doc_class` blank (honestly unclassified). `motion_sheet` / `agenda` rows are not
target classes.

### Council portal — classes NOT separable/extractable (B-no ruling, 2026-07-16)
The Council side (504 `full_packet` rows, index-only) was **ruled not separable** for this
rollout. The four attachment classes (`staff_report`, `member_memo`, `plan_amendment`,
`development_agreement`) **cannot be broken out of the Council portal**: PrimeGov serves the
whole Council meeting as ONE compiled `Meeting Materials` PDF — there is no per-agenda-item
document (see *Not applicable* above). These bundles are **monolithic and index-only**
(median 31 MB, mean 62 MB, up to 438 MB; ~15–30 GB total, nothing stored), and are
**vision/OCR-heavy** (site-plan/plat imagery, not `pdftotext`-friendly), so no high-confidence
section cut is possible. No `doc_class` is assigned to any Council row. To read a Council
packet's staff analysis, fetch its `source_url` (fresh SAS) and use vision/OCR, as before.

### Pre-2026 PC packets remain a real acquisition gap
Unchanged from Gap #1 above: SLC PC staff reports are machine-discoverable for the **current
year only** (2026); 2020–2025 are published minutes-only with no crawlable staff-report
index. That pre-2026 gap is a genuine acquisition gap, not something this rollout closed.

## Regenerate / refresh
See `CLAUDE.md` → *Regenerate / refresh*. If SLC ever exposes an older-year PC agenda index,
backfill PC 2020–2025 from slcdocs. Re-sample Council Content-Length yearly to keep the size
estimate current.
