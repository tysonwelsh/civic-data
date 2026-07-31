# Agenda Packets / Staff Reports — Availability & Coverage (STORED) — as-of 2026-07-13

**Dataset:** `packets/` — agenda packets, staff reports, and per-item supporting materials
behind Town of Alta **Town Council** and **Planning Commission** agenda items.
**Portal:** the town's `/meetings/` page is a JS-only Juniper (WordPress) search app with no
static doc links, so documents were enumerated from **Utah Public Notice (PMN)** — council
body **1601**, Planning Commission body **1602** — via the cumulative list
`https://www.utah.gov/pmn/list/notices.html?id=<body>&page=200` (one GET returns the body's
entire notice history: 425 council notices, 134 PC notices). Each notice's attachments are
`https://www.utah.gov/pmn/files/<fileId>.pdf`.

## Mode decision: STORED (not index-only)
The full candidate set HEAD-sized to **1005 MB across 852 attachments** — under the ~1.5 GB disk
budget — so every packet document is **retained on disk** in `raw/<date>/` (born-digital and
scanned PDFs verbatim; **969 MB / 847 PDFs** after excluding 5 mislabeled minutes-type files that
were actually agendas/packets were *added* and 10 filename-minutes docs were *excluded* — see
below), with `raw/_fetch_log.jsonl` as byte-level provenance. Of the 847 stored PDFs,
**829 are born-digital** with a `text/` sidecar (`extract_packet_text.py`, `pdftotext -layout`)
and **18 are image-only** bundled packets that carry no sidecar (vision/OCR is the documented
path — each logged `image_only` in `text/_extraction_log.csv`).

## ⚠ Alta is SPARSE BY DESIGN
~380 residents. Council meets ~monthly (2nd Wednesday, ~12/yr); the PC meets 4th Wednesday
**as-needed and is frequently cancelled**. Low counts — especially the thin PC record
(1 meeting in 2021, 2 in 2022) — are the *correct* record for a town this small, **not** a gap.

## ⚠ The structural fact that shapes this dataset: Alta unbundled its packet
Alta's document practice **evolved**, and this drives the file counts:
- **2020 – mid-2025 (unbundled era):** Alta posted **no single "Meeting Packet" PDF**. Each
  agenda item's supporting document — draft resolutions/ordinances, budget worksheets, staff
  reports, memos, zoning redlines, studies, exhibits — was posted as a **separate handout**
  alongside a per-meeting **Agenda**. So the honest "packet" for these meetings is the
  **Agenda + the set of individual handouts**, which is why 2020–2024 have the *most* files
  (107–169 council files/yr).
- **Mid-2025 → present (bundled era):** Alta switched to a single bundled
  **"… Meeting Packet.pdf"** (agenda + all staff materials in one PDF), so file counts *drop*
  (50 in 2025, 21 in 2026) even though coverage is complete. First bundled council packet
  **2023-06-07**; standard from ~2025-08. First bundled PC packet **2024-12-18**.

`packet_kind` records which kind each row is: `full_packet` (bundled), `agenda_packet` (the
meeting agenda outline), `staff_report` (memo/report/presentation/slides), `supporting_doc`
(draft ordinances/resolutions, budgets, exhibits, studies, letters — the unbundled item
materials).

## ⚠ PMN attachment TYPE labels are UNRELIABLE — classified by FILENAME
Alta's clerk mislabels PMN attachment types: e.g. the **2026-03-11 council Agenda and Meeting
Packet are both tagged "(Meeting Minutes)"** on PMN. Enumeration therefore classifies and
filters **by filename**, not by the PMN type label. Minutes documents (filename contains
"minutes" — approved council/PC minutes, draft minutes, budget-committee minutes attached as
exhibits) are **excluded** here; the audited minutes live in the `meeting_minutes/` and
`planning_commission/` datasets. Audio (`.mp3`) is never a packet. **Any future refresh MUST key
on filename, not the type label** (a type-label filter silently drops mislabeled agendas/packets).

## Coverage (what exists)

