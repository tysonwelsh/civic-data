# Source & citation index — repo summary

> **⚠ SNAPSHOT of 2026-07-06 — predates the county/MPO/state tiers (16-city era).**
> Regenerate with `python3 scripts/build_sources_index.py --summary`. Per-record
> provenance truth lives in each dataset's `sources.csv` / `index.csv`, not here.

Generated 2026-07-06 by `scripts/build_sources_index.py --summary` from the per-city `sources.csv` files. Per-city detail: `<city>_city_council/SOURCES.md`.

## Provenance model

Every document in this collection is indexed in its city's `sources.csv` with the original government-source URL where one was recorded at retrieval time. That URL index is the **recovery path**: if retained originals under the datasets' `raw/` directories ever have to be deleted for disk space, every document with a recorded URL can be re-fetched from its publisher, and every document without one carries the name of the issuing office (`unrecorded (…)`) so it can be re-obtained by request. Raw originals are retained where present (comments, elections, the Lehi expansion datasets; minutes PDFs are being backfilled under Phase 3.2). The processing chain from source document to dataset is documented per city in the dataset-level `CLAUDE.md` files referenced by each row's `processing_ref`. No URL is ever reconstructed or guessed; `verified_date` marks rows whose URL was re-checked live on that date (a stratified sample, not an exhaustive sweep).

## Coverage (documents indexed / % with a recorded direct URL)

