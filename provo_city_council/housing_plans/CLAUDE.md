# housing_plans — Provo General Plan + Moderate Income Housing (MIH) plan & annual reports

Source 2 of the `expand-city-sources` skill. **Additive dataset** — nothing here modifies the
existing `meeting_minutes/`, `planning_commission/`, `public_comments/`, `db/`, etc. **As-of 2026-07-03.**

## What this is

Provo's land-use / housing planning record, from two repositories:
1. **City of Provo** (`www.provo.gov`, CivicPlus CivicEngage) — the current adopted **General Plan
   2023** and its **Moderate-Income Housing (MIH) element** (General Plan Appendix B: MIH Supply and
   Strategies 2022-2027).
2. **Utah DWS / Housing & Community Development (HCD)** — the **annual MIH implementation reports**
   Provo files with the state, as published in HCD's statewide compilations, plus the SB 34 progress
   summary.

## Statutory context (why these documents exist)

- **Utah Code § 10-9a-403** — every municipality's general plan must include a **moderate income
  housing (MIH) element**: a written plan that **selects three or more strategies** from a statutory
  menu (plus one additional strategy for larger cities) to provide a "reasonable opportunity" for
  households at **≤ 80% of county area median income** to live in the city.
- **Utah Code § 10-9a-408** — requires each municipality to file an **annual MIH implementation
  report** with HCD documenting progress on its chosen strategies. HCD reviews the self-reported data.
- **HB 462 (2022)** and later amendments strengthened these: required/expanded strategy menus, tied
  transportation funding eligibility to compliance, and — for cities with fixed-guideway transit
  (Provo's UVX BRT / FrontRunner) — required **Station Area Plans**. Provo's MIH element covers the
  **2022-2027** period; the 2023/2024/2025 annual reports describe Station Area Plan work (`provosap.com`).

## Documents (see `index.csv` for the machine-readable list)

`doc_type` ∈ `general_plan` / `mih_element` / `mih_annual_report` / `compliance_letter`.

- **general_plan** — General Plan 2023 (108 pp, `DocumentCenter/View/919`), the current adopted plan.
  HOUSING chapter at p.35; its goals defer the statutory MIH detail to Appendix B.
- **mih_element** — General Plan **Appendix B: Moderate-Income Housing Supply and Strategies 2022-2027**
  (22 pp, `DocumentCenter/View/4020`). Cites 10-9a-403, does the AMI/affordability gap analysis, and
  selects the strategies. This is the statutory MIH element of record.
- **mih_annual_report** — HCD statewide compilations for report years **2023, 2024, 2025**; Provo's
  filing is a page-range within each (see the `notes`/page ranges in `index.csv`; sidecars
  `text/provo-<year>.txt`).
- **compliance_letter** — HCD **SB 34 Municipal Progress Summaries 2019–2021** (Provo = entry #57). HCD
  does not issue per-city compliance letters; this progress summary is the closest published artifact.

## Build method / provenance

- Every raw PDF fetched through `.claude/skills/expand-city-sources/scripts/polite_fetch.py`
  (browser UA, Referer, ≥1s/host, logged, `--now 2026-07-03T00:00:00Z`) into `raw/`. Byte-level
  provenance: `raw/_fetch_log.jsonl` (url, http status, bytes, sha256, content_type, final_url,
  retrieved_utc).
- City docs discovered by crawling `https://www.provo.gov/sitemap.xml` → the General Plan page
  `https://www.provo.gov/276/General-Plan-and-Citywide-Plans` (GP + citywide sub-plans) and, for the
  MIH element (not linked on that page), a web search → `DocumentCenter/View/4020`. State docs from
  `https://jobs.utah.gov/housing/affordable/moderate/reporting/`.
- The newer `www.provo.org` site is bot-gated (403); all authoritative planning docs were retrievable
  on `www.provo.gov`. See `AVAILABILITY.md`.

## Extraction

- Born-digital PDFs → `pdftotext -layout` sidecars in `text/` (`extraction_method=pdftotext-layout`):
  General Plan 2023, MIH element (Appendix B), and the **Provo-only page ranges** cut from each state
  compilation (`text/provo-<year>.txt`). Page ranges bracketed by the next jurisdiction header
  (Providence before / Riverdale after) and grep-verified for zero bleed.
- The SB 34 compilation is retained verbatim only (Provo = entry #57), not sidecar-extracted.
- **General Plan Table-of-Contents dot-leaders** render as U+FFFD replacement chars (1576 of them, all
  in the ToC decoration — the leader-dot glyph has no Unicode mapping). Body text is clean; this is
  cosmetic, not corruption. Preserved verbatim (not "cleaned").
- `screen_corpus.py` run on `text/` (5 sidecars) → clean: 0 cid-artifacts / mojibake / PUA-garbled /
  duplicate bodies / read errors. Only advisory flags: the GP ToC-leader replacement chars noted
  above, gov-doc repeated header/footer lines, hyphen line-breaks, and page-boundary "ends-mid".

## Linkage to the rest of the repo

- The **MIH element / General Plan 2023 adoption** corresponds to a Provo Municipal Council action —
  joinable to `meeting_minutes/all_votes.csv` by adoption date once the ordinance/resolution number is
  confirmed (no adopting-ordinance PDF was located on the city site; see `AVAILABILITY.md`).
- MIH strategies and the annual reports reference the **UVX / FrontRunner Station Area Plans**
  (`provosap.com`) — the same transit-oriented density work that appears in Planning Commission and
  Council rezone items (`planning_commission/`, `db/`).

## Caveats

- The state "annual report" of record is a **statewide compilation**, not a standalone Provo PDF; the
  whole compilation is retained and Provo's pages are sidecar-extracted. Cite the page range.
- MIH self-reported data is reviewed but not audited by HCD — treat report figures as the city's
  self-report.
- The MIH element covers **2022-2027**; the General Plan is dated **2023**. Pre-2023 GP (2004) and
  pre-2023 annual compilations were not retrieved (superseded / not on the current index).
