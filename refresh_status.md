# Refresh status — 31-city portal probe dashboard

> **⚠ SNAPSHOT of the 2026-07-19 Q3 refresh** — regenerated at each quarterly refresh
> (next: early Oct 2026); do not read as current portal state.

Generated 2026-07-19 by `scripts/refresh_status.py`. Probe data comes from each
city's `fetch_new.py --probe` run (stored in `<city>_city_council/refresh_probe.json`);
index max dates are measured live from the dataset files.

| City | Dataset | Portal | Index max date | Rows | Probed | Probe result | New on portal | Fetch command |
|---|---|---|---|---|---|---|---|---|
| lehi | meeting_minutes | granicus | 2026-01-27 | 175 | 2026-07-18 | ok | 0 | `cd lehi_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| lehi | planning_commission | granicus | 2026-06-11 | 161 | 2026-07-19 | ok | 1 | `cd lehi_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| logan | meeting_minutes | revize | 2026-06-02 | 198 | 2026-07-19 | ok | 0 | `cd logan_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| logan | planning_commission | revize | 2026-07-09 | 131 | 2026-07-19 | ok | 1 | `cd logan_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| nephi | meeting_minutes | civicplus-agendacenter | 2026-06-16 | 252 | 2026-07-19 | ok | 1 | `cd nephi_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| nephi | planning_commission | civicplus-agendacenter | 2026-05-13 | 72 | 2026-07-19 | ok | 2 | `cd nephi_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| ogden | meeting_minutes | civicplus-documentcenter | 2026-06-30 | 505 | 2026-07-19 | ok | 1 | `cd ogden_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| ogden | planning_commission | civicplus-agendacenter | 2026-06-17 | 75 | 2026-07-19 | ok | 2 | `cd ogden_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| orem | meeting_minutes | gdrive+civicclerk | 2026-06-23 | 135 | 2026-07-19 | ok | 5 | `cd orem_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| orem | planning_commission | gdrive+civicclerk | 2026-05-06 | 114 | 2026-07-18 | ok | 0 | `cd orem_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| park_city | meeting_minutes | civicclerk | 2026-07-09 | 242 | 2026-07-19 | ok | 4 | `cd park_city_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| park_city | planning_commission | civicclerk | 2026-06-24 | 162 | 2026-07-19 | ok | 2 | `cd park_city_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| provo | meeting_minutes | onbase | 2026-05-26 | 312 | 2026-07-18 | ok | 0 | `cd provo_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| provo | planning_commission | civicplus-agendacenter | 2026-07-08 | 28 | 2026-07-19 | ok | 2 | `cd provo_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| sandy | meeting_minutes | legistar | 2026-06-23 | 277 | 2026-07-19 | ok | 5 | `cd sandy_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| sandy | planning_commission | legistar-api | 2026-06-18 * | 115 | 2026-07-18 | ok | 2 | `cd sandy_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| slc | meeting_minutes | primegov | 2026-06-16 | 477 | 2026-07-18 | ok | 2 | `cd slc_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| slc | planning_commission | primegov+slcdocs | 2026-06-24 | 146 | 2026-07-19 | ok | 1 | `cd slc_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| slc | public_comments | slcdocs | 2026-04-07 | 221 | 2026-07-18 | ok | 0 | `cd slc_city_council && python3 fetch_new.py --fetch --dataset public_comments` |
| st_george | meeting_minutes | revize | 2026-07-02 | 308 | 2026-07-19 | ok | 4 | `cd st_george_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| st_george | planning_commission | revize | 2026-06-23 | 133 | 2026-07-19 | ok | 1 | `cd st_george_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| vineyard | meeting_minutes | civicclerk | 2026-06-09 | 172 | 2026-07-18 | ok | 0 | `cd vineyard_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| vineyard | planning_commission | civicclerk | 2026-05-06 | 102 | 2026-07-18 | ok | 0 | `cd vineyard_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| west_jordan | meeting_minutes | primegov | 2026-06-23 | 323 | 2026-07-19 | ok | 2 | `cd west_jordan_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| west_jordan | planning_commission | primegov | 2026-06-16 | 86 | 2026-07-19 | ok | 2 | `cd west_jordan_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| west_valley | meeting_minutes | onbase | 2026-06-23 | 555 | 2026-07-19 | ok | 4 | `cd west_valley_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| west_valley | planning_commission | onbase | 2026-05-27 | 266 | 2026-07-19 | ok | 3 | `cd west_valley_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| south_jordan | meeting_minutes | civicplus | 2026-05-19 | 243 | 2026-07-18 | ok | 0 | `cd south_jordan_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| south_jordan | planning_commission | civicplus | 2026-05-26 | 127 | 2026-07-19 | ok | 1 | `cd south_jordan_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| millcreek | meeting_minutes | civicplus-agendacenter | 2026-06-22 | 373 | 2026-07-19 | ok | 1 | `cd millcreek_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| millcreek | planning_commission | civicplus-agendacenter | 2026-06-17 | 150 | 2026-07-19 | ok | 1 | `cd millcreek_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| taylorsville | meeting_minutes | civicengage-central | 2026-06-03 | 150 | 2026-07-18 | ok | 0 | `cd taylorsville_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| taylorsville | planning_commission | civicengage-central | 2026-04-28 | 91 | 2026-07-18 | ok | 0 | `cd taylorsville_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| murray | meeting_minutes | civicplus-archive | 2026-06-16 | 170 | 2026-07-19 | ok | 0 | `cd murray_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| murray | planning_commission | civicplus-archive | 2026-05-07 | 120 | 2026-07-19 | ok | 0 | `cd murray_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| herriman | meeting_minutes | primegov | 2026-05-27 | 180 | 2026-07-19 | ok | 0 | `cd herriman_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| herriman | planning_commission | primegov | 2026-06-03 | 131 | 2026-07-19 | ok | 0 | `cd herriman_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| draper | meeting_minutes | granicus | 2026-06-09 | 155 | 2026-07-18 | ok | 0 | `cd draper_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| draper | planning_commission | granicus | 2026-05-28 | 143 | 2026-07-18 | ok | 0 | `cd draper_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| riverton | meeting_minutes | pmn | 2026-06-02 | 128 | 2026-07-19 | ok | 0 | `cd riverton_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| riverton | planning_commission | pmn | 2026-06-11 | 119 | 2026-07-19 | ok | 0 | `cd riverton_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| alta | meeting_minutes | pmn | 2026-06-17 | 85 | 2026-07-19 | ok | 0 | `cd alta_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| alta | planning_commission | pmn | 2025-12-17 | 17 | 2026-07-19 | ok | 0 | `cd alta_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| midvale | meeting_minutes | revize | 2026-06-16 | 151 | 2026-07-18 | ok | 0 | `cd midvale_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| midvale | planning_commission | revize | 2026-06-24 | 104 | 2026-07-18 | ok | 0 | `cd midvale_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| cottonwood_heights | meeting_minutes | civicplus+pmn | 2026-06-16 | 185 | 2026-07-19 | ok | 0 | `cd cottonwood_heights_city_council && python3 fetch_new.py --ingest --dataset meeting_minutes` |
| cottonwood_heights | planning_commission | civicplus+pmn | 2026-02-04 | 103 | 2026-07-19 | ok | 0 | `cd cottonwood_heights_city_council && python3 fetch_new.py --ingest --dataset planning_commission` |
| holladay | meeting_minutes | pmn/body-388 | 2026-04-16 | 152 | 2026-07-19 | ok | 3 | `cd holladay_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| holladay | planning_commission | pmn/body-389 | 2026-04-28 | 71 | 2026-07-19 | ok | 4 | `cd holladay_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| south_salt_lake | meeting_minutes | ? | 2026-07-08 | 139 | (json, undated) | ok | 2 | `cd south_salt_lake_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| south_salt_lake | planning_commission | ? | 2026-06-18 | 61 | (json, undated) | ok | 2 | `cd south_salt_lake_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| bluffdale | meeting_minutes | civicplus-agendacenter | 2026-06-24 | 166 | 2026-07-18 | ok | 0 | `cd bluffdale_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| bluffdale | planning_commission | civicplus-agendacenter | 2026-06-03 | 91 | 2026-07-18 | ok | 1 | `cd bluffdale_city_council && python3 fetch_new.py --fetch --dataset planning_commission` |
| white_city | meeting_minutes | streamline | 2026-06-11 | 124 | 2026-07-19 | ok | 0 | `cd white_city_city_council && python3 fetch_new.py --fetch --dataset meeting_minutes` |
| white_city | planning_commission | pmn-5879-crosscheck | 2025-05-20 | 22 | 2026-07-19 | ok | 0 | `cd white_city_city_council && PC minutes are PMN-recovered (body 5879) — a separate reviewed step` |
| kearns | meeting_minutes | pmn | 2026-05-29 | 119 | 2026-07-19 | ok | 0 | `cd kearns_city_council && acquisition is a separate reviewed step (see recon.md)` |
| kearns | planning_commission | pmn | 2026-06-01 | 44 | 2026-07-19 | ok | 0 | `cd kearns_city_council && acquisition is a separate reviewed step (see recon.md)` |
| magna | meeting_minutes | civicplus+pmn | 2026-05-26 | 173 | 2026-07-19 | ok | 0 | `cd magna_city_council && download new dates' minutes to raw/ then extract (see docstring)` |
| magna | planning_commission | pmn | 2026-06-11 | 80 | 2026-07-19 | ok | 0 | `cd magna_city_council && download new dates' minutes to raw/ then extract (see docstring)` |
| copperton | meeting_minutes | godaddy+pmn | 2026-05-20 | 106 | 2026-07-19 | ok | 19 | `cd copperton_city_council && feed real NEW dates to meeting_minutes/fetch_minutes.py` |
| copperton | planning_commission | pmn | 2025-05-13 | 17 | 2026-07-19 | ok | 100 | `cd copperton_city_council && feed real NEW dates to meeting_minutes/fetch_minutes.py` |
| emigration_canyon | meeting_minutes | pmn | 2026-05-19 | 89 | 2026-07-19 | ok | 0 | `cd emigration_canyon_city_council && acquisition is a separate reviewed step (see recon.md)` |
| emigration_canyon | planning_commission | pmn | 2026-06-11 | 60 | 2026-07-19 | ok | 7 | `cd emigration_canyon_city_council && acquisition is a separate reviewed step (see recon.md)` |