| city | dataset | documents | % with URL | source host(s) |
|---|---|---:|---:|---|
| slc | meeting_minutes | 457 | 85% | slc.primegov.com |
| slc | planning_commission | 145 | 100% | webdme.slcgov.com, www.slc.gov, www.slcdocs.com |
| slc | public_comments | 217 | 100% | www.slcdocs.com |
| slc | election_results | 18 | 0% | — (issuing office named per row) |
| slc | packets | 582 | 100% | slc.primegov.com, www.slc.gov, www.slcdocs.com |
| slc | housing_plans | 11 | 100% | jobs.utah.gov, www.slc.gov, www.slcdocs.com |
| slc | ordinances | 443 | 100% | slc.primegov.com |
| slc | pmn_backfill | 7 | 100% | www.utah.gov |
| slc | transcripts | 10 | 100% | www.youtube.com |
| lehi | meeting_minutes | 175 | 100% | lehi.granicus.com |
| lehi | planning_commission | 160 | 100% | lehi.granicus.com |
| lehi | public_comments | 4 | 100% | lehi.granicus.com |
| lehi | election_results | 22 | 0% | — (issuing office named per row) |
| lehi | packets | 564 | 100% | legistarweb-production.s3.amazonaws.com, lehi.granicus.com |
| lehi | housing_plans | 9 | 100% | jobs.utah.gov, www.lehi-ut.gov |
| lehi | ordinances | 313 | 100% | lehi.granicus.com, www.lehi-ut.gov |
| lehi | pmn_backfill | 6 | 100% | www.utah.gov |
| lehi | transcripts | 12 | 100% | lehi.openutah.org |
| lehi | campaign_finance | 134 | 100% | www.lehi-ut.gov |
| logan | meeting_minutes | 198 | 100% | cms9files.revize.com |
| logan | planning_commission | 130 | 100% | www.loganutah.gov |
| logan | election_results | 17 | 0% | — (issuing office named per row) |
| logan | packets | 1124 | 100% | cms9files.revize.com, www.loganutah.gov |
| logan | housing_plans | 7 | 100% | cms9files.revize.com, jobs.utah.gov |
| logan | ordinances | 496 | 100% | cms9files.revize.com, www.loganutah.gov |
| logan | pmn_backfill | 3 | 100% | www.utah.gov |
| logan | transcripts | 153 | 100% | www.youtube.com |
| logan | campaign_finance | 45 | 100% | www.loganutah.gov, www.loganutah.org |
| nephi | meeting_minutes | 243 | 100% | www.nephi.utah.gov, www.utah.gov |
| nephi | planning_commission | 70 | 100% | www.nephi.utah.gov |
| nephi | election_results | 11 | 27% | juabcounty.gov, midutahradio.com, www.deseret.com |
| nephi | packets | 328 | 100% | www.nephi.utah.gov |
| nephi | housing_plans | 6 | 100% | jobs.utah.gov, www.nephi.utah.gov |
| nephi | ordinances | 103 | 100% | www.nephi.utah.gov, www.utah.gov |
| nephi | pmn_backfill | 9 | 100% | www.utah.gov |
| nephi | transcripts | 5 | 100% | www.youtube.com |
| nephi | campaign_finance | 43 | 100% | www.nephi.utah.gov |
| ogden | meeting_minutes | 504 | 100% | www.ogdencity.gov |
| ogden | planning_commission | 72 | 100% | brand.ogdencity.com, www.ogdencity.gov |
| ogden | election_results | 27 | 0% | — (issuing office named per row) |
| ogden | packets | 166 | 100% | www.ogdencity.gov |
| ogden | housing_plans | 6 | 100% | jobs.utah.gov, www.ogdencity.gov |
| ogden | ordinances | 308 | 100% | www.ogdencity.gov, www.utah.gov |
| ogden | pmn_backfill | 10 | 100% | www.utah.gov |
| ogden | transcripts | 11 | 100% | www.youtube.com |
| ogden | campaign_finance | 38 | 100% | www.ogdencity.com |
| orem | meeting_minutes | 130 | 100% | drive.google.com, oremut.api.civicclerk.com |
| orem | planning_commission | 114 | 100% | drive.google.com, oremut.api.civicclerk.com |
| orem | public_comments | 9 | 100% | drive.google.com |
| orem | election_results | 9 | 67% | vote.utahcounty.gov |
| orem | packets | 425 | 100% | oremut.api.civicclerk.com |
| orem | housing_plans | 14 | 100% | jobs.utah.gov, orem.gov |
| orem | ordinances | 95 | 100% | drive.google.com, orem.gov, oremut.api.civicclerk.com |
| orem | pmn_backfill | 39 | 100% | www.utah.gov |
| orem | transcripts | 108 | 100% | www.youtube.com |
| orem | campaign_finance | 91 | 100% | orem.gov |
| park_city | meeting_minutes | 238 | 100% | parkcityut.api.civicclerk.com |
| park_city | planning_commission | 160 | 100% | parkcityut.api.civicclerk.com |
| park_city | public_comments | 97 | 100% | parkcityut.api.civicclerk.com |
| park_city | election_results | 8 | 12% | www.parkcity.gov |
| park_city | packets | 942 | 100% | parkcityut.api.civicclerk.com |
| park_city | housing_plans | 15 | 100% | jobs.utah.gov, www.parkcity.gov |
| park_city | ordinances | 260 | 100% | parkcityut.api.civicclerk.com, s3-us-west-2.amazonaws.com |
| park_city | pmn_backfill | 16 | 100% | www.utah.gov |
| park_city | transcripts | 194 | 100% | parkcityut.portal.civicclerk.com |
| park_city | campaign_finance | 136 | 100% | www.parkcity.gov |
| provo | meeting_minutes | 311 | 100% | agendas.provo.gov |
| provo | planning_commission | 26 | 100% | www.provo.gov |
| provo | public_comments | 15 | 100% | agendas.provo.gov |
| provo | election_results | 14 | 0% | — (issuing office named per row) |
| provo | packets | 391 | 100% | agendas.provo.gov, www.provo.gov |
| provo | housing_plans | 6 | 100% | jobs.utah.gov, www.provo.gov |
| provo | ordinances | 213 | 100% | agendas.provo.gov, www.utah.gov |
| provo | pmn_backfill | 390 | 100% | www.utah.gov |
| provo | transcripts | 10 | 100% | www.youtube.com |
| provo | campaign_finance | 41 | 100% | www.provo.gov |
| sandy | meeting_minutes | 274 | 100% | sandyutah.legistar.com |
| sandy | planning_commission | 1 | 0% | — (issuing office named per row) |
| sandy | election_results | 6 | 0% | — (issuing office named per row) |
| sandy | packets | 6908 | 100% | content.civicplus.com, docs.google.com, extension.usu.edu, luau.utah.gov, privacy.utah.gov, sandy.utah.gov, sandyutah.granicusideas.com, sandyutah.legistar1.com, soundcloud.com, tinyurl.com, training.auditor.utah.gov, www.mwdsls.org, www.sandy.utah.gov, www.slc.gov, www.youtube.com, youtu.be |
| sandy | housing_plans | 8 | 100% | content.civicplus.com, jobs.utah.gov, www.sandy.utah.gov |
| sandy | ordinances | 170 | 100% | sandyutah.legistar.com, sandyutah.legistar1.com |
| sandy | pmn_backfill | 8 | 100% | www.utah.gov |
| sandy | transcripts | 88 | 100% | sandy.openutah.org, www.youtube.com |
| sandy | campaign_finance | 83 | 100% | sandycityut.easyvotecampaignfinance.com |
| st_george | meeting_minutes | 305 | 100% | sgcityutah.gov, www.utah.gov |
| st_george | planning_commission | 132 | 100% | sgcityutah.gov, www.utah.gov |
| st_george | public_comments | 53 | 100% | sgcityutah.gov |
| st_george | election_results | 13 | 0% | — (issuing office named per row) |
| st_george | packets | 224 | 100% | sgcityutah.gov |
| st_george | housing_plans | 7 | 100% | jobs.utah.gov, sgcityutah.gov |
| st_george | ordinances | 252 | 100% | sgcityutah.gov, www.utah.gov |
| st_george | pmn_backfill | 20 | 100% | www.utah.gov |
| st_george | transcripts | 47 | 100% | www.youtube.com |
| st_george | campaign_finance | 104 | 100% | sgcityutah.gov, web.archive.org |
| vineyard | meeting_minutes | 172 | 100% | vineyardut.api.civicclerk.com, www.utah.gov |
| vineyard | planning_commission | 102 | 100% | vineyardut.api.civicclerk.com, www.utah.gov |
| vineyard | election_results | 12 | 0% | — (issuing office named per row) |
| vineyard | packets | 926 | 100% | vineyardut.api.civicclerk.com |
| vineyard | housing_plans | 7 | 100% | jobs.utah.gov, s3-us-west-2.amazonaws.com, www.vineyardutah.gov |
| vineyard | ordinances | 84 | 99% | vineyardut.api.civicclerk.com, www.utah.gov |
| vineyard | pmn_backfill | 296 | 100% | www.utah.gov |
| vineyard | transcripts | 34 | 100% | www.youtube.com |
| vineyard | campaign_finance | 59 | 100% | web.archive.org, www.vineyardutah.gov |
| west_jordan | meeting_minutes | 321 | 100% | westjordan.primegov.com |
| west_jordan | planning_commission | 84 | 100% | westjordan.primegov.com |
| west_jordan | public_comments | 2 | 100% | westjordan.primegov.com |
| west_jordan | election_results | 4 | 0% | — (issuing office named per row) |
| west_jordan | packets | 222 | 100% | westjordan.primegov.com |
| west_jordan | housing_plans | 11 | 100% | assets.westjordan.utah.gov, jobs.utah.gov, www.westjordan.utah.gov |
| west_jordan | ordinances | 285 | 100% | assets.westjordan.utah.gov, westjordan.primegov.com, www.westjordan.utah.gov |
| west_jordan | pmn_backfill | 33 | 100% | www.utah.gov |
| west_jordan | transcripts | 10 | 100% | www.youtube.com |
| west_jordan | campaign_finance | 135 | 100% | ecf-api.easyvoteapp.com, www.westjordan.utah.gov |
| west_valley | meeting_minutes | 550 | 100% | ob.wvc-ut.gov |
| west_valley | planning_commission | 263 | 100% | ob.wvc-ut.gov |
| west_valley | election_results | 4 | 0% | — (issuing office named per row) |
| west_valley | packets | 965 | 100% | ob.wvc-ut.gov |
| west_valley | housing_plans | 7 | 100% | jobs.utah.gov, www.wvc-ut.gov |
| west_valley | ordinances | 324 | 100% | ob.wvc-ut.gov, www.wvc-ut.gov |
| west_valley | pmn_backfill | 11 | 100% | www.utah.gov |
| west_valley | transcripts | 461 | 100% | www.youtube.com |
| west_valley | campaign_finance | 105 | 100% | www.wvc-ut.gov |
| south_jordan | meeting_minutes | 243 | 100% | www.sjc.utah.gov, www.utah.gov |
| south_jordan | planning_commission | 125 | 100% | www.sjc.utah.gov, www.utah.gov |
| south_jordan | election_results | 17 | 0% | — (issuing office named per row) |
| south_jordan | packets | 169 | 100% | mccmeetings.blob.core.usgovcloudapi.net |
| south_jordan | housing_plans | 6 | 100% | jobs.utah.gov, www.sjc.utah.gov |
| south_jordan | ordinances | 129 | 100% | s3-us-west-2.amazonaws.com, www.sjc.utah.gov, www.utah.gov |
| south_jordan | pmn_backfill | 13 | 100% | www.utah.gov |
| south_jordan | transcripts | 125 | 100% | www.youtube.com |
| south_jordan | campaign_finance | 46 | 100% | www.sjc.utah.gov |
| millcreek | meeting_minutes | 372 | 100% | www.millcreekut.gov |
| millcreek | planning_commission | 149 | 100% | www.millcreekut.gov |
| millcreek | election_results | 3 | 0% | — (issuing office named per row) |
| millcreek | packets | 552 | 100% | www.millcreekut.gov |
| millcreek | housing_plans | 7 | 100% | jobs.utah.gov, www.millcreekut.gov, www.utah.gov |
| millcreek | ordinances | 550 | 100% | s3.us-west-2.amazonaws.com |
| millcreek | pmn_backfill | 1 | 100% | www.utah.gov |
| millcreek | transcripts | 92 | 100% | www.youtube.com |
| millcreek | campaign_finance | 41 | 100% | web.archive.org, www.millcreekut.gov |
| taylorsville | meeting_minutes | 150 | 100% | www.taylorsvilleut.gov |
| taylorsville | planning_commission | 91 | 100% | www.taylorsvilleut.gov |
| taylorsville | election_results | 3 | 0% | — (issuing office named per row) |
| taylorsville | packets | 7 | 100% | www.taylorsvilleut.gov |
| taylorsville | housing_plans | 14 | 100% | jobs.utah.gov, www.taylorsvilleut.gov |
| taylorsville | ordinances | 90 | 100% | www.taylorsvilleut.gov, www.utah.gov |
| taylorsville | pmn_backfill | 2 | 100% | www.utah.gov |
| taylorsville | transcripts | 1 | 100% | www.youtube.com |
| taylorsville | campaign_finance | 71 | 100% | www.taylorsvilleut.gov |

