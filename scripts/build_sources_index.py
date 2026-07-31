#!/usr/bin/env python3
"""Build the unified per-city source/citation index (Phase 2.8, REMEDIATION_PLAN.md).

For each city this harvests per-DOCUMENT provenance from every dataset's existing
machine-readable provenance (minutes_index.csv, comment manifests/scan records,
election raw/ files + documented issuing offices, expansion index.csv files) and writes:

    <city>_city_council/sources.csv    machine-readable, one row per source document
    <city>_city_council/SOURCES.md     human-readable, citation-ready summary

Columns of sources.csv:
    dataset, record_key, title, date, local_path, source_url, source_host,
    retrieved_date, verified_date, extraction_method, processing_ref

Rules honored here:
  * No URL is ever invented. Where a document's URL was recorded, it is carried
    verbatim; where the docs only name the issuing office, source_url is
    "unrecorded (<office>)".
  * retrieved_date only where actually recorded (expansion indexes).
  * verified_date is only written by the --verify-sample mode (live check) and is
    preserved across regenerations.

Usage:
    python3 scripts/build_sources_index.py                 # all cities
    python3 scripts/build_sources_index.py lehi slc        # subset
    python3 scripts/build_sources_index.py --verify-sample 5   # liveness-check a
        stratified sample of recorded URLs per city and stamp verified_date on the
        sampled rows that answered (run after a normal build)

stdlib-only; idempotent; read-only with respect to all dataset files.
"""

import argparse
import csv
import datetime
import fnmatch
import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FIELDS = ["dataset", "record_key", "title", "date", "local_path", "source_url",
          "source_host", "retrieved_date", "verified_date", "extraction_method",
          "processing_ref"]

# City list comes from the shared registry (scripts/cities.py).
from cities import DIRS as CITIES

EXPANSION_DATASETS = ["packets", "housing_plans", "ordinances", "pmn_backfill",
                      "transcripts", "campaign_finance"]

# ---------------------------------------------------------------------------
# Curated, citation-facing metadata (institution / portal per dataset).
# recon.md is the source of these facts; they are frozen here so SOURCES.md is
# regenerable from this script alone.
# ---------------------------------------------------------------------------