`*` = dataset has no minutes_index.csv; max date measured from all_votes.csv
(rows = distinct meetings). "New on portal" counts documents newer than the
index max that the portal actually serves (meetings held but not yet posted
are excluded — they appear in the notes).

## Probe notes & failures

- **lehi / meeting_minutes**: 21 newer meeting(s) listed with no Minutes link yet (unposted)
- **lehi / planning_commission**: 1 newer meeting(s) listed with no Minutes link yet (unposted)
- **logan / meeting_minutes**: council PDFs may embed an RDA section — split manually (see header)
- **ogden / meeting_minutes**: council minutes typically post ~4-6 weeks after the meeting; the hub is the authoritative surface (AgendaCenter CC category is stale); UNRECOGNIZED suffixes skipped: ['2026-06-30-Agenda']
- **ogden / planning_commission**: PC minutes are scanned (format=ocr) — see OCR caveat in header
- **orem / meeting_minutes**: minutes from Google Drive archive; CivicClerk carries agendas/packets only; 1 held meeting(s) have no minutes on Drive yet: 2026-07-14
- **orem / planning_commission**: minutes from Google Drive archive; CivicClerk carries agendas/packets only; 5 held meeting(s) have no minutes on Drive yet: 2026-05-20, 2026-06-03, 2026-06-17, 2026-07-01, 2026-07-15
- **park_city / meeting_minutes**: 1 held meeting(s) have no Minutes file yet (unapproved): 2026-07-16
- **park_city / planning_commission**: 1 held meeting(s) have no Minutes file yet (unapproved): 2026-07-08
- **provo / meeting_minutes**: 4 newer council meeting date(s) have no published minutes yet (OnBase comments the link out until approval); secondary AgendaCenter portal already lists council minutes for: 2026-06-09
- **sandy / meeting_minutes**: 2 of 5 still have Draft minutes — the M=M PDF is typically posted only once approved (council) / votes may be incomplete until finalized (PC)
- **sandy / planning_commission**: 2 of 2 still have Draft minutes — the M=M PDF is typically posted only once approved (council) / votes may be incomplete until finalized (PC)
- **slc / meeting_minutes**: 4 newer meeting(s) have no HTML Minutes yet (unapproved)
- **slc / planning_commission**: probed 5 candidate Wednesday(s) on slcdocs (PrimeGov does not list PC meetings — minutes may lag ~1 month behind a meeting)
- **slc / public_comments**: delegated to check_new_comments.py --dry-run — up to date
- **vineyard / meeting_minutes**: 3 held meeting(s) have no Minutes file yet (unapproved): 2026-06-23, 2026-07-07, 2026-07-14
- **vineyard / planning_commission**: 3 held meeting(s) have no Minutes file yet (unapproved): 2026-05-20, 2026-06-17, 2026-07-15
- **west_jordan / meeting_minutes**: 1 newer meeting(s) have no Minutes doc yet (unapproved)
- **west_jordan / planning_commission**: 4 newer meeting(s) have no Minutes doc yet (unapproved)
- **west_valley / meeting_minutes**: 1 newer meeting date(s) have no published minutes yet
- **west_valley / planning_commission**: 6 newer meeting date(s) have no published minutes yet
- **south_jordan / meeting_minutes**: CivicPlus ArchiveCenter; PMN (utah.gov/pmn) was the 2020 backfill only — floor already met, not re-probed.
- **south_jordan / planning_commission**: CivicPlus ArchiveCenter; PMN (utah.gov/pmn) was the 2020 backfill only — floor already met, not re-probed.
- **millcreek / meeting_minutes**: CivicPlus AgendaCenter landing (current window); cat3=Council + cat7=CRA. | PMN body 5741: 0 council notice(s) newer than index max (cross-check only — CivicPlus is the authoritative fetch source)
- **millcreek / planning_commission**: CivicPlus AgendaCenter landing (current window); cat2=Planning Commission.
- **taylorsville / meeting_minutes**: CivicEngage Central Minutes year folders (first-column = Minutes, verified live); dates already indexed or in minutes_unrecovered.csv are excluded. | PMN body 720: 2 council notice date(s) newer than index max (cross-check only — CivicEngage is the authoritative fetch source; PMN exposes only the most-recent window via GET)
- **taylorsville / planning_commission**: CivicEngage Central Minutes year folders (first-column = Minutes, verified live); dates already indexed or in minutes_unrecovered.csv are excluded.
- **murray / meeting_minutes**: 2023 council + post-2022 PC minutes live on a Tyler Minutes Management SPA, not this Archive — an empty result there is expected. | PMN body 735 (floor 2020-01-01): 11 minutes-bearing date(s) >= floor not in index/unrecovered/exceptions (2020-01-08, 2020-02-20, 2020-05-15, 2021-03-18, 2022-02-18, 2022-05-04, 2023-01-11, 2023-07-11, 2023-08-23, 2023-12-07, 2026-03-17) — raw candidate LEAD(s), NOT ingested; verify against scripts/pmn_crosscheck.py (authoritative diff)
- **murray / planning_commission**: 2023 council + post-2022 PC minutes live on a Tyler Minutes Management SPA, not this Archive — an empty result there is expected. | PMN body 983 (floor 2020-01-01): 0 minutes-bearing date(s) >= floor not in index/unrecovered/exceptions; CivicPlus Archive is the authoritative fetch source | 2026 agenda-only PC watch: 2026-02-05=still agenda-only; 2026-05-21=still agenda-only; 2026-06-18=still agenda-only; 2026-07-02=still agenda-only
- **herriman / meeting_minutes**: read-only probe; ingest via `fetch_new.py --ingest` (append-only) — NEVER --build-md/--full-build (destructive full rebuild)
- **herriman / planning_commission**: read-only probe; ingest via `fetch_new.py --ingest` (append-only) — NEVER --build-md/--full-build (destructive full rebuild)
- **draper / meeting_minutes**: 1 meeting(s) with only a tally-only Recap (minutes not yet adopted) — recorded pending, NOT fetched; 2 past meeting(s) with no minutes doc on the portal (honest gap); 1 future meeting row(s) skipped
- **draper / planning_commission**: 3 past meeting(s) with no minutes doc on the portal (honest gap); 2 future meeting row(s) skipped
- **riverton / meeting_minutes**: PMN body 889; 128 meetings enumerated >= 2020-01-01 from the cached notice list (run --fetch/--refresh-notices to refresh it)
- **riverton / planning_commission**: PMN body 5473; 119 meetings enumerated >= 2020-01-01 from the cached notice list (run --fetch/--refresh-notices to refresh it)
- **alta / meeting_minutes**: PMN body 1601; 100 meetings enumerated >= 2020-01-01 from the cached notice list (run --fetch/--refresh-notices to refresh it). Alta is sparse (~12 council mtgs/yr) — an empty result is normal.
- **alta / planning_commission**: PMN body 1602; 22 meetings enumerated >= 2020-01-01 from the cached notice list (run --fetch/--refresh-notices to refresh it). Alta is sparse (~12 council mtgs/yr) — an empty result is normal.
- **midvale / planning_commission**: recent PC minutes are bare-relative root-level files served at the site root
- **cottonwood_heights / meeting_minutes**: portal (CivicEngage) ∪ PMN body 2147; 0 candidate meeting(s). Routine refresh is --ingest (append-only).
- **cottonwood_heights / planning_commission**: portal (CivicEngage) ∪ PMN body 2148; 0 candidate meeting(s). Routine refresh is --ingest (append-only).
- **holladay / meeting_minutes**: PMN posts minutes AFTER the meeting — a listed meeting whose notice has only an agenda/packet is 'pending', logged in minutes_unrecovered.csv, not fetched.
- **holladay / planning_commission**: PMN posts minutes AFTER the meeting — a listed meeting whose notice has only an agenda/packet is 'pending', logged in minutes_unrecovered.csv, not fetched. PC PMN coverage is intermittent (no 2020/2021/2023 minutes on PMN — city Revize/SuiteOne would be needed).
- **bluffdale / meeting_minutes**: CivicPlus AgendaCenter landing (current window); CID=2 = City Council (RDA/LBA are in-session in the same doc, split by the extractor).
- **bluffdale / planning_commission**: CivicPlus AgendaCenter landing (current window); CID=3 = Planning Commission.
- **white_city / meeting_minutes**: Streamline year pages (/meetings-archive + /council-meeting?year=YYYY + /council-meetings); minutes docs only (agendas/packets/PC/audio excluded); dates already indexed or in minutes_unrecovered.csv are excluded. | PMN body 5805: 0 council notice date(s) newer than index max (cross-check only — Streamline is the authoritative fetch source) | PMN PC body 5879: 0 PC notice date(s) newer than the PC index max — cross-check only (open to confirm minutes vs agenda; the sporadic PC series is never auto-ingested)
- **white_city / planning_commission**: PMN PC body 5879: 0 PC notice date(s) newer than the PC index max — cross-check only (open to confirm minutes vs agenda; the sporadic PC series is never auto-ingested)
- **kearns / meeting_minutes**: PMN body 5823: 10 recent notices; 0 new minutes lead(s). Back-catalog / acquisition detail in stdout.
- **kearns / planning_commission**: PMN body 1561: 7 recent notices; 0 new minutes lead(s). Back-catalog / acquisition detail in stdout.
- **magna / meeting_minutes**: PMN body 5803 + CivicPlus catID 3; 0 newer portal date(s) (cross-check — open to confirm minutes vs agenda before ingesting) | CRA body 6925: no unhandled dates
- **magna / planning_commission**: PMN body 1559; 0 newer portal date(s) (cross-check — open to confirm minutes vs agenda before ingesting)
- **copperton / meeting_minutes**: PMN body 5831 + GoDaddy town site; 19 candidate new meeting date(s); 1 pre-2018-07 notices 404-purged (honest gap). Open each doc to confirm minutes vs agenda before ingesting.
- **copperton / planning_commission**: PMN body 1560; 100 candidate new meeting date(s); 116 pre-2018-07 notices 404-purged (honest gap). Open each doc to confirm minutes vs agenda before ingesting.
- **emigration_canyon / meeting_minutes**: PMN body 5809: 238 notices enumerated; 0 new minutes lead(s) (coverage begins 2018-10-25; pre-floor is verified-purged).
- **emigration_canyon / planning_commission**: PMN body 1562: 290 notices enumerated; 7 new minutes lead(s) (coverage begins 2018-11-15; pre-floor is verified-purged).

