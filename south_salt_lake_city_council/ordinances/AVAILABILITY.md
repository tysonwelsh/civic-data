# ordinances/ — availability & provenance (South Salt Lake) — as-of 2026-07-13

What was checked, what exists, what does not. Additive dataset (expand-city-sources
Source 3); read-only on every existing dataset.

## Code host / codifier — Municode (confirmed)
- **Codifier: Municode** (`library.municode.com/ut/south_salt_lake`), product **16638**
  ("Code of Ordinances"), client **4410**. The public library page is a JS SPA (6 KB
  shell to a plain GET), but the **Municode NEXT JSON API (`api.municode.com`) is openly
  reachable** — no auth, GET-only.
- The code is **codified through Ordinance No. 2026-03, passed 2026-01-28** (Supplement
  No. 68; `Jobs/latest/16638`).
- **Municode gives the current CONSOLIDATED text, not per-ordinance PDFs.** The **OrdBank**
  feature is enabled but **`newOrdCount = 0`** — there are no ordinances pending
  codification right now, so no individual signed-ordinance PDFs are downloadable there.

## The enumeration source used — the Municode disposition table (authoritative, minutes-INDEPENDENT)
Municode publishes, inside the code, a **"Code Comparative Table and Disposition List"**
(nodeId `COCOTADILI`) — a chronological table of **every adopted ordinance** with its
**Number, adoption Date, Description, and Code Section**. Retained raw:
`raw/municode_cocotadili_comparative_table.json` (born-digital API JSON; text sidecar in
`text/`). The legacy pre-Supp-20 table (`ORLIDITA`) is retained too for provenance.
This is a real, independent cross-source for the number→date→subject map — better than the
Lehi/notice-only situation.

- **100 ordinances enumerated for the 2020→present window** (2020-01-08 … 2026-01-28),
  plus **14 within_source** rows (below) = **114 index rows**.
- Gaps in the ordinance numbering (e.g. 2020-04, 2020-10, 2025-03/-12/-15) are **honest**:
  those numbers are not in the disposition table (ordinances that did not amend the code, or
  were superseded/repealed before codification). The table is the disposition list, not a
  guarantee that every issued number appears — do not infer a missing number was never adopted.

## Sources that do NOT hold SSL ordinance texts (checked)
- **PMN council body 1295** — crawled the cumulative notices list (`notices.html?id=1295&page=300`,
  568 attachments). **Every attachment is labelled `(Meeting Minutes)`; there are no
  adopted-ordinance PDFs.** SSL's PMN body is a minutes/agenda archive, **not** an ordinance
  archive (same negative finding as Holladay's PMN — checked, not assumed).
- **CivicPlus DocumentCenter (`sslc.gov/DocumentCenter`)** — no browsable ordinance folder in
  the served HTML (JS-rendered); no per-ordinance PDF listing surfaced.
- **AgendaCenter packets** embed ordinance **DRAFTS** (unsigned, pre-adoption) inside the
  bundled agenda packets — a future `packets/` layer, not signed adoptions; not mined here.
- **American Legal** (`codelibrary.amlegal.com/codes/southsaltlakeut`) — **403 bot-gated**;
  recorded, not mirrored. (SSL's real codifier is Municode anyway.)

→ **No online archive of individual signed ordinance PDFs exists for South Salt Lake.** The
Municode disposition table is the authoritative enumeration; full current text of any codified
ordinance is browsable in the Municode code by its Code Section (see `code_section` column).

## Motion linkage — thin BY DESIGN (the coverage cliff)
SSL council motions **describe ordinances by subject/title, never by number** (verified: zero
`#YYYY-NN` tokens in `meeting_minutes/all_votes.csv`). Linkage is therefore by **adoption date
(+ cited code section / subject)**, never by number — so `high` (date+number in a motion) is
**not producible** and is 0 by construction.

Combined with SSL's **recorded-minutes coverage cliff** (council minutes exist essentially only
for 2020–early-2021 plus sporadic recent meetings; 253 council dates are agenda-only in
`meeting_minutes/minutes_unrecovered.csv`), **most ordinances cannot be linked to a recorded
adopting motion** — an honest `none`, not a scraper miss:

| match_confidence | rows | meaning |
|---|---|---|
| high | 0 | date+number in a motion — not producible (SSL motions cite no ordinance number) |
| medium | 1 | recorded adopting motion on the adoption date whose **cited code section matches** (2025-06, §17.10.120) |
| low | 3 | recorded ordinance-adopting motion on the date, specific ordinance unconfirmed (motion text truncated at item title) |
| none | 96 | no recorded adopting motion on the adoption date (the coverage-cliff gap) |
| within_source | 14 | adopted AFTER Municode's 2026-01-28 codification cutoff; known only from recorded minutes (FY2026-27 budget/tax ordinances) — SSL motions carry no number, so `ordinance_no` is blank |

Mayor is **non-voting** (max council roll = 7); no linkage assumes the mayor is a voter.

## Reproduce
`python3 build_ssl_ordinances.py` (idempotent; parses the retained raw Municode JSON +
`meeting_minutes/all_votes.csv`). Refresh the raw with `polite_fetch.py` against
`api.municode.com/CodesContent?jobId=<latest>&nodeId=COCOTADILI&productId=16638`
(get `<latest>` jobId from `Jobs/latest/16638`).
