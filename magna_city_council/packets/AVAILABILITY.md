# Magna — agenda packets / staff reports: availability & coverage

**As-of:** 2026-07-14 · **Mode:** **STORED** (born-digital PDFs on disk, 1.2 GB) ·
**Sources:** CivicPlus AgendaCenter (`magna.utah.gov`) + Utah Public Notice (PMN).

Additive `expand-city-sources` dataset (source type 1) — the staff-analysis / "why"
layer that joins to `meeting_minutes/` + `planning_commission/` by meeting **date +
body (+ meeting_type)**. It does **not** modify any existing dataset.

## What a "packet" is here
The agenda **packet** (agenda + staff reports + ordinance/resolution drafts + exhibits)
behind each Magna **City Council**, in-session **CRA** (Community Reinvestment Agency),
and **Planning Commission (PC)** agenda item. Recorded roll-call **minutes** are the
core repo's job (`meeting_minutes/`, `planning_commission/`) — they are **not** here.

## The two portals (and why both)
1. **CivicPlus AgendaCenter** — `https://magna.utah.gov/AgendaCenter`, category
   **cat3 only** ("City Council"; catIDs 1/2/4/5 all HTTP-404 — Magna publishes a
   single category). It carries **both** City Council and the in-session **CRA**
   meetings; `body` is classified from the item **title** (`CRA`/`Reinvestment` → CRA,
   else Council). The packet endpoint is the item's Agenda-slot ViewFile with
   **`?packet=true`** (the assembled full packet; `>=` the plain slot). **Coverage:
   2022+** only — the AJAX listing `UpdateCategoryList?catID=3&year=<YYYY>` returns 0
   items for 2018–2021. There is **no PC category on CivicPlus** — PC comes entirely
   from PMN.
