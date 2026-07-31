# Taylorsville — agenda packets / staff reports: availability

**As-of:** 2026-07-06 · **Portal:** CivicPlus / CivicEngage Central (`taylorsvilleut.gov`;
Akamai edge 403s bare bots — browser UA required, fetched via `scripts/polite_fetch.py`).

## Verdict — packets ARE published, but only the CURRENT cycle; there is NO archive

Taylorsville posts agenda packets / staff reports on **three dedicated "Packet" pages** (one
per body), NOT as a column on the Agendas-&-Minutes page and NOT in any year-folder archive:

| Body | Packet page |
|---|---|
| City Council | `/government/elected-officials/council-packet` |
| Planning Commission | `/government/planning-commission/planning-commission-packet` |
| RDA Board | `/government/rda-board/rda-board-packet` |

Each page is a single CivicEngage **"Document Folder Box"** widget bound to one document-center
folder. **The folder holds only the current / upcoming meeting cycle's documents** — staff
replace its contents each cycle, so prior packets are rotated off and are **not browsable,
paginated, or archived** anywhere on the site. There is no `-folder-<N>` history for packets,
no "view all"/archive link, and no Document Center packet tree. Verified live 2026-07-06:
the three pages held **1 / 2 / 4** documents respectively, all from the June–July 2026 cycle.

### What IS archived (and why it is NOT a packet substitute)
The Agendas-&-Minutes page has year folders **2008→2026**, but its three columns are
**Agendas | Meeting Minutes | Audio Recordings** — there is **no packet column** (a sibling
verification confirmed the columns; the recon's folder-id table was the wrong column, already
corrected in `fetch_new.py`). The archived **agenda** documents are **thin agenda outlines**,
NOT staff-report bundles: recent council agendas are 1–2-page scanned signed agendas
(~0.3–4 MB of image), and PC agendas are ~0.6–1.1 MB / 2 pages. On the June 9 2026 PC cycle
the agenda (0.66 MB, 2 pp) and the staff report (8.09 MB, 45 pp) are **separate documents** —
only the agenda is archivable, the staff report lives only on the rotating packet page. So the
year-folder archive does **not** back-fill packets.

### Consequence for the research window (2020→present)
Historical agenda packets / staff reports for 2020–2026 are **not retrievable** from the city
portal — they were never archived. This is an **honest publishing gap**, not a scraper miss.
See `unrecovered.csv`.

## What was stored — a dated snapshot of the current cycle (2026-07-06)

The current-cycle documents on the three packet pages were captured verbatim to `raw/<date>/`
(7 files, ~11.6 MB total) so the dataset has real, non-decoy content and a provenance anchor:

- **PC 2026-06-09** — 45-page born-digital staff report (case **19C23**, revocation
  consideration) + the 2-page signed agenda. The staff report is a genuine substantive packet.
- **RDA 2026-06-03** — RDA agenda + FY2026-27 budget documents (proposed amended budget, 16 pp
  born-digital PDF; final budget **Resolution RDA 26-03**, a Word `.docx`; signed resolution
  scan, 19 pp).
- **Council 2026-07-01** — a cancellation notice (the only item then on the council-packet
  page; retained as evidence of the current-cycle-only behavior — not itself a packet).

### Join coverage to existing votes
Keyed by `date` (+ `body`, `meeting_type`) to join `meeting_minutes/all_votes.csv`
(council+RDA) and `planning_commission/all_votes.csv` (PC):
- **RDA 2026-06-03** → the date matches an existing Council meeting in the council CSV
  (2026-06-03, 16 `body=Council` vote rows), so it joins by date to that meeting bundle.
  Note: `body=RDA` vote rows only exist for 2021–2022 (2021-06-02, 2022-01-05, 2022-05-04);
  the 2026 RDA budget-adoption vote is not separately extracted under `body=RDA`, so this is a
  date-level join to the council meeting, not to an RDA-body vote row.
- **PC 2026-06-09** → later than the PC vote floor's current max (2026-04-28) — no vote row yet
  (a future meeting relative to the last vote extraction).
- **Council 2026-07-01** → meeting cancelled, correctly has no votes.

Net: the stored snapshot joins by date to just **1** existing meeting date and **~0 %** of the
historical 2020→2026 vote dates (142 council + 90 PC) — a direct measure of the archive gap.
Only the live current cycle is obtainable.

## Checked and NOT found
- A council/PC/RDA **packet year-folder archive** — none exists (only the rotating widget).
- A **Document Center** packet folder tree / "view all" archive link — none present.
- **Agendas as fat packets** — no; archived agendas are thin outlines (sizes/pages above).

## Possible future recovery (not pursued here — noted for the queue)
Wayback Machine captures of the three packet pages at different past dates could each hold a
different cycle's `showpublisheddocument` links, allowing partial reconstruction of historical
packets. This is a heavy, low-yield lift (large PDFs rarely captured) and out of scope for the
initial packets pass; logged in the repo TODO as a candidate backfill.

## Primary-document classes (doc_class rollout, 2026-07-16)

Ruled **Bucket C** in `../../PRIMARY_DOCS_ROLLOUT.md` (triage table; Wave 4, doc-only).
The four packet-attachment primary-document classes (staff reports, memos, development
agreements, plan amendments) **cannot be built** — an **HONEST GAP**. No fetch, no
classification was performed.

The packets corpus is a **7-document current-cycle snapshot** (June–July 2026): no historical
archive exists (the three packet pages rotate their contents per cycle), and the Agendas-&-
Minutes year folders hold only **thin agenda outlines**, not staff-report bundles. There is
therefore no historical primary-document corpus to classify. Wayback recovery of prior cycles
is already logged in the repo `TODO.md` as heavy / low-yield. **Class 3 (General Plan text) is
already complete** in `housing_plans/` (14 sidecars, incl. the 2025 GP chapters + the adopted
MIH Ordinance 23-03).
