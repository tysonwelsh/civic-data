# Salt Lake County — Plans module: SOURCES & provenance

Governing planning documents for **unincorporated Salt Lake County** and its
**metro townships**, as a searchable text corpus for growth/housing/development
research. Built 2026-07-11.

## Where these come from

Two publishers hold the authoritative unincorporated-county planning documents:

1. **Salt Lake County — Office of Regional Development, Planning & Transportation**
   (`saltlakecounty.gov`, legacy host `slco.org`). Publishes the county-level
   general plans (West General Plan, Wasatch Canyons General Plan), the general-plan
   elements (Moderate-Income Housing element, Water Use & Preservation element),
   the Resource Management Plan, and the HUD Consolidated Plan.
   - Landing: https://www.saltlakecounty.gov/regional-development/planning-transportation/plans-projects/
   - Housing plans/reports: https://www.saltlakecounty.gov/regional-development/housing-community-development/plans--reports/
   - NOTE on URLs: `slco.org/globalassets/...` links **301-redirect** to
     `www.saltlakecounty.gov/globalassets/...`, but the paths surfaced by the site
     search were stale and 404'd. The working `globalassets` paths recorded in
     `index.csv` were resolved from the live plan pages and verified (HTTP 200,
     `content-type: application/pdf`).

2. **Greater Salt Lake Municipal Services District (MSD)** (`msd.utah.gov`, CivicPlus;
   canonical host also appears as `ut-greatersaltlakemsd.civicplus.com`). MSD provides
   planning services to the metro townships and publishes each township's adopted
   general plan and MIH plan via its DocumentCenter.
   - General Plans index: https://msd.utah.gov/371/General-Plans
   - Planning & Development: https://msd.utah.gov/203/Planning-Development
   - Moderate-Income Housing Efforts: https://msd.utah.gov/407/Moderate-Income-Housing-Efforts
   - `msd.utah.gov/DocumentCenter/View/<id>` URLs verified downloading real PDFs.

## Retrieval method

- Documents discovered via WebSearch + WebFetch of the two publishers' plan pages.
- PDFs fetched with `curl` (retries on failure). Text extracted with `pypdf`
  (`PdfReader`, per-page `extract_text()`) into `text/<stem>.txt`.
- All 14 documents produced substantial born-digital text (no scan/OCR floor hit —
  spot-checked titles/adoption lines against the PDFs; all clean).

## Size policy (per module instructions: link, don't download, if >~50MB)

Raw PDFs **retained in `raw/`** (<=50MB): Emigration Canyon GP, both unincorporated
MIH docs, White City MIH, Resource Management Plan, Consolidated Plan.

Raw PDFs **link-only** (>50MB — `path` blank in index, `source_url` is the live PDF,
**text still extracted** to `text/`): West General Plan (112MB), Wasatch Canyons GP
(177MB), Water element (96MB), Magna GP (94MB), Kearns GP (98MB), White City GP (53MB),
Copperton GP (57MB), Brighton GP (73MB).

## Inventory (14 documents, all with extracted text)

| doc_type | title | jurisdiction | raw? |
|---|---|---|---|
| general_plan | West General Plan (2022) | Unincorp. west county | link |
| general_plan | Wasatch Canyons General Plan (2020) | Unincorp. canyons | link |
| general_plan_element | Water Use & Preservation Element (2026) | Unincorp. county | link |
| township_general_plan | Magna GP (2021) | Magna | link |
| township_general_plan | Kearns GP (2020) | Kearns | link |
| township_general_plan | White City GP (2022) | White City | link |
| township_general_plan | Emigration Canyon GP (2022) | Emigration Canyon | raw |
| township_general_plan | Copperton GP (2020) | Copperton | link |
| township_general_plan | Brighton GP (2022) | Brighton | link |
| moderate_income_housing | Unincorporated MIH Plan (2022) | Unincorp. county | raw |
| moderate_income_housing | Unincorporated MIH Element (2019) | Unincorp. county | raw |
| moderate_income_housing | White City MIH Plan (2022) | White City | raw |
| resource_management_plan | Resource Management Plan (2017) | Countywide | raw |
| consolidated_plan | Consolidated Plan 2025-2029 (HUD) | County entitlement area | raw |

## Honest gaps / not-retrieved

- **Kearns and Magna have no *separate* published MIH plan document.** Their MIH
  components were folded into the general plan via 2022 amendments (noted on the MSD
  pages and in the GP text), so there is no standalone PDF to capture. Not a fabricated
  zero — the strategy content lives inside `kearns_general_plan_2020.txt` /
  `magna_general_plan_2021.txt`.
- **Copperton, Emigration Canyon, Brighton MIH:** no standalone MIH plan PDF located
  on the MSD DocumentCenter as of this build. These are very small jurisdictions; MIH
  obligations may be addressed inside the general plan or handled county-wide.
  Recorded as a gap, not fabricated.
- **Wasatch Canyons GP and the Water element** are captured as text but the raw PDFs
  (177MB / 96MB) are link-only; if a pixel-faithful copy is later needed, re-fetch from
  `source_url`.
- **Small-area / community master plans:** the county publishes area studies (e.g.
  Oquirrh View Plan, West Traverse Mountain Military Compatibility study) referenced on
  the plans-projects page. Only growth/housing *general* plans and MIH plans were in
  scope here; the compatibility study and the Oquirrh View / other neighborhood studies
  were **not** downloaded this pass — logged as follow-up, not claimed as retrieved.
- **Legacy pre-incorporation community general plans** (the old unincorporated
  "township" community plans that predate 2017 metro-township incorporation) were not
  separately located; the current adopted general plans above supersede them.

## Verify a link

    curl -sSI -A Mozilla/5.0 -L "<source_url>" | grep -i "http/\|content-type"

Expect `200` and `application/pdf`.
