# West Valley City — Utah Public Notice (PMN) availability

CONFIRMED via the global PMN entity chain, as-of **2026-07-06**.
Source of truth: `https://www.utah.gov/pmn/`. All ids verified by crawling
`/pmn/list/entities.html?id=3` → West Valley entity → `/pmn/list/publicBodies.html`.
Crawl HTML retained in `raw/_pmn_meta/`.

## Entity

| Entity | PMN entity id |
|--------|---------------|
| West Valley City | **307** (`/pmn/list/publicBodies.html?id=307`) |

## Public bodies (the four this backfill diffs)

| Body | Abbrev | PMN body id | Notices page |
|------|--------|-------------|--------------|
| City Council | CC | **398** | `/pmn/list/notices.html?id=398&page=300` |
| Redevelopment Agency | RDA | **399** | `/pmn/list/notices.html?id=399&page=300` |
| Municipal Building Authority | MBA | **401** | `/pmn/list/notices.html?id=401&page=300` |
| Planning Commission | PC | **402** | `/pmn/list/notices.html?id=402&page=300` |

**No combined CC/RDA/MBA body exists** — WVC files each body separately (checked the
full 27-body list for entity 307; the other bodies are Board of Adjustments=403,
Housing Authority=400, and assorted committees/dissolved boards, none of which the
repo's minutes layer covers). Board of Adjustments (403) is out of scope for this
CC/RDA/MBA/PC backfill.

## File access

- Notice detail: `/pmn/sitemap/notice/<noticeId>.html`
- Attachment blob: `/pmn/files/<fileId>.pdf`  (verified sample 1396745 = 2026-02-10 Regular)
- The `notices.html?id=<body>&page=300` table returns the **full cumulative history**
  (WVC's goes back to 2008/2012) despite a boilerplate "past 6 months" banner — one GET
  per body suffices; the search form (POST-only, out of policy) was not needed.

## Coverage reality (see `coverage.md` for the per-year table)

- **CC / RDA / MBA:** PMN carries `(Meeting Minutes)`-labeled PDFs and is essentially
  co-extensive with the repo's OnBase-sourced minutes. PMN is a valuable independent
  check here because WVC's OnBase portal intermittently 403s.
- **PC:** PMN publishes **agendas only** for the Planning Commission — **zero**
  `(Meeting Minutes)` attachments across all 450 PC notices (2008–2026). PC minutes are
  an OnBase-only artifact; the repo's 263 PC minutes files are the authoritative record
  and PMN adds nothing recoverable for PC. This is an honest source ceiling, not a gap.

## Attachment-label vocabulary (as observed)

`Meeting Minutes`, `Public Information Handout`, `Other`, and blank. The label is the
publisher's tag, not proof of doc type — every recovered PDF here was opened and its
internal meeting date + minutes heading verified before promotion.
