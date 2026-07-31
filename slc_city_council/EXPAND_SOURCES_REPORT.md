# expand-city-sources — Salt Lake City expansion report

**Date:** 2026-07-06 · **City:** Salt Lake City (Salt Lake County) · **Skill:** `.claude/skills/expand-city-sources/`
**Eleventh city launched / final flagship.** Portal: **PrimeGov** (2021+) + a bounded 2020 **Laserfiche**
slice; the Council series interleaves **four bodies** (Council / RDA / CRA / LBA) in one minutes doc.
**5 of 6 datasets complete; campaign finance is a documented portal-blocked gap** (see below). Every built
dataset passes `validate_dataset.py`; no existing dataset modified. Concurrency pre-flight clean.

## Per-source results

| # | Source → dataset | Yield | Notes |
|---|---|---|---|
| 1 | Packets → `packets/` (**HYBRID**) | **582 rows**: Council 530 INDEX-ONLY (~15–30 GB, median 31 MB each) + PC 52 (39 stored, 13 index-only) | PrimeGov `documentList` (`Meeting Materials`). **SLC PrimeGov holds ONLY the Council family** — Planning Commission lives separately on slcdocs.com and is machine-discoverable **for 2026 only** (pre-2026 PC = minutes-only, a real gap). 100% Council vote-date coverage |
| 2 | Housing → `housing_plans/` | **11 docs (~89 MB)** | The landmark **"Growing SLC" (2018–2022)** + current **"Housing SLC" (2023–2027)** five-year plans (standalone, w/ signed ordinance) + **Thriving in Place** anti-displacement strategy + Plan Salt Lake (GP) |
| 3 | Ordinances → `ordinances/` | **443 adopted** (146 land-use) | **All `body=Council`** (RDA/CRA/LBA pass resolutions, not numbered ordinances). **9 high** / 49 medium / 331 within_source / 54 none (48 = 2020 pre-vote-floor OCR). Signed archive is a JS-gated Laserfiche SPA; American Legal 403 — corroborated via SLC Planning's adopted-zoning list + PMN synopsis notices. Only 6 in-era ords missing from votes (2021 budget consent-folded) |
| 4 | PMN backfill → `pmn_backfill/` | **7 recovered** + **65 of 68 2020-minutes URLs recovered** | Entity 259; Council 1360 / PC 1274 / RDA 1277 / CRA 9033 / LBA 3475. Recovered 7 council minutes (incl. 2 Formal meetings the repo had only Work Sessions for — caught by diffing date+**session-type**). **Bonus: `url_recovery_2020.csv` gives citable PMN URLs for 65 of the 68 previously un-URL'd 2020 Laserfiche minutes** (closes a standing TODO) |
| 5 | Transcripts → `transcripts/` | **1,142 videos mapped / 10 ASR sampled** | "SLC Live Meetings" YouTube (all bodies, continuous 2011→present, full ASR). The largest video map in the repo. Whisper candidates chosen by cross-referencing contested land-use votes in `db/slc.db` |
| 6 | Campaign finance → `campaign_finance/` | **0 filings — PORTAL BLOCKED (documented gap)** | SLC self-hosts a data-only JSON WebAPI (`dotnet.slcgov.com/Attorneys/CampaignFinance_Public/`). The agent **fully reverse-engineered the API surface** and wrote a ready harvester, but the .NET backend returned **HTTP 503 "scheduled maintenance" on every dynamic call** throughout the run (static assets served — that's how the API was mapped). No alternate source (state redirects back to it; no EasyVote; nothing in Wayback). **Honest-empty + scaffolded; RE-RUN THE HARVESTER when the portal is up** (see TODO) |

**Existing layer untouched:** `all_votes.csv` (7-district council, strong mayor, 4 interleaved bodies; votes 2021+ LLM-extracted), 457 council + 145 PC minutes, **13,334 public comments** (the repo's richest comment corpus), `db/slc.db` unchanged.
**New footprint on disk:** ~240 MB raw (Council packets index-only off-disk; PC packets 48 MB + housing 89 + ordinances 83 + pmn/transcripts small).

## Cross-dataset / audit signals surfaced (flagged, NOT fixed — additive-only)
1. **65 of 68 un-URL'd 2020 Laserfiche minutes now have citable PMN URLs** (`pmn_backfill/url_recovery_2020.csv`)
   — merge into `minutes_index.csv` provenance in a deliberate pass (closes the SLC-2020-URL TODO).
2. **2 Formal council meetings** (2020-06-09, 2020-06-16) were in the repo as Work Sessions only — recovered.
3. **Pre-2026 Planning Commission agendas/packets not machine-discoverable** (slcdocs.com surfaces only the
   current year) — a backfill target if SLC exposes an older PC index.
4. **Campaign-finance API mapped but portal down** — the one dataset that couldn't complete; ready to harvest.

## Skill changes worth folding in
- **PrimeGov holds only the sponsoring body's series** (SLC = Council family only; PC elsewhere) — don't assume
  a city's PrimeGov archive contains every body.
- **PMN date-diff must key on (date, session-type)** for interleaved-series cities (Work Session vs Formal share
  a date), and the 2020-URL-recovery trick (fetch PMN minutes, match by in-PDF date, record the `/pmn/files/<id>.pdf`
  URL) is a reusable way to citation-backfill session-portal minutes.
- **Campaign-finance data-only portals** (SLC's JSON WebAPI, no PDFs): reverse-engineer the endpoints from the
  Angular bundle, but budget for maintenance windows — scaffold + honest-empty + a ready harvester if it's down.
- YouTube caption recipe needs `--js-runtimes node --extractor-args "youtube:player_client=android"`, and
  `/streams`+`/videos` are disjoint (union both).

## Source index
`slc_city_council/sources.csv` regenerated: **1,890 documents indexed, 95% with recorded URLs** (up from 837;
the shortfall = the portal-blocked campaign finance + the 68 Laserfiche-2020 minutes, 65 of which now have a
recovered PMN URL logged in `pmn_backfill/url_recovery_2020.csv`). Repo-root `sources_summary.md` refreshed.
