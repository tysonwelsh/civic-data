# ut_state / statutes — sources & provenance

Verbatim current text of the three Utah Code chapters that **every city and county in
this repo administers**: the Municipal and County Land Use, Development, and Management
Acts (LUDMA) and the Property Rights Ombudsman Act. Nothing here is paraphrased or
modeled — each section file is the official statutory text lifted from the Utah
Legislature's published Utah Code XML. Corrections, if ever needed, re-extract from the
linked source; never hand-edit the section text.

## Publisher (official)

**Office of Legislative Research and General Counsel, Utah State Legislature** —
the official publisher of the Utah Code (`le.utah.gov/xcode/...`). The `le.utah.gov`
section pages render their text through JavaScript (a plain fetch returns only the site
skeleton), but the same official text is served as a static **chapter-level XML** file,
which is what was extracted here. The developer API (`glen.le.utah.gov/code/...`) requires
a gated developer token and was **not** used (no account created); the public chapter XML
is the same authoritative text.

## Code-as-of

- **Retrieved:** 2026-07-20.
- **Version:** current published Utah Code. Both LUDMA chapters carry chapter-level
  `<effdate>11/6/2025</effdate>` — they are the product of the **2025 recodification**
  (see below). The Property Rights Ombudsman Act (13-43) is unchanged original text
  (2006 enactment, later amendments), current-version code stamp `1800010118000101`.
- The filename version stamp on the two recodified chapters is `2025110620251206`.

## IMPORTANT — the 2025 LUDMA recodification (a live finding)

Both land-use acts were **renumbered and amended effective 11/6/2025** (2025 Special
Session 1). This happened days before this pull, so third-party mirrors (Justia, FindLaw)
still show the OLD chapters and are stale; `le.utah.gov` is the only current source.

| formerly | now (current) | act | effective | renumber bill |
|---|---|---|---|---|
| Title 10, Chapter **9a** | Title 10, **Chapter 20** | Municipal LUDMA | 11/6/2025 | 2025 S1 ch. 15 |
| Title 17, Chapter **27a** | Title 17, **Chapter 79** | County LUDMA | 11/6/2025 | 2025 S1 ch. 14 |
| Title 13, Chapter **43** | (unchanged) Title 13, Chapter 43 | Property Rights Ombudsman Act | — | — |

Old §10-9a-101 / §17-27a-101 now return "Repealed 11/6/2025" stubs. The
moderate-income-housing / housing-preemption sections the task pointed at (old
`10-9a-403` area) live in the **new Chapter 20** — e.g. `10-20-403` (Moderate income
housing element) — and are included here. Legislature crosswalks:
<https://le.utah.gov/lrgc/Recodification/Chapter_10_9a_Crosswalk.pdf> and
<https://le.utah.gov/lrgc/Recodification/Title_17_Cross_Walk.pdf>.

## Exact source files (byte-verified 2026-07-20)

| chapter | catchline | sections | XML URL | bytes |
|---|---|---|---|---|
| 10-20 | Municipal Land Use, Development, and Management Act | 109 | <https://le.utah.gov/xcode/Title10/Chapter20/C10-20_2025110620251206.xml> | 467,544 |
| 17-79 | County Land Use, Development, and Management Act | 101 | <https://le.utah.gov/xcode/Title17/Chapter79/C17-79_2025110620251206.xml> | 501,151 |
| 13-43 | Property Rights Ombudsman Act | 8 | <https://le.utah.gov/xcode/Title13/Chapter43/C13-43_1800010118000101.xml> | 39,590 |

**218 sections total.** Each chapter XML also has a matching `.pdf` and `.rtf` at the same
stem; part-level compiled PDFs exist too (e.g. `C10-20-P9_2025110620251206.pdf`).

## What was extracted / layout

- One **plain-text file per section**, `text/<chapter>/<section>.txt` (e.g.
  `text/10-20/10-20-403.txt`), rendered verbatim from the XML: section number + heading,
  a `[History: ...]` line (the enacting/amending source), then the subsection text with
  its native `(1)/(a)/(i)` labels and nesting preserved.
- `index.csv` — one row per section: `title, chapter, chapter_title, section, heading,
  path, source_url, chapter_xml_url, retrieved_date, doc_class`. `source_url` is the
  durable canonical section page (`.../10-20-S403.html`, verified to resolve);
  `chapter_xml_url` is the exact byte-verified file the text came from.
- `doc_class=statute` (per SCHEMA_SPEC §9 doc-class convention).

## Honest gaps / notes

- Section headings and text are **verbatim** current version. Prior (pre-recodification)
  versions and historical amendments are NOT captured — this is a point-in-time snapshot
  (retrieved 2026-07-20); re-extract from the linked XML to refresh.
- Only the three requested chapters are here. Related land-use statutes referenced by
  cross-reference (e.g. Title 63I sunset provisions, impact-fee Title 11 ch. 36a) are
  out of scope.
- Each section's `<history>` line is captured, but the full annotation apparatus
  (notes, cross-references, session-law detail) published in annotated third-party
  editions is not — this is the official un-annotated text only.
