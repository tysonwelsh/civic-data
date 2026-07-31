# METHODS — how each layer was built, and how much to trust it

A citing researcher should know three things about every number here: where the source
document came from, what extracted it, and what audit stands behind it. This file states
all three per layer. The deeper references are each entity's `CLAUDE.md` /
`VERIFICATION.md`, the `_audits/` reports, and the `caveat` table inside the federated
database (joined into the analysis views, so ceilings surface at query time).

## Acquisition & provenance

Documents were fetched from each government's own publishing channel (CivicPlus, Granicus,
CivicClerk, Legistar, PrimeGov, Revize, OnBase, Utah Public Notice (PMN), le.utah.gov,
county portals), with gap recovery via the Utah Public Notice archive, the Wayback
Machine, legacy city-site hosts, and agenda-packet carves. Every document row carries a
`source_url` (99.98% coverage in the `document` catalog) plus retrieval date and
extraction method in the per-dataset `sources.csv` / `index.csv`. Recovered-vs-audited
rows are distinguishable: city-tier motions carry a `provenance` column (`minutes` =
audited primary; `pmn_roa`, `pmn_minutes`, `agendacenter_minutes`, `wayback_minutes`,
`citysite_minutes`, `doccenter_draft`, `packet_carve` = recovery channels, always
filterable). Raw binaries (PDF/audio/video) are retained locally but not committed —
re-fetchable via the recorded URLs.

## Extraction methods by layer

| Layer | Method | Notes |
|---|---|---|
| Minutes → markdown | pdftotext/OCR (tesseract) + per-city converters | OCR-era files flagged per city (see caveats) |
| Roll-call votes (most cities/counties) | **Deterministic per-city grammar/regex parsers** | The norm; parser code committed per city |
| SLC council votes | **LLM-extracted** | SLC PC is pure-regex; 2021+ only (2020 is OCR) |
| Sandy PC votes | Legistar API (structured source) | Not minutes-derived; full harvest in `legistar_*` tables |
| ut_state legislator votes | Parsed from public le.utah.gov pages | 1,208 roll calls, 0 tally mismatches on ingest checks |
| Public comments — SLC | **Claude Vision over scanned comment PDFs** (13,334) | The largest comment corpus; largest model-extracted layer |
| Public comments — Provo/Millcreek | Packet page-walk classifiers (letters extracted from agenda packets) | |
| Elections | County canvass (SOVC) normalizers + per-city audited race files | `election_race` is the audited/authoritative winners layer |
| Campaign finance | OCR + **Claude Vision transcription of scanned filings**, with per-filing reconcile checks against the filer's own printed totals | `cf_cycle` is the only sanctioned per-candidate total |
| Normalization (`motion_std`) | Shared deterministic classifier (`scripts/normalize_motions.py`) across all tiers | Per-entity classification ceilings carried as caveats (8.6%–61.1% honest no-signal share for non-city entities) |
| `disposition` / `outcome` | Derived classifier, tally-guarded | Ground-truth audited across all 31 cities (~500 motions vs source minutes), `_audits/2026-07-12-motion-classification/` |
| PC→Council referrals | **Reconstructed** subject/key matching, confidence-scored | `high` ≈ exact; `low` = flagged, don't quote. Never a looked-up key |
| Rosters | Curated seat-tenure drivers + documented overrides | Per-row confidence + sources; `VACANT` gaps kept |

Model-extracted layers (SLC council votes, SLC comments, CF vision transcriptions) are
disclosed as such; everything else is deterministic code you can read and re-run. CF
vision transcriptions reconcile against each filing's printed cover totals, with every
unresolved delta dispositioned in writing (per-city `campaign_finance/CLAUDE.md`).

## Audit regime

- **Ground-truth audits** against source documents: repo-wide extraction audit
  (`_audits/2026-07-02/`), the 31-city motion-classification audit
  (`_audits/2026-07-12-motion-classification/`), the non-city-tier audit
  (`_audits/2026-07-25/`), and the 245-item publication review
  (`_audits/2026-07-31-publication-review/`). Post-ingest audits follow large recoveries.
- **Continuous validation:** `python3 scripts/validate_entity.py <slug>` per entity, and
  `--federation` as a staleness gate (row counts + content digest between every entity db
  and the federated db; run before trusting any cross-entity number).
- **Reconciliation invariants:** federated builds assert FK integrity, doc/vote
  reconciliation, and roster seat counts; overrides that go stale fail builds loudly.

## The honesty rules the data is built under

1. **Never fabricate.** Blank member/vote = the source printed no names (tally-only);
   `minutes_unrecovered.csv` = meeting exists, minutes don't; an empty comments file =
   the city publishes none. Honest gaps are data — reported, never filled.
2. **Source-faithful values are never overwritten.** `result` / `motion_type` are
   verbatim; normalization lives alongside; corrections go through documented override
   files with evidence, never in-place edits.
3. **Derived layers are regenerated, never hand-edited.**
4. **Every known measurement ceiling is carried IN the database** as a `caveat` row that
   the analysis views join, so a query that crosses a ceiling returns the warning with
   the rows. Read `v_coverage` for the full per-entity caveat text.

## Known limitations (the short list)

Coverage floors differ by entity (city floor 2020; millcreek 2016; five township-origin
entities 2017; county depths vary — see `coverage.json`). Vote-attribution ceilings
differ (tally-only and dissent-only recording styles are per-source properties). MPO
minutes are tally-only (no member-votes by source). Public comments are substantive in
only 2 of 31 cities. The state tier's bill records are staged for reintegration on their
own terms. Every one of these is documented where you'd hit it — in the `caveat` table
and each entity's `CLAUDE.md`.
