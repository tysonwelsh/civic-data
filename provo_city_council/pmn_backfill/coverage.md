# Provo PMN backfill — coverage cross-check

Cross-check of Provo meeting-minutes coverage in this repo against the Utah Public
Notice website (PMN, `https://www.utah.gov/pmn/`), by **meeting DATE** (±4-day
tolerance for posted-vs-meeting-date offset). As-of **2026-07-03**.

PMN body ids (confirmed via `entities.html?id=3` → Provo entity **244** →
`publicBodies.html?id=244`): **Provo Municipal Council = 1600**, **Provo City
Planning Commission = 1662**, Redevelopment Agency Governing Board = 2318 (crawled
for context; RDA board = the Council sitting as RDA, so its minutes duplicate
council content and were not separately recovered).

History was pulled with the cumulative-GET trick
(`/pmn/list/notices.html?id=<body>&page=500` returns the body's ENTIRE notice
history in one GET): **1,589** council notices (to 2026-06-23), **365** Planning
Commission notices (2008→2026), **174** RDA notices.

## Attachment-label reality (recon correction)
Recon warned PMN for Provo is *"generally agendas only, not minutes."* That is **wrong
for the Council body**: PMN carries **468** `…Minutes…` + **268** `…Summary…` council
attachments. But the **repo's OnBase source is the superset for regular Council
meetings** — for 2024–2026 PMN actually has *fewer* council minutes than the repo
(see table). PMN's genuine value-add is (a) **special/joint/retreat** council meetings
the OnBase regular-meeting harvest missed, and (b) the **entire Planning Commission
2020–2024 backlog**, which the repo lacks (documented city source gap; repo PC is
2025+ only). The PC posts **per-item "Report of Action" (ROA)** PDFs, not a
consolidated minutes doc — each ROA is a structured, vote-bearing record
(`On a vote of N:0 …`, named movers/voters), the PC minutes-equivalent.

## Council (Provo Municipal Council, body 1600) — by year
"Minutes-equivalent dates" = distinct dates carrying a `Minutes` or `Summary` attachment.

| metric | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | total |
|---|---|---|---|---|---|---|---|---|
| Repo minutes dates | 29 | 28 | 27 | 25 | 27 | 26 | 11 | 173 |
| PMN minutes dates | 34 | 30 | 29 | 24 | 23 | 19 | 10 | 169 |
| Recovered (PMN∖repo) | 4 | 2 | 1 | 0 | 0 | 1 | 0 | 8 |
| Still missing | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

**All 8 recovered council dates are special meetings absent from the OnBase regular-
meeting archive** (genuine content-verified Municipal Council minutes):

- **2020-03-05** — Council Retreat
- **2020-05-12** — Budget Retreat
- **2020-08-13** — Joint Meeting w/ Provo School District
- **2020-09-10** — Joint Meeting w/ Orem City Council
- **2021-09-02** — Joint Meeting w/ Provo School Board
- **2021-11-08** — Joint Meeting w/ State Legislators
- **2022-03-10** — Joint Meeting w/ Orem City Council
- **2025-03-18** — Joint Meeting w/ Planning Commission

Note: PMN's *lower* recent-year council counts (e.g. 2024: PMN 23 vs repo 27) are a
PMN publishing lag/gap, **not** a repo gap — the repo already holds those regular
meetings from OnBase. No council minutes on PMN are missing from this repo after backfill.

## Planning Commission (body 1662) — by year
"PMN dates" = distinct dates carrying a `Report of Action`/minutes attachment. Repo PC
is **2025+ only** (documented source gap, `planning_commission/minutes_unrecovered.csv`).

| metric | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | total |
|---|---|---|---|---|---|---|---|---|
| Repo PC dates | 0 | 0 | 0 | 0 | 0 | 16 | 10 | 26 |
| PMN PC dates | 19 | 18 | 19 | 14 | 18 | 13 | 10 | 111 |
| Recovered (PMN∖repo) | 19 | 18 | 19 | 14 | 18 | 3 | 1 | 92 |
| Still missing | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

**92 PC meeting dates recovered** (382 per-item ROA PDFs — 381 action records + 1
code-section exhibit bundled under an item; 2 byte-identical source re-posts flagged
`doc_kind=roa_duplicate`). This backfills the repo's empty 2020–2024 PC record
(70 dates) plus 4 additional 2025–2026 PC dates PMN had that the AgendaCenter harvest
missed. **0 PC minutes-bearing dates on PMN remain missing** after backfill.

## Method / honesty notes
- Cross-check is per-DATE set-difference (±4d), not per-year counts (PMN attaches
  minutes sporadically, so counts hide real gaps).
- Every recovered file was content-verified: correct body-name header + internal
  meeting date + motion/vote structure. All 390 are **born-digital text** (pdftotext
  -layout; 0 scanned/OCR). `screen_corpus.py`: 0 cid/mojibake/stub/dict outliers.
- This is a **separate, additive** dataset. The audited `meeting_minutes/` and
  `planning_commission/` layers were NOT modified. Merge deliberately if desired.
