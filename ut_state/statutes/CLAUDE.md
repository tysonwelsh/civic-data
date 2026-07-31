# ut_state / statutes — the LUDMA + Ombudsman statutory text

Verbatim current text of the three Utah Code chapters that **every city and county in this
repo administers**: the Municipal and County Land Use, Development, and Management Acts
(LUDMA) and the Property Rights Ombudsman Act. This is the statutory backbone under every
rezone, subdivision, exaction, and moderate-income-housing action in the local vote record,
and the law the advisory opinions (`../advisory_opinions/`) interpret.

## The 2025 recodification (READ THIS FIRST)

Both LUDMA chapters were **renumbered and amended effective 11/6/2025** (2025 Special
Session 1). Cite the CURRENT chapters, not the old ones — and note third-party mirrors
(Justia/FindLaw) are still stale:

| act | OLD (repealed) | CURRENT | sections here |
|---|---|---|---|
| Municipal LUDMA | Title 10 Ch **9a** | **Title 10 Ch 20** | 109 |
| County LUDMA | Title 17 Ch **27a** | **Title 17 Ch 79** | 101 |
| Property Rights Ombudsman Act | — | Title 13 Ch 43 | 8 |

The moderate-income-housing / housing-preemption provisions (old `10-9a-403` area) are in
Chapter 20 — e.g. **`10-20-403`** (Moderate income housing plan). Full detail + the
legislature crosswalk links in `SOURCES.md`.

## Files

- `text/<chapter>/<section>.txt` — one plain-text file per section (e.g.
  `text/10-20/10-20-403.txt`), rendered verbatim from the official Utah Code chapter XML:
  section number + heading, a `[History: …]` line, then subsection text with native
  `(1)/(a)/(i)` labels and nesting preserved. **218 files.**
- `index.csv` — one row per section: `title, chapter, chapter_title, section, heading,
  path, source_url, chapter_xml_url, retrieved_date, doc_class`. `source_url` = the durable
  canonical section page; `chapter_xml_url` = the exact byte-verified file the text came
  from. `doc_class=statute`.
- `SOURCES.md` — publisher, code-as-of date, the recodification finding, the byte-verified
  source ledger, and honest gaps.

## Caveats

1. **Verbatim, current version, point-in-time** (retrieved 2026-07-20). Prior versions and
   the full annotation apparatus are not captured — re-extract from `chapter_xml_url` to
   refresh. This is the official un-annotated text.
2. **Official source only.** Text is from `le.utah.gov` chapter XML (the Office of
   Legislative Research and General Counsel is the official publisher). The `le.utah.gov`
   HTML pages render via JavaScript (skeleton-only to fetchers); the chapter XML is the
   same authoritative text. The developer API (`glen.le.utah.gov`) needs a gated token and
   was not used.
3. **Scope** = these three chapters only; cross-referenced statutes (impact fees Title 11
   ch. 36a, sunset Title 63I, etc.) are out of scope.

## Refresh

Re-fetch each `chapter_xml_url` (browser User-Agent), re-run the XML→section parser (method
in `SOURCES.md`), and update `retrieved_date`. Watch the filename version stamp — a new
stamp means the chapter was amended (e.g. a future legislative session).
