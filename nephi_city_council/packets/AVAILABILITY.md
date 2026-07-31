# Nephi packets — availability, coverage & storage decision

**Source**: CivicPlus CivicEngage AgendaCenter, `https://www.nephi.utah.gov/AgendaCenter`.
**Window**: 2020–2026. **Retrieved**: 2026-07-05. **Fetcher**: `scripts/polite_fetch.py`
(browser UA, GET-only, throttled; provenance in `_fetch_log.jsonl`).

## Enumeration method (reproducible)
The AgendaCenter Search endpoint returns dated rows with Agenda/Minutes links per category:
```
https://www.nephi.utah.gov/AgendaCenter/Search/?term=&CIDs=all&startDate=01/01/YYYY&endDate=12/31/YYYY
```
Fetched once per year (2020..2026), parsed each `catAgendaRow` for its primary
`ViewFile/Agenda/_<MMDDYYYY>-<id>` link + title, classified body by title
(Planning→PlanningCommission, Reinvestment→CRA, else Council), **excluded all `ViewFile/Minutes/…`**
(minutes already live in `meeting_minutes/` and `planning_commission/`). De-duplicated on
`(MMDDYYYY,id)`. There is **no `AgendaPacket` document type** on this portal — only `Agenda` and
`Minutes`. Result: **328 unique agenda documents**.

## Storage decision — STORED LOCALLY (all 328)
Size probed **inline** via HEAD (`content_length`) on every URL before download — no async/Monitor.
- Sum of Content-Length over 328 files: **~10.8 MB** (Council 7.14 MB / PC 3.61 MB / CRA 0.01 MB).
- On-disk `raw/` after download: **12 MB** (325 PDF + 3 DOCX; largest single file 0.31 MB).
- Budget was ~400 MB. 10.8 MB ≪ 400 MB → **store to `raw/<date>/…`**. Not index-only; nothing
  capped or dropped. All 328 fetches returned HTTP 200 (`ok=true`).

## Coverage by body / year (index.csv)
| body | total | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|------|------:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|
| Council | 254 | 43 | 46 | 39 | 36 | 35 | 37 | 18 |
| PlanningCommission | 72 | 6 | 9 | 17 | 13 | 11 | 11 | 5 |
| CRA | 2 | – | 1 | – | 1 | – | – | – |

2026 is partial (through mid-June, the harvest date). Every year 2020–2026 is represented.

## Council vs Planning-Commission asymmetry
Council posts ~3.5× more agendas than PC (254 vs 72). This mirrors meeting cadence (Council 1st &
3rd Tuesday + work sessions; PC ~monthly) — it is **not** a harvest gap. The only quality
asymmetry is on the PC side: **all 4 scanned (no-text) agendas are PC** (2020-01-08, 2022-02-16,
2022-04-27, 2022-06-22), and PC agendas are short. Council agendas are uniformly born-digital text.

## Join integrity
- **Council**: 194/194 council-vote meeting dates have a matching agenda (100%).
- **PC**: 61/63 PC-vote dates match. The 2 unmatched are minor date-labeling differences, not
  missing agendas; agenda dates otherwise *exceed* vote dates (work sessions / no-motion meetings).

## Text-corpus health
Screened with `audit-city-data/scripts/screen_corpus.py` (324 text files): **0** cid_artifacts,
**0** replacement_chars, **0** PUA-garbled, **0** mojibake, **0** long-token runs. Flags raised are
benign for agenda documents: `ends_mid` (agendas are lists, no terminal punctuation), `short<500B`
(22 brief PC agendas). Corpus is clean.

## Format anomalies retained verbatim
- 3 `.docx` uploaded to the Agenda slot: `raw/2022-06-21/council_232_agenda.docx`,
  `raw/2023-01-11/pc_267_agenda.docx`, `raw/2025-05-14/pc_382_agenda.docx`.
- 4 scanned PDFs (listed above) — `format=scanned`, no committed text layer.

## Gaps
None beyond the above. No dates were found for which an Agenda existed but could not be retrieved.
Minutes are intentionally out of scope (excluded, not missing).

## Primary-document classes (doc_class rollout, 2026-07-16)

Ruled **Bucket C** in `../../PRIMARY_DOCS_ROLLOUT.md` (triage table; Wave 4, doc-only).
The four packet-attachment primary-document classes (staff reports, memos, development
agreements, plan amendments) are **HONEST ZEROS** — no packet/staff-report layer exists on the
portal. No fetch, no classification was performed.

The CivicPlus **AgendaCenter** exposes only two document types, **Agenda** and **Minutes** —
there is no `AgendaPacket` / staff-report / attachment type. The **328** stored agendas are the
whole corpus (**323** carry a `.txt` sidecar in `text/`; the index marks **324 text / 4
scanned**, and 3 of the "text" rows are `.docx` uploaded to the agenda slot). These are
agenda-item-level content, not primary documents. Class 3 (General Plan text) is independent —
Nephi's MIH element is General Plan Element 6, tracked in `housing_plans/`.
