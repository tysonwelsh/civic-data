# expand-city-sources — St. George expansion report

**Date:** 2026-07-02 · **City:** St. George (Washington County) · **Skill:** `.claude/skills/expand-city-sources/`
**Second city after the Lehi pilot.** All six new source types built; every dataset passes
`validate_dataset.py`; no existing dataset modified. Concurrency pre-flight ran clean (a
remediation session had finished St. George ~40 min earlier; repo quiet throughout my run).

Purpose of this run: exercise the skill on a **different vendor family** (Revize static CMS +
Washington County) than Lehi's Granicus, and confirm the Lehi revisions hold up. They largely
did — and surfaced one real regression (the packet size-cap) plus several refinements below.

---

## Per-source results (all validate PASS)

| # | Source → dataset | Yield | Gaps / notes |
|---|---|---|---|
| 1 | Packets → `packets/` (**LINK INDEX**) | **224 packets indexed** (Council 177 · 2022–25; PC 47 · 2024–25) — URL + size + kind per row, no PDFs stored | Revize bundles each meeting into one 10–150 MB image/map-heavy PDF (7.5 GB total, not text-convertible); by owner decision kept as an on-demand link index (356 KB). **Resolved (below).** |
| 2 | Housing → `housing_plans/` | **7 docs, ~88 MB**: General Plan (web/HTML), 2040 Downtown Area Plan, 2022 MIH Plan, 2023/24/25 state compilations + SB 34 | GP is web-only (no PDF); state files are statewide compilations (St. George pages bracketed out — corrected a "St. George < Summit County" alphabetization bleed) |
| 3 | Ordinances → `ordinances/` | **252 rows, 35 PDFs**; ~99% land-use; **118 genuine `high` cross-matches** via independent Recorder notices | Sterling code host 403-blocked (same as American Legal); Title 10 recovered from PMN; 2020–22 predate numbering |
| 4 | PMN backfill → `pmn_backfill/` | **20 docs / 17 dates recovered** (mostly 2022–25 work/joint council meetings) | Corrected recon (241=Council, **242=PC**); repo is a superset; PMN's own "minutes" labels were wrong 3 ways (verified past them); PC 2023-05-23 still missing |
| 5 | Transcripts → `transcripts/` | **10 ASR transcripts (~106k words)**; `yt-dlp` auto-install worked | 37 uncaptioned (near-total **2023–24 gap**); council on **two channels**; PC not on video; 2024 = top Whisper candidate (not run) |
| 6 | Campaign finance → `campaign_finance/` | **104 rows / 14 packets** (2021/23/25); **40/40 (year,candidate) join to elections** | Filed with City Recorder (not state/county); 2021 via Wayback; **2019 proven absent**; scanned → OCR |

**Existing layer:** untouched — `all_votes.csv` 8,313 lines, 305 council + 132 PC minutes, `db/civic.db` unchanged.

---

## Timing (wall-clock, six agents in parallel)

PMN ~10 min · housing ~15 · ordinances ~15 · packets ~35 (throttled 224-fetch) · campaign
finance ~25 (Wayback + 230-page OCR) · transcripts ~37 (incl. a ~15-min YouTube rate-limit
cooldown). End-to-end ≈ slowest (~37 min) + verification/docs.

---

## Agenda-packet decision — RESOLVED: index-only

St. George's Revize CMS bundles each meeting into **one 10–150 MB PDF** heavy with maps/plats/site
plans — **not text-convertible** (vision/OCR only), and **7.5 GB for the full 224-packet set**.
Given disk constraints and the low text-conversion value, the owner chose to keep `packets/` as a
**link index, not a document store**. Done:
- `index.csv` = all **224 packets** (Council 177 · 2022–25, PC 47 · 2024–25), each with a live
  `source_url`, `size_mb`, and `packet_kind` (`full_packet` vs thin `agenda_packet`). Every URL
  verified HTTP 200 on 2026-07-02.
- The 35 briefly-fetched PDFs were removed (public + re-fetchable); dataset is now **356 KB**.
  `raw/_fetch_log.jsonl` keeps the discovery/probe provenance.
- `packets/CLAUDE.md` documents the retention exception + **how an LLM fetches/reads a packet on
  demand** (fetch `source_url`, use vision/OCR, prefer `full_packet`). `validate_dataset.py` PASS.

