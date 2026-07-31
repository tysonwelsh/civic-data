# land_use/ — sources (Washington County Planning Commission)

Unincorporated-county land-use body. Meets **Tuesdays 1:30 pm**. Two harvest channels
(2026-07-20):

1. **County archive** (`washco.utah.gov`) — PC minutes carry the ` PLAN` suffix at
   `/forms/pdf/minutes/{year}/M {date} PLAN.pdf`, enumerated via the month-query form
   (`/forms/commission/minutes/?m=MM&y=YYYY`). Covers **2019–2023** well (43 docs) then drops
   off (2024:0, 2025:1, 2026:1). Mostly born-digital; some scanned (OCR'd, `ocr:true`).
   `provenance: citysite_minutes`.
2. **Utah Public Notice (PMN), public body `701`** — the Washington County **Land Use
   Authority** (this IS the Planning Commission; PMN labels the body "Land Use Authority"
   while its notices are titled "Planning Commission Agenda/Meeting"). Harvested via the PMN
   JSON search API (`POST /pmn/searchresult.html`, entity="Washington County", paginated;
   filtered to the Land Use Authority body). Minutes are attached to each meeting's notice as
   `YYMMDD PC Minutes.pdf`. This channel supplies the **2024-10 → 2026 minutes** the county
   archive stopped posting (15 docs added, all born-digital). `provenance: pmn_minutes`.

**Recording ceiling:** narrative minutes; **no vote extraction** (see `../CLAUDE.md` scope
decision). Born-digital docs `ocr:false`; scanned `ocr:true` with a verify note.

**Coverage / honest gaps** (`gaps.csv`): PMN body 701 shows **28 PC meeting dates in
2024–2025; 13 carry a minutes PDF, 15 are agenda/audio-only** (no minutes published on either
PMN or the county archive as of harvest). Notably **all 2024 meetings Jan–Sep have no
published minutes** — PMN minutes uploads begin **2024-10-08**. These are logged in
`gaps.csv`, never fabricated. 2025-06-10 exists on BOTH channels; the county-archive copy is
retained (PMN duplicate skipped).

PMN search note: the interactive search page loads reCAPTCHA and the browser form returns
"Technical Difficulties" to naive POSTs; the working path is a **JSON** POST body with the
`X-CSRF-TOKEN` header (the app's `stat.ajax.req` JSON-stringifies params). Entity-name search
works; the `publicBodyName` exact-match filter does not, so filter the body client-side.