| Body | Files | Meeting dates | Date range | full_packet | agenda_packet | staff_report | supporting_doc |
|---|---|---|---|---|---|---|---|
| Town Council (1601) | 778 | 112 | 2020-01-08 → 2026-07-08 | 31 | 190 | 89 | 468 |
| Planning Commission (1602) | 69 | 24 | 2020-07-28 → 2026-03-25 | 14 | 23 | 9 | 23 |
| **Total** | **847** | **136** | | **45** | **213** | **98** | **491** |

Files per year — Council: 2020×122, 2021×161, 2022×169, 2023×148, 2024×107, 2025×50, 2026×21.
PC: 2020×12, 2021×1, 2022×2, 2023×4, 2024×22, 2025×23, 2026×5 (the sparse-by-design PC record).

## Vote-date join coverage (`date` + `body` → `../*/all_votes.csv` / minutes)
- **Council:** of **84** council minutes dates, **83** have a packet document indexed here. The
  one gap — **2026-03-04** — is a special meeting for which Alta posted **only audio + minutes**
  on PMN (no agenda/packet); honest, not a scraper miss. (29 additional packet dates carry no
  minutes: work sessions, budget-committee meetings, special meetings, and the most recent
  meetings whose minutes are not yet approved/posted.)
- **Planning Commission:** of **17** PC minutes dates, **15** have a packet. Gaps —
  **2022-06-02** and **2023-10-24** — have minutes on PMN but no separately-posted agenda/packet.

## What was checked and is genuinely absent
- **2026-03-04 council special meeting** — no agenda/packet on PMN (audio + minutes only).
- **2022-06-02, 2023-10-24 PC** — minutes only, no packet on PMN.
- **2020-01-08 council** appears under two PMN notices (a duplicate re-post); both notices'
  attachments were enumerated and de-duplicated by PMN file id.
- Some meetings post an **Amended** agenda/packet in addition to the original — both are retained
  as distinct rows (distinct file ids), never collapsed.

## Primary-document text layer (`doc_class`, 2026-07-16 — classify-in-place)
The stored attachments were classified into the four content-bearing primary-document classes
(SKILL.md Source 7). Alta already carries `text/` sidecars, so nothing was fetched — the
`doc_class, fetch_status, sha256, text_path, text_chars` columns were added by
`classify_attachments.py`. **Result: `staff_report` = 11 (10 with sidecar text / 1 image-only
scan flagged `needs_ocr`); `member_memo`, `plan_amendment`, `development_agreement` = 0 (honest
empties — verified).** For a ~380-person town whose land-use docket is a few ski-area
CUPs/variances plus a subdivision-ordinance rewrite, a small classified count IS the correct
record. Precision 11/11 = 100% (whole-class ground-truth); recall via exhaustive title +
sidecar-header sweeps (est. miss <5%). The 11 land-use staff reports: zoning-map ratification
(2021-04-14), RACS/Conex CUPs (2022-06-15, 2023-07-18), ski-area slope variances to the Appeal
Authority (2022-06-15, 2023-08-09), Sugarplum Meadows site-plan/PUD (2023-10-11), a zoning-
amendment memo (2020-08-12), and subdivision-ordinance staff reports (2024-03-27/05-22/09-11).
**Boundary decisions** (see `CLAUDE.md`): business-license/STR, parking, noise, budget, and
PC-governance staff reports are out of scope (not land-use); Shallow Shaft rezone PRESENTATIONS
are excluded (slide decks, not staff reports — no separate staff report was posted); the
"Peruvian Estates West Line Memo" is a waterline budget item, not land-use.

## Reading the bundled packets
The bundled `full_packet` PDFs are large (typical 10–30 MB) and **map/plat/site-plan heavy**;
several are image-only and are **not text-convertible** — a text sidecar is absent by design and
vision/OCR is required to read them (each such file is logged `image_only` in
`text/_extraction_log.csv`). The unbundled-era `agenda_packet`/`staff_report`/`supporting_doc`
PDFs are overwhelmingly born-digital and have `text/` sidecars.