To re-hydrate any subset later: `polite_fetch.py --batch <source_urls>` uncapped (7.5 GB for all).

---

## Skill revisions surfaced this run (proposed — not yet applied)

Higher-impact first:

1. **Packet size-cap must be portal-aware (regression fix).** Static-CMS/Revize packets are one
   whole-meeting PDF — the `--max-bytes 4 MB` default drops most content. Fix: only apply the cap
   to Granicus-style separable attachments; for Revize/CivicPlus single-PDF packets use no cap (or
   ~60 MB). Recon should record "packet = one bundled PDF" vs "separable attachments" per city.
2. **Fan-out doc-ownership conflict (process).** Skill rule #6 tells each agent to update the
   parent `README.md`/`CLAUDE.md`; my orchestration told them to defer it. Two of six agents
   followed the skill and edited the parent docs concurrently (no corruption this time — lucky
   ordering). Fix: when fanning out, agents write **only their own dataset `CLAUDE.md`**; the
   orchestrator writes the parent docs once, at the end. Encode this in the fan-out step.
3. **Sterling Codifiers is NOT reliably open** — correct the skill's "Sterling usually more open
   than American Legal" line. `stgeorge.municipal.codes` is Cloudflare-gated (`/Code/*` → 403,
   robots disallows ClaudeBot). Bucket Sterling with American Legal; and add: **when the code host
   is blocked, search PMN attachments for the codified title** (Title 10 was on PMN).
4. **"Notice of Ordinance Adoption" PDFs are the confidence upgrade** — they're a source
   independent of the minutes, so they convert `within_source` into genuine `high`. Note the
   gotcha that cities often post them only for recent years (St. George: 2024-10+), and that
   consent-calendar adoptions appear in the notice but cite no number in any motion (→ `medium`).
5. **yt-dlp caption reality (expand Source 5).** Auto-install worked, but: use `--sub-lang
   en-orig` (not `en.*`, which pulls ~200 translations); many videos need a JS runtime (`node`)
   or the **Python API** (`extract_info` → `automatic_captions['en-orig']`) to get captions at all
   (`--remote-components ejs:github` is code-exec-blocked); throttle after ~100 probes or YouTube
   demands sign-in; expect whole-year caption gaps and council split across two channels; PC often
   not on video.
6. **Revize doc-center path gotchas (add to the Revize note).** Doc-center links render
   `Documents/<f>.pdf` (404) but resolve at `cms3.revize.com/revize/stgeorge/Documents/<f>.pdf`;
   some newest files are root-relative `sgcityutah.gov/<name>.pdf`. Scrape links + resolve against
   `<base href>`; never guess. Also: sitemap-first discovery confirmed essential.
7. **State MIH compilation bracketing** — "St. George" sorts before "Summit County"/"Snyderville";
   bracket by the NEXT jurisdiction header and grep the sidecar for the neighbor's name to confirm
   no bleed (a county can split into multiple sub-entity blocks). TOC page numbers ≠ PDF pages.
8. **PMN "(Meeting Minutes)" labels are not authoritative** — content-verify body-name header +
   internal date + MOTION/VOTE presence before recovering (this run: Arts-Commission file under
   the council body, wrong-year filenames, an agenda packet labeled minutes). Filenames lie; trust
   the notice event date + internal text.
9. **Wayback = the only route to pre-CMS-migration cycles** (campaign finance 2021 recovered; 2019
   proven absent via a `matchType=prefix` CDX sweep) — promote the CDX gap-proof recipe.

---

## Cross-dataset wins (why expansion pays off)

- **Ordinances × minutes:** 118 ordinances now cross-matched to their adopting motions via an
  independent Recorder-notice source — richer than Lehi's within-source-only linkage.
- **PMN backfill** recovered 17 council/PC dates the city portal never surfaced, and its
  verification caught 3 mislabeled PMN documents.
- **Campaign finance × elections:** 40/40 candidate-year pairs join; the finance trail now
  completes elections → members → votes for 2021/2023/2025.

## Suggested next step
Apply revisions #1 (packet cap) and #2 (fan-out doc ownership) before the next city — both are
correctness/process fixes. Then either re-fetch St. George packets uncapped (decision above) or
move to the next city (a PrimeGov/CivicClerk city would exercise the remaining vendor family).
