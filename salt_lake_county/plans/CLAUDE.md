# salt_lake_county/plans — how to use this module

The **governing planning documents** for unincorporated Salt Lake County and its
metro townships, as a **searchable plain-text corpus** for growth / housing /
development questions. This module is self-contained: raw PDFs (or their live links),
extracted text, and a manifest. Nothing here feeds gov.db/cities.db — it is a document
layer.

## Layout

- `raw/<stem>.pdf` — source PDF, when <=50MB. Larger plans are **link-only** (not
  stored); fetch from `source_url` in `index.csv` if you need the PDF itself.
- `text/<stem>.txt` — pypdf-extracted plain text of **every** document (14/14),
  including the link-only ones. **This is the searchable layer — read/grep these.**
- `index.csv` — the manifest. Columns:
  `doc_type,title,adopted_date,jurisdiction,path,text_path,format,source_url,notes`.
  `path` is blank for link-only docs; `text_path` is always present.
- `SOURCES.md` — provenance, publishers, size policy, and honest gaps.

## Which document for which question

- **Countywide growth vision (west side):** `west_general_plan_2022` — the statutory
  general plan; land use / housing / transportation elements + county-added elements.
- **Canyon land use / development limits:** `wasatch_canyons_general_plan`.
- **A specific township's land use / zoning vision:** the matching
  `*_general_plan_*` (Magna, Kearns, White City, Emigration Canyon, Copperton, Brighton).
- **Moderate-income / affordable housing obligations & strategies:**
  `mih_plan_unincorporated_2022` (current), `mih_element_unincorporated_2019`
  (predecessor), `white_city_mih_plan_2022`. Kearns & Magna MIH content lives **inside**
  their general-plan text (2022 amendments) — grep those, there is no standalone PDF.
- **Federal housing/CD funding strategy:** `consolidated_plan_2025_2029` (HUD CDBG/HOME/ESG).
- **Natural-resource/land planning:** `slco_resource_management_plan_2017`.
- **Water & growth:** `water_use_preservation_element`.

## doc_type vocabulary

`general_plan`, `township_general_plan`, `general_plan_element`,
`moderate_income_housing`, `resource_management_plan`, `consolidated_plan`.
(Open set — extend if new types are added.)

## Cardinal rules (inherited from repo root)

- **Never fabricate.** Missing standalone plans (e.g. Kearns/Magna separate MIH PDF,
  small-area plans) are recorded as **honest gaps** in `SOURCES.md`, not invented rows.
  `index.csv` lists **only documents actually retrieved or verified to exist** with a
  live `source_url`.
- **Text is derived, PDFs/URLs are canonical.** To regenerate a `text/` file, re-run
  pypdf on the PDF (re-fetch link-only ones from `source_url`):

      python3 -c "from pypdf import PdfReader; \
      open('text/<stem>.txt','w').write('\n'.join((p.extract_text() or '') \
      for p in PdfReader('raw/<stem>.pdf').pages))"

- Two publishers: **saltlakecounty.gov** (Office of Regional Development) for
  county-level plans; **msd.utah.gov** (Greater Salt Lake MSD, CivicPlus) for
  township plans. `slco.org` 301-redirects to `saltlakecounty.gov`. See SOURCES.md.

## Scope note

Growth/housing-relevant general plans + MIH plans were the target and are complete for
every currently-adopted unincorporated jurisdiction. Small-area/community studies
(Oquirrh View Plan, West Traverse Mtn military-compatibility study, etc.) are a logged
follow-up, not yet ingested — see SOURCES.md "Honest gaps".