<!-- liveness:begin -->
## URL liveness (sampled 2026-07-02)

A stratified sample of 5 recorded URLs per city (65 total, spread across datasets)
was probed with polite HEAD/ranged-GET requests
(`python3 scripts/build_sources_index.py --verify-sample 5`). Sampled rows that
answered carry `verified_date=2026-07-02` in their city's `sources.csv`.

**Result: 64/65 live. No dead or rotted host was found.**

| host | live | note |
|---|---|---|
| agendas.provo.gov | 3/3 | |
| cms9files.revize.com | 3/3 | |
| drive.google.com | 3/3 | |
| jobs.utah.gov | 1/1 | |
| juabcounty.gov | 1/1 | |
| legistarweb-production.s3.amazonaws.com | 1/1 | |
| lehi.granicus.com | 2/2 | |
| midutahradio.com | 1/1 | |
| ob.wvc-ut.gov | 5/5 | |
| parkcityut.api.civicclerk.com | 4/4 | |
| sandyutah.legistar.com | 5/5 | |
| sgcityutah.gov | 5/5 | |
| slc.primegov.com | 2/2 | |
| vineyardut.api.civicclerk.com | 4/5 | the 1 failure is a recorded-URL defect, not rot — see below |
| vote.utahcounty.gov | 2/2 | |
| webdme.slcgov.com | 2/2 | |
| westjordan.primegov.com | 5/5 | |
| www.lehi-ut.gov | 1/1 | |
| www.loganutah.gov | 2/2 | |
| www.nephi.utah.gov | 3/3 | |
| www.ogdencity.gov | 5/5 | 404s non-browser user agents; the probe retries with a browser UA |
| www.parkcity.gov | 1/1 | |
| www.provo.gov | 2/2 | |
| www.slcdocs.com | 1/1 | |