## Quarterly refresh routine

Suggested cadence: the first week of Jan / Apr / Jul / Oct (minutes are
approved 2–6 weeks after a meeting, so a quarterly pass catches everything).

1. **Probe everything** (read-only, ~5 min):
   `for c in *_city_council; do (cd $c && python3 fetch_new.py --probe); done`
2. **Regenerate this dashboard**: `python3 scripts/refresh_status.py`
3. **Fetch per city where new items exist**: `cd <city>_city_council &&
   python3 fetch_new.py --fetch` (downloads raw docs, converts to markdown,
   appends index rows, runs that city's extract_votes.py + validate_votes.py).
   SLC public comments delegate to `public_comments/check_new_comments.py`
   (then vision_extract.py + clean_comments.py).
4. **Rebuild derived layers** in each touched city: `python3 db/build_db.py`
   (+ `db/build_referrals.py` where present), `python3 build_weeks.py`, and
   `python3 scripts/normalize_motions.py --all` from the repo root for motions_std.
5. **Validate**: `python3 scripts/validate_city.py <city>_city_council` must
   stay at 0 FAIL; investigate any new WARN before committing.
6. If a probe FAILs (portal moved/auth wall), re-recon that vendor section in
   the city's recon.md and update its fetch_new.py — never fake availability.

