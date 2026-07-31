# SLC Council — Meeting Minutes

Scrapes Salt Lake City Council (and CRA/RDA/LBA) meeting **minutes** as text, then
uses Claude to extract a **votes table** per meeting. Sibling of `../public_comments`.

## Pipeline

```
scrape_primegov.py     PrimeGov portal -> minutes/<year>/<week>/<date>_<slug>.md   (PRIMARY, 2021+)
scrape_laserfiche.py   Laserfiche portal -> minutes/.../<date>_<slug>.txt          (only source pre-2021)
                       -> minutes_index.csv   (every file on disk; repo-standard schema
                          date,year,title,slug,path,source,source_url,format;
                          source = primegov|laserfiche, format = text|ocr)
extract_votes.py       Claude per meeting -> votes/<year>/<week>/<date>_<slug>.json
                       -> all_votes.csv       (long format: one row per member-vote; the analysis file)
```

- **Index schemas (2026-07-02 retrofit):** `minutes_index.csv` was migrated to the
  clone-standard schema above; the pre-retrofit index's extra columns
  (`week_start`, `chars`, `ref_id`) live in the frozen `minutes_index_legacy.csv`.
  `scrape_primegov.py`'s `rebuild_index()` maintains the standard file;
  `scrape_laserfiche.py` writes its richer per-page provenance (pages/chars/entry_id
  + per-doc source_url for the 2020 files) to `index_laserfiche.csv`.
- **2020 `source_url` (citation-provenance fix, 2026-07-19):** the 68 Laserfiche 2020
  rows were originally URL-less in the standard `minutes_index.csv` (the
  `index_laserfiche.csv` `webdme.slcgov.com/…/DocView.aspx?id=` links are session/portal
  DocView URLs, not durable third-party citations). **65 of the 68 now carry a durable
  Utah Public Notice citation** (`source_url=https://www.utah.gov/pmn/files/<id>.pdf`)
  matched + re-verified in-body to the same meeting's PMN-posted minutes (see
  `../pmn_backfill/url_recovery_2020.csv` + its CLAUDE.md). `source` stays `laserfiche`
  (the stored OCR text is unchanged — the URL cites the equivalent record). The 3
  Jan-2020 Formal dates PMN never posted (only their Work Session) stay honestly URL-less.
