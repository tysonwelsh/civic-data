# salt_lake_county / land_use — SOURCES

Land-use authority minutes for Salt Lake County: the **county Planning Commission**
(unincorporated county + metro-township land use). Retrieved 2026-07-11.

## The two commissions (nuance)

Salt Lake County runs **two** distinct volunteer planning commissions, differing by
geography and commissioner-residency rules. Both are land-use recommending bodies to
the County Council, so both are captured here and distinguished by the `body` column:

| `body` value | Meets | Jurisdiction |
|---|---|---|
| `Planning Commission` | ~2nd Wednesday monthly, 8:30 a.m. | Unincorporated county valley + metro townships |
| `Mountainous Planning District Planning Commission` | ~monthly (day varies) | Mountainous Planning District (canyons / mountain areas) |

Markdown filenames disambiguate them: `<date>_planning_commission.md` vs
`<date>_mountainous_planning_commission.md`.

## Where the documents come from

- **Primary source: Utah Public Notice (pmn.utah.gov), public body 712.** Both
  commissions' notices are posted under body 712. Approved minutes are attached to the
  meeting notices as born-digital PDFs (file URLs `https://www.utah.gov/pmn/files/<id>.pdf`).
- The **county website**
  (`saltlakecounty.gov/.../planning-commissions/salt-lake-county-planning-commission/`)
  publishes only **agendas** and links out to PMN body 712 for minutes — it hosts no
  minutes files of its own (the `.../minutes/<MMDDYYYY>.pdf` pattern 404s). We therefore
  sourced all minutes from PMN.

## How the list was enumerated

PMN's public-body page shows only a ~1-year rolling window, so the full 2020–present set
was gathered via the PMN keyword search (`search.html`, POST) windowed per calendar year
(title = "Salt Lake County Planning Commission" and "Mountainous Planning District",
2020-01-01 … 2026-12-31). Each returned notice page was fetched and its file list
classified: PDFs whose attachment label contains "Minutes" are the minutes; agendas,
packets, staff reports, hearing notices and audio (.MP3) were ignored.

## Dating

The meeting date for each minutes file is taken from the filename's embedded `YYMMDD`
prefix when present (the county's `YYMMDD_SLCoPC/MPDPC_MinutesApproved.pdf` convention),
otherwise parsed from the minutes header text (many older files are labeled only by the
month they cover, e.g. "October minutes.pdf", and are attached to the *following*
meeting's notice — the notice date is NOT the meeting date). Every content-parsed date
was cross-checked against its label month (0 mismatches). Approved-minutes files are
preferred; where the same meeting's minutes were uploaded to multiple notices, duplicates
were collapsed to one record.

## Extraction

All PDFs are born-digital; text extracted with `pypdf`. **Zero image-only / OCR files** —
every retrieved PDF yielded clean text (min ~2.1k chars body). No fabrication: only text
pypdf produced is stored.
