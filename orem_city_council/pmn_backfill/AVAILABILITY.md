# Orem on Utah Public Notice (PMN) — entity & body IDs

As-of **2026-07-05**. Source: `https://www.utah.gov/pmn/`.

## Crawl chain (all GET, no POST)

1. `https://www.utah.gov/pmn/list/entities.html?id=3&limit=2000` (govType 3 = Municipality)
   → **Orem entity id = `229`** (`<a href="#" id="229">Orem</a>`).
2. `https://www.utah.gov/pmn/list/publicBodies.html?id=229&limit=2000` → every Orem body id.
3. `https://www.utah.gov/pmn/list/notices.html?id=<bodyId>&page=300` → the body's **entire**
   notice history in one GET (default view is 6 months; historical SEARCH is POST/CSRF and
   cannot be used with a GET-only fetcher — the high `page` number is the workaround).
4. Notice page: `https://www.utah.gov/pmn/sitemap/notice/<noticeId>.html`.
   Attachment file: `https://www.utah.gov/pmn/files/<fileId>.pdf` (opaque ids — crawl, never
   template by date).

## Orem public bodies (entity 229)

| Body | PMN body id | Notices (history) | Minutes attachments | In repo? |
|---|---|---|---|---|
| **City Council** | **734** | 805 | 313 | yes (meeting_minutes/) |
| **Planning Commission** | **642** | 491 | 181 | yes (planning_commission/) |
| **Board of Adjustments** | **643** | 29 | 11 | no |
| **Redevelopment Agency of the City of Orem** | **893** | 62 | 37 | no |
| **Municipal Building Authority of the City of Orem** | **894** | 26 | 10 | no |
| Special Service Lighting District of the City of Orem | 895 | — | (bundled under Council) | no |

Other Orem bodies present but out of scope for minutes backfill (advisory commissions,
CARE, CDBG, Development Review Committee, Heritage, Library, Youth Council, etc.). Full list
captured during the crawl; ids are global (not sequential) so they must be read from
`publicBodies.html`, never guessed.

## Notes on the notice-list HTML

- Each `<tr>` = one notice: a `sitemap/notice/<id>.html` link + human title (often carrying
  the meeting date as `MM.DD.YYYY` or `Month DD, YYYY`), a meeting-datetime column
  (`YYYY/MM/DD hh:mm AM/PM`), and a `<ul>` of attachments. Each attachment `<li>` has the
  file link + a parenthesized **type label**: `(Meeting Minutes)`, `(Public Information
  Handout)`, `(Audio Recording)`, `(Other)`, or unlabeled. **There is no `(Agenda)` label** —
  agendas ride under `(Public Information Handout)`/`(Other)`. Minutes were filtered on the
  `(Meeting Minutes)` label.
- The meeting-datetime column is occasionally wrong (stale posting date, or a bundled notice
  covering a different meeting). The attachment **filename** is the strongest signal of the
  minutes' own meeting date, then the notice title, then the datetime column. Three files had
  a filename-year typo contradicted by the document's own header (settled from the OCR/text):
  `976307` (fn "6.14.2023") → **2022-06-14 MBA**; `1097627` (fn "06.13.2024") → **2023-06-13
  RDA**; and a notice titled "9.20.2023 Planning Commission" actually carried the already-held
  `2023-09-06` PC minutes (already in repo — not a gap).
