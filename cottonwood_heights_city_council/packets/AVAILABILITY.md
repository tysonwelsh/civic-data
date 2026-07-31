# Cottonwood Heights — agenda packets / staff reports: availability

**As-of:** 2026-07-13 · **Portal:** Granicus / CivicPlus **CivicEngage Central**
(`cottonwoodheights.utah.gov`; Akamai-style edge **403s a bare UA AND a bare browser UA** —
the full browser header set from `recon.md` is required, fetched via `scripts/polite_fetch.py`).

## Verdict — packets ARE published as a distinct column, but only for a NARROW recent window

Cottonwood Heights posts a **Packet** document alongside the **Agenda** and **Minutes** on its
two agendas landing pages (one anchor per meeting date, `showpublisheddocument/<docId>/<token>`):

| Body | Landing page |
|---|---|
| City Council (incl. in-session CDRA) | `/your-government/elected-officials/council-meeting-agendas-and-minutes` |
| Planning Commission (+ Administrative Hearings) | `/your-government/boards-and-commissions/planning-commission/agendas-packets-minutes` |

Each **Packet** is a **single bundled whole-meeting PDF** — the agenda + every staff report +
appendices/exhibits (WUI maps, site plans, ordinance drafts, prior-meeting minutes as an
appendix). They are **born-digital**: `pdftotext -layout` yields clean, substantial staff-analysis
text for **all 52** (no image-only bundle, no OCR seam) — sidecars in `text/`.

### The Packet column is a MUCH shorter rolling window than the Minutes column
This is the headline gap. The **Minutes** column on these pages reaches back to ~2022 (council) /
~2024 (PC), but the **Packet** column is trimmed far more aggressively:

| Body | Packet anchors on portal | Window | Minutes window (for contrast) |
|---|---|---|---|
| Council | 20 | **2025-08-19 → 2026-07-07** | ~2022 → 2026 |
| Planning Commission | 32 (22 regular + 10 Administrative Hearing) | **2024-11-06 → 2026-07-01** | ~2024 → 2026 |

So packets exist on the live portal only for roughly the **last ~11 months (council)** and
**~20 months (PC)**. Everything older — including the entire **2020–2024 council** and
**2020–2024 PC** span, and the **2020–2021 data floor** — is **not on the portal** and is
**GRAMA-only** (records request to `recorder@ch.utah.gov`). This is an **honest portal-retention
limit, not a scraper miss.** PMN (Utah Public Notice) is **not** a fallback for packets: PMN
carries agendas and minutes, not the staff-report **packet** bundles.

## What was stored — the full available window (STORED mode)

The complete set of 52 Packet PDFs on the two landing pages was captured verbatim to
`raw/<date>/` (**471.6 MB total**, min 0.16 MB / median 7.8 MB / max 28.8 MB per packet). The
whole set is **well under the ~1.5 GB disk budget**, so this is a **STORED** dataset (not
index-only): every packet is on disk with a text sidecar, plus `raw/<date>/_fetch_log.jsonl`
provenance (52 logged fetches).

Size math: 52 packets × median ~7.8 MB ≈ 0.47 GB ≪ 1.5 GB → store all. (Had the archive spanned
the full 2020→present window at this per-packet size it would be multi-GB and index-only; the
portal's narrow retention is what keeps it small.)

## Join coverage to existing votes
Keyed by `date` (+ `body`, `meeting_type`) to `meeting_minutes/all_votes.csv` (Council/CDRA) and
`planning_commission/all_votes.csv` (PC):

- **Council: 18 of 20** packet dates match an existing council vote date. The 2 that don't:
  **2025-12-02** (a meeting with no extracted council motions on that date) and **2026-07-07**
  (post-dates the current council vote max, 2026-06-16 — a future meeting relative to the last
  extraction).
- **PC: 13 of 25** distinct packet dates match an existing PC vote date. Most non-matches are
  **Administrative Hearing** packets (an admin-hearing has no PC roll-call vote row) and dates
  that **post-date the current PC vote max (2026-02-04)** — a refresh of the PC vote layer would
  absorb them.

The dataset is therefore **forward-looking**: it documents the staff analysis behind the most
recent ~1–2 years of meetings and will accumulate more with each refresh.

## Checked and NOT found
- **Council/PC packets before 2025-08 / 2024-11** — not on the live portal (trimmed rolling
  window); GRAMA-only.
- **A packet archive / year-folder history** — none; the portal keeps only the recent window.
- **PMN as a packet fallback** — no; PMN carries agendas/minutes, not staff-report bundles.
- **A separate CDRA packet** — none; CDRA business rides inside the council packet as an appendix
  (in-session body, matching the `body=CDRA` vote modeling).

## Section layer — land-use staff-report cuts (primary-documents rollout, 2026-07-16)

CH is **Bucket-B SEPARABLE**: the **12 council work-session packets 2025-08-19 → 2026-02-17**
carry an explicit machine-readable **appendix TOC manifest** (`Appendix N - Staff Report/<title>`
+ an indented body divider cover-page per appendix). `split_sections.py` cuts each **in-scope
(land-use)** appendix into its own text sidecar under `text/sections/` and adds one additive
`packet_kind='packet_section'` index row. **17 sections** were cut (16 `staff_report` +
1 `general_plan`); the 52 `full_packet` containers and their raw PDFs are untouched.

**The appendix-TOC manifest exists only for 2025-08 → 2026-02 council packets.** Not section-cut:
- **All 32 PC packets** — open with the agenda; carry inconsistent (0–4) `STAFF REPORT` banners,
  no appendix manifest → boundaries not high-confidence separable.
- **The 8 newer council packets (2026-03-03 → 2026-07-07)** — use an agenda-outline structure
  (`4.0 STAFF REPORTS / 4a./4b.`), no appendix divider pages.

These remain full-packet text only (their existing sidecars already serve `fts_packet`) — an
honest "not section-cut for this portal era", not a miss. Scope is **land-use only**: CH labels
every work-session item `Staff Report/<subject>`, so most sections are general-government
(personnel, tax, curfew, events) and are left UNCUT (blank `doc_class`). One documented skip:
**10625 Appendix 6** (Legislative Priorities) is in the TOC but has no body divider (dividers
jump 5→7) → boundary unlocatable → skipped (out of scope regardless). Build/verification detail
and the acceptance candidate (ZMA-25-003, joins to Ordinance 452 on 2025-11-18) are in
`CLAUDE.md` → "Section layer".

## Possible future recovery (noted, not pursued)
- **GRAMA** to `recorder@ch.utah.gov` for 2020–2024 packets (owner decision; heavy manual lift).
- **Wayback Machine** captures of the two landing pages at earlier dates may each hold a different
  cycle's `showpublisheddocument` Packet links — low-yield for large PDFs; logged as a candidate
  backfill, not attempted here.