2. **Utah Public Notice (PMN)** — the deep archive and the **only** source of PC
   packets. Enumerated from the **cumulative** notice list
   `https://www.utah.gov/pmn/list/notices.html?id=<body>&page=400` (one GET returns the
   body's entire history). Files fetched from **`www.utah.gov/pmn/files/<id>.pdf`**
   (the `pmn.utah.gov` host 302-redirects to HTML — do not use it).
   - **Body 5803** ("Magna Council") — used here for **pre-2022 council packets only**
     (2022+ council = CivicPlus). Each city/township meeting notice carries an
     **`Agenda`** + a bundled **`Supporting Documents`** PDF (or a
     `YYMMDD_Magna…_Packet.pdf`).
   - **Body 1559** ("Magna Planning Commission", MSD-staffed) — **all years**. Each
     notice carries a bundled **`YYMMDD_MagnaPC_Packet.pdf`** (older era
     `MagnaTPC`/`MagnaMetro…`) plus, on land-use items, standalone staff reports keyed
     to the `REZ/SUB/OAM<YYYY>-<NNNNNN>` case number.
   - **PMN attachment TYPE LABELS are unreliable** ("Public Information Handout" /
     "Other") — packet files are classified by **filename** (priority
     packet > supporting > staff report > agenda; minutes/audio/ordinance-only notices
     carry no packet and are skipped). One best packet file is kept per notice (highest
     file id in the top-priority class = the final/amended upload).

## Mode decision — STORED
Every live packet was **HEAD-sized** first (`size_packets_magna.py`,
`raw/_fetch_log.jsonl`): **297 live packets = 1.33 GB** (min 0.06 MB, median 0.37 MB,
p90 13.8 MB, **max 55.1 MB**; 17 > 20 MB, 1 > 50 MB, **0 > 100 MB**). That is **under
the ~1.5 GB disk budget** and not multi-GB, so — matching the metro-township siblings
**kearns** (584 MB) and **white_city** which also store packets — the PDFs are
**retained on disk** (`raw/<date>/<key>.<ext>`) with **text sidecars**
(`text/<stem>.txt`, `pdftotext -layout`; the one born-digital `.docx` via a
`word/document.xml` strip). This is the preferred default; INDEX-ONLY is the exception
reserved for sets that *exceed* the budget.

- CivicPlus packets are **thin** (142 items, 0.15 GB, median 0.26 MB) — Magna uploads
  agenda-outline PDFs, so `?packet=true` mostly equals the plain agenda.
- PMN packets are the **substance** (155 items, 1.18 GB, median 3.5 MB) — the bundled
  `_Packet.pdf` with staff reports + exhibits.

## Coverage (STORED — 297 packets, 1.2 GB on disk)
| Body | Packets | Window | Source split | Kinds |
|---|---|---|---|---|
| Council | 161 | 2019-08-27 → 2026-07-14 | CivicPlus 123 (2022–26) + PMN 38 (2019–21) | 147 full_packet + 14 agenda_packet |
| CRA | 19 | 2024-10-22 → 2026-06-09 | CivicPlus 19 (2024–26) | 19 full_packet |
| PC | 117 | 2019-01-10 → 2026-07-09 | PMN 117 (2019–26) | 93 full_packet + 24 agenda_packet |
| **Total** | **297** | 2019 → 2026 | CivicPlus 142 / PMN 155 | 259 full_packet + 38 agenda_packet |

Per-year counts — **Council:** 2019×5, 2020×17, 2021×16 (PMN); 2022×25, 2023×27,
2024×25, 2025×28, 2026×18 (CivicPlus). **CRA:** 2024×2, 2025×9, 2026×8. **PC:** 2019×20,
2020×29, 2021×17, 2022×15, 2023×13, 2024×9, 2025×9, 2026×5.

- `meeting_type` (parsed from title/filename): 275 regular, 11 work, 11 special.
- `format`: **295 text** (born-digital, `pdftotext -layout`; corpus screen clean — the
  weird-char outliers are bullet glyphs `•`, not garble) + **2 scanned** image-only
  (`text/`-less; vision/OCR to read): CivicPlus CRA `05132025-143` (2025-05-13) and
  council `07092024-38` (2024-07-09).
- Text sidecars: **295** (294 PDF + 1 docx; the 2 scanned yield none — logged
  `image_only` in `text/_extraction_log.csv`).

## Gaps — honest, verified (see `unrecovered.csv`)
1. **PC packets 2017-02 → 2018-12 are PMN-purged — 52 files, HTTP 404**
   (`unrecovered.csv`, `reason=pmn_purged_404`). The body-1559 notices still *list*
   a `..._Packet.pdf`/`_Agenda.pdf`, but the file blob returns 404 (a 315-byte error
   page) — the documented **2017–mid-2018 PMN blob purge** that also hit Magna's core
   minutes and its sibling townships. This is a source-side deletion, not a scraper
   miss; the ids are preserved in `unrecovered.csv` for a future re-check. (A few of
   these 2017 body-1559 entries are actually *council* packets — early PMN 1559 briefly
   mixed council + PC — but all are 404, so the distinction is moot.)
2. **Pre-2019 council packets are not distinctly published.** On PMN 5803 the 2017–2018
   council notices carry only meeting **audio (MP3)** + an **unlabeled combined PDF**
   (`MM-DD-YY.pdf` / `Scan_NNNN.pdf`) that cannot be reliably classified as a
   staff-analysis packet vs an agenda vs minutes. The distinctly-labeled
   `Supporting Documents` / `_Packet.pdf` convention begins **2019** (council) — so the
   council-via-PMN packet floor is **2019-08-27**, mirroring the core minutes gap
   (council record begins 2018-07-17). Unlabeled combined PDFs are **not** indexed here
   (would require guessing they are packets — a fabrication risk).
3. **CivicPlus floor 2022.** No Council/CRA packets exist on the AgendaCenter before
   2022 (`UpdateCategoryList` returns 0 items for 2018–2021) — a portal-retention
   boundary. Pre-2022 council is covered from PMN 5803.
4. **Pre-2017 PC (2008–2016) is out of entity scope.** PMN 1559 holds PC notices back to
   2008, but Magna incorporated 2017-01-01 (data floor 2017) and those predecessor
   Salt-Lake-County-township planning notices are not Magna-entity packets; they are not
   indexed (and the ≤2018 blobs are purged anyway — see gap 1).
5. **CRA appears only 2024+** — the CRA is an in-session council body that begins
   noticing its own agenda items on CivicPlus in 2024; no separate pre-2024 CRA packet
   exists.
6. **Minor duplicates (faithful to the portals, retained):** one CivicPlus re-post
   (2023-05-09 amended council agenda under two item ids `-49`/`-77`, identical bytes)
   and a PMN clerk mis-attachment (the same 2020 agenda bytes posted on two dates). Both
   are kept as honest rows; `sha256` in `raw/_fetch_log.jsonl` identifies them.

## Primary-document section layer (2026-07-16)

Magna is **Bucket-B SEPARABLE**: the PMN packets bundle one MSD "Summary and
Recommendation" **staff report** per land-use item, cut out of the existing full-packet
text sidecars into **204 additive `packet_kind=packet_section` rows** (+ one
`text/sections/*.txt` each) by `split_sections.py`. The 297 parent packets are untouched;
no new fetch (in-place slice of the parent `pdftotext -layout` sidecar). Details +
splitter/anchor design in `CLAUDE.md`. Coverage of the section layer:

| Body | Sections | Section-bearing packets | Note |
|---|---|---|---|
| PC | 186 | 78 | the substance — all land-use staff reports |
| Council | 18 | 17 | 2019–21 township-era PMN packets carrying the PC-forwarded staff report |
| CRA | 0 | 0 | **honest zero** — CRA files are thin CivicPlus agendas, no staff-report block |
| **Total** | **204** | **95** | ~51.7 M chars; spread 2019–2026 |

- Case-key classes of the 204: `FILE#`(pre-2020) 76, CUP 34, REZ 30, **(none) 26**,
  SUB 21, OAM 16, RWD 1. The 26 `(none)` are text-amendment / no-printed-case items —
  still cut, seq-named (`case_key` blank).
- `doc_class=staff_report` for all 204; `sha256` blank by design (§9: a text slice has no
  binary hash — provenance is on the parent row); `extraction_method=section_split`.
- **Honest non-yield:** 200 of 295 sidecar files produce 0 sections — the 19 CRA + 123
  CivicPlus council thin agendas + PMN agenda-only packets carry no MSD staff report.
- **Excluded (no text):** the 2 scanned image-only packets (`05132025-143` CRA
  2025-05-13, `07092024-38` Council 2024-07-09) — no sidecar, skipped.
- **Two OAM sections dominated by an embedded plan document** — `OAM2022-000776`
  (2023-04-13) and `OAM2024-001175` (2024-06-13, the Magna Historic District Area Plan /
  a GP element). Kept as `staff_report`; the standalone plan docs are **class-3
  (`general_plan`) candidates for a future `housing_plans/` pass** (not duplicated here).
- **Verification:** all-204 invariant sweep (text==parent slice, exactly-one-anchor) 204/204;
  random n=50 = 100%; 6 boundary-sample packets + 2 OAM giants verified end-to-end;
  `validate_dataset.py` PASS. Acceptance: `text/sections/908569__03_CUP2022-000691.txt`
  (home-day-care CUP, Christina Robles) joins the contested PC vote 2022-11-10 #4
  (`Pass (dissent: Cripps)`).

## To read a packet
Open the stored PDF at `path` (e.g. `raw/2026-07-09/1456253.pdf`) or its
`text/<stem>.txt` sidecar; the 2 `scanned` council packets need vision/OCR. To refresh,
re-run the build (below) — it is idempotent and re-fetches only new dates.