META = {
    "slc": {
        "name": "Salt Lake City",
        "preamble": (
            "Civic records of the Salt Lake City Council and Planning Commission, "
            "2020–present, plus municipal election results back to 2007. Council "
            "minutes are published by the City Recorder / Council Office on the "
            "PrimeGov portal (slc.primegov.com; born-digital, 2021+) with the older "
            "material on the city's Laserfiche WebLink archive "
            "(webdme.slcgov.com/AgendasMinutes; scanned + OCR). Planning Commission "
            "minutes are published by the Planning Division on slcdocs.com and "
            "Laserfiche. Written public comments are published as weekly PDF "
            "compilations on slcdocs.com. Election results are produced by the Salt "
            "Lake County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Salt Lake City Recorder / City Council Office",
                "portal": "PrimeGov (slc.primegov.com); archival: Laserfiche WebLink (webdme.slcgov.com)",
                "note": "2021+ born-digital HTML minutes converted to text; 2020 files are OCR of Laserfiche scans (65 of 68 carry equivalent-record PMN citation URLs since 2026-07-19; 3 formal-session dates are verified no-PMN gaps)."},
            "planning_commission": {
                "institution": "Salt Lake City Planning Division",
                "portal": "slcdocs.com / Laserfiche WebLink / slc.gov",
                "note": "Born-digital PDFs on slcdocs.com; older items from Laserfiche."},
            "public_comments": {
                "institution": "Salt Lake City Council Office",
                "portal": "slcdocs.com (weekly public-comment PDF compilations)",
                "note": "Extracted from the weekly PDFs with Claude Vision; ~8 unrecoverable pages documented in public_comments/CLAUDE.md."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "County-wide canvass exports (2007–2025) filtered to Salt Lake City races; per-file download URLs were not recorded at capture time."},
        },
    },
    "lehi": {
        "name": "Lehi",
        "preamble": (
            "Civic records of the Lehi City Council and Planning Commission, "
            "2020–present. Minutes are published by the Lehi City Recorder on the "
            "city's Granicus portal (lehi.granicus.com). Public comments appear only "
            "inside council minutes (no separate comment channel). Election results "
            "are produced by the Utah County Clerk (vote.utahcounty.gov) and the Utah "
            "state Enhanced Voting portal (electionresults.utah.gov); ranked-choice "
            "rounds via rcvis.com. Expansion datasets (agenda packets, housing/general "
            "plan, ordinances, public-notice backfill, transcripts, campaign finance) "
            "carry their own per-document URLs."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Lehi City Recorder",
                "portal": "Granicus (lehi.granicus.com)",
                "note": "Born-digital PDFs served via MinutesViewer/DocumentViewer."},
            "planning_commission": {
                "institution": "Lehi City Planning Department",
                "portal": "Granicus (lehi.granicus.com)",
                "note": "Born-digital PDFs, same portal as council minutes."},
            "public_comments": {
                "institution": "Lehi City Recorder (via council minutes)",
                "portal": "Granicus (lehi.granicus.com)",
                "note": "Lehi publishes no separate comment compilations; the few written comments read into the record live inside the cited minutes documents."},
            "election_results": {
                "institution": "Utah County Clerk; Utah Lt. Governor's Enhanced Voting portal; rcvis.com (RCV rounds)",
                "portal": "vote.utahcounty.gov / electionresults.utah.gov / rcvis.com",
                "note": "Raw county/state files mirrored verbatim in election_results/raw/; per-file URLs documented for the county portal only as hashed /cms/uploads/ names (see election_results/CLAUDE.md)."},
            "packets": {
                "institution": "Lehi City Recorder",
                "portal": "Granicus (lehi.granicus.com)",
                "note": "Agendas and agenda packets, raw PDFs retained."},
            "housing_plans": {
                "institution": "Lehi City (lehi-ut.gov); Utah DWS/HCD filings",
                "portal": "lehi-ut.gov",
                "note": "General plan + moderate-income housing element documents."},
            "ordinances": {
                "institution": "Lehi City Council (via adopted-motion record)",
                "portal": "Granicus (lehi.granicus.com) — reconstructed from minutes",
                "note": "Ordinance actions reconstructed from council minutes motions; source_url resolves to the minutes document that records adoption."},
            "pmn_backfill": {
                "institution": "Utah Public Notice Website (Lt. Governor)",
                "portal": "utah.gov/pmn",
                "note": "State-mandated public-notice copies of agendas/minutes."},
            "transcripts": {
                "institution": "Lehi City (YouTube channel); OpenUtah mirror",
                "portal": "lehi.openutah.org / YouTube",
                "note": "No caption files were retrievable (yt-dlp absent at build time); index rows carry the source URLs only — no local documents."},
            "campaign_finance": {
                "institution": "Lehi City Recorder (candidate financial statements)",
                "portal": "lehi-ut.gov",
                "note": "Born-digital PDFs, raw retained."},
        },
    },
    "logan": {
        "name": "Logan",
        "preamble": (
            "Civic records of the Logan Municipal Council and Planning Commission, "
            "2020–present. Minutes are published on the city's Revize CMS "
            "(loganutah.gov; files served from the Revize CDN). Logan publishes no "
            "written public-comment compilations. Election results: Logan "
            "administered its own 2019/2021 municipal elections (City Recorder); "
            "from 2023 the Cache County Clerk administers them; 2025 results come "
            "from the Utah state Enhanced Voting portal."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Logan City Recorder",
                "portal": "Revize CMS (loganutah.gov)",
                "note": "Static PDF files linked from year-by-year listing pages."},
            "planning_commission": {
                "institution": "Logan Community Development Department",
                "portal": "Revize CMS (loganutah.gov)",
                "note": "Mix of born-digital and scanned (OCR) PDFs."},
            "public_comments": {
                "institution": "—",
                "portal": "—",
                "note": "Logan publishes no written public comments (see public_comments/AVAILABILITY.md); in-person speakers are logged from minutes in minutes_speaker_log.csv."},
            "election_results": {
                "institution": "Logan City Recorder (2019/2021); Cache County Clerk (2023+); Utah Enhanced Voting portal (2025)",
                "portal": "loganutah.gov / cachecounty.gov / electionresults.utah.gov",
                "note": "Raw official PDFs/JSON mirrored in election_results/raw/; per-file URLs were not recorded."},
        },
    },
    "nephi": {
        "name": "Nephi",
        "preamble": (
            "Civic records of the Nephi City Council and Planning Commission, "
            "2020–present. Minutes are published on the city's CivicPlus CivicEngage "
            "AgendaCenter (nephi.utah.gov). Nephi publishes no written "
            "public-comment compilations. Election results come from the Utah state "
            "Enhanced Voting portal (Juab County, 2023+) and archived news canvasses "
            "for 2019/2021 (no county archive exists)."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Nephi City Recorder",
                "portal": "CivicPlus AgendaCenter (nephi.utah.gov)",
                "note": "Born-digital documents."},
            "planning_commission": {
                "institution": "Nephi City Planning Commission",
                "portal": "CivicPlus AgendaCenter (nephi.utah.gov)",
                "note": "Born-digital documents (some .docx)."},
            "public_comments": {
                "institution": "—",
                "portal": "—",
                "note": "Nephi publishes no written public comments (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Utah Enhanced Voting portal (Juab County); archived news canvasses (2019 Deseret News, 2021 Mid-Utah Radio)",
                "portal": "electionresults.utah.gov / juabcounty.gov",
                "note": "No pre-existing Juab County election archive; 2019/2021 numbers rest on archived unofficial canvasses (documented in election_results/CLAUDE.md)."},
        },
    },
    "ogden": {
        "name": "Ogden",
        "preamble": (
            "Civic records of the Ogden City Council (with RDA/MBA sessions) and "
            "Planning Commission, 2020–present. Minutes are published on the city's "
            "CivicPlus site (ogdencity.gov DocumentCenter) — 2020–2023 as annual "
            "compilation PDFs, 2024+ per meeting. Ogden publishes no written "
            "public-comment compilations. Election results come from Weber County "
            "Elections (weberelections.gov) and, for gaps, the Utah state Enhanced "
            "Voting portal."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Ogden City Recorder",
                "portal": "CivicPlus DocumentCenter (ogdencity.gov)",
                "note": "2020–2023 meetings extracted from annual compilation PDFs (source_url points at the year compilation); 2024+ per-meeting PDFs."},
            "planning_commission": {
                "institution": "Ogden Planning Division",
                "portal": "CivicPlus (ogdencity.gov)",
                "note": "Mix of born-digital and scanned (OCR) PDFs."},
            "public_comments": {
                "institution": "—",
                "portal": "—",
                "note": "Ogden publishes no written public comments (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Weber County Elections; Utah Enhanced Voting portal (2023 general, 2025)",
                "portal": "weberelections.gov / electionresults.utah.gov",
                "note": "Raw PDFs/JSON mirrored in election_results/raw/; per-file URLs were not recorded (the Weber site serves files from a CDN bucket)."},
        },
    },
    "orem": {
        "name": "Orem",
        "preamble": (
            "Civic records of the Orem City Council and Planning Commission, "
            "2020–present. The city's official minutes archive is a public Google "
            "Drive folder linked from orem.gov/meetings; newer meetings are on the "
            "CivicClerk portal (oremut.api.civicclerk.com). Written public comments "
            "appear only inside council minutes. Election results are produced by "
            "the Utah County Clerk (vote.utahcounty.gov)."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Orem City Recorder",
                "portal": "Google Drive archive (drive.google.com) + CivicClerk (oremut)",
                "note": "Mix of born-digital and scanned (OCR) documents."},
            "planning_commission": {
                "institution": "Orem Development Services / Planning Commission",
                "portal": "Google Drive archive + CivicClerk (oremut)",
                "note": "Mix of born-digital, .docx and OCR documents."},
            "public_comments": {
                "institution": "Orem City Recorder (via council minutes)",
                "portal": "Google Drive archive + CivicClerk",
                "note": "Orem publishes no separate comment compilations; written comments read into the record live inside the cited minutes documents."},
            "election_results": {
                "institution": "Utah County Clerk",
                "portal": "vote.utahcounty.gov",
                "note": "County SOVC CSVs / results PDFs mirrored verbatim in election_results/raw/; live URLs recorded in election_results/CLAUDE.md for 6 of 9 files."},
        },
    },
    "park_city": {
        "name": "Park City",
        "preamble": (
            "Civic records of the Park City Council and Planning Commission, "
            "2020–present. Minutes are published via the city's CivicClerk portal "
            "(parkcityut.api.civicclerk.com). Written public comments appear inside "
            "minutes and, for a handful of meetings, inside agenda packets on the "
            "same portal. Election results are certified by the city (Board of "
            "Canvassers) with tabulation by the Summit County Clerk; the canvass "
            "PDFs are published on the city's election-results page (parkcity.gov)."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Park City Municipal Corporation (City Recorder)",
                "portal": "CivicClerk (parkcityut.api.civicclerk.com)",
                "note": "Born-digital text streams from the CivicClerk API."},
            "planning_commission": {
                "institution": "Park City Planning Department",
                "portal": "CivicClerk (parkcityut.api.civicclerk.com)",
                "note": "Born-digital text streams from the CivicClerk API."},
            "public_comments": {
                "institution": "Park City Municipal Corporation",
                "portal": "CivicClerk (minutes + agenda packets)",
                "note": "Most comments are transcribed from minutes documents; 26 come from 5 agenda packets fetched from the CivicClerk file API."},
            "election_results": {
                "institution": "Park City Recorder / Board of Canvassers (tabulation: Summit County Clerk)",
                "portal": "parkcity.gov/government/elections/election_results.php",
                "note": "Canvass/precinct PDFs saved from the city page and renamed locally (original file names collide across cycles); per-file URLs were not recorded."},
        },
    },
    "provo": {
        "name": "Provo",
        "preamble": (
            "Civic records of the Provo Municipal Council and Planning Commission, "
            "2020–present. Council minutes and agenda packets are published on the "
            "city's Hyland OnBase 'Agenda Online' portal (agendas.provo.gov); recent "
            "Planning Commission minutes on the CivicPlus AgendaCenter (provo.gov). "
            "Written public comments were harvested from council agenda packets. "
            "Election results are produced by the Utah County Clerk "
            "(vote.utahcounty.gov)."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Provo Municipal Council Office / City Recorder",
                "portal": "OnBase Agenda Online (agendas.provo.gov)",
                "note": "PDF minutes (one 2020 file OCR)."},
            "planning_commission": {
                "institution": "Provo Development Services",
                "portal": "CivicPlus AgendaCenter (provo.gov)",
                "note": "Born-digital documents, 2025+ only (earlier PC minutes not published there)."},
            "public_comments": {
                "institution": "Provo Municipal Council Office",
                "portal": "OnBase Agenda Online (agendas.provo.gov) — agenda packets",
                "note": "138 packets scanned (record: public_comments/packets_scanned.csv); the 15 packets that contributed comments to the dataset are indexed here. Raw packet text retained under public_comments/raw/packet_txt/."},
            "election_results": {
                "institution": "Utah County Clerk",
                "portal": "vote.utahcounty.gov",
                "note": "County SOVC CSVs / results PDFs mirrored verbatim in election_results/raw/; per-file URLs were not recorded (hashed /cms/uploads/ names, see CLAUDE.md)."},
        },
    },
    "sandy": {
        "name": "Sandy",
        "preamble": (
            "Civic records of the Sandy City Council and Planning Commission, "
            "2020–present. Council minutes are published on Granicus Legistar "
            "(sandyutah.legistar.com). Planning Commission votes come from the "
            "Legistar web API (structured EventItemVote records; Sandy publishes no "
            "separate PC minutes files in this pipeline). Sandy publishes no written "
            "public-comment compilations. Election results are produced by the Salt "
            "Lake County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Sandy City Recorder",
                "portal": "Granicus Legistar (sandyutah.legistar.com)",
                "note": "Born-digital PDFs (some with PUA-encoded fonts, decoded; some OCR)."},
            "planning_commission": {
                "institution": "Sandy Community Development",
                "portal": "Granicus Legistar web API (sandyutah.legistar.com)",
                "note": "Votes built from Legistar EventItemVote API records staged in db/staging/ — not from minutes documents."},
            "public_comments": {
                "institution": "—",
                "portal": "—",
                "note": "Sandy publishes no written public comments (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "County SOVC workbooks + RCV reports copied verbatim from a local mirror of the county results site; per-file URLs were not recorded."},
        },
    },
    "st_george": {
        "name": "St. George",
        "preamble": (
            "Civic records of the St. George City Council and Planning Commission, "
            "2020–present. Minutes are published on the city's Revize CMS "
            "(sgcityutah.gov), with some meetings recovered from the Utah Public "
            "Notice Website. Written public comments are published as weekly PDF "
            "compilations on sgcityutah.gov. Election results are produced by the "
            "Washington County Clerk (washco.utah.gov)."),
        "datasets": {
            "meeting_minutes": {
                "institution": "St. George City Recorder",
                "portal": "Revize CMS (sgcityutah.gov); fallback: Utah Public Notice (utah.gov/pmn)",
                "note": "Born-digital PDFs/doc files."},
            "planning_commission": {
                "institution": "St. George Planning Division",
                "portal": "Revize CMS (sgcityutah.gov); Utah Public Notice (utah.gov/pmn)",
                "note": "Born-digital documents."},
            "public_comments": {
                "institution": "St. George City Council Office",
                "portal": "sgcityutah.gov (weekly 'Public Comments Received' PDFs)",
                "note": "Weekly PDFs mirrored under public_comments/raw/ with a full URL manifest (comments_json/_manifest.json)."},
            "election_results": {
                "institution": "Washington County Clerk",
                "portal": "washco.utah.gov (files served from outpost.washco.utah.gov)",
                "note": "County CSV exports + precinct PDFs mirrored verbatim in election_results/raw/; the CLAUDE.md source table records the host and partial paths, not full URLs."},
        },
    },
    "vineyard": {
        "name": "Vineyard",
        "preamble": (
            "Civic records of the Vineyard City Council and Planning Commission, "
            "2020–present. Minutes are published via the city's CivicClerk portal "
            "(vineyardut.api.civicclerk.com), with one meeting recovered from the "
            "Utah Public Notice Website. Vineyard publishes no written "
            "public-comment compilations. Election results come from rcvis.com "
            "(2019–2023 ranked-choice rounds) and the Utah state Enhanced Voting "
            "portal (2025)."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Vineyard City Recorder",
                "portal": "CivicClerk (vineyardut.api.civicclerk.com)",
                "note": "Born-digital text streams (a few OCR)."},
            "planning_commission": {
                "institution": "Vineyard Planning Commission",
                "portal": "CivicClerk (vineyardut.api.civicclerk.com)",
                "note": "Born-digital text streams."},
            "public_comments": {
                "institution": "—",
                "portal": "—",
                "note": "Vineyard publishes no written public comments (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "rcvis.com (RCV rounds 2019–2023); Utah Enhanced Voting portal (2025, Utah County)",
                "portal": "rcvis.com / electionresults.utah.gov",
                "note": "Raw HTML/JSON mirrored verbatim in election_results/raw/; per-file URLs were not recorded (rcvis slugs documented in CLAUDE.md)."},
        },
    },
    "west_jordan": {
        "name": "West Jordan",
        "preamble": (
            "Civic records of the West Jordan City Council and Planning Commission, "
            "2020–present. Minutes are published on the city's PrimeGov portal "
            "(westjordan.primegov.com). Written public comments were harvested from "
            "council agenda packets on the same portal. Election results are "
            "produced by the Salt Lake County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "West Jordan City Recorder",
                "portal": "PrimeGov (westjordan.primegov.com)",
                "note": "PDF minutes (born-digital text; some OCR'd signature pages)."},
            "planning_commission": {
                "institution": "West Jordan Planning Division",
                "portal": "PrimeGov (westjordan.primegov.com)",
                "note": "36 of 84 documents are OCR."},
            "public_comments": {
                "institution": "West Jordan City Council Office",
                "portal": "PrimeGov (westjordan.primegov.com) — compiled agenda packets",
                "note": "120 packets scanned (record: public_comments/packets_scanned.csv; 15 contained comments, mostly duplicates of one another); the 2 packets contributing the deduplicated dataset are indexed here with raw PDFs retained."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "County SOVC workbooks copied verbatim from a local mirror of the county results site; per-file URLs were not recorded."},
        },
    },
    "west_valley": {
        "name": "West Valley City",
        "preamble": (
            "Civic records of the West Valley City Council and Planning Commission, "
            "2020–present. Minutes are published on the city's self-hosted Hyland "
            "OnBase 'Agenda Online' portal (ob.wvc-ut.gov). West Valley publishes no "
            "written public-comment compilations. Election results are produced by "
            "the Salt Lake County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "West Valley City Recorder",
                "portal": "OnBase Agenda Online (ob.wvc-ut.gov)",
                "note": "Born-digital documents."},
            "planning_commission": {
                "institution": "West Valley City Community & Economic Development",
                "portal": "OnBase Agenda Online (ob.wvc-ut.gov)",
                "note": "Born-digital documents."},
            "public_comments": {
                "institution": "—",
                "portal": "—",
                "note": "West Valley publishes no written public comments (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "County SOVC workbooks copied verbatim from a local mirror of the county results site; per-file URLs were not recorded."},
        },
    },
    "south_jordan": {
        "name": "South Jordan",
        "preamble": (
            "Civic records of the South Jordan City Council (with in-session RDA/MBA "
            "sessions) and Planning Commission, 2020-present, plus municipal election "
            "results back to 2007. Council and Planning Commission minutes are "
            "published by the City Recorder on the city's CivicPlus/CivicEngage site "
            "(sjc.utah.gov DocumentCenter/ArchiveCenter), with 2020 backfilled from the "
            "Municode Meetings portal and the Utah Public Notice Website. South Jordan "
            "publishes no written public-comment compilations (comment is submit-only, "
            "by email or in person). Election results are produced by the Salt Lake "
            "County Clerk. Expansion datasets (agenda packets, housing/general plan, "
            "ordinances, public-notice backfill, transcripts, campaign finance) carry "
            "their own per-document provenance."),
        "datasets": {
            "meeting_minutes": {
                "institution": "South Jordan City Recorder",
                "portal": "CivicPlus/CivicEngage (sjc.utah.gov); 2020 backfill: Municode Meetings + Utah Public Notice (utah.gov/pmn)",
                "note": "Born-digital text PDFs harvested from the DocumentCenter/ArchiveCenter year archives; the council sits in-session as the RDA and MBA (no separate RDA/MBA minutes files)."},
            "planning_commission": {
                "institution": "South Jordan City Planning Division",
                "portal": "CivicPlus/CivicEngage (sjc.utah.gov); Utah Public Notice (utah.gov/pmn)",
                "note": "Born-digital text PDFs from the Planning Commission minutes archive; 2020 supplemented from Utah PMN."},
            "public_comments": {
                "institution": "-",
                "portal": "-",
                "note": "South Jordan publishes no written public comments - comment is submit-only (email to the City Recorder or in person), neither archived (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "County SOVC workbooks copied verbatim from the local slco-election-archive mirror of the county results site; per-file URLs were not recorded."},
            "packets": {
                "institution": "South Jordan City Recorder",
                "portal": "CivicPlus/CivicEngage (sjc.utah.gov); Municode Meetings",
                "note": "Agendas and agenda packets, raw retained."},
            "housing_plans": {
                "institution": "South Jordan City (sjc.utah.gov); Utah DWS/HCD filings",
                "portal": "sjc.utah.gov",
                "note": "General plan + moderate-income housing element documents."},
            "ordinances": {
                "institution": "South Jordan City Council (via adopted-motion record)",
                "portal": "CivicPlus/CivicEngage (sjc.utah.gov) - reconstructed from minutes",
                "note": "Ordinance actions reconstructed from council minutes motions; source_url resolves to the minutes document that records adoption."},
            "pmn_backfill": {
                "institution": "Utah Public Notice Website (Lt. Governor)",
                "portal": "utah.gov/pmn",
                "note": "State-mandated public-notice copies of agendas/minutes."},
            "transcripts": {
                "institution": "South Jordan City (meeting video)",
                "portal": "sjc.utah.gov / YouTube",
                "note": "Meeting-video transcripts; per-row source URLs carried where recorded."},
            "campaign_finance": {
                "institution": "South Jordan City Recorder (candidate financial statements)",
                "portal": "sjc.utah.gov",
                "note": "Candidate financial disclosures, raw retained."},
        },
    },
    "millcreek": {
        "name": "Millcreek",
        "preamble": (
            "Civic records of the Millcreek City Council, Community Reinvestment "
            "Agency (CRA), and Planning Commission, 2016-present (Millcreek "
            "incorporated December 2016 - the short history is the city's entire "
            "legislative life, not a gap). Minutes for all bodies are published by the "
            "City Recorder on the city's CivicPlus/CivicEngage AgendaCenter "
            "(millcreekut.gov). Millcreek publishes genuine written public comment only "
            "inside agenda-packet PDFs (no standalone comment archive). Election "
            "results are produced by the Salt Lake County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Millcreek City Recorder",
                "portal": "CivicPlus/CivicEngage AgendaCenter (millcreekut.gov)",
                "note": "Combined Agenda+Packet+Minutes PDFs with a scanned/OCR text layer (garble-tolerant extraction); the council also convenes in-session as the Community Reinvestment Agency (CRA), tagged body=CRA - no separate CRA portal files."},
            "planning_commission": {
                "institution": "Millcreek City Planning Commission",
                "portal": "CivicPlus/CivicEngage AgendaCenter (millcreekut.gov)",
                "note": "Millcreek runs its own Planning Commission (not Salt Lake County); mix of born-digital text and OCR PDFs."},
            "public_comments": {
                "institution": "Millcreek City (via agenda packets)",
                "portal": "CivicPlus/CivicEngage AgendaCenter (millcreekut.gov)",
                "note": "Millcreek publishes no standalone comment compilations; verbatim resident letters appear inside PC agenda-packet PDFs - a Provo-style packet harvest is a documented pending follow-up (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "County SOVC workbooks copied verbatim from the local slco-election-archive mirror of the county results site; per-file URLs were not recorded. 2021 & 2023 municipal races used ranked-choice voting."},
        },
    },
    "taylorsville": {
        "name": "Taylorsville",
        "preamble": (
            "Civic records of the Taylorsville City Council (with in-session RDA "
            "sessions) and Planning Commission, 2020-present, plus municipal election "
            "results back to 2007. Minutes are published by the City Recorder on the "
            "city's CivicPlus/CivicEngage Central site (taylorsvilleut.gov), with the "
            "Utah Public Notice Website as a cross-check/fallback. Taylorsville "
            "publishes no written public-comment compilations (comment is "
            "in-person/livestream, submit-only). Election results are produced by the "
            "Salt Lake County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Taylorsville City Recorder",
                "portal": "CivicPlus/CivicEngage Central (taylorsvilleut.gov); fallback: Utah Public Notice (utah.gov/pmn)",
                "note": "Born-digital text PDFs (showpublisheddocument) with a mid-2025 switch to scanned RICOH OCR PDFs; the council also convenes in-session as the Redevelopment Agency (RDA), tagged body=RDA - no separate RDA portal files."},
            "planning_commission": {
                "institution": "Taylorsville City Planning Division",
                "portal": "CivicPlus/CivicEngage Central (taylorsvilleut.gov)",
                "note": "Taylorsville runs its own Planning Commission (not Salt Lake County); mix of born-digital text and OCR PDFs."},
            "public_comments": {
                "institution": "-",
                "portal": "-",
                "note": "Taylorsville publishes no written public comments - comment is in-person/livestream, submit-only and not archived (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "County SOVC workbooks copied verbatim from the local slco-election-archive mirror of the county results site (2019 re-parsed from the raw SOVC); per-file URLs were not recorded."},
        },
    },
    "murray": {
        "name": "Murray",
        "preamble": (
            "Civic records of the Murray City Municipal Council and Planning "
            "Commission, 2020-present, plus municipal election results (2021/2023/2025 "
            "in scope). Minutes are published by the City Recorder on the city's "
            "CivicPlus Archive Center (murray.utah.gov). Murray publishes no written "
            "public-comment compilations (comment is in-person, submit-only). Election "
            "results are produced by the Salt Lake County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Murray City Recorder",
                "portal": "CivicPlus Archive Center (murray.utah.gov, Archive.aspx?AMID=31)",
                "note": "Born-digital text PDFs (Archive/ViewFile/Item); named roll-call votes on legislative items, tally-only voice votes on routine items; mayor is executive and does not vote (max council roll = 5). 2023 council minutes are a portal gap (diverted to a Tyler Minutes Management SPA; only 5 of ~24 recovered)."},
            "planning_commission": {
                "institution": "Murray City Community Development",
                "portal": "CivicPlus Archive Center (murray.utah.gov, Archive.aspx?AMID=33)",
                "note": "Murray runs its own Planning Commission; born-digital text PDFs, named roll calls. Portal archive ends 2022-11 - no PC minutes published 2023+ (acquisition gap)."},
            "public_comments": {
                "institution": "-",
                "portal": "-",
                "note": "Murray publishes no written public comments - comment is in-person, submit-only and not archived (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "Filtered from the canonical Salt Lake County results (salt_lake_county/elections/slco_municipal_results_long.csv); 2021 general recovered from the raw SOVC workbook due to method-split privacy suppression in the long file."},
        },
    },
    "herriman": {
        "name": "Herriman",
        "preamble": (
            "Civic records of the Herriman City Council (with in-session CDRA / "
            "HCSEA / HCFSA sessions) and Planning Commission, 2020-present, plus "
            "municipal election results back to 2007. Minutes are published on the "
            "city's PrimeGov portal (herriman.primegov.com); 2020 minutes were "
            "recovered from the city's legacy AWS S3 agenda bucket. Herriman "
            "publishes no written public-comment compilations (comment is "
            "in-person/eComment-window, submit-only). Election results are produced "
            "by the Salt Lake County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Herriman City Recorder",
                "portal": "PrimeGov (herriman.primegov.com; committeeId 3); 2020 backfill from the legacy herriman-agendas S3 bucket",
                "note": "Born-digital text PDFs (CompiledDocument). Named roll-call votes; the MAYOR VOTES as a full member (max council roll = 5: 4 districts + mayor). Council also convenes in-session as CDRA (17C renewal agency), HCSEA (Safety Enforcement Area) and HCFSA (Fire Service Area), tagged by the body column. 2020 recovered from legacy S3 (PrimeGov only goes back to 2021-01)."},
            "planning_commission": {
                "institution": "Herriman City Planning Division",
                "portal": "PrimeGov (herriman.primegov.com; committeeId 14)",
                "note": "Herriman runs its own Planning Commission; born-digital text PDFs, named roll calls; 2020 recovered from legacy S3."},
            "public_comments": {
                "institution": "-",
                "portal": "-",
                "note": "Herriman publishes no written public comments - comment is in-person / PrimeGov eComment-window, submit-only and not archived (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "Filtered from the canonical Salt Lake County results; 2011 general, 2019 general, and 2021 general recovered from raw SOVC workbooks (canonical long-file misses/suppresses them)."},
        },
    },
    "draper": {
        "name": "Draper",
        "preamble": (
            "Civic records of the Draper City Council and Planning Commission, "
            "2020-present, plus municipal election results back to 2007. Minutes are "
            "published on the city's Granicus portal (draper.granicus.com); Draper is "
            "governed by 5 AT-LARGE councilmembers + a separately-elected, NON-voting "
            "Mayor. Draper straddles Salt Lake (primary) and Utah counties, but Salt "
            "Lake County administers the entire city election. Draper publishes no "
            "written public-comment compilations (comment is in-person/email, "
            "submit-only)."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Draper City Recorder",
                "portal": "Granicus (draper.granicus.com, ViewPublisher view_id=1)",
                "note": "Born-digital text PDFs via the Granicus MinutesViewer. Recent meetings publish BOTH a tally-only 'Recap' and the full 'Minutes' behind a JS document selector; the build resolves to the full Minutes and drops every Recap. Mayor is non-voting except one 2024-10-15 tie-break (recorded as a plain Aye). 3 broken Granicus docs (299-byte stubs) logged in minutes_unrecovered.csv."},
            "planning_commission": {
                "institution": "Draper City Planning Division",
                "portal": "Granicus (draper.granicus.com, ViewPublisher view_id=1)",
                "note": "Draper runs its own Planning Commission (Thursday); named Yes/No/Abstained/Not-Participating/Absent grid; land-use motions cite case numbers YYYY-NNNN-<TYPE>."},
            "public_comments": {
                "institution": "-",
                "portal": "-",
                "note": "Draper publishes no written public comments - comment is in-person / email (public.comment@draper.ut.us), submit-only and not archived (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "Filtered from the canonical Salt Lake County results; 2019 general + 2021 general recovered from raw SOVC. NOTE: the canonical long file undercounts 2025 Draper (dropped Utah-vintage 25DR0N precinct labels) - Draper's races here are re-parsed from raw SOVC and reconcile to the certified totals (see TODO.md)."},
        },
    },
    "riverton": {
        "name": "Riverton",
        "preamble": (
            "Civic records of the Riverton City Council and Planning Commission, "
            "2020-present, plus municipal election results back to 2007. Minutes are "
            "published on the city's Granicus portal and mirrored on Utah Public "
            "Notice (the machine-readable spine used here). Riverton is governed by 5 "
            "district councilmembers + a separately-elected Mayor who is NON-voting "
            "except to break ties (the Park City model). Riverton publishes no written "
            "public-comment compilations (comment is in-person/eComment, submit-only). "
            "Election results are produced by the Salt Lake County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Riverton City Recorder",
                "portal": "Utah Public Notice (utah.gov/pmn; council + PC body 5473) mirroring the city's Granicus archive (rivertoncity.granicus.com)",
                "note": "Born-digital text PDFs. Named roll-call votes. The Mayor is non-voting on ordinary motions (max council roll = 5) EXCEPT tie-breaks, captured as the 'Aye (Mayor tie-break)' vocabulary extension (1 row, 2025-12-16, Mayor Staggs). The city's Revize CMS lists dates only; acquisition is via PMN/Granicus."},
            "planning_commission": {
                "institution": "Riverton City Planning Division",
                "portal": "Utah Public Notice (utah.gov/pmn; body 5473) / Granicus",
                "note": "Riverton runs its own Planning Commission (2nd & 4th Thursday); prints a full named roll call on DIVIDED votes and 'unanimous consent' (unnamed placeholder) on unanimous ones - the honest tally-only convention."},
            "public_comments": {
                "institution": "-",
                "portal": "-",
                "note": "Riverton publishes no written public comments - comment is in-person (paraphrased inline in minutes) / Granicus eComment, submit-only and not archived (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "Filtered from the canonical Salt Lake County results; 2019 general + 2021 general recovered from raw SOVC (2021 was method-split privacy-suppressed in the long file). NOTE the D3<->D4 renumber by 2022 Ord 22-07 - person<->district joins across 2022 must not assume stable numbers (see election_results/CLAUDE.md)."},
        },
    },
    "alta": {
        "name": "Alta",
        "preamble": (
            "Civic records of the Town of Alta (~380 residents, a Little Cottonwood "
            "Canyon ski-resort town) Town Council and Planning Commission, 2020-present, "
            "plus municipal election results. Alta uses Utah's Town form: 4 at-large "
            "councilmembers + a VOTING Mayor (max council roll = 5). Minutes are "
            "enumerated via Utah Public Notice (council body 1601, PC body 1602). Alta "
            "publishes no written public-comment archive (submit-only). Election results "
            "are produced by the Salt Lake County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Alta Town Clerk",
                "portal": "Utah Public Notice (utah.gov/pmn; council body 1601)",
                "note": "Born-digital text PDFs. Named per-member roll calls INCLUDING the Mayor (Town form - the mayor votes; max tally 5). Sparse by design: the Town Council meets monthly (2nd Wednesday, ~12/yr). Advisory Budget/Capital committee minutes are excluded (not the Town Council body)."},
            "planning_commission": {
                "institution": "Alta Planning Commission",
                "portal": "Utah Public Notice (utah.gov/pmn; body 1602)",
                "note": "Alta's Planning Commission (Land Use Authority) meets 4th Wednesday AS-NEEDED (often cancelled) - thin but real (17 docs 2022-06 -> 2025-12; none 2020-2021). Votes are tally-only in this era."},
            "public_comments": {
                "institution": "-",
                "portal": "-",
                "note": "Alta publishes no written public comments - comment is in-person / submit-only, not archived (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "Filtered from the canonical Salt Lake County results - genuine Town-of-Alta contests only (COUNCIL AT LARGE + ALTA MAYOR); the ALTA CANYON RECREATION special-service-district contests are EXCLUDED (not the Town). At-large multi-seat races."},
        },
    },
    "midvale": {
        "name": "Midvale",
        "preamble": (
            "Civic records of the Midvale City Council (with in-session RDA sessions) "
            "and Planning Commission, 2020-present, plus municipal election results "
            "back to 2007. Minutes are published on the city's Revize Document Center "
            "(midvale.utah.gov). Midvale uses Utah's six-member council form: 5 district "
            "councilmembers legislate and the Mayor votes only to break ties (max "
            "ordinary council roll = 5). Midvale publishes no written public-comment "
            "compilations (submit-only). Election results are produced by the Salt Lake "
            "County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Midvale City Recorder",
                "portal": "Revize Document Center (midvale.utah.gov)",
                "note": "Born-digital text PDFs 2022+, but the 2020-2021 council minutes are SCANNED image PDFs recovered via OCR (format=ocr; recon's 'born-digital' claim held only for recent years). Named tabular roll calls. The council also convenes in-session as the RDA (body=RDA). Mayor votes only on ties (max ordinary roll = 5)."},
            "planning_commission": {
                "institution": "Midvale City Planning Division",
                "portal": "Revize Document Center (midvale.utah.gov)",
                "note": "Midvale runs its own Planning & Zoning Commission (2nd & 4th Wednesday); mix of born-digital text and OCR'd scans. One 2020 PC doc had a corrupt source PDF (logged in minutes_unrecovered.csv)."},
            "public_comments": {
                "institution": "-",
                "portal": "-",
                "note": "Midvale publishes no written public comments - inline 'Public Comments' speaker notes in minutes; submit-only, not archived (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "Filtered from the canonical Salt Lake County results; 2019 general recovered from raw SOVC. A 2023 bond question is kept out of the council/mayor races file."},
        },
    },
    "cottonwood_heights": {
        "name": "Cottonwood Heights",
        "preamble": (
            "Civic records of the Cottonwood Heights City Council (with in-session CDRA "
            "sessions) and Planning Commission, 2020-present, plus municipal election "
            "results back to 2009 (incorporated 2005). Minutes are published on the "
            "city's Granicus/CivicEngage portal, whose rolling ~5-year window was "
            "backfilled from Utah Public Notice. 4 district councilmembers + a "
            "separately-elected VOTING Mayor (max council roll = 5). Cottonwood Heights "
            "publishes no written public-comment compilations (submit-only). Election "
            "results are produced by the Salt Lake County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Cottonwood Heights City Recorder",
                "portal": "Granicus/CivicEngage (cottonwoodheights.utah.gov) unioned with Utah Public Notice (council body 2147)",
                "note": "Born-digital text PDFs (+ a few .docx). The CivicEngage portal only retains ~5 years (2022 column decayed to 4 docs), so 2020-2024 was backfilled from PMN. The MAYOR VOTES (max council roll = 5: 4 districts + mayor). Council also convenes in-session as the CDRA (Community Development & Renewal Agency; body=CDRA)."},
            "planning_commission": {
                "institution": "Cottonwood Heights Planning Division",
                "portal": "Granicus/CivicEngage (cottonwoodheights.utah.gov) + Utah Public Notice (body 2148)",
                "note": "Cottonwood Heights runs its own Planning Commission (Wednesday); born-digital text. Administrative-hearing-officer sessions carry no roll-call votes (legitimate 0-motion files)."},
            "public_comments": {
                "institution": "-",
                "portal": "-",
                "note": "Cottonwood Heights publishes no written public comments - eComment submission form + emailed to the City Recorder + inline hearing speaker notes; submit-only, not archived (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "Filtered from the canonical Salt Lake County results; 2011 & 2019 recovered from raw SOVC, 2021 re-parsed for privacy suppression. Parks & Rec Service Area and Cottonwood Improvement Board contests are EXCLUDED (not the city)."},
        },
    },
    "holladay": {
        "name": "Holladay",
        "preamble": (
            "Civic records of the Holladay City Council (with in-session RDA and LBA "
            "sessions) and Planning Commission, 2020-present, plus municipal election "
            "results back to 2007 (incorporated 1999). Minutes are published on Utah "
            "Public Notice (council body 388, PC body 389). Holladay is Council-Manager: "
            "5 district councilmembers + a VOTING Mayor (max council roll = 6); the City "
            "Manager is the executive. Holladay publishes no written public-comment "
            "compilations (submit-only). Election results are produced by the Salt Lake "
            "County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Holladay City Recorder",
                "portal": "Utah Public Notice (utah.gov/pmn; council body 388); city Revize (holladayut.gov) + SuiteOne mirror",
                "note": "Born-digital text PDFs. The MAYOR VOTES (max council roll = 6). Two vote-grammar eras (2020-21 prose 'in favor'; 2022+ 'Name-Aye/Yes' - printed Yes/No normalized to Aye/Nay per SCHEMA_SPEC §4). Council also convenes in-session as the RDA and LBA (body=RDA / body=LBA). 25 honest gaps (retreats/pending) in minutes_unrecovered.csv."},
            "planning_commission": {
                "institution": "Holladay City Planning Division",
                "portal": "Utah Public Notice (utah.gov/pmn; body 389)",
                "note": "Holladay runs its own 7-member Planning Commission (Tuesday). NOTE: Holladay posts PC minutes to PMN only intermittently - 2026-07-16: the 2020 H1 + 2021 H1 PC minutes (27 docs) were recovered from the former cityofholladay.com WordPress site via Wayback and promoted (provenance=wayback_minutes); 2020 H2, 2021 H2 and all of 2023 remain genuine gaps (62 rows in minutes_unrecovered.csv; dead on PMN/Revize/SuiteOne/Wayback)."},
            "public_comments": {
                "institution": "-",
                "portal": "-",
                "note": "Holladay publishes no written public comments - emailed comments are read aloud + paraphrased inline; no eComment portal, no correspondence archive; submit-only (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "Filtered from the canonical Salt Lake County results; 2019 general recovered from raw SOVC (HOL Council sheets), 2021 re-parsed for privacy suppression. Cycle A = Mayor+D1+D3, Cycle B = D2/D4/D5."},
        },
    },
    "south_salt_lake": {
        "name": "South Salt Lake",
        "preamble": (
            "Civic records of the South Salt Lake City Council (with a separate "
            "Redevelopment Agency) and Planning Commission, plus municipal election "
            "results back to 2007. Minutes come from Utah Public Notice (council body "
            "1295, RDA 1296, PC 1297). South Salt Lake is a strong-mayor city: a "
            "7-member council (5 districts + 2 at-large) legislates and the executive "
            "Mayor does NOT vote (max council roll = 7). South Salt Lake publishes no "
            "written public-comment archive (submit-only). Election results are produced "
            "by the Salt Lake County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "South Salt Lake City Recorder",
                "portal": "Utah Public Notice (utah.gov/pmn; council body 1295, RDA body 1296)",
                "note": "⚠ COVERAGE: the PMN 'Meeting Minutes' slot usually serves the AGENDA PACKET (no roll call), even for files labelled '...RC Minutes.pdf' - real recorded minutes were content-detected by roll-call grammar. The city posts RECORDED council minutes essentially only for 2020-early-2021 plus sporadic recent meetings; 2021-mid through 2025 it published agenda packets only (253 agenda-only gaps logged in minutes_unrecovered.csv - an HONEST publication gap, not a scraper miss). The council also convenes as a separate RDA (body=RDA). Mayor is non-voting (max roll 7). SSL prints no result string, so `result` is a synthesized <aye>-<nay> tally."},
            "planning_commission": {
                "institution": "South Salt Lake Planning Division",
                "portal": "Utah Public Notice (utah.gov/pmn; body 1297)",
                "note": "South Salt Lake runs its own Planning Commission (up to 8 commissioners). Recorded PC minutes begin 2023-01-19 (2020-2022 were never published as minutes - agendas only)."},
            "public_comments": {
                "institution": "-",
                "portal": "-",
                "note": "South Salt Lake publishes no written public comments - in-person + Zoom + connect@sslc.gov; submit-only, not archived (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "Filtered from the canonical Salt Lake County results; 2011 & 2019 recovered from raw SOVC, 2021 re-parsed for privacy suppression. 5 districts + 2 At-Large + Mayor; a 2025 off-cycle At-Large 2-year special (deWolfe)."},
        },
    },
    "bluffdale": {
        "name": "Bluffdale",
        "preamble": (
            "Civic records of the Bluffdale City Council (with in-session RDA and LBA "
            "sessions) and Planning Commission, 2020-present, plus municipal election "
            "results back to 2007. Minutes are published on the city's CivicPlus/"
            "CivicEngage AgendaCenter (bluffdale.gov). Bluffdale is a 5 at-large council "
            "+ Mayor; the Mayor is non-voting in the Council (max member tally = 5) except "
            "rare tie-breaks, but votes as Chair in the in-session RDA/LBA (max 6). "
            "Bluffdale straddles Salt Lake (primary) + Utah (unpopulated Camp Williams) "
            "counties; Salt Lake County administers the whole election. Bluffdale "
            "publishes no written public-comment archive (submit-only)."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Bluffdale City Recorder",
                "portal": "CivicPlus/CivicEngage AgendaCenter (bluffdale.gov, CID=2 council)",
                "note": "Mix of born-digital text PDFs, 2 .docx, and scanned PDFs recovered via OCR (only 29 of 166 council docs needed OCR - recon overstated the scan rate; format=ocr where used). Full named roll calls. The council convenes in-session as the RDA and LBA (body=RDA / body=LBA), where the Mayor votes as Chair; in the pure Council body the Mayor is non-voting except 2 recorded tie-breaks."},
            "planning_commission": {
                "institution": "Bluffdale City Planning Division",
                "portal": "CivicPlus/CivicEngage AgendaCenter (bluffdale.gov, CID=3)",
                "note": "Bluffdale runs its own Planning Commission (1st & 3rd Wednesday); mix of born-digital and OCR'd scans. One 2025-10-15 PC tally is OCR-garbled (printed 4-2 vs counted 3-1) and surfaced honestly, not patched."},
            "public_comments": {
                "institution": "-",
                "portal": "-",
                "note": "Bluffdale publishes no written public comments - emailed comments (councilmeetingcomment@bluffdale.gov) are submitted but NOT read at the meeting and not posted; submit-only (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "Filtered from the canonical Salt Lake County results; 2019 recovered from raw SOVC. At-large multi-seat races. 2021 was the Utah RCV pilot (2-seat ranked-choice; take winners Aston seat-1 + Crockett seat-2 from the canvass, NOT first-choice rank)."},
        },
    },
    "white_city": {
        "name": "White City",
        "preamble": (
            "Civic records of the White City Council and its MSD-staffed Planning "
            "Commission from 2018 (earliest published minutes; incorporated as a metro "
            "township 2017, converted to a CITY 2024-05-01 under Utah H.B. 35), plus "
            "municipal election results. Council minutes are published on the city's "
            "Streamline CMS (whitecity.utah.gov), mirrored on Utah PMN (body 5805); PC "
            "minutes exist only on PMN (body 5879). White City is a "
            "5-member at-large body; the presiding Chair (township era) / directly-elected "
            "Mayor (city era, 2026+) VOTES (max tally 5). White City publishes no written "
            "public-comment archive (submit-only). Election results are produced by the "
            "Salt Lake County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "White City Recorder",
                "portal": "Streamline CMS (whitecity.utah.gov); Utah PMN body 5805 fallback",
                "note": "Born-digital text PDFs (12 mid/late-2024 minutes were image-only scans recovered via OCR; format=ocr). Three vote-grammar eras across the ~Jan-2026 seam: narrative-tally (2018-2025), narrative-named-dissent (2020-2022), and full named roll calls (2026+). The Chair/Mayor votes in every era (max tally 5). 2017 is agenda-only (no minutes published)."},
            "planning_commission": {
                "institution": "White City Planning Commission (MSD-staffed; minuted by Greater Salt Lake MSD Planning & Development Services)",
                "portal": "Utah Public Notice (utah.gov/pmn; PC body 5879)",
                "note": "RECOVERED FROM PMN BODY 5879 (promoted 2026-07-16): the Streamline site publishes no PC minutes, but PMN carries a sporadic MSD 'MEETING MINUTE SUMMARY' series - 22 minutes docs 2019-01-29 -> 2025-05-20 (106 motions, provenance=pmn_minutes). MSD narrative-tally style: only mover/seconder (+ a named abstainer) are named; unanimous rolls are tally-only placeholders; hearing open/close/adjourn motions print no outcome (empty result = honest NULL). Land-use cases keyed OAM/EXP/WVR + county file #. The series is sporadic: 28 further PC dates were noticed with agendas but no minutes were ever posted (minutes_unrecovered.csv); many other months the PC simply cancelled."},
            "public_comments": {
                "institution": "-",
                "portal": "-",
                "note": "White City publishes no written public comments - in-meeting speaker input only, no eComment portal; submit-only (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "Filtered from the canonical Salt Lake County results; 2019 metro-township council recovered from raw SOVC. 2017 & 2021 are genuine no-election years (initial council elected Nov-2016; some seats filled uncontested). The White City Water Improvement District + 2015 MSD/incorporation ballot questions are EXCLUDED (not the city)."},
        },
    },
    "kearns": {
        "name": "Kearns",
        "preamble": (
            "Civic records of the Kearns City Council (formerly Metro Township) and its "
            "MSD-staffed Planning Commission, plus municipal election results. Kearns was "
            "a metro township 2017-2024, converted to a CITY 2024-05-01 (Utah H.B. 35); "
            "the first city election was Nov 2025 (Mayor Jesse Valdez, Utah's first "
            "Hispanic mayor). City-era: directly-elected Mayor who VOTES + 4 district "
            "councilmembers (max council roll = 5). Minutes are on Utah PMN (the city site "
            "is Cloudflare-blocked). Kearns publishes no written public-comment archive "
            "(submit-only). Election results are produced by the Salt Lake County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Kearns City Recorder (via Greater Salt Lake MSD)",
                "portal": "Utah Public Notice (utah.gov/pmn; council body 5823)",
                "note": "COVERAGE: written 'Meeting Minutes' ARE published to PMN body 5823 across the township era; the 2026-07-12 backfill harvested them, so council minutes now run 2018-07-09 -> 2026 (85 township-era docs + 32 city-era). Format: OCR for scanned minutes, text for born-digital (incl. 2 .docx via textutil). REMAINING GAPS (minutes_unrecovered.csv, 41 rows): 25 township meetings (2017-01 -> 2018-06) whose 'Meeting Minutes' attachment WAS published but whose file blob has been purged from PMN's pre-~July-2018 file store (file_id<~450000 now 404; notice link is stale; not on the Internet Archive either); 7 township meetings that posted only an agenda + MP3 audio (no minutes ever published); 9 recent meetings not yet approved/posted. Votes are narrative-tally (unanimous rolls unnamed/tally-only; abstainers named), EXCEPT some 2018-2023 minutes print a full named roll call - those per-member Ayes/Nays are captured verbatim. City-era Mayor votes (max 5). A CRA convenes in-recess (referenced in docs) but its own PMN body is separate/un-acquired (0 CRA rows)."},
            "planning_commission": {
                "institution": "Greater Salt Lake MSD Planning & Development (for Kearns)",
                "portal": "Utah Public Notice (utah.gov/pmn; body 1561)",
                "note": "Kearns' Planning Commission is MSD-administered; approved-minutes PDFs begin 2019-03 (2017-2018 posted agendas only). Land-use cases keyed OAM<YYYY>-<NNNNNN>; recommends to Council. Born-digital."},
            "public_comments": {
                "institution": "-",
                "portal": "-",
                "note": "Kearns publishes no written public comments - in-meeting 3-min input + email to the MSD recorder; submit-only, not archived (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "⚠ Parsed from RAW SOVC by content - the canonical slco_municipal_results_long.csv is CORRUPTED for Kearns (2019 dropped entirely; the 2025 SheetNN->contest mapping merged OTHER municipalities' candidates under 'CITY OF KEARNS MAYOR'). kearns_races.csv is authoritative; the county-grain election_result tag for Kearns is unreliable (see TODO.md). Oquirrh Park / Improvement District / MSD decoys excluded."},
        },
    },
    "magna": {
        "name": "Magna",
        "preamble": (
            "Civic records of the Magna City Council (with in-recess CRA sessions) and its "
            "MSD-staffed Planning Commission, 2017-present, plus municipal election results. "
            "Magna was a metro township 2017-2024, converted to a CITY 2024-05-01 (Utah H.B. "
            "35). 5 district councilmembers. Across the seam the presiding officer's vote "
            "flips: the township-era elected Chair (titled 'Mayor') VOTED, but the 2026+ "
            "directly-elected executive Mayor (Mick Sudbury) does NOT vote (max council roll "
            "= 5 both eras). Minutes are on CivicPlus (2022+) and Utah PMN (2017-2021). Magna "
            "publishes no written public-comment archive (submit-only). Election results are "
            "produced by the Salt Lake County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Magna City Recorder",
                "portal": "CivicPlus AgendaCenter (magna.utah.gov, catID 3) + Utah PMN body 5803 (2017-2021 archive)",
                "note": "Born-digital text PDFs (2024 Apr-Dec + early 2025 signed-scan minutes were image-only, OCR'd; format=pdf-ocr). Narrative-tally votes. The Chair-titled-'Mayor' votes pre-2026; the exec Mayor Sudbury does not vote 2026+ (max 5). Council also convenes in-recess as the CRA ('Board Member' roles; body=CRA). ⚠ CivicPlus sometimes serves wrong docs in the Minutes slot (agendas/spreadsheets/correspondence) - recovered real minutes from PMN where possible. 2017 + Jan-Jun 2018 council minutes (36 mtgs) are 404-unrecoverable on PMN (logged in minutes_unrecovered.csv)."},
            "planning_commission": {
                "institution": "Greater Salt Lake MSD Planning & Development (for Magna)",
                "portal": "Utah Public Notice (utah.gov/pmn; body 1559)",
                "note": "Magna's Planning Commission is MSD-staffed; minutes begin 2019 (2017-2018 posted agendas only, 57 logged). Rezones keyed REZ####; recommends to Council. Born-digital."},
            "public_comments": {
                "institution": "-",
                "portal": "-",
                "note": "Magna publishes no written public comments - in-person sign-up sheet + QR-to-staff; no eComment portal; PMN posts audio only; submit-only (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "Filtered from the canonical Salt Lake County results; the 2016 founding election + 2019 D1/D3/D5 recovered from raw SOVC, 2021 re-parsed for suppression; the 2025 primary/general split. The Magna Water District (all variants) + MSD + 2015 incorporation ballot questions are EXCLUDED (~95% of raw 'magna' rows are the Water District)."},
        },
    },
    "copperton": {
        "name": "Copperton",
        "preamble": (
            "Civic records of the Town of Copperton Council (~800 residents) and its "
            "(mostly-cancelled) Planning Commission, plus municipal election results. "
            "Copperton was a metro township 2017-2024, converted to a TOWN 2024-05-01 "
            "(Utah H.B. 35). 5 at-large seats; the Mayor/Chair VOTES in both eras (max "
            "tally 5). Minutes are on the town's GoDaddy site + Utah PMN (council body "
            "5831, PC body 1560). Copperton publishes no written public-comment archive "
            "(submit-only). Election results are produced by the Salt Lake County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Town of Copperton Recorder",
                "portal": "copperton.utah.gov (GoDaddy, curl -k for the TLS mismatch) + Utah PMN body 5831",
                "note": "Born-digital text PDFs (14 town-era 2024-2025 minutes were RICOH scans, OCR'd; format=ocr). Narrative-tally votes (mover+seconder named, collective tally; per-member roll calls rare). The Mayor/Chair votes in both eras (max 5). ⚠ 2017-02 -> 2018-06 council minutes are 404-PURGED from PMN (retention window) and predate the GoDaddy site (2023+) - 29 meetings logged in minutes_unrecovered.csv."},
            "planning_commission": {
                "institution": "Town of Copperton Planning Commission (MSD-supported)",
                "portal": "Utah Public Notice (utah.gov/pmn; body 1560)",
                "note": "Copperton's PC is nominal - most scheduled meetings are CANCELLED (tiny land-use volume); 18 minutes docs 2019-2025, tally-only/mover-only, no mayor. Thin by design."},
            "public_comments": {
                "institution": "-",
                "portal": "-",
                "note": "Copperton publishes no written public comments - in-person 'Community Input' + inline speaker notes; submit-only (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "Filtered from the canonical Salt Lake County results; at-large seats A-E (2017/2021/2023). 2019 council absent from the county archive; the 2025 first-Mayor race (Clayton unopposed) was NOT tabulated by the county (all seats unopposed). Copperton MSD / Improvement-District / 2015 ballot questions EXCLUDED."},
        },
    },
    "emigration_canyon": {
        "name": "Emigration Canyon",
        "preamble": (
            "Civic records of the Emigration Canyon City Council and its Planning "
            "Commission, plus municipal election results. Emigration Canyon was a metro "
            "township 2017-2024, converted to a CITY 2024-05-01 (Utah H.B. 35). 5 "
            "at-large councilmembers; the Mayor is peer-selected (Smolka township -> "
            "Brems city) and PRESIDES AND VOTES (Millcreek pattern, max tally 5). Minutes "
            "are on Utah PMN (council body 5809, PC body 1562) - there is no separate city "
            "CMS. Emigration Canyon publishes no written public-comment archive (submit-only). "
            "Election results are produced by the Salt Lake County Clerk."),
        "datasets": {
            "meeting_minutes": {
                "institution": "Emigration Canyon City Recorder (via Greater Salt Lake MSD)",
                "portal": "Utah Public Notice (utah.gov/pmn; council body 5809)",
                "note": "Born-digital text PDFs (DocuSign-signed; 7 scanned council docs OCR'd, 2 of which yielded 0 motions - OCR-quality gap, born-digital re-fetch is a TODO). Narrative-tally votes; the peer-selected Mayor votes (max 5). ⚠ PMN purged its 2017 (+ scattered 2018-19) file store (404) - recovered coverage begins 2018-10 (council) / 2018-11 (PC); logged in minutes_unrecovered.csv."},
            "planning_commission": {
                "institution": "Emigration Canyon Planning Commission",
                "portal": "Utah Public Notice (utah.gov/pmn; body 1562)",
                "note": "Emigration Canyon runs its own Planning Commission (monthly); structured Motion/Vote grammar; land-use recommendations to Council. Born-digital; coverage from 2018-11."},
            "public_comments": {
                "institution": "-",
                "portal": "-",
                "note": "Emigration Canyon publishes no written public comments - in-person/Zoom + email/phone; minutes paraphrase speakers only; submit-only (see public_comments/AVAILABILITY.md)."},
            "election_results": {
                "institution": "Salt Lake County Clerk (Elections Division)",
                "portal": "saltlakecounty.gov/clerk/elections/election-results",
                "note": "Filtered from the canonical Salt Lake County results; at-large seats (2017/2023/2025). The mayor is council-selected (no separate mayor contest). The Emigration Improvement District (sewer) + 2015 MSD/incorporation ballot questions are EXCLUDED. 2019/2021 had no council contest; the 2016 founding election is even-year (outside the municipal archive)."},
        },
    },
}

# ---------------------------------------------------------------------------
# Election adapter config: never invent URLs. 'overrides' are file->URL mappings
# explicitly stated in the city's election docs; 'fallbacks' are (glob, office
# label) pairs — the label goes into source_url as "unrecorded (<office>)".
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Verified SL County Clerk source URLs (probed + byte/content-verified 2026-07-19;
# each per-year SOVC below returned HTTP 200 and was confirmed md5-identical to the
# copy retained under the relevant city's election_results/raw/ — the 2016 file's
# .zip unpacks to the byte-identical inner xlsx). The multi-year city long-slices are
# derived from the county canonical (salt_lake_county/elections/), whose own public
# source is the Clerk's election-results page (_SLCO_LAND).
# ---------------------------------------------------------------------------
_SLCO_LAND = "https://www.saltlakecounty.gov/clerk/elections/election-results/"
_SLCO_GA = "https://www.saltlakecounty.gov/globalassets/1-site-files/clerk/elections/election-results"
_SLCO_HIST = f"{_SLCO_GA}/historical-election-results"
SLCO_SOVC = {
    # -- byte-verified 2026-07-19 (prior pass): each returned HTTP 200 and is md5/sha256
    # identical to the retained raw copy (the 2016 .zip unpacks to a byte-identical inner
    # xlsx).
    "2011-11-08-municipal-general-sovc.xlsx": f"{_SLCO_HIST}/2011-11-08-municipal-general-sovc.xlsx",
    "2011-09-13-municipal-primary-sovc.xlsx": f"{_SLCO_HIST}/2011-09-13-municipal-primary-sovc.xlsx",
    "2016-11-08-general-election-sovc.xlsx": f"{_SLCO_HIST}/2016-11-08-general-election-statement-of-votes-cast.zip",
    "2019-11-05-general-election-sovc.xlsx": f"{_SLCO_HIST}/2019-11-05-general-election-sovc.xlsx",
    "2019-08-13-municipal-primary-sovc.xlsx": f"{_SLCO_HIST}/2019-08-13-municipal-primary-sovc.xlsx",
    "2021-11-02-general-election-sovc.xlsx": f"{_SLCO_GA}/2021/november-2-2021-general-election-statement-of-votes-cast.xlsx",
    "november-2-2021-general-election-statement-of-votes-cast.xlsx": f"{_SLCO_GA}/2021/november-2-2021-general-election-statement-of-votes-cast.xlsx",
    "2025-11-04-general-election-sovc.xlsx": f"{_SLCO_GA}/2025-general-election-statementofvotescastrpt.xlsx",
    "2025-08-12-primary-election-sovc.xlsx": f"{_SLCO_GA}/final_official_statementofvotescastrpt_20250826.xlsx",
    # -- byte-verified 2026-07-20 (this pass, P4 URL residue): the pre-2019 historical
    # SOVC (only South Jordan retains them) + the 2023 general, each sha256-matched to the
    # county-mirror download_log (raw .xls/.xlsx served directly; the 2015-general and
    # 2017 primary/general are served as .zip whose inner xlsx is sha256-identical to the
    # retained copy). All returned HTTP 200/206 live 2026-07-20.
    "2007-11-06-municipal-general-sovc.xls": f"{_SLCO_HIST}/2007-11-06-municipal-general-sovc.xls",
    "2009-09-15-municipal-primary-sovc.xls": f"{_SLCO_HIST}/2009-09-15-municipal-primary-sovc.xls",
    "2009-11-03-municipal-general-sovc.xls": f"{_SLCO_HIST}/2009-11-03-municipal-general-sovc.xls",
    "2013-08-13-municipal-primary-sovc.xlsx": f"{_SLCO_HIST}/2013-08-13-municipal-primary-sovc.xlsx",
    "2013-11-05-municipal-general-sovc.xlsx": f"{_SLCO_HIST}/2013-11-05-municipal-general-sovc.xlsx",
    "2015-08-11-municipal-primary-sovc.xlsx": f"{_SLCO_HIST}/2015-08-11-municipal-primary-sovc.xlsx",
    "2015-11-03-municipal-general-sovc.xlsx": f"{_SLCO_HIST}/2015-11-03-municipal-general-election-statement-of-votes-cast.zip",
    "2017-08-15-municipal-primary-sovc.xlsx": f"{_SLCO_HIST}/2017-08-15-primary-election-statement-of-votes-cast.zip",
    "2017-11-07-municipal-general-sovc.xlsx": f"{_SLCO_HIST}/2017-11-07-general-election-statement-of-votes-cast.zip",
    "2023-11-21-general-election-sovc.xlsx": f"{_SLCO_GA}/2023/statementofvotescastrpt-official-report-12-05-2023-5.22pm.xlsx",
}

ELECTION_CFG = {
    "lehi": {
        # Utah County files md5-verified byte-identical to the vote.utahcounty.gov CDN
        # (2026-07-19); rcvis permalinks content-verified (winner final-round total
        # identical to the stored HTML). ev_*.json are undocumented state-portal API
        # pulls with no durable archive URL.
        "overrides": {
            "uc_2019_general_precinct_SOVC.pdf": "https://vote.utahcounty.gov/cms/uploads/19_G_Countywide_Precinct_Official_Suppressed_c07b072cdf.pdf",
            "uc_2019_general_results.pdf": "https://vote.utahcounty.gov/cms/uploads/2019_General_Results_PDF_a69d246ddc.pdf",
            "uc_2021_general_SOVC.csv": "https://vote.utahcounty.gov/cms/uploads/21_G_Countywide_SOVC_suppressed_1b85ad469d.csv",
            "uc_2021_general_results.pdf": "https://vote.utahcounty.gov/cms/uploads/2021_General_PDF_4d36475691.pdf",
            "uc_2023_general_results.pdf": "https://vote.utahcounty.gov/cms/uploads/2023_General_voting_results_be47c5636c.pdf",
            "utahcounty_results_index_2019.html": "https://vote.utahcounty.gov/results/2019",
            "utahcounty_results_index_2021.html": "https://vote.utahcounty.gov/results/2021",
            "utahcounty_results_index_2023.html": "https://vote.utahcounty.gov/results/2023",
            "rcvis_2021_council_seat1_condie.html": "https://www.rcvis.com/v/21g_le_cc_1_u4",
            "rcvis_2021_council_seat2_hancock.html": "https://www.rcvis.com/v/21g_le_cc_2_u2",
            "rcvis_2023_council_primary_astill.html": "https://www.rcvis.com/v/2023-lehi-city-council-primary",
            "rcvis_2023_council_seat1_albrecht.html": "https://www.rcvis.com/v/2023-lehi-city-council",
            "rcvis_2023_council_fullfield_update.html": "https://www.rcvis.com/v/2023-lehi-city-council-3",
            "rcvis_2023_council_seat3_newall.html": "https://www.rcvis.com/v/2023-lehi-city-council-2",
        },
        "fallbacks": [
            ("ev_*.json", "verified-no-stable-archive (Utah state Enhanced Voting portal electionresults.utah.gov, utah-county-ut API — dynamic SPA / undocumented unofficial live API, no durable archive URL; checked 2026-07-19)"),
        ],
        "default": "Utah County Clerk",
    },
    "logan": {
        # Cache County publishes each result set at a stable named .html endpoint that
        # 301-redirects to the results PDF; all 5 content-verified 2026-07-19 to serve
        # the matching Logan council/mayor canvass. The 2019/2021 city-administered
        # official PDFs have no surviving stable loganutah.gov URL; ev-* = state portal.
        "overrides": {
            "cache-2021-municipal-general-results.pdf": "https://www.cachecounty.gov/elections/election-results/2021municipalgeneralresults.html",
            "cache-2021-municipal-primary-results.pdf": "https://www.cachecounty.gov/elections/election-results/2021municipalprimaryresults.html",
            "cache-2023-nov-general-results.pdf": "https://www.cachecounty.gov/elections/election-results/2023novgeneralresults.html",
            "cache-2023-nov-general-details.pdf": "https://www.cachecounty.gov/elections/election-results/2023-nov-general-details.html",
            "cache-2023-primary-results.pdf": "https://www.cachecounty.gov/elections/election-results/2023-primary-results.html",
        },
        "fallbacks": [
            ("logan-*", "verified-no-stable-archive (Logan City Recorder — city-administered 2019/2021 municipal elections; official PDFs no longer at a stable loganutah.gov URL; checked 2026-07-19)"),
            ("ev-*", "verified-no-stable-archive (Utah state Enhanced Voting portal electionresults.utah.gov — dynamic SPA / undocumented unofficial live API, no durable archive URL; checked 2026-07-19)"),
        ],
        "default": "Cache County Clerk / Logan City Recorder",
    },
    "nephi": {
        "overrides": {
            "deseret-2019-utah-municipal-general-results.html":
                "https://www.deseret.com/utah/2019/11/6/20951150/utah-2019-election-results-general-municipal/",
            "midutahradio-2021-municipal-election-results.html":
                "https://midutahradio.com/news/local-news/unofficial-2021-municipal-election-results/",
            "juabcounty-election-results-index.html":
                "https://juabcounty.gov/residents/election-information/election-results/",
        },
        # ev-juab-*.json were pulled from the undocumented state-portal API (no durable
        # archive URL). The equivalent official Juab County 2023 canvass PDFs DO exist
        # and were content-verified 2026-07-19 (Nephi City Council present) — recorded
        # in election_results/CLAUDE.md.
        "fallbacks": [
            ("ev-*", "verified-no-stable-archive (Utah state Enhanced Voting portal electionresults.utah.gov, juab-county-ut API — dynamic SPA / undocumented unofficial live API; official Juab County 2023 canvass PDFs recorded in election_results/CLAUDE.md; checked 2026-07-19)"),
        ],
        "default": "Juab County Clerk",
    },
    "ogden": {
        # 4 files md5-verified byte-identical to the Weber Elections Wix asset store
        # (weberelections.gov/_files/ugd/…, which 301-redirects to filesusr.com) on
        # 2026-07-19. The remaining Weber PDFs could not be matched to an opaque Wix
        # asset hash, and state_api/* are undocumented state-portal API pulls.
        "overrides": {
            "2019_general_results.pdf": "https://www.weberelections.gov/_files/ugd/7e3a53_23ef3f3f90864dfa9f4ddc93a9363215.pdf",
            "2021_general_b.pdf": "https://www.weberelections.gov/_files/ugd/7dc173_05b2df57deb54c439e8964cd6184e90c.pdf",
            "2025_general_summary.pdf": "https://www.weberelections.gov/_files/ugd/92078f_ba3a3d05a36449399444d85e915efa14.pdf",
            "2025_general_precinct.pdf": "https://www.weberelections.gov/_files/ugd/92078f_dc2ffea70dfb409aa3f2b615a678de4b.pdf",
        },
        "fallbacks": [
            ("state_api/*", "verified-no-stable-archive (Utah state Enhanced Voting portal electionresults.utah.gov — dynamic SPA / undocumented unofficial live API, no durable archive URL; checked 2026-07-19)"),
            ("*", "verified-no-stable-archive (Weber County Elections, weberelections.gov — file served from an opaque Wix asset URL that could not be matched to this stored copy; checked 2026-07-19)"),
        ],
        "default": "Weber County Elections",
    },
    "orem": {
        "fallbacks": [("*", "Utah County Clerk results portal, vote.utahcounty.gov")],
        "default": "Utah County Clerk",
    },
    "park_city": {
        "overrides": {
            "parkcity_election_results_page_2026-06-26.html":
                "https://www.parkcity.gov/government/elections/election_results.php",
        },
        # The authoritative page (above) is stable and embeds the CURRENT results inline,
        # but Park City's Revize CMS reuses generic per-cycle PDF filenames ("Canvass
        # Resolution.pdf", "Votes by Precinct.pdf") that are overwritten each election, so
        # the historical canvass/precinct PDFs have no durable per-file archive URL
        # (verified 2026-07-19: the live election_results.php links no per-canvass PDFs;
        # the older files were renamed locally on capture).
        "fallbacks": [
            ("*", "verified-no-stable-archive (Park City Recorder / Summit County Clerk — city Revize CMS embeds results inline and reuses generic per-cycle PDF filenames overwritten each election; authoritative page https://www.parkcity.gov/government/elections/election_results.php; checked 2026-07-19)"),
        ],
        "default": "Park City Recorder",
    },
    "provo": {
        "fallbacks": [("*", "Utah County Clerk results portal, vote.utahcounty.gov")],
        "default": "Utah County Clerk",
    },
    "sandy": {
        # SOVC layer derives from the county canonical (the per-city raw SOVC copies were
        # retired 2026-07-19, proven byte-identical). The two 2021 RCV-pilot final-round
        # PDFs are NON-county-SOVC sources kept in raw/ and are sha256-identical (2026-07-20)
        # to the Salt Lake County Clerk's live 2021 RCV postings.
        "canonical_pointer": True,
        "overrides": {
            "2021-general-election-ranked-choice-summary-report.pdf": f"{_SLCO_GA}/2021/2021-general-election-ranked-choice-summary-report.pdf",
            "2021-general-election-sandy-recount-results.pdf": f"{_SLCO_GA}/2021/2021-general-election-sandy-recount-results.pdf",
        },
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive, saltlakecounty.gov/clerk/elections/election-results")],
        "default": "Salt Lake County Clerk",
    },
    "slc": {
        "canonical_pointer": True,
        "fallbacks": [("*", "Salt Lake County Clerk canvass export")],
        "default": "Salt Lake County Clerk",
    },
    "st_george": {
        # 10 of 13 files md5-verified byte-identical to the Washington County outpost
        # (outpost.washco.utah.gov) 2026-07-19; the 3 unresolved (2021 primary
        # precinct-summary, 2023 primary export + precinct) fall to the checked-gap note.
        "overrides": {
            "washco-2019-general-municipal-export.csv": "https://outpost.washco.utah.gov/apps/clerk/elections/2019/11/2019-general-municipal-export.csv",
            "washco-20210810-municipal-primary.csv": "https://outpost.washco.utah.gov/apps/clerk/elections/2021/08/washco_elections_20210810_OFFICIAL_municipal-primary.csv",
            "washco-20211102-results-export.csv": "https://outpost.washco.utah.gov/apps/clerk/elections/2021/11/washco-election-20211102-results-export.csv",
            "washco-20211102-results-precinct.pdf": "https://outpost.washco.utah.gov/apps/clerk/elections/2021/11/washco-election-20211102-results-precinct.pdf",
            "washco-20231121-results-export.csv": "https://outpost.washco.utah.gov/apps/clerk/elections/2023/11/washco-election-20231121-results-export.csv",
            "washco-20231121-results-precinct.pdf": "https://outpost.washco.utah.gov/apps/clerk/elections/2023/11/washco-election-20231121-results-precinct.pdf",
            "washco-20250812-results-export.csv": "https://outpost.washco.utah.gov/apps/clerk/elections/2025/08/washco-election-20250812-results-export.csv",
            "washco-20250812-results-precinct.pdf": "https://outpost.washco.utah.gov/apps/clerk/elections/2025/08/washco-election-20250812-results-precinct.pdf",
            "washco-20251104-results-export.csv": "https://outpost.washco.utah.gov/apps/clerk/elections/2025/11/washco-election-20251104-results-export.csv",
            "washco-20251104-results-precinct.pdf": "https://outpost.washco.utah.gov/apps/clerk/elections/2025/11/washco-election-20251104-results-precinct.pdf",
        },
        "fallbacks": [("*", "verified-no-stable-archive (Washington County Clerk, outpost.washco.utah.gov — 2021 primary precinct-summary + 2023 primary export/precinct exact archive paths not resolved; checked 2026-07-19)")],
        "default": "Washington County Clerk",
    },
    "vineyard": {
        # rcvis permalinks content-verified (winner final-round total identical to the
        # stored HTML, 2026-07-19). ev_*.json = undocumented state-portal API pulls.
        "overrides": {
            "rcvis_2019_seat1.html": "https://www.rcvis.com/v/vineyard-seat-1-updated-2019-11-19_11-20-30json",
            "rcvis_2019_seat2.html": "https://www.rcvis.com/v/vineyard-seat-2-2019-11-19_11-20-30_summary_2json",
            "rcvis_2021_mayor.html": "https://www.rcvis.com/v/21g_vi_m_u4",
            "rcvis_2021_seat1_sifuentes.html": "https://www.rcvis.com/v/21g_vi_cc_1_u4",
            "rcvis_2021_seat2_rasmussen.html": "https://www.rcvis.com/v/21g_vi_cc_2_u2",
            "rcvis_2023_cameron.html": "https://www.rcvis.com/v/2023-vineyard-city-council-7",
            "rcvis_2023_holdaway.html": "https://www.rcvis.com/v/2023-vineyard-city-council-6",
        },
        "fallbacks": [
            ("ev_*", "verified-no-stable-archive (Utah state Enhanced Voting portal electionresults.utah.gov, utah-county-ut API — dynamic SPA / undocumented unofficial live API, no durable archive URL; checked 2026-07-19)"),
        ],
        "default": "Utah County Clerk",
    },
    "west_jordan": {
        # Raw SOVC copies retired 2026-07-19 (byte-identical to the county canonical);
        # derives directly from salt_lake_county/elections/. SLCO_SOVC kept for any raw
        # that is re-added.
        "canonical_pointer": True,
        "overrides": {**SLCO_SOVC},
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (copied from local slco-election-archive mirror)")],
        "default": "Salt Lake County Clerk",
    },
    "west_valley": {
        "canonical_pointer": True,
        "overrides": {**SLCO_SOVC},
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (copied from local slco-election-archive mirror)")],
        "default": "Salt Lake County Clerk",
    },
    "south_jordan": {
        # Derives from the county canonical; ALSO retains the full raw SOVC set under
        # raw/sovc/ (2007-2025) for the suppression/sheet-code recovery years. Every
        # retained file's URL is byte-verified in SLCO_SOVC (2026-07-19/-20).
        "canonical_pointer": True,
        "overrides": {**SLCO_SOVC},
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (copied from local slco-election-archive mirror)")],
        "default": "Salt Lake County Clerk",
    },
    "millcreek": {
        "overrides": {**SLCO_SOVC, "municipal_results_long_millcreek.csv": _SLCO_LAND},
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (copied from local slco-election-archive mirror)")],
        "default": "Salt Lake County Clerk",
    },
    "taylorsville": {
        # Derives from the county canonical; retains raw/sovc/ 2019+2021 for the
        # District-recovery / suppression years (both byte-verified in SLCO_SOVC).
        "canonical_pointer": True,
        "overrides": {**SLCO_SOVC},
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (copied from local slco-election-archive mirror)")],
        "default": "Salt Lake County Clerk",
    },
    "murray": {
        "canonical_pointer": True,
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (filtered from the canonical county slco_municipal_results_long.csv)")],
        "default": "Salt Lake County Clerk",
    },
    "herriman": {
        "overrides": {**SLCO_SOVC, "municipal_results_long_herriman.csv": _SLCO_LAND},
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (filtered from the canonical county slco_municipal_results_long.csv; 2011/2019/2021 from raw SOVC)")],
        "default": "Salt Lake County Clerk",
    },
    "draper": {
        "overrides": {**SLCO_SOVC, "municipal_results_long_draper.csv": _SLCO_LAND},
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (filtered from the canonical county file; 2019/2021 + 2025 re-parsed from raw SOVC)")],
        "default": "Salt Lake County Clerk",
    },
    "riverton": {
        "overrides": {**SLCO_SOVC, "riverton_slco_results_long.csv": _SLCO_LAND},
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (filtered from the canonical county file; 2019 + 2021 recovered from raw SOVC)")],
        "default": "Salt Lake County Clerk",
    },
    "alta": {
        "canonical_pointer": True,
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (genuine Town-of-Alta council/mayor contests; Alta Canyon rec-district excluded)")],
        "default": "Salt Lake County Clerk",
    },
    "midvale": {
        "overrides": {**SLCO_SOVC, "municipal_results_long_midvale.csv": _SLCO_LAND},
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (filtered from the canonical county file; 2019 recovered from raw SOVC)")],
        "default": "Salt Lake County Clerk",
    },
    "cottonwood_heights": {
        "overrides": {**SLCO_SOVC,
                      "municipal_results_long_cottonwood_heights.csv": _SLCO_LAND,
                      "municipal_2011_general_cottonwood_heights.csv": SLCO_SOVC["2011-11-08-municipal-general-sovc.xlsx"]},
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (filtered from the canonical county file; 2011/2019 recovered + 2021 re-parsed from raw SOVC; Parks&Rec / Improvement-Board contests excluded)")],
        "default": "Salt Lake County Clerk",
    },
    "holladay": {
        "overrides": {**SLCO_SOVC},
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (filtered from the canonical county file; 2019 recovered + 2021 re-parsed from raw SOVC)")],
        "default": "Salt Lake County Clerk",
    },
    "south_salt_lake": {
        "overrides": {**SLCO_SOVC, "municipal_results_long_south_salt_lake.csv": _SLCO_LAND},
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (filtered from the canonical county file; 2011 & 2019 recovered + 2021 re-parsed from raw SOVC)")],
        "default": "Salt Lake County Clerk",
    },
    "bluffdale": {
        "overrides": {**SLCO_SOVC, "municipal_results_long_bluffdale.csv": _SLCO_LAND},
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (filtered from the canonical county file; 2019 recovered + 2021 RCV/suppression re-parsed from raw SOVC)")],
        "default": "Salt Lake County Clerk",
    },
    "white_city": {
        "overrides": {**SLCO_SOVC, "slco_municipal_results_white_city.csv": _SLCO_LAND},
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (2019 recovered from raw SOVC; 2017/2021 genuine no-election years; water-district decoys excluded)")],
        "default": "Salt Lake County Clerk",
    },
    "kearns": {
        # Kearns does NOT read the county canonical long file (it is corrupted for Kearns —
        # 2019 dropped, the 2025 sheet->contest mapping merges foreign candidates). Its
        # races are parsed BY CONTENT directly from the raw SLCo Clerk SOVC workbooks, so
        # the pointer records that provenance (the county Clerk election-results page) with
        # a Kearns-specific note rather than claiming the long file.
        "canonical_pointer": {
            "record_key": "slco_raw_sovc_workbooks_kearns",
            "title": "Salt Lake County Clerk raw SOVC workbooks (Kearns parsed by content; the canonical long file is corrupted for Kearns)",
            "local_path": "salt_lake_county/elections/raw/SOURCES.md",
            "source_url": _SLCO_LAND,
            "extraction_method": "parsed by content directly from the raw SLCo Clerk SOVC workbooks (clean_elections.py; the county canonical long file drops 2019 / merges foreign candidates for Kearns)",
            "processing_ref": "election_results/CLAUDE.md §sources (clean_elections.py; raw SOVC provenance: salt_lake_county/elections/raw/SOURCES.md)",
        },
        "fallbacks": [("*", "Salt Lake County Clerk raw SOVC workbooks (the canonical long file is corrupted for Kearns - 2019 dropped, 2025 sheet->contest mapping merged foreign candidates - so races were parsed from raw SOVC by content)")],
        "default": "Salt Lake County Clerk",
    },
    "magna": {
        "overrides": {**SLCO_SOVC, "municipal_results_long_magna.csv": _SLCO_LAND},
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (filtered from the canonical county file; 2016/2019 D1/D3/D5 + 2021 recovered from raw SOVC; Magna Water District / MSD decoys excluded)")],
        "default": "Salt Lake County Clerk",
    },
    "copperton": {
        "overrides": {**SLCO_SOVC, "municipal_results_long_copperton.csv": _SLCO_LAND},
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (2017/2021/2023 at-large council; Improvement-District / MSD decoys excluded; 2019 absent + 2025 unopposed-untabulated gaps)")],
        "default": "Salt Lake County Clerk",
    },
    "emigration_canyon": {
        "canonical_pointer": True,
        "fallbacks": [("*", "Salt Lake County Clerk election-results archive (2017/2023/2025 at-large council; Emigration Improvement District / MSD decoys excluded; 2019/2021 no council contest)")],
        "default": "Salt Lake County Clerk",
    },
}

DATASET_LABELS = {
    "meeting_minutes": "Council meeting minutes",
    "planning_commission": "Planning Commission minutes",
    "public_comments": "Public comments",
    "election_results": "Municipal election results",
    "packets": "Agenda packets / staff reports",
    "housing_plans": "Housing plans / general plan",
    "ordinances": "Ordinances (adoption record)",
    "pmn_backfill": "Utah Public Notice backfill",
    "transcripts": "Meeting-video transcripts",
    "campaign_finance": "Campaign-finance disclosures",
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def host_of(url):
    if url.startswith("http"):
        return urllib.parse.urlparse(url).netloc
    return ""


def norm_city_rel(path, dataset):
    """Normalize an index 'path' value to city-root-relative."""
    p = path.strip().lstrip("/")
    if not p:
        return ""
    for cdir in CITIES.values():
        if p.startswith(cdir + "/"):
            p = p[len(cdir) + 1:]
            break
    if not p.startswith(dataset + "/"):
        p = f"{dataset}/{p}"
    return p


def year_from_name(name):
    m = re.search(r"(20[0-2][0-9])", name)
    return m.group(1) if m else ""


def make_row(dataset, record_key, title="", date="", local_path="", source_url="",
             retrieved_date="", extraction_method="", processing_ref=""):
    return {
        "dataset": dataset,
        "record_key": record_key,
        "title": title,
        "date": date,
        "local_path": local_path,
        "source_url": source_url,
        "source_host": host_of(source_url),
        "retrieved_date": retrieved_date,
        "verified_date": "",
        "extraction_method": extraction_method,
        "processing_ref": processing_ref,
    }


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# minutes datasets (meeting_minutes + planning_commission)
# ---------------------------------------------------------------------------

# column aliases tolerated for legacy / mid-migration index variants
MINUTES_ALIASES = {
    "date": ["date", "meeting_date"],
    "title": ["title", "meeting_title"],
    "slug": ["slug", "file_slug"],
    "path": ["path", "file", "filepath", "md_path", "local_path"],
    "source": ["source", "portal", "source_portal"],
    "source_url": ["source_url", "url", "pdf_url", "doc_url"],
    "format": ["format", "extraction", "text_format"],
}


def pick(row, key):
    for alias in MINUTES_ALIASES[key]:
        if alias in row:
            return (row.get(alias) or "").strip()
    return ""


def harvest_minutes(city, cdir, dataset):
    idx = cdir / dataset / "minutes_index.csv"
    rows = []
    if not idx.exists():
        if city == "sandy" and dataset == "planning_commission":
            rows.append(make_row(
                dataset, "legistar_staging_export",
                title="Legistar web-API staging export (Planning Commission votes; EventItemVote records)",
                date="", local_path="db/staging/",
                source_url="unrecorded (Granicus Legistar web API — sandyutah.legistar.com; "
                           "minutes PDFs retrievable from Legistar InSite)",
                extraction_method="legistar-api",
                processing_ref="planning_commission/CLAUDE.md §pipeline (build_from_legistar.py)"))
        return rows
    pref = f"{dataset}/CLAUDE.md §pipeline"
    for r in read_csv(idx):
        date, slug = pick(r, "date"), pick(r, "slug")
        url = pick(r, "source_url")
        if not url:
            src = pick(r, "source")
            url = f"unrecorded ({src} portal — see recon.md)" if src else "unrecorded"
        rows.append(make_row(
            dataset, f"{date}_{slug}" if slug else date,
            title=pick(r, "title"), date=date,
            local_path=norm_city_rel(pick(r, "path"), dataset),
            source_url=url, extraction_method=pick(r, "format"),
            processing_ref=pref))
    return rows


# ---------------------------------------------------------------------------
# public comments — per-city adapters
# ---------------------------------------------------------------------------

def comment_doc_dates(clean_csv):
    """per source_file: (min date, min period_start, max period_end, n rows)"""
    agg = {}
    for r in read_csv(clean_csv):
        sf = r["source_file"]
        a = agg.setdefault(sf, {"dates": [], "ps": [], "pe": [], "n": 0})
        a["n"] += 1
        for key, col in (("dates", "date_normalized"), ("dates", "date"),
                         ("ps", "period_start"), ("pe", "period_end")):
            v = (r.get(col) or "").strip()
            if v:
                a[key].append(v)
    return agg


def minutes_url_map(cdir):
    m = {}
    idx = cdir / "meeting_minutes" / "minutes_index.csv"
    if idx.exists():
        for r in read_csv(idx):
            p = norm_city_rel(pick(r, "path"), "meeting_minutes")
            m[p] = r
    return m


def harvest_comments(city, cdir):
    ds = "public_comments"
    clean = cdir / ds / "all_comments_clean.csv"
    if not clean.exists() or len(read_csv(clean)) == 0:
        return []  # honest-empty comment corpora get no rows
    agg = comment_doc_dates(clean)
    rows = []

    if city == "slc":
        # URL of record: download_comments.sh (check_new_comments.py appends new
        # weekly URLs to it). Local name mirrors the script's transformation.
        urlmap = {}
        sh = cdir / ds / "download_comments.sh"
        for line in sh.read_text(encoding="utf-8").splitlines():
            m = re.search(r'download "(.*)"', line)
            if not m:
                continue
            u = m.group(1).replace("http://", "https://").replace("\\", "/")
            ym = re.search(r"20[0-9]{2}", u)
            fn = urllib.parse.unquote(u.rsplit("/", 1)[-1]).replace(" ", "_")
            urlmap[f"{ym.group(0)}/{fn}"] = u
        for sf, a in sorted(agg.items()):
            url = urlmap.get(sf) or "unrecorded (slcdocs.com weekly comment PDF)"
            pe = max(a["pe"]) if a["pe"] else ""
            ps = min(a["ps"]) if a["ps"] else ""
            if ps and pe and ps != pe:
                title = f"Public comments received {ps} to {pe}"
            else:
                title = f"Public comments received {pe or ps}".strip()
            rows.append(make_row(
                ds, sf, title=title,
                date=pe or (max(a["dates"]) if a["dates"] else ""),
                local_path=f"{ds}/{sf}", source_url=url,
                extraction_method="claude-vision (vision_extract.py)",
                processing_ref="public_comments/CLAUDE.md §pipeline (download_comments.sh → vision_extract.py → clean_comments.py)"))

    elif city == "st_george":
        man = json.loads((cdir / ds / "comments_json" / "_manifest.json").read_text())
        bylocal = {m["local"]: m for m in man}
        for sf, a in sorted(agg.items()):
            m = bylocal.get(sf)
            url = m["url"] if m else "unrecorded (sgcityutah.gov weekly comment PDF)"
            rows.append(make_row(
                ds, Path(sf).name, title=(m["filename"] if m else Path(sf).name),
                date=(m.get("period_end", "") if m else ""),
                local_path=norm_city_rel(sf, ds), source_url=url,
                extraction_method="claude-vision (extract_comments.py)",
                processing_ref="public_comments/CLAUDE.md §pipeline (extract_comments.py → build_clean_csv.py)"))

    elif city == "provo":
        scan = {r["date"]: r for r in read_csv(cdir / ds / "packets_scanned.csv")}
        for sf, a in sorted(agg.items()):
            dm = re.search(r"packet_(\d{4}-\d{2}-\d{2})", sf)
            date = dm.group(1) if dm else ""
            sr = scan.get(date)
            url = sr["packet_url"] if sr else "unrecorded (agendas.provo.gov agenda packet)"
            rows.append(make_row(
                ds, Path(sf).name, title=f"Council agenda packet {date} (public-comment section)",
                date=date, local_path=norm_city_rel(sf, ds), source_url=url,
                extraction_method="pdftotext + page-walk comment classifier",
                processing_ref="public_comments/CLAUDE.md §pipeline (harvest_packets.py → extract_packet_comments.py)"))

    elif city == "west_jordan":
        scan = {r["meetingTemplateId"]: r for r in read_csv(cdir / ds / "packets_scanned.csv")}
        for sf, a in sorted(agg.items()):
            tm = re.search(r"tid(\d+)", sf)
            sr = scan.get(tm.group(1)) if tm else None
            url = sr["url"] if sr else "unrecorded (westjordan.primegov.com compiled packet)"
            date = sr["date"] if sr else (max(a["dates"]) if a["dates"] else "")
            rows.append(make_row(
                ds, sf, title=f"Council compiled agenda packet {date} (public-comment section)",
                date=date, local_path=f"{ds}/raw/{sf}", source_url=url,
                extraction_method="pdf text extraction",
                processing_ref="public_comments/CLAUDE.md §pipeline (packets_scanned.csv is the full 120-packet scan record)"))

    elif city == "park_city":
        mmap = minutes_url_map(cdir)
        plist = {}
        pl = cdir / ds / "raw" / "packetlist.json"
        if pl.exists():
            for d, fid, title in json.loads(pl.read_text()):
                plist[str(fid)] = (d, title)
        for sf, a in sorted(agg.items()):
            fm = re.match(r"meeting_minutes \(agenda packet\) fileId=(\d+)", sf)
            if fm:
                fid = fm.group(1)
                d, title = plist.get(fid, ("", f"CC packet fileId={fid}"))
                rows.append(make_row(
                    ds, f"packet_fileId_{fid}",
                    title=f"{title} (public-comment section)", date=d,
                    local_path="public_comments/raw/packet_comments_cache.json",
                    source_url=f"https://parkcityut.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId={fid},plainText=true)",
                    extraction_method="civicclerk plain-text stream, comment-section parse",
                    processing_ref="public_comments/CLAUDE.md §pipeline (raw/harvest_packets.py → raw/build_comments.py)"))
            else:
                mr = mmap.get(sf)
                url = pick(mr, "source_url") if mr else "unrecorded (see meeting_minutes/minutes_index.csv)"
                rows.append(make_row(
                    ds, Path(sf).stem, title=(pick(mr, "title") + " (public-comment section)") if mr else Path(sf).stem,
                    date=pick(mr, "date") if mr else "", local_path=sf, source_url=url,
                    extraction_method="transcribed from minutes text",
                    processing_ref="public_comments/CLAUDE.md §pipeline (comments extracted from council minutes; source_url is the minutes document)"))

    elif city in ("lehi", "orem"):
        mmap = minutes_url_map(cdir)
        for sf, a in sorted(agg.items()):
            mr = mmap.get(sf)
            url = pick(mr, "source_url") if mr else "unrecorded (see meeting_minutes/minutes_index.csv)"
            rows.append(make_row(
                ds, Path(sf).stem,
                title=(pick(mr, "title") + " (public-comment section)") if mr else Path(sf).stem,
                date=pick(mr, "date") if mr else "", local_path=sf, source_url=url,
                extraction_method="transcribed from minutes text",
                processing_ref="public_comments/CLAUDE.md §pipeline (comments extracted from council minutes; source_url is the minutes document)"))

    return rows


# ---------------------------------------------------------------------------
# election results
# ---------------------------------------------------------------------------

def harvest_elections(city, cdir):
    ds = "election_results"
    ed = cdir / ds
    cfg = ELECTION_CFG[city]
    # URLs explicitly stated in the city's election docs, matched by exact basename.
    doc_urls = {}
    for docname in ("CLAUDE.md", "ELECTION_VERIFICATION.md"):
        p = ed / docname
        if p.exists():
            for u in re.findall(r"https?://[^\s`)\]>\"']+", p.read_text(encoding="utf-8")):
                u = u.rstrip(".,;`")
                base = urllib.parse.unquote(urllib.parse.urlparse(u).path.rsplit("/", 1)[-1])
                if base:
                    doc_urls.setdefault(base, u)
    overrides = cfg.get("overrides", {})

    files = []
    raw = ed / "raw"
    if raw.exists():
        files = sorted(p for p in raw.rglob("*") if p.is_file() and not p.name.startswith("."))

    # 2026-07-19/-20 pipeline re-point: several cities derive their election layer
    # DIRECTLY from the Salt Lake County canonical (salt_lake_county/elections/
    # slco_municipal_results_long.csv) rather than a per-city raw copy — clean_elections.py
    # reads the county file. Where that is the case the city carries a `canonical_pointer`
    # in ELECTION_CFG so the county-canonical read is recorded explicitly (local_path is
    # REPO-relative, outside the city dir). It is emitted whether or not the city ALSO
    # retains raw files (e.g. sandy keeps its 2021 RCV PDFs; south_jordan/taylorsville keep
    # SOVC spreadsheets for suppression-recovery years) — for those, the pointer row rides
    # alongside the per-file rows. `canonical_pointer` may be True (default long-file
    # pointer) or a dict overriding any make_row field (kearns parses the raw SOVC
    # workbooks because the long file is corrupted for it). Byte-identity of the per-year
    # county SOVC files was verified 2026-07-19/-20 (SLCO_SOVC).
    script = next((s.name for s in ed.glob("*.py") if s.name.startswith(("clean_", "build_"))), "clean_elections.py")
    pointer_rows = []
    ptr = cfg.get("canonical_pointer")
    if ptr:
        d = ptr if isinstance(ptr, dict) else {}
        pointer_rows = [make_row(
            ds, d.get("record_key", "slco_municipal_results_long.csv"),
            title=d.get("title", "Salt Lake County canonical municipal canvass (SOVC, tidy long form, 2007-2025)"),
            local_path=d.get("local_path", "salt_lake_county/elections/slco_municipal_results_long.csv"),
            source_url=d.get("source_url", _SLCO_LAND),
            extraction_method=d.get("extraction_method", f"filtered directly from the county canonical ({script})"),
            processing_ref=d.get("processing_ref", f"election_results/CLAUDE.md ({script}; canonical provenance: salt_lake_county/elections/CLAUDE.md + raw/SOURCES.md)"))]
    if not files:
        return pointer_rows

    rows = list(pointer_rows)
    for f in files:
        rel = f.relative_to(ed).as_posix()          # e.g. raw/x.pdf or 2007_...csv
        key = f.relative_to(raw).as_posix() if raw.exists() else f.name
        url = overrides.get(f.name) or doc_urls.get(f.name)
        if not url:
            label = cfg["default"]
            for pat, lab in cfg.get("fallbacks", []):
                if fnmatch.fnmatch(key, pat) or fnmatch.fnmatch(f.name, pat):
                    label = lab
                    break
            # A label pre-marked "verified-no-stable-archive (…)" is a checked, dated
            # honest gap (probed 2026-07-19, no durable public archive URL exists) and
            # is emitted verbatim; anything else is an as-yet-unrecorded issuing office.
            url = label if label.startswith("verified-no-stable-archive") else f"unrecorded ({label})"
        rows.append(make_row(
            ds, key, title=f.name, date=year_from_name(f.name) or year_from_name(rel),
            local_path=f"{ds}/{rel}",
            source_url=url,
            extraction_method=f"{f.suffix.lstrip('.').lower() or 'file'} (raw retained verbatim)",
            processing_ref=f"election_results/CLAUDE.md §sources ({script})"))
    return rows


# ---------------------------------------------------------------------------
# expansion datasets (index.csv contract: source_url + retrieved_date per doc)
# ---------------------------------------------------------------------------

def harvest_expansion(city, cdir, dataset):
    idx = cdir / dataset / "index.csv"
    if not idx.exists():
        return []
    mmap = minutes_url_map(cdir)
    rows, seen = [], {}
    for i, r in enumerate(read_csv(idx), 1):
        url = (r.get("source_url") or "").strip()
        note = ""
        if url and not url.startswith("http"):
            # ordinances cite the minutes document that records adoption —
            # resolve to that document's recorded portal URL.
            mr = mmap.get(norm_city_rel(url, "meeting_minutes"))
            if mr and pick(mr, "source_url"):
                url = pick(mr, "source_url")
                note = " (via minutes document)"
            else:
                url = f"unrecorded (cited local document: {url})"
        path = (r.get("path") or r.get("local_path") or "").strip()
        if not path and dataset == "ordinances":
            path = (r.get("minutes_source") or "").strip()
        local = norm_city_rel(path, dataset) if path else ""
        key = (Path(path).name if path else "") or (r.get("ordinance_no") or "").strip() \
            or f"{(r.get('date') or '').strip()}_{i}"
        if key in seen:
            seen[key] += 1
            key = f"{key}-{seen[key]}"
        else:
            seen[key] = 1
        rows.append(make_row(
            dataset, key, title=(r.get("title") or r.get("candidate") or "").strip(),
            date=(r.get("date") or r.get("adoption_date") or "").strip(),
            local_path=local, source_url=url,
            retrieved_date=(r.get("retrieved_date") or "").strip(),
            extraction_method=((r.get("extraction_method") or r.get("format") or "").strip() + note).strip(),
            processing_ref=f"{dataset}/CLAUDE.md"))
    return rows


# ---------------------------------------------------------------------------
# build / write
# ---------------------------------------------------------------------------

def build_city(city):
    cdir = ROOT / CITIES[city]
    rows = []
    rows += harvest_minutes(city, cdir, "meeting_minutes")
    rows += harvest_minutes(city, cdir, "planning_commission")
    rows += harvest_comments(city, cdir)
    rows += harvest_elections(city, cdir)
    for ds in EXPANSION_DATASETS:
        rows += harvest_expansion(city, cdir, ds)

    # de-dup record keys within a dataset
    seen = {}
    for r in rows:
        k = (r["dataset"], r["record_key"])
        if k in seen:
            seen[k] += 1
            r["record_key"] = f"{r['record_key']}-{seen[k]}"
        else:
            seen[k] = 1

    # preserve verified_date stamped by an earlier --verify-sample run
    out = cdir / "sources.csv"
    if out.exists():
        old = {(r["dataset"], r["record_key"]): r for r in read_csv(out)}
        for r in rows:
            o = old.get((r["dataset"], r["record_key"]))
            if o and o.get("verified_date") and o.get("source_url") == r["source_url"]:
                r["verified_date"] = o["verified_date"]

    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    write_sources_md(city, cdir, rows)
    return rows


def dataset_stats(rows):
    stats = {}
    for r in rows:
        s = stats.setdefault(r["dataset"], {"n": 0, "url": 0, "hosts": {}, "dates": [],
                                            "methods": {}, "verified": 0})
        s["n"] += 1
        if r["source_url"].startswith("http"):
            s["url"] += 1
            s["hosts"][r["source_host"]] = s["hosts"].get(r["source_host"], 0) + 1
        if r["date"]:
            s["dates"].append(r["date"])
        m = r["extraction_method"] or "—"
        s["methods"][m] = s["methods"].get(m, 0) + 1
        if r["verified_date"]:
            s["verified"] += 1
    return stats


def write_sources_md(city, cdir, rows):
    meta = META[city]
    stats = dataset_stats(rows)
    today = datetime.date.today().isoformat()
    L = []
    L.append(f"# Sources — {meta['name']} civic data")
    L.append("")
    L.append(meta["preamble"])
    L.append("")
    L.append(f"The machine-readable companion to this page is [`sources.csv`](sources.csv) — "
             f"one row per source document with its original URL (where recorded), local "
             f"path, and extraction method. Generated {today} by "
             f"`scripts/build_sources_index.py`; regenerate with "
             f"`python3 scripts/build_sources_index.py {city}`.")
    L.append("")
    order = ["meeting_minutes", "planning_commission", "public_comments",
             "election_results"] + EXPANSION_DATASETS
    for ds in order:
        info = meta["datasets"].get(ds)
        s = stats.get(ds)
        if not info and not s:
            continue
        L.append(f"## {DATASET_LABELS.get(ds, ds)}")
        L.append("")
        if info:
            L.append(f"- **Published by:** {info['institution']}")
            L.append(f"- **Portal:** {info['portal']}")
        if s:
            dr = f"{min(s['dates'])} to {max(s['dates'])}" if s["dates"] else "n/a"
            pct = round(100 * s["url"] / s["n"]) if s["n"] else 0
            hosts = ", ".join(sorted(s["hosts"])) or "—"
            L.append(f"- **Documents indexed:** {s['n']}  ·  **Date range:** {dr}")
            L.append(f"- **Direct source URLs recorded:** {s['url']}/{s['n']} ({pct}%)"
                     + (f"  ·  **Host(s):** {hosts}" if s["url"] else ""))
            methods = ", ".join(f"{k} ({v})" for k, v in
                                sorted(s["methods"].items(), key=lambda kv: -kv[1]))
            L.append(f"- **How the text was obtained:** {methods}")
        else:
            L.append("- **Documents indexed:** none — this city publishes no documents "
                     "of this type (an honest gap, not missing data).")
        if info and info.get("note"):
            L.append(f"- **Note:** {info['note']}")
        L.append("")
    L.append("---")
    L.append("")
    L.append("*Where a row's `source_url` reads `unrecorded (…)`, the original download "
             "URL was not captured at retrieval time; the parenthetical names the "
             "issuing office/portal so the document can be re-obtained from the "
             "publisher. `verified_date` is stamped only on rows whose URL was "
             "re-checked live on that date (sampled, not exhaustive). No URL in this "
             "index is reconstructed or guessed.*")
    (cdir / "SOURCES.md").write_text("\n".join(L) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# liveness sampling (--verify-sample N)
# ---------------------------------------------------------------------------

UA = "civic-data-sources-index/1.0 (provenance liveness check; contact: tysonwelsh@gmail.com)"
BROWSER_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def check_url(url, timeout=25):
    """Polite liveness probe: HEAD, then a 1 KB ranged GET, then a plain GET with a
    browser User-Agent (CivicPlus DocumentCenter and similar hosts 404 non-browser
    agents / ranged requests even for live documents)."""
    attempts = (("HEAD", UA, {}),
                ("GET", UA, {"Range": "bytes=0-1023"}),
                ("GET", BROWSER_UA, {}))
    last = (None, "unreachable")
    for i, (method, ua, hdrs) in enumerate(attempts):
        final = i == len(attempts) - 1
        req = urllib.request.Request(url, method=method,
                                     headers={"User-Agent": ua, **hdrs})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if method == "GET" and "Range" not in hdrs:
                    resp.read(1024)  # confirm the body actually streams
                return resp.status, resp.geturl()
        except urllib.error.HTTPError as e:
            last = (e.code, url)
            if final:
                return last
        except Exception as e:
            last = (None, f"{type(e).__name__}: {e}")
            if final:
                return last
    return last


def verify_city(city, n_sample, sleep=0.8):
    cdir = ROOT / CITIES[city]
    out = cdir / "sources.csv"
    if not out.exists():
        print(f"{city}: no sources.csv — run a build first", file=sys.stderr)
        return []
    rows = read_csv(out)
    with_url = [(i, r) for i, r in enumerate(rows) if r["source_url"].startswith("http")]
    if not with_url:
        print(f"{city}: no recorded URLs to sample")
        return []
    # stratified: round-robin across datasets, deterministic
    rng = random.Random(f"sources-{city}-20260702")
    by_ds = {}
    for i, r in with_url:
        by_ds.setdefault(r["dataset"], []).append((i, r))
    for lst in by_ds.values():
        rng.shuffle(lst)
    picked, ds_cycle = [], sorted(by_ds)
    while len(picked) < n_sample and any(by_ds.values()):
        for ds in ds_cycle:
            if by_ds[ds] and len(picked) < n_sample:
                picked.append(by_ds[ds].pop())
    results = []
    today = datetime.date.today().isoformat()
    for i, r in picked:
        status, final = check_url(r["source_url"])
        ok = status is not None and 200 <= status < 400
        results.append({"city": city, "dataset": r["dataset"],
                        "record_key": r["record_key"], "url": r["source_url"],
                        "host": r["source_host"], "status": status, "ok": ok,
                        "detail": final})
        if ok:
            rows[i]["verified_date"] = today
        print(f"  [{status if status is not None else 'ERR'}] {r['source_url'][:110]}"
              + ("" if ok else f"  <- {final[:80]}"))
        time.sleep(sleep)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    # refresh SOURCES.md (verified counts unchanged in layout; regenerate for date)
    write_sources_md(city, cdir, rows)
    return results


def write_summary():
    """Regenerate repo-root sources_summary.md from the per-city sources.csv files.
    A '## URL liveness' section between the liveness markers is preserved verbatim
    (it is maintained from --verify-sample runs)."""
    out = ROOT / "sources_summary.md"
    BEGIN, END = "<!-- liveness:begin -->", "<!-- liveness:end -->"
    liveness_block = ""
    if out.exists():
        t = out.read_text(encoding="utf-8")
        if BEGIN in t and END in t:
            liveness_block = t.split(BEGIN, 1)[1].split(END, 1)[0]
    today = datetime.date.today().isoformat()
    L = [
        "# Source & citation index — repo summary",
        "",
        f"Generated {today} by `scripts/build_sources_index.py --summary` from the "
        "per-city `sources.csv` files. Per-city detail: `<city>_city_council/SOURCES.md`.",
        "",
        "## Provenance model",
        "",
        "Every document in this collection is indexed in its city's `sources.csv` with "
        "the original government-source URL where one was recorded at retrieval time. "
        "That URL index is the **recovery path**: if retained originals under the "
        "datasets' `raw/` directories ever have to be deleted for disk space, every "
        "document with a recorded URL can be re-fetched from its publisher, and every "
        "document without one carries the name of the issuing office "
        "(`unrecorded (…)`) so it can be re-obtained by request. Raw originals are "
        "retained where present (comments, elections, the Lehi expansion datasets; "
        "minutes PDFs are being backfilled under Phase 3.2). The processing chain "
        "from source document to dataset is documented per city in the dataset-level "
        "`CLAUDE.md` files referenced by each row's `processing_ref`. No URL is ever "
        "reconstructed or guessed; `verified_date` marks rows whose URL was re-checked "
        "live on that date (a stratified sample, not an exhaustive sweep).",
        "",
        "## Coverage (documents indexed / % with a recorded direct URL)",
        "",
        "| city | dataset | documents | % with URL | source host(s) |",
        "|---|---|---:|---:|---|",
    ]
    for city, cdir in CITIES.items():
        p = ROOT / cdir / "sources.csv"
        if not p.exists():
            continue
        stats = dataset_stats(read_csv(p))
        for ds in (["meeting_minutes", "planning_commission", "public_comments",
                    "election_results"] + EXPANSION_DATASETS):
            s = stats.get(ds)
            if not s:
                continue
            pct = round(100 * s["url"] / s["n"]) if s["n"] else 0
            hosts = ", ".join(sorted(s["hosts"])) or "— (issuing office named per row)"
            L.append(f"| {city} | {ds} | {s['n']} | {pct}% | {hosts} |")
    L += ["", BEGIN + (liveness_block or "\n## URL liveness\n\n(not yet sampled — run "
          "`python3 scripts/build_sources_index.py --verify-sample 5`)\n") + END, ""]
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cities", nargs="*", help="city short names (default: all)")
    ap.add_argument("--verify-sample", type=int, metavar="N",
                    help="liveness-check N recorded URLs per city and stamp verified_date")
    ap.add_argument("--summary", action="store_true",
                    help="regenerate repo-root sources_summary.md from the sources.csv files")
    args = ap.parse_args()
    targets = args.cities or list(CITIES)
    bad = [c for c in targets if c not in CITIES]
    if bad:
        ap.error(f"unknown city: {bad} (choose from {list(CITIES)})")

    if args.summary:
        write_summary()
        return

    if args.verify_sample:
        all_results = []
        for city in targets:
            print(f"== verifying {city}")
            all_results += verify_city(city, args.verify_sample)
        live = sum(1 for r in all_results if r["ok"])
        print(f"\nliveness: {live}/{len(all_results)} sampled URLs answered")
        byhost = {}
        for r in all_results:
            h = byhost.setdefault(r["host"], [0, 0])
            h[0] += r["ok"]
            h[1] += 1
        for h, (okc, tot) in sorted(byhost.items()):
            print(f"  {h}: {okc}/{tot}")
        return

    for city in targets:
        rows = build_city(city)
        stats = dataset_stats(rows)
        n = sum(s["n"] for s in stats.values())
        u = sum(s["url"] for s in stats.values())
        print(f"{city}: {n} documents indexed, {u} with recorded URLs "
              f"({round(100*u/n) if n else 0}%) -> {CITIES[city]}/sources.csv + SOURCES.md")


if __name__ == "__main__":
    main()
