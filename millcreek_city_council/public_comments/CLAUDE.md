# Millcreek public_comments — IN-PACKETS harvest (built 2026-07-19; ?packet=true wave same day)

**The bar (READ FIRST):** `all_comments_clean.csv` holds ONLY **genuine public-submitted
written comments** — text a resident actually wrote and the city published (forwarded
resident emails, the city's FormCenter "Public Comments" web-form submissions, and standalone
"Public Comments from Residents" letters, all bundled into Planning Commission packets).
**Clerk third-person paraphrases of in-person speakers in the minutes do NOT count** (they are
meeting-record notes; not harvested). Applicants / developers / consultants / staff / the
Community Council are EXCLUDED. Same bar as Provo / SLC.

## Two harvest waves → 27 comments
1. **Retained Minutes-view packets** (`raw/packet_txt/`, no network) → **9** letters —
   the 2021 & 2024 digital-billboard fights + a 2022 FCOZ slope-waiver.
2. **Large `?packet=true` land-use packets** (fetched 2026-07-19; binaries discarded per
   SCHEMA_SPEC §9) → **18** new comments after content-dedup — these are a **different, much
   larger PDF** than the Minutes-view doc, whose staff-report appendices carry standalone
   resident letters, forwarded emails, AND the city's web-form submissions the Minutes-view
   omits. This **substantially closes the honest ceiling** the first wave documented.

`all_comments_clean.csv` = **27 genuine written comments** (`source=agenda_packet`, SLC 14-col
schema, 100 % `date_normalized`). By year: **2020 ×12, 2021 ×5, 2022 ×2, 2024 ×5, 2026 ×3**.
By channel: web-form 10, standalone letter 6, forwarded email 2, Minutes-view 9.

## Files
| File | What it is |
|---|---|
| **`all_comments_clean.csv`** | Canonical merged output (SLC 14-col). **27** comments. `quality_flag` records the channel (`web_form` / `letter_appendix` / `email_block`) + honesty flags (`date_from_filename`, `ocr_garbled`, `name_unreliable`, `header_residue`, `truncated_long`). |
| **`build_comments.py`** | **Canonical builder** — runs both extractors, merges, **content-dedups** (a letter in both a Minutes-view and a `?packet=true` doc, or under a name variant like "ClinicalTeam"/"Clinical Team", is ingested once; Minutes-view wins ties), and prunes the `packet_true_txt` sidecars to comment-bearing only. Deterministic, no network. |
| `harvest_packets.py` + `extract_packet_comments.py` | Wave 1: the 99 retained Minutes-view PC packets → the 9. Unchanged; still reproduces the 9 byte-for-byte. |
| **`harvest_packet_true.py`** | Wave 2 (NETWORK): fetches each PC `full_packet`'s `?packet=true` URL (browser UA, polite), sha256's it, `pdftotext -layout`, **DISCARDS the binary** (§9), keeps text in `raw/packet_true_txt/`. Every fetch logged to `packet_true_fetch.csv`. Resumable; carries sha256 forward on resume. |
| **`extract_packet_true_comments.py`** | Wave 2 extractor — **three channels** (web-form submittals, forwarded resident emails w/ a real `Sent:`/`Date:`, signature-anchored resident letters). Positive gate = first-person RESIDENT dwelling self-ID; negative gates = author org/role (applied to signer/signature only, never the body — residents discuss "the developer") + staff/applicant DOCUMENT markers. → `all_comments_packet_true.csv` + `all_comments_packet_true_dropped.csv`. |
| **`packet_true_fetch.csv`** | Full-coverage fetch ledger — one row per PC `?packet=true` (all **100**): `fetch_status` (§9 closed vocab), `bytes`, `sha256`, `pages`, `text_chars`. Provenance for the discarded binaries; proves every packet was fetched. |
| `packets_scanned.csv` | Wave-1 audit — every retained Minutes-view PC packet scanned (all 99). |
| `all_comments_dropped.csv` / `all_comments_packet_true_dropped.csv` | Audit trails with `_drop_reason` (13 wave-1; 180 wave-2 — applicants, consultants, staff, Community-Council recs, forwarder wrappers, un-signed letters, too-short/OCR). |
| `AVAILABILITY.md` | Availability audit + the 2026-07-19 harvest & `?packet=true` addenda (stats + the residual ceiling). |
| `raw/packet_txt/` (5) · `raw/packet_true_txt/` (5) | `pdftotext -layout` sidecars for the **comment-bearing** packets only (provenance for every row; non-comment-bearing `?packet=true` text is not kept — re-derivable via `harvest_packet_true.py`, logged in the fetch ledger). |

## Re-run
`python3 harvest_packet_true.py` (network; re-fetches the ~4.8 GB, discards binaries) then
`python3 build_comments.py` (does both extractors + merge + dedup + prune), then rebuild
`weeks/` (`python3 ../build_weeks.py` — **comments DO feed weeks**). `build_comments.py` alone
(no re-fetch) rebuilds the CSV from the retained sidecars and is idempotent.

## Coverage + the residual (honest) ceiling
The `?packet=true` route was fetched for **all 100** PC full-packets (99 ok, 1 `not_pdf` =
2023-03-15 doc674, an HTML error page — recorded, not fabricated; doc757/2023-12-20 has no
combined packet, a known city gap). Comments cluster on contentious land-use: **2020**
Countryside/Hillside-Lane subdivisions + Old Meeting House (web-form era), **2021/2024**
digital billboards, **2022** height/FCOZ waivers, **2026** Lexington Village. **Residual
ceiling (still honest):** letters whose signer is unrecoverable in OCR (6 `no_recoverable_signer`
drops), any image-only appendix pages `pdftotext` can't read, and the pre-2018 agenda-only
era (no combined packet existed). Never fabricated: OCR garble in bodies is preserved verbatim
(e.g. Susan Bowlden's `wri ng`/`distrac ng` fi-ligature drops, Kathy Blake's `I'tn`/`@et`),
never "corrected"; ambiguous authorship is DROPPED, never guessed.