**Flagged — Vineyard recorded-URL defect (not portal rot):** 26 rows of
`vineyard_city_council/*/minutes_index.csv` recorded the CivicClerk stream URL
without the required `plainText` parameter
(`…/GetMeetingFileStream(fileId=N)` → HTTP 404 as written). The documents are
still on the portal — the working form is
`…/GetMeetingFileStream(fileId=N,plainText=true)` — but the URLs need correcting
in the city's index before they can serve as a recovery path.

## Biggest provenance gaps

- **Election results are mostly prose-provenance** (0% direct URLs in 10 of 13
  cities, 186 documents total): raw county/state files were mirrored verbatim but
  download URLs were rarely recorded — rows name the issuing office instead
  (e.g. `unrecorded (Salt Lake County Clerk election-results archive, …)`).
  Exceptions: orem (6/9 URLs in its CLAUDE.md), nephi (3 archived-canvass URLs),
  park_city (results page URL).
- **SLC's 68 Laserfiche council minutes (2020)** have no per-file URLs
  (session-based portal); they are the only minutes documents in the collection
  without a recorded URL (85% URL coverage for SLC meeting_minutes).
- **Sandy Planning Commission** votes come from the Legistar web API, not minutes
  files — one staging-export row, no per-document URLs.
- **Lehi transcripts** (12 rows) have source URLs but no local documents —
  captions were never retrievable (documented in transcripts/CLAUDE.md).
- Honest-empty comment corpora (logan, nephi, ogden, sandy, vineyard,
  west_valley) correctly have **no** sources rows — there are no documents.
<!-- liveness:end -->