- **all_votes.csv is the standard 13-col schema + the documented trailing `provenance`
  column** (`body` after `title`, short codes `Council`/`RDA`/`CRA`/`LBA` — added
  2026-07-02, derived from the minutes' section headers via the db build; see
  `../VERIFICATION.md`. `provenance` added 2026-07-17: `minutes` = portal-scraped
  audited primary, `pmn_minutes` = the 4 PMN-recovered 2021/2023 docs' 20 rows —
  emitted by `rebuild_csv()` from `minutes_index.csv`'s `source`).

- **API key**: `ANTHROPIC_API_KEY` auto-loads from a gitignored `.env` via `config.py`
  (same key/pattern as the comments project). Don't ask for it; don't print it.
- **Model**: `claude-sonnet-4-6` (set in `config.py`).
- **Dependency**: `extract_votes.py` needs `anthropic`; `scrape_primegov.py` needs
  `markdownify` (`pip install markdownify`).

## Sources — two portals, why PrimeGov wins

| | PrimeGov (slc.primegov.com) | Laserfiche (webdme.slcgov.com) |
|---|---|---|
| Minutes format | born-digital **HTML** -> clean Markdown | scanned images + **OCR** |
| Coverage | minutes 2021–present (agendas 2018+) | 1982–present |
| Currency | current, incl. pending/unapproved | lags ~3 months |
| Access | plain JSON API | cookie/session dance |

**Use PrimeGov for 2021+.** Laserfiche is only needed for pre-2021 minutes (we keep
2020 from it; 2018–2019 could be added with `scrape_laserfiche.py` if wanted).
PrimeGov has **no minutes before 2021** (agendas only) — don't go hunting for them there.

### PrimeGov API (no auth)
- List meetings: `GET /api/v2/PublicPortal/ListArchivedMeetings?year=YYYY` -> JSON,
  each meeting has `title`, `dateTime`, and a `documentList`.
- A meeting's minutes = the `documentList` entry with `templateName == "HTML Minutes"`;
  take its `templateId` and `GET /Portal/Meeting?meetingTemplateId=<templateId>`. That
  page embeds the compiled minutes as an HTML doc; `extract_minutes()` slices its
  `<body>` and converts to Markdown.
- **Scope filter** (`BODY_RE`): Council + CRA/RDA/LBA; minor committees/commissions skipped.

### Why Markdown, and the table caveat
Minutes are saved as **Markdown** (not plain text) to keep attachment **links** and
motion/vote **emphasis** that plain text loses. BUT PrimeGov nests HTML tables purely
for *layout* (agenda-item number | text), not data — converting them to MD tables makes
garbage, so `extract_minutes()` **linearizes** tables (cell→space, row→break) before
markdownify. Real vote data ("**AYE:** … **Final Result:** 7–0") is inline text and is
preserved. The 2020 Laserfiche files stay `.txt` (OCR, no HTML).

## PMN-recovered minutes (2026-07-17) — votes EXTRACTED same day
Four PMN-recovered council minutes docs were promoted into this layer 2026-07-17 (PMN-crosscheck
missing_minutes leads; `source=pmn`, `format=text`): **2021-05-13 Special Limited Formal**,
**2021-05-13 Council Work Session**, **2021-06-10 Council Work Session**, **2023-05-25 Council
Work Session Meeting** (COVID-era Thursday electronic meetings). ✅ **Votes extracted 2026-07-17
(evening)** by direct read of the promoted markdown (no API batch; same JSON schema): the Special
Limited Formal carries **1 motion** (Resolution 17 of 2021 appointing Dennis Faris to the D2
vacancy, 6-0 — six members present, the D2 seat itself vacant, so no absent row) and the
2021-06-10 Work Session **2 motions** (enter/exit Closed Session, both 7-0); the **2021-05-13
Work Session and 2023-05-25 Work Session have honestly ZERO formal votes** (D2-candidate straw
polls only / "Item not held") — their `.votes.json` carry empty `votes` arrays by design.
`all_votes.csv` now carries the repo-standard trailing **`provenance` column** (`minutes` =
portal-scraped audited primary; `pmn_minutes` = these 20 rows), derived from
`minutes_index.csv`'s `source` by `rebuild_csv()`; `db/build_db.py` stores it on `motion`.
Provenance + full write-up: `../pmn_backfill/CLAUDE.md`.

## 2022-08-29 two-session recovery (2026-07-19) — born-digital PrimeGov, votes by direct read
The Q3 refresh surfaced **two distinct same-date, same-title PrimeGov docs** for the
2022-08-29 "Special Limited Formal Meeting" (templates **2955** and **2920**). In-body
evidence (times, agendas, roll calls) confirmed they are **two genuinely separate sequential
sessions the same evening**, not versions of one another — ingest BOTH (west_jordan
work-session precedent). Both promoted here as born-digital PrimeGov (`source=primegov`,
`provenance=minutes`, `> Source:` header), disambiguated slugs under
`minutes/2022/2022-08-29/`:
- **`…truth-in-taxation`** (template 2955, 6:05–6:15 pm, approved Oct 18, 2022) — the
  FY2022-23 **Truth-in-Taxation** hearing, **1 motion** (adopt final tax-levy ordinance, 7-0).
- **`…budget-amendment`** (template 2920, 6:20–6:40 pm, approved Nov 10, 2022) — **Budget
  Amendment No. 1** + Other Side Village consent + closed session, **5 motions**
  (7-0/7-0/7-0/6-0/7-0; the 6-0 is the exit-closed vote with Valdemoros absent).

Votes extracted by direct read (no API), **6 motions / 42 member-vote rows**, all tallies
cross-checked 6/6; screen_corpus clean; validate_city 0 FAIL. The born-digital 2920
supersedes the earlier PMN OCR copy (`pmn_backfill/` file 913093, which was mislabeled
"Truth-in-Taxation" — it is actually the budget-amendment session). Disambiguation evidence +
the ceremonial Oath/Redistricting do-not-ingest ruling: `../pmn_backfill/AVAILABILITY.md`
(2026-07-19 note) and `../pmn_backfill/pmn_exceptions.csv`.

## Votes extraction (`extract_votes.py`)
Per meeting, Claude returns each recorded vote: `motion`, `description`, `motion_type`
(Resolution / Ordinance / Budget Amendment / Appointment / Public Hearing Action / …),
`mover`, `seconder`, `result` (e.g. "6-1 Pass"), and `aye/nay/abstain/absent` member lists.
Output: one structured `votes/.../<meeting>.json` per meeting; `all_votes.csv` (long format,
one row per member-vote) is rebuilt from those JSONs and is the analysis file. Resumable:
skips meetings whose `.json` exists. Runs over PrimeGov `.md` only by default; `--include-ocr`
also tries 2020 `.txt` (messier OCR -> less reliable roll-call parsing).

## Organization & joins
- Files: `minutes/<year>/<week-start Monday date>/<meeting-date>_<meeting-slug>.<md|txt>`.
- Same-day distinct meetings are kept; byte-identical same-day dupes are removed.
- Join to the public-comments dataset on the **meeting date** (Tuesday); in the comments
  data that's `period_end`.

## Don't
- Don't expect PrimeGov minutes before 2021.
- Don't convert the layout tables to Markdown tables (linearize — see above).
- Don't commit `.env`.
