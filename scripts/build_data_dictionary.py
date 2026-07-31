#!/usr/bin/env python3
"""Generate DATA_DICTIONARY.md from the live gov.db (PRAGMA-driven, so it cannot
drift) plus curated one-line purposes/glosses. Re-run after any federation that
changes schema; row counts are stamped with the build date. (G6, 2026-07-31.)"""
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "gov.db")
OUT = os.path.join(ROOT, "DATA_DICTIONARY.md")

PURPOSE = {
    "entity": "The 44-entity registry (mirror of registry/entities.csv).",
    "entity_relationship": "Geography graph: which city sits in which county, MPO coverage.",
    "body": "Deliberative bodies per entity (council, PC, RDA, …).",
    "person": "Voting members. ⚠ ut_state legislators are a DISJOINT population — never surname-join across tiers.",
    "meeting": "One row per meeting document ingested.",
    "motion": "The vote spine: every motion with VERBATIM motion_type/result_raw, derived outcome/disposition, provenance.",
    "vote": "One row per member-vote; vote_value is the source's verbatim vocabulary (see vote_values).",
    "application": "Development applications / matters. ⚠ includes ut_state's 264 bills (app_key 'bill:…') pending state-tier reintegration.",
    "referral": "Reconstructed PC→Council links, confidence-scored ('low' = don't quote).",
    "role": "Person × body service spans derived from votes.",
    "motion_std": "Cross-entity normalization: motion_type_std / land_use_type / action_class / outcome / tallies / vote_mode.",
    "motion_type_crosswalk": "Native motion_type label → standard vocabulary, per entity.",
    "body_crosswalk": "Native body labels → canonical body names.",
    "vote_values": "Each entity's verbatim vote vocabulary and its recorded meaning.",
    "election_race": "AUDITED races: winners/margins per contest — the authoritative election layer.",
    "election_result": "SLCo SOVC candidate×contest tallies 2007–2025 (rank_in_contest is plurality order; RCV finals differ).",
    "cf_filing": "One row per campaign-finance filing with the filer's own printed totals + reconciliation columns.",
    "cf_contribution": "Itemized contributions (donor city/state only — street addresses deliberately not stored).",
    "cf_expenditure": "Itemized expenditures.",
    "cf_cycle": "THE only sanctioned per-candidate totals (filings overlap — never sum cf_filing columns).",
    "cf_candidate_person": "Candidate → person_id resolution (exact name-key; unmatched stay NULL).",
    "comment": "Public comments (published layers are email/phone-redacted per PRIVACY.md).",
    "document": "Catalog of every source document. ⚠ path resolves only in a full local build; use text_path/source_url in a clone.",
    "ordinance": "Adopted ordinances; motion_id present only where the enacting-motion link is unique.",
    "term": "Roster: seat-tenure intervals, half-open [start,end), per-row confidence/sources.",
    "district_version": "Redistricting-versioned council-district boundaries.",
    "district_precinct": "Precinct→district assignment per boundary plan.",
    "regional_project": "MPO programmed projects (WFRC 8 TIP vintages + RTP-2050; MAG TIP/RTP/RPO).",
    "project_vintage": "Per-(pin × TIP vintage) programmed-cost/status snapshot.",
    "project_history": "Per-pin lifecycle across vintages (slippage, cost drift; left-censored window — see caveats).",
    "projection": "Population/HH/employment projections: county, annual city-area regional, state grains.",
    "development_application": "County development pipeline rows.",
    "gis_layer": "GIS catalog with per-layer license.",
    "caveat": "Measurement ceilings, joined into the views so warnings ride result rows.",
    "build_info": "Build metadata + per-layer counts — the numeric source of truth.",
}

GLOSS = {
    ("motion", "provenance"): "CITY tier: 'minutes'=audited primary vs recovery channels. NON-CITY tier: extractor names. Two vocabularies — see CLAUDE.md.",
    ("motion", "outcome"): "Did the motion CARRY (Pass/Fail) — orthogonal to disposition.",
    ("motion", "disposition"): "What the motion DID (approve|deny|continue|table|procedural); NULL = unclassified (cities) or not-yet-computed (most non-city — see caveat).",
    ("motion", "names_recorded"): "0 = tally-only motion: the source printed no names. Honest gap, never filled.",
    ("motion_std", "dataset"): "City tier: directory-derived. Non-city: BODY-derived (land_use = PC(s), legislative = the rest).",
    ("motion_std", "tally_other"): "NULL (never 0) when the source printed no third number — named rows then supply abstain/recuse counts.",
    ("election_race", "voting_method"): "RCV cities (millcreek; draper/bluffdale 2021 pilots): take winners here, not from tallies.",
    ("term", "end_date"): "Half-open: '' = serving now. Point-in-time roster: start<=d AND (end='' OR end>d).",
    ("cf_cycle", "basis"): "How the total was computed (sum-interim / summary / override) — see each city's campaign_finance/CLAUDE.md.",
    ("document", "has_text"): "1 = text_path is directly readable (99.96% resolvable in a clone).",
    ("fts_minutes", "path"): "ENTITY-relative; prefix city||'_city_council/' (cities) or city||'/' (others) to open from repo root.",
}

VIEWS = {
    "v_contested_all": "Every non-unanimous motion (named OR tally dissent); tally_* = authoritative, named_* = attribution-only; dissent_caveats attached.",
    "v_member_record_all": "Per-member vote record with record_caveats attached.",
    "v_landuse_outcomes": "Land-use action × outcome rollup with caveats.",
    "v_pc_divergence": "PC recommendation vs council outcome (low-confidence links excluded by design; city tier only today).",
    "v_coverage": "Caveat-aware coverage matrix with FULL caveat text — read this first per entity.",
    "v_council_current": "Who serves now (from term).",
    "v_term_provenance": "Per-city roster confidence mix.",
    "v_election_city": "Audited races per city.",
}


def main():
    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    built = db.execute("SELECT value FROM build_info WHERE key='built_at'").fetchone()[0]
    lines = [
        "# DATA DICTIONARY — gov.db",
        "",
        f"GENERATED by `scripts/build_data_dictionary.py` from the build of **{built}**",
        "— regenerate after any federation; do not hand-edit. Concepts and query",
        "guidance: `gov_db_SCHEMA.md`. Ceilings: the `caveat` table / `v_coverage`.",
        "",
        "## Views",
        "",
    ]
    for v, purpose in VIEWS.items():
        lines.append(f"- **`{v}`** — {purpose}")
    lines += ["", "## Tables", ""]
    tables = [r[0] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'fts_%' ORDER BY name")]
    for t in tables:
        n = db.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        lines.append(f"### `{t}` — {n:,} rows")
        lines.append("")
        if t in PURPOSE:
            lines.append(PURPOSE[t])
            lines.append("")
        lines.append("| column | type | notes |")
        lines.append("|---|---|---|")
        for _, name, ctype, *_ in db.execute(f"PRAGMA table_info([{t}])"):
            gloss = GLOSS.get((t, name), "")
            lines.append(f"| `{name}` | {ctype or ''} | {gloss} |")
        lines.append("")
    lines += [
        "## FTS5 search tables",
        "",
        "`fts_minutes` (full minutes/plan/opinion/statute + recovered-pmn text; columns "
        "text, city, dataset, date, path), `fts_motion`, `fts_comment` (external-content "
        "over motion/comment), `fts_ordinance`, `fts_packet`. "
        + GLOSS[("fts_minutes", "path")],
        "",
    ]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {OUT} ({len(tables)} tables, build {built})")


if __name__ == "__main__":
    sys.exit(main())
