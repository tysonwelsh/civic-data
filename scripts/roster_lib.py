#!/usr/bin/env python3
"""roster_lib.py — shared mechanics for the rolling council-roster builders.

The roster layer is a slowly-changing-dimension / interval table of WHO HOLDS
EACH council + mayor seat over time, reconciled from elections + cities.db vote
bounds + minutes events + hand overrides, with per-row provenance/confidence.

This module holds the GENERIC mechanics; each city's
`<city>_city_council/roster/build_roster.py` is a THIN DRIVER that supplies a
`RosterConfig` + the hand-curated `TENURES` list + name maps and calls
`roster_lib.build(cfg, TENURES)`. Nothing city-specific lives here: every
per-city value (seat map, name normalization, the district/precinct prose,
redistricting facts) is carried on the config object. The library handles BOTH
the AT-LARGE case (no districts/redistricting → Nephi) and the DISTRICT case
(real districts + a redistricting + a precinct map → Provo); the district-only
features degrade cleanly when the config omits them (`redistrict=None`,
`precinct_map_path=None`).

DERIVED LAYER — the generated CSVs are regenerable, never hand-edited; all
corrections go through each city's `roster/roster_overrides.csv` (applied last,
wins ties). Cardinal rule: NEVER fabricate — an unknown seat-holder/date/boundary
becomes an explicit gap (confidence=low + a note), never a guess.

------------------------------------------------------------------------------
Adding a new city
------------------------------------------------------------------------------
Create `<city>_city_council/roster/build_roster.py` that:
  1. builds a `RosterConfig` (paths, `seat_district` map, `name_to_key`
     normalization, `db_key` cities.db→person_key map, the election filters,
     and — for a district city — a `Redistrict` with the district list, plan
     ids/dates, and the boundary/precinct prose as data),
  2. defines the curated `TENURES` list (city-specific seat assignments with
     cited `sources` + `confidence`),
  3. calls `roster_lib.build(cfg, TENURES)` in `__main__`, then prints its own
     "Wrote …" summary and dispatches `--check` / `--demo` using the generic
     query helpers (`roster_as_of`, `representatives_for_address`,
     `precinct_crosscheck`).
An at-large city omits `redistrict` and `precinct_*`; a district city supplies
them. The federation step (`scripts/build_cities_db.py`) then picks up any city
that HAS a `roster/` dir automatically.

Public API (all take the config as the first arg):
  RosterConfig, Redistrict        — the per-city config schema (dataclasses)
  TERM_COLUMNS, DISTRICT_COLUMNS, PRECINCT_COLUMNS   — the CSV contracts
  canon_key(cfg, name_upper)      — UPPER-CASE election name → person_key
  load_election_winners(cfg)      — municipal-general winners (year,office,district,name)
  load_vote_bounds(cfg)           — person_key → (first_vote,last_vote) from cities.db
  load_overrides(cfg)             — the hand-correction layer
  chain_end_dates(cfg, rows)      — per-seat end_date chaining + VACANT insertion
                                    (H-F: a TERMINAL_END_EVENTS tenure keeps its
                                    explicit end_date — abolished seats stay closed)
  reverse_election_crosscheck(cfg, rows) — H-C: elected tenure → is_winner row
  vote_window_sentinel(cfg, rows) — H-B: votes outside every tenure window (flag)
  validate(cfg, rows)             — no-overlap + sources/confidence present
  build(cfg, tenures)             — full pipeline; writes the CSVs; returns rows
  roster_as_of(cfg, date, body)   — tenures active on a date
  representatives_for_address(cfg, address, date, …)  — address+date → reps;
                                    prior-plan dates resolve against the prior
                                    geojson ONLY when its district_versions
                                    geometry confidence is high/medium (per-
                                    district gate; low/blank = honest gap)
  precinct_crosscheck(cfg, …)     — district city: precinct sums vs roster winner
"""
import csv
import os
import sqlite3
import sys
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Callable, Optional

# --- the three CSV contracts (shared by every city) -------------------------
TERM_COLUMNS = [
    "city", "body", "seat_id", "district", "person_name", "person_key",
    "start_date", "end_date", "start_event", "end_event", "election_year",
    "first_vote", "last_vote", "sources", "confidence", "note",
]
DISTRICT_COLUMNS = [
    "city", "district_id", "plan_id", "effective_start", "effective_end",
    "geometry_ref", "adopted_by", "source_url", "confidence", "note",
]
PRECINCT_COLUMNS = [
    "city", "plan_id", "district_id", "precinct_id",
    "effective_start", "effective_end", "source", "confidence", "note",
]


@dataclass
class Redistrict:
    """District-case config: the real districts + one redistricting event + the
    prose that describes them (carried as DATA — the library only loops)."""
    plan_old: str
    plan_new: str
    plan_switch: str            # effective boundary date between the two plans
    ord: str                    # enacting ordinance label (adopted_by on current rows)
    adopted: str                # adoption date (informational; used by the driver summary)
    districts: list             # e.g. ["District 1", … "District 5"]
    geom_ref: str               # current-plan geometry pointer
    source_url: str
    data_floor: str
    # district_versions prose
    current_note: str           # note on every current-plan (plan_new) district row
    prior_adopted_by: str       # adopted_by on the prior-plan (plan_old) gap rows
    prior_note: str             # note on every prior-plan gap row
    citywide_rows: list         # [(district_id, plan_id, who), …] whole-city rows
    citywide_adopted_by: str
    citywide_note_template: str  # formatted with {who}
    # district_precincts prose / rules
    precinct_hi_source: str = "2025"   # source_year value that earns confidence=high
    # H-A (2026-07-19): fallback source token used by write_precincts when the precinct
    # map carries NO source_year column/value (the SLCo district cities' canonical
    # geo/precinct_to_district.csv schemas vary and mostly omit it). EXPLICIT OPT-IN:
    # empty (default) preserves the old fail-loud behavior — a missing source_year
    # aborts the build rather than silently defaulting. Because the token isn't a year,
    # per-precinct MISMATCH detection stays dormant (the aggregate winner cross-check
    # still runs) — the documented "token-not-a-year" limitation. Retires the
    # roster-local `_precinct_to_district.csv` source_year-wrapper sidecars.
    precinct_source_default: str = ""
    precinct_hi_note: str = ""
    precinct_med_note: str = ""
    precinct_prior_note: str = ""      # note on the plan_old precinct gap rows
    # precinct cross-check parameters
    crosscheck_districts: tuple = ()   # district numbers with precinct-level data
    precinct_prefix: str = ""          # e.g. "25" (current precinct-code prefix)
    geo_seat_prefix: str = "D"         # seat_id = geo_seat_prefix + district number
    plan_switch_year: str = ""         # year >= this uses plan_new in the cross-check
    citywide_seats: tuple = ()         # seat_ids that represent the whole city
    # prior-plan (plan_old) DISTRICT geometry — blank/low = honest acquisition GAP (default);
    # a repo-reconstructed prior map (current precinct shapes dissolved by the pre-2022
    # assignment) sets a geometry_ref + confidence='medium' (approximate, see the driver note).
    # prior_confidence accepts EITHER a single string (uniform across every district — the common
    # case, e.g. the 5 clean 2026-07-11 reconstructions) OR a dict {district_label: confidence}
    # for a reconstruction whose fidelity varies by district (e.g. slc, whose D1-D6 recover cleanly
    # but whose D7 is 16/22 renumbered-precinct HOLES -> its dissolved polygon is a fragment, marked
    # 'low'). Unlisted districts fall back to `prior_confidence_default`. Backward-compatible: a
    # plain string leaves the scalar cities byte-identical.
    prior_geom_ref: str = ""
    prior_confidence: object = "low"
    prior_confidence_default: str = "medium"
    # optional per-district note override on the plan_old rows (district_label -> note); a district
    # not present here uses `prior_note`. Lets a hole-dominated district (slc D7) carry its own
    # honest caveat without changing the others' prose.
    prior_note_by_district: dict = field(default_factory=dict)
    # source_url stamped on the plan_old district_versions rows. Default "" keeps every city
    # that has NOT sourced an authoritative prior layer byte-identical (blank source_url, as
    # before). Set it when the prior geometry is an AUTHORITATIVE fetched layer rather than a
    # repo dissolve (e.g. millcreek's 2026-07-19 'City Council District Boundaries 2017-2022').
    prior_source_url: str = ""
    # H-D (2026-07-19): confidence stamped on the plan_new (current-plan) district rows —
    # was hardcoded 'high'. Lets a city whose redistricting is documented-in-effect but
    # whose ADOPTING ordinance / switch date is estimated (cottonwood_heights' 2022 plan)
    # mark the current-plan rows below high instead of relying on note prose alone.
    # Default 'high' keeps every existing city byte-identical.
    current_confidence: str = "high"
    # H-H (2026-07-19): the PRIOR plan's district list, when a redistricting CHANGED the
    # district COUNT (kearns' HB35 5->4 restructure abolished District 5). None (default)
    # = same list as `districts` (byte-identical for every same-count city). When set,
    # plan_old district_versions rows — and the plan_old GAP rows in district_precincts —
    # iterate THIS list, so an abolished district gets its own honest prior-plan row
    # instead of being folded invisibly into the surviving districts' gap prose.
    districts_old: Optional[list] = None


@dataclass
class RosterConfig:
    city: str
    city_dir: str                  # absolute path to <city>_city_council/
    repo_root: str
    data_floor: str
    geom_ref: str
    elections_path: str
    cities_db_path: str
    overrides_path: str
    terms_out: str
    districts_out: str
    seat_district: dict            # seat_id -> district label (for At-Large: all -> "At-Large")
    name_to_key: dict              # UPPER-CASE token -> person_key
    db_key: dict                   # cities.db person.name_key -> person_key
    keep_election_row: Callable    # (row) -> bool  (which election rows are municipal-general)
    contest_key: Callable          # (office, district) -> crosscheck key (seat_id or body) or None
    crosscheck_field: str          # tenure field the crosscheck key compares against ("body"/"seat_id")
    columns: list = field(default_factory=lambda: list(TERM_COLUMNS))
    seat_order: Optional[list] = None      # explicit seat ordering; None => (body!=Mayor, seat_id)
    winner_offices: tuple = ("Council", "Mayor")
    winners_have_district: bool = False
    elected_events: tuple = ("elected", "became-mayor", "reelected")
    disambiguators: dict = field(default_factory=dict)  # surname -> {FIRST: person_key}
    # Mayor with no council-vote role (presides / tie-break only — the common Utah
    # case). When True, MAYOR-body rows get EMPTY vote bounds and validate() enforces
    # it, so a stray tie-break vote can't smear a person-level span across the mayor's
    # tenures. Replaces the old implicit "omit the mayor from db_key" convention.
    non_voting_mayor: bool = False
    # H-C (2026-07-19): documented exceptions for the REVERSE election cross-check —
    # {(election_year, crosscheck_field_value, person_key): "reason + citation"}.
    # Legitimate tenure->no-winner-row classes: canceled-uncontested race certified by
    # resolution and never on the SOVC (draper 2025 Res #25-49); privacy-suppressed or
    # not-yet-in-county-file winners (alta 2021/2025); source winner-flag defects while
    # unfixed. Pre-floor election years (below the elections CSV's own coverage floor)
    # are auto-exempt and never need an entry.
    reverse_crosscheck_exceptions: dict = field(default_factory=dict)
    # at-large single-row district data (used when redistrict is None)
    atlarge: Optional[dict] = None
    # district-case extras (all optional; absent => at-large)
    redistrict: Optional[Redistrict] = None
    precincts_out: Optional[str] = None
    precinct_map_path: Optional[str] = None
    precincts_byprecinct_path: Optional[str] = None
    # prior-plan (plan_old) precinct->district composition. None = emit blank GAP rows
    # (default). Set to a reconstructed precinct_to_district_pre2022.csv to populate the
    # plan_old district_precincts rows with the real pre-2022 assignment (confidence=medium).
    prior_precinct_map_path: Optional[str] = None


# ---------------------------------------------------------------------------
# Name normalization
# ---------------------------------------------------------------------------
def canon_key(cfg, name_upper):
    """Normalize an UPPER-CASE election name to a person_key used in TENURES.
    Shared-surname disambiguation (e.g. two Worwoods / two Davids) is handled by
    cfg.disambiguators BEFORE the flat surname/first-name table lookup."""
    n = name_upper.replace(".", "").replace(",", "").upper()
    for surname, mapping in cfg.disambiguators.items():
        if surname in n:
            for firstname, pk in mapping.items():
                if firstname in n:
                    return pk
    for tok in n.split():
        if tok in cfg.name_to_key:
            return cfg.name_to_key[tok]
    return None


# ---------------------------------------------------------------------------
# Layer 1: election winners
# ---------------------------------------------------------------------------
def load_election_winners(cfg):
    """Municipal GENERAL winners only (each city's cfg.keep_election_row drops
    the primary 'advancer' rows). Returns sorted unique (year, office, district,
    name_upper) tuples — district='' for an at-large city."""
    winners = []
    with open(cfg.elections_path, newline="") as f:
        for r in csv.DictReader(f):
            if r["is_winner"].strip().lower() not in ("true", "1", "yes", "y", "t"):
                continue
            if not cfg.keep_election_row(r):
                continue
            office = r["office"].strip()
            if office not in cfg.winner_offices:
                continue
            district = r["district"].strip() if cfg.winners_have_district else ""
            winners.append((r["year"], office, district, r["candidate"].strip().upper()))
    return sorted(set(winners))


def election_crosscheck(cfg, rows):
    """Assert every general-election winner maps to an `elected`/`reelected`/
    `became-mayor` tenure; prints drift to stderr (never mutates)."""
    have = {(r["election_year"], r[cfg.crosscheck_field], r["person_key"])
            for r in rows if r["start_event"] in cfg.elected_events}
    for yr, office, dist, name in load_election_winners(cfg):
        pk = canon_key(cfg, name)
        key = cfg.contest_key(office, dist)
        label = ("%s %s %s %s" % (yr, office, dist, name)).replace("  ", " ").strip()
        if pk is None:
            print("  [election cross-check] unmapped winner %s" % label, file=sys.stderr)
            continue
        if key is None:
            print("  [election cross-check] unmapped contest %s %s %s"
                  % (yr, office, dist), file=sys.stderr)
            continue
        if (yr, key, pk) not in have:
            print("  [election cross-check] winner not in roster: %s %s %s (%s)"
                  % (yr, key, name, pk), file=sys.stderr)


def reverse_election_crosscheck(cfg, rows):
    """H-C (2026-07-19) — the REVERSE of election_crosscheck: every `elected`/
    `reelected`/`became-mayor` tenure that carries an election_year must map back to
    an `is_winner` municipal-general row in the city's elections CSV. Informational
    (prints drift to stderr, never mutates, never fails the build — mirroring the
    forward check): legitimate no-winner-row classes exist and are handled two ways:
      * AUTO-EXEMPT: an election_year below the elections CSV's own coverage floor
        (the earliest kept winner year) — the layer honestly doesn't cover it, so a
        pre-floor election-anchored `medium` term is not drift.
      * cfg.reverse_crosscheck_exceptions — per-city DOCUMENTED exceptions keyed
        (election_year, crosscheck_field_value, person_key) with a cited reason
        (canceled-uncontested certifications, privacy-suppressed winners, source
        winner-flag defects while unfixed)."""
    winners = set()
    for yr, office, dist, name in load_election_winners(cfg):
        pk = canon_key(cfg, name)
        key = cfg.contest_key(office, dist)
        if pk is not None and key is not None:
            winners.add((yr, key, pk))
    if not winners:
        return 0
    floor_yr = min(yr for yr, _, _ in winners)
    n_flagged = 0
    _used_exceptions = set()
    for r in rows:
        if r.get("start_event") not in cfg.elected_events:
            continue
        ey = (r.get("election_year") or "").strip()
        if not ey or ey < floor_yr:
            continue                     # no anchor / below the elections coverage floor
        k = (ey, r[cfg.crosscheck_field], r["person_key"])
        if k in winners:
            continue
        if k in cfg.reverse_crosscheck_exceptions:
            _used_exceptions.add(k)      # documented exception (cited in the driver)
            continue
        n_flagged += 1
        print("  [reverse election cross-check] tenure has no matching winner row: "
              "%s %s %s (%s %s)" % (ey, r[cfg.crosscheck_field], r["person_key"],
                                    r["seat_id"], r.get("start_event")), file=sys.stderr)
    # stale-exception discipline: an allowlist entry that no longer shields anything
    # (the winner row appeared, or the tenure changed) must be surfaced, never rot.
    for k in sorted(set(cfg.reverse_crosscheck_exceptions) - _used_exceptions):
        print("  [reverse election cross-check] STALE documented exception (matches no "
              "flagged tenure): %s" % (k,), file=sys.stderr)
    return n_flagged


# ---------------------------------------------------------------------------
# Layer 2: observed vote bounds from cities.db
# ---------------------------------------------------------------------------
def load_vote_bounds(cfg):
    """person_key -> (first_vote, last_vote) from cities.db role table
    (city=cfg.city, body='Council'), mapped through cfg.db_key."""
    bounds = {}
    if not os.path.exists(cfg.cities_db_path):
        print("  [warn] cities.db not found — first_vote/last_vote left blank",
              file=sys.stderr)
        return bounds
    con = sqlite3.connect(cfg.cities_db_path)
    rows = con.execute(
        "SELECT p.name_key, r.first_seen, r.last_seen "
        "FROM role r JOIN person p ON p.person_id = r.person_id AND p.city = r.city "
        "            JOIN body b   ON b.body_id = r.body_id "
        "WHERE r.city = ? AND b.name = 'Council'", (cfg.city,)).fetchall()
    con.close()
    for name_key, fs, ls in rows:
        pk = cfg.db_key.get(name_key)
        if not pk:
            continue
        # UNION across every name_key that maps to one person_key — a member who
        # changed their name (e.g. Petro-Eschler -> Petro) has multiple db name_keys;
        # take the earliest first_seen and latest last_seen so the vote span is whole.
        pf, pl = bounds.get(pk, ("", ""))
        firsts = [d for d in (pf, fs) if d]
        lasts = [d for d in (pl, ls) if d]
        bounds[pk] = (min(firsts) if firsts else "", max(lasts) if lasts else "")
    return bounds


def load_vote_dates(cfg):
    """person_key -> sorted list of DISTINCT Council-body vote dates from cities.db.

    Unlike load_vote_bounds (which returns only a person's overall min/max, so a
    councilmember->mayor person's mayor-era votes smear back onto the council tenure,
    and consecutive re-elected terms all show the whole span), this returns the full
    date set so build() can CLAMP each tenure's first_vote/last_vote to that tenure's
    own [start_date, end_date) window — the tenure-window clamp. Dates are UNIONed
    across every db name_key that maps to one person_key (name changes)."""
    dates = defaultdict(set)
    if not os.path.exists(cfg.cities_db_path):
        print("  [warn] cities.db not found — first_vote/last_vote left blank",
              file=sys.stderr)
        return {}
    con = sqlite3.connect(cfg.cities_db_path)
    rows = con.execute(
        "SELECT p.name_key, m.meeting_date "
        "FROM vote v JOIN motion mo ON mo.motion_id = v.motion_id "
        "            JOIN meeting m ON m.meeting_id = mo.meeting_id "
        "            JOIN body b    ON b.body_id = m.body_id "
        "            JOIN person p  ON p.person_id = v.person_id AND p.city = v.city "
        "WHERE v.city = ? AND b.name = 'Council'", (cfg.city,)).fetchall()
    con.close()
    for name_key, d in rows:
        pk = cfg.db_key.get(name_key)
        if pk and d:
            dates[pk].add(d)
    return {pk: sorted(ds) for pk, ds in dates.items()}


def clamp_vote_bounds(cfg, rows):
    """Assign first_vote/last_vote as the earliest/latest observed Council vote that
    falls WITHIN each tenure's own [start_date, end_date) half-open window (blank when
    the window contains no observed vote — e.g. a pre-floor term whose holder's only
    recorded votes belong to a later tenure). Must run AFTER chain_end_dates() so
    end_date is known. Kills the councilmember->mayor cross-tenure smear structurally,
    obviating the per-city de-smear overrides (Park City Worel, St George Randall)."""
    dates = load_vote_dates(cfg)
    for r in rows:
        if r["person_key"] == "vacant":
            continue                                   # VACANT rows carry no bounds
        if cfg.non_voting_mayor and r["body"] == "Mayor":
            r["first_vote"] = r["last_vote"] = ""      # presides/tie-break only
            continue
        ds = dates.get(r["person_key"], [])
        end = r["end_date"] or "9999-12-31"            # open tenure => no upper bound
        inwin = [d for d in ds if r["start_date"] <= d < end]
        r["first_vote"] = inwin[0] if inwin else ""
        r["last_vote"] = inwin[-1] if inwin else ""
    return rows


def vote_window_sentinel(cfg, rows):
    """H-B (2026-07-19) — build-time flag: a db-mapped person who cast Council votes
    OUTSIDE every one of their tenure windows. The tenure-window clamp silently absorbs
    such votes (correct for the roster), but the underlying votes-pipeline artifacts —
    post-departure stray votes (holladay `gibbons` x4), staff/treasurer-as-voter (alta
    `craigheimark`), extraction false-positives — were invisible to the build. Prints
    to stderr, NEVER fails: the roster is right; the flag is about the upstream votes
    layer (queue fixes in TODO, not here). Windows include EVERY tenure the person
    holds (Mayor rows too), so a faithful recorded mayoral tie-break inside a mayor
    tenure never false-flags (the bluffdale S2 class). Unrostered voters are out of
    scope here — that's the update-council-roster skill's unrostered-voter query."""
    dates = load_vote_dates(cfg)
    windows = defaultdict(list)
    for r in rows:
        if r["person_key"] == "vacant":
            continue
        windows[r["person_key"]].append((r["start_date"],
                                         r["end_date"] or "9999-12-31"))
    n_people = 0
    for pk in sorted(dates):
        w = windows.get(pk)
        if not w:
            continue
        stray = [d for d in dates[pk]
                 if not any(s <= d < e for s, e in w)]
        if stray:
            n_people += 1
            shown = ", ".join(stray[:6]) + (" …(+%d)" % (len(stray) - 6)
                                            if len(stray) > 6 else "")
            print("  [vote-window sentinel] %s cast %d Council vote(s) outside every "
                  "tenure window: %s — clamp absorbed it. CAUSE IS UNKNOWN: verify against "
                  "the PRIMARY document before assuming an extraction fault. Known causes, "
                  "all seen 2026-07-29: (1) a SOURCE/clerk error faithfully extracted "
                  "(holladay — a stale closed-session template named a departed member; "
                  "alta — an approved-minutes roll call transposed a name), retain verbatim "
                  "per cardinal rule 2; (2) a real vote on a DIFFERENT body minuted in the "
                  "same file (alta Budget Committee — fix the body walk, not the name); "
                  "(3) a genuine non-council attendee sharing a roster surname "
                  "(emigration_canyon — a county liaison under 'Others Present'); "
                  "(4) an actual extraction artifact. Only (4) is a votes-layer fix"
                  % (pk, len(stray), shown), file=sys.stderr)
    return n_people


# ---------------------------------------------------------------------------
# Layer 4: overrides
# ---------------------------------------------------------------------------
def load_overrides(cfg):
    """Hand corrections applied last (win ties). Keyed by
    (seat_id, person_key, start_date)."""
    ov = {}
    if not os.path.exists(cfg.overrides_path):
        return ov
    with open(cfg.overrides_path, newline="") as f:
        for r in csv.DictReader(row for row in f if not row.lstrip().startswith("#")):
            if not r.get("seat_id") or not r.get("person_key"):
                continue
            ov[(r["seat_id"], r["person_key"], r.get("start_date", ""))] = r
    return ov


def apply_overrides(cfg, rows):
    ov = load_overrides(cfg)
    for r in rows:
        key = (r["seat_id"], r["person_key"], r["start_date"])
        if key in ov:
            for k, v in ov[key].items():
                if k in cfg.columns and v.strip():
                    r[k] = v
            r["sources"] = (r["sources"] + "; override:roster_overrides.csv").strip("; ")


# ---------------------------------------------------------------------------
# Chaining + VACANT-interval insertion
# ---------------------------------------------------------------------------
# H-F (2026-07-19): end_events that TERMINATE a seat itself (no successor will ever
# chain from them). The terminal tenure on such a seat keeps its explicit driver-
# supplied end_date instead of being blanked to "serving" — an abolished seat must
# not resurface in v_council_current (the kearns D5 5->4 HB35 restructure bug,
# previously pinned via roster_overrides.csv).
TERMINAL_END_EVENTS = ("seat-abolished",)


def chain_end_dates(cfg, rows):
    """Compute end_date per seat (a tenure ends when the next on the seat begins)
    and, where a documented departure precedes the successor's start, insert an
    explicit VACANT interval so no two people ever 'hold' one seat and no gap is
    silently swallowed. Cities with no mid-term vacancy yield 0 VACANT rows."""
    by_seat = defaultdict(list)
    for r in rows:
        by_seat[r["seat_id"]].append(r)
    vacants = []
    for seat, trs in by_seat.items():
        trs.sort(key=lambda r: r["start_date"])
        for i, r in enumerate(trs):
            if i + 1 < len(trs):
                nxt = trs[i + 1]
                r["end_date"] = nxt["start_date"]
                if r.get("vacate_date") and r["vacate_date"] < nxt["start_date"]:
                    r["end_date"] = r["vacate_date"]
                    vac = {c: "" for c in cfg.columns}
                    vac.update(city=cfg.city, body=r["body"], seat_id=seat,
                               district=r["district"], person_name="VACANT",
                               person_key="vacant", start_date=r["vacate_date"],
                               end_date=nxt["start_date"], start_event="vacated",
                               end_event="filled",
                               vacate_unrecovered_ack=r.get("vacate_unrecovered_ack", ""),
                               confidence=r.get("vacate_confidence", "high"),
                               sources=r.get("vacate_source", "chained from documented departure"),
                               note="Explicit VACANT interval: seat empty between the "
                                    "predecessor's documented departure and the successor's "
                                    "seating (no two people hold one seat at once).")
                    vacants.append(vac)
            else:
                # terminal tenure on the seat: open-ended (serving) — UNLESS the seat
                # itself was terminated (H-F): a terminating end_event with an explicit
                # driver-supplied end_date keeps that date (there is no successor to
                # chain from, and blanking it would wrongly resurrect the seat).
                if not (r.get("end_event") in TERMINAL_END_EVENTS and r.get("end_date")):
                    r["end_date"] = ""   # currently serving / open-ended
    return rows + vacants


def _unrecovered_dates(cfg):
    """The city's documented un-recovered minutes dates (meetings that exist but whose
    minutes aren't on disk). Used to auto-detect gap-bounded roster claims. Empty set
    if the file is absent."""
    path = os.path.join(cfg.city_dir, "meeting_minutes", "minutes_unrecovered.csv")
    out = set()
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                d = (r.get("date") or "").strip()
                if d:
                    out.add(d)
    return out


def validate(cfg, rows):
    """No two tenures overlap on a seat_id; every row has sources + a valid
    confidence + a known seat_id; and no `high` claim rests on an un-recovered
    minutes gap."""
    errs = []
    unrec = _unrecovered_dates(cfg)
    if cfg.non_voting_mayor:
        for r in rows:
            if r["body"] == "Mayor" and (r["first_vote"] or r["last_vote"]):
                errs.append("non_voting_mayor set but MAYOR row carries vote bounds "
                            "(%s %s) — a tie-break vote leaked into the span"
                            % (r["seat_id"], r["person_key"]))
    for r in rows:
        if not r["sources"].strip():
            errs.append("missing sources: %s %s" % (r["seat_id"], r["person_key"]))
        if r["confidence"] not in ("high", "medium", "low"):
            errs.append("bad confidence '%s': %s %s"
                        % (r["confidence"], r["seat_id"], r["person_key"]))
        if r["seat_id"] not in cfg.seat_district:
            errs.append("unknown seat_id %s" % r["seat_id"])
        # Gap-provenance guard (added 2026-07-11 after the Vineyard audit): a tenure
        # that vacates mid-term cannot be MORE confident than the evidence for HOW/WHEN
        # it ended. If the vacancy is only gap-bounded (vacate_confidence=medium/low),
        # the departing tenure — and the VACANT row it spawns — must be capped to match.
        # Prevents a `high` row whose end date rests on an un-recovered minutes gap
        # (the Vineyard Cameron→Nair defect).
        _rank = {"high": 3, "medium": 2, "low": 1}
        if r.get("vacate_date"):
            vc = r.get("vacate_confidence", "high")
            if _rank.get(r["confidence"], 0) > _rank.get(vc, 0):
                errs.append("confidence '%s' exceeds vacate_confidence '%s' (gap-bounded "
                            "departure): %s %s" % (r["confidence"], vc, r["seat_id"],
                                                   r["person_key"]))
        # Auto-detect: a `high` VACANT interval whose window contains an un-recovered
        # minutes date has inferred (not documented) dates — cap it at medium.
        # ACK exception (2026-07-19, found via logan during the H-pass): when BOTH
        # bracket dates of the vacancy are attested in RECOVERED minutes (verbatim
        # resignation date + oath/seating), a mid-window un-recovered date (e.g. an
        # agenda-only interview meeting) does not undermine them. The driver
        # acknowledges each such date explicitly via `vacate_unrecovered_ack`
        # (comma-separated dates) on the departing tenure, with the justification
        # documented in vacate_source. A stale/mis-dated ack fails loudly.
        if r["start_event"] == "vacated" and unrec:
            ack = {d.strip() for d in
                   (r.get("vacate_unrecovered_ack") or "").split(",") if d.strip()}
            for d in sorted(ack):
                if d not in unrec or not (r["start_date"] <= d < r["end_date"]):
                    errs.append("stale vacate_unrecovered_ack date %s on VACANT %s "
                                "[%s,%s) — not an un-recovered minutes date inside "
                                "the window (remove or fix the ack)"
                                % (d, r["seat_id"], r["start_date"], r["end_date"]))
            if r["confidence"] == "high":
                gap = sorted(d for d in unrec
                             if r["start_date"] <= d < r["end_date"] and d not in ack)
                if gap:
                    errs.append("VACANT %s [%s,%s) marked 'high' but its window contains "
                                "un-recovered minutes %s — dates inferred; set "
                                "vacate_confidence<=medium on the predecessor (or, if "
                                "both bracket dates are attested in recovered minutes, "
                                "acknowledge via vacate_unrecovered_ack + vacate_source)"
                                % (r["seat_id"], r["start_date"], r["end_date"], gap))
    by_seat = defaultdict(list)
    for r in rows:
        by_seat[r["seat_id"]].append(r)
    for seat, trs in by_seat.items():
        trs.sort(key=lambda r: r["start_date"])
        for a, b in zip(trs, trs[1:]):
            if a["end_date"] and a["end_date"] > b["start_date"]:
                errs.append("OVERLAP on %s: %s ends %s > %s starts %s"
                            % (seat, a["person_key"], a["end_date"],
                               b["person_key"], b["start_date"]))
    return errs


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------
def write_csv(path, columns, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_terms(cfg, rows):
    if cfg.seat_order:
        rows.sort(key=lambda r: (cfg.seat_order.index(r["seat_id"]), r["start_date"]))
    else:
        rows.sort(key=lambda r: (r["body"] != "Mayor", r["seat_id"], r["start_date"]))
    write_csv(cfg.terms_out, cfg.columns, rows)


def write_districts(cfg):
    """district_versions.csv — one degenerate row (at-large) OR the real
    districts × two plans + citywide/mayor rows (district city)."""
    rows = []
    if cfg.redistrict is None:
        row = dict(cfg.atlarge)
        row["city"] = cfg.city
        rows.append(row)
    else:
        rd = cfg.redistrict
        # H-H: a district-count-changing redistricting supplies districts_old — the
        # prior plan's own list — so an abolished district still gets its honest
        # plan_old row. None (default) = same list (byte-identical for every city).
        d_old = rd.districts_old if rd.districts_old is not None else rd.districts

        def _prior_row(d):
            if isinstance(rd.prior_confidence, dict):
                pconf = rd.prior_confidence.get(d, rd.prior_confidence_default)
            else:
                pconf = rd.prior_confidence
            pnote = rd.prior_note_by_district.get(d, rd.prior_note)
            return dict(
                city=cfg.city, district_id=d, plan_id=rd.plan_old,
                effective_start=rd.data_floor, effective_end=rd.plan_switch,
                geometry_ref=rd.prior_geom_ref, adopted_by=rd.prior_adopted_by,
                source_url=rd.prior_source_url, confidence=pconf, note=pnote)

        for d in rd.districts:
            rows.append(dict(
                city=cfg.city, district_id=d, plan_id=rd.plan_new,
                effective_start=rd.plan_switch, effective_end="",
                geometry_ref=rd.geom_ref, adopted_by=rd.ord,
                source_url=rd.source_url, confidence=rd.current_confidence,
                note=rd.current_note))
            if d in d_old:
                rows.append(_prior_row(d))
        for d in d_old:                      # abolished districts (in old, not new)
            if d not in rd.districts:
                rows.append(_prior_row(d))
        for did, plan, who in rd.citywide_rows:
            rows.append(dict(
                city=cfg.city, district_id=did, plan_id=plan,
                effective_start=rd.data_floor, effective_end="",
                geometry_ref=rd.geom_ref, adopted_by=rd.citywide_adopted_by,
                source_url=rd.source_url, confidence="high",
                note=rd.citywide_note_template.format(who=who)))
    write_csv(cfg.districts_out, DISTRICT_COLUMNS, rows)


def _hi_srcs(rd):
    """The source_year value(s) that earn precinct confidence=high. Accepts a single token
    (str) OR several (tuple/list/set), so a city whose canonical `geo/precinct_to_district.csv`
    carries per-row years for ONE current plan (e.g. 2023 + 2025) marks them ALL high with no
    collapse sidecar. Backward-compatible with the old single-string form."""
    h = rd.precinct_hi_source
    return tuple(h) if isinstance(h, (tuple, list, set)) else (h,)


def _winner_matches(cfg, sovc_upper, roster_name):
    """Robust precinct-sum-winner vs roster-winner compare: resolve BOTH to a person_key via
    canon_key so name-format differences (middle names, case — 'ERNEST GLEN BURGESS' vs
    'Ernest Glen Burgess', 'RICHARD HYER' vs 'Rich Hyer') never false-flag; fall back to
    shared-surname token overlap when a name doesn't resolve. Only a genuine person mismatch
    reads as DISCREPANCY. Replaces the old exact-string compare that forced per-city
    crosscheck_districts exclusions + hand-verification."""
    if not roster_name:
        return False
    spk, rpk = canon_key(cfg, sovc_upper), canon_key(cfg, roster_name.upper())
    if spk and rpk:
        return spk == rpk
    def toks(s):
        return [t for t in s.upper().replace(".", "").replace(",", "").split() if t.isalpha()]
    st, rt = toks(sovc_upper), toks(roster_name)
    return bool(st and rt and st[-1] == rt[-1])   # shared surname (last alpha token)


def write_precincts(cfg):
    """district_precincts.csv — versioned precinct→district composition
    (plan-scoped). Only meaningful for a district city with a precinct map."""
    rd = cfg.redistrict
    rows = []
    with open(cfg.precinct_map_path, newline="") as f:
        for r in csv.DictReader(f):
            # H-A: a canonical precinct map with no source_year column/value falls back
            # to the EXPLICITLY configured token (rd.precinct_source_default). No config
            # -> fail loudly, exactly as visible as the old KeyError: a silently
            # defaulted source would erode the high/medium provenance.
            src = (r.get("source_year") or "").strip() or rd.precinct_source_default
            if not src:
                raise SystemExit(
                    "write_precincts: %s has no source_year for precinct %r and "
                    "rd.precinct_source_default is not set — refusing to default "
                    "silently (H-A)" % (cfg.precinct_map_path, r.get("precinct")))
            hi = src in _hi_srcs(rd)
            rows.append(dict(
                city=cfg.city, plan_id=rd.plan_new,
                district_id="District " + r["district"], precinct_id=r["precinct"],
                effective_start=rd.plan_switch, effective_end="",
                source="geo/precinct_to_district.csv (" + src + ")",
                confidence="high" if hi else "medium",
                note=rd.precinct_hi_note if hi else rd.precinct_med_note))
    if cfg.prior_precinct_map_path and os.path.exists(cfg.prior_precinct_map_path):
        # Reconstructed prior-plan composition: populate the plan_old rows with the real
        # pre-2022 precinct->district assignment (confidence=medium, approximate — see note).
        with open(cfg.prior_precinct_map_path, newline="") as f:
            for r in csv.DictReader(f):
                rows.append(dict(
                    city=cfg.city, plan_id=rd.plan_old,
                    district_id="District " + r["district"], precinct_id=r["precinct"],
                    effective_start=rd.data_floor, effective_end=rd.plan_switch,
                    source=os.path.basename(cfg.prior_precinct_map_path),
                    confidence="medium", note=rd.precinct_prior_note))
    else:
        # H-H: the plan_old GAP rows iterate the PRIOR plan's district list when a
        # redistricting changed the district count (abolished districts included).
        for d in [x.split()[-1] for x in (rd.districts_old
                                          if rd.districts_old is not None
                                          else rd.districts)]:
            rows.append(dict(
                city=cfg.city, plan_id=rd.plan_old, district_id="District " + d,
                precinct_id="", effective_start=rd.data_floor,
                effective_end=rd.plan_switch, source="", confidence="low",
                note=rd.precinct_prior_note))
    rows.sort(key=lambda r: (r["plan_id"] != rd.plan_new, r["district_id"],
                             r["precinct_id"]))
    write_csv(cfg.precincts_out, PRECINCT_COLUMNS, rows)


# ---------------------------------------------------------------------------
# The full pipeline
# ---------------------------------------------------------------------------
def build(cfg, tenures):
    rows = []
    for t in tenures:
        r = {c: "" for c in cfg.columns}
        r.update({k: v for k, v in t.items() if k in cfg.columns})
        r["city"] = cfg.city
        r["district"] = cfg.seat_district[t["seat_id"]]
        r["vacate_date"] = t.get("vacate_date", "")       # carried for chaining only
        r["vacate_source"] = t.get("vacate_source", "")
        r["vacate_confidence"] = t.get("vacate_confidence", "high")
        r["vacate_unrecovered_ack"] = t.get("vacate_unrecovered_ack", "")
        rows.append(r)

    election_crosscheck(cfg, rows)
    reverse_election_crosscheck(cfg, rows)   # H-C: tenure -> winner-row (informational)

    rows = chain_end_dates(cfg, rows)
    # Vote bounds are clamped to each tenure's [start,end) window — must run AFTER
    # chaining (end_date must be known). See clamp_vote_bounds().
    clamp_vote_bounds(cfg, rows)
    apply_overrides(cfg, rows)
    vote_window_sentinel(cfg, rows)          # H-B: stray-vote flag (informational)

    errs = validate(cfg, rows)
    if errs:
        print("VALIDATION ERRORS:", file=sys.stderr)
        for e in errs:
            print("  " + e, file=sys.stderr)
        raise SystemExit(1)

    write_terms(cfg, rows)
    write_districts(cfg)
    if cfg.precinct_map_path:
        write_precincts(cfg)
    return rows


# ---------------------------------------------------------------------------
# Query helpers (read the written CSVs)
# ---------------------------------------------------------------------------
def load_terms(cfg):
    with open(cfg.terms_out, newline="") as f:
        return list(csv.DictReader(f))


def load_district_versions(cfg):
    with open(cfg.districts_out, newline="") as f:
        return list(csv.DictReader(f))


def roster_as_of(cfg, date, body=None):
    """All tenures active on `date` (start <= date < end, end blank = serving)."""
    out = []
    for r in load_terms(cfg):
        if body and r["body"] != body:
            continue
        if r["start_date"] and r["start_date"] > date:
            continue
        if r["end_date"] and r["end_date"] <= date:
            continue
        out.append(r)
    if cfg.seat_order:
        order = cfg.seat_order
        return sorted(out, key=lambda r: order.index(r["seat_id"])
                      if r["seat_id"] in order else 99)
    return sorted(out, key=lambda r: r["seat_id"])


def _resolve_address_to_district(cfg, address, latlon_fallback=None,
                                 precinct_fallback=None):
    """address -> (district, precinct, method). Tries the real geo tool; degrades
    gracefully (offline / no geopandas) to a stated lat-lon then a stated precinct."""
    sys.path.insert(0, os.path.join(cfg.city_dir, "geo"))
    try:
        import address_to_district as a2d
        info = a2d.district_for_address(address)
        if info.get("district"):
            return info["district"], info.get("precinct"), "geocode+point-in-polygon"
        if latlon_fallback:
            info = a2d.district_for_point(latlon_fallback[1], latlon_fallback[0])
            if info.get("district"):
                return info["district"], info.get("precinct"), "offline lat/lon point-in-polygon"
    except Exception as e:
        print("    (geo tool unavailable: %s; using stated precinct)"
              % e.__class__.__name__)
    if precinct_fallback:
        with open(cfg.precinct_map_path, newline="") as f:
            m = {r["precinct"]: r["district"] for r in csv.DictReader(f)}
        return (m.get(precinct_fallback), precinct_fallback,
                "stated precinct -> precinct_to_district.csv")
    return None, None, "unresolved"


def _point_in_geojson_geom(lon, lat, geom):
    """Pure-python even-odd ray-cast containment test for a GeoJSON Polygon /
    MultiPolygon (holes handled by the even-odd rule; no geopandas dependency,
    so the prior-plan query path works in the same degraded environments as the
    rest of the query helpers)."""
    def _in_rings(rings):
        inside = False
        for ring in rings:
            j = len(ring) - 1
            for i in range(len(ring)):
                xi, yi = ring[i][0], ring[i][1]
                xj, yj = ring[j][0], ring[j][1]
                if (yi > lat) != (yj > lat) and \
                        lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
                    inside = not inside
                j = i
        return inside
    if geom["type"] == "Polygon":
        return _in_rings(geom["coordinates"])
    if geom["type"] == "MultiPolygon":
        return any(_in_rings(p) for p in geom["coordinates"])
    return False


def _latlon_for_address(cfg, address, latlon):
    """(lon, lat) for the query point: geocode via the city's own geo tool when
    possible (same Census geocoder the current-plan path uses), else the caller's
    stated latlon=(lat, lon) fallback. Returns None when neither works."""
    sys.path.insert(0, os.path.join(cfg.city_dir, "geo"))
    try:
        import address_to_district as a2d
        g = a2d.geocode(address)
        if g:
            return g[0], g[1]                      # geocode() returns (lon, lat, matched)
    except Exception:
        pass
    if latlon:
        return latlon[1], latlon[0]                # latlon is (lat, lon)
    return None


def _prior_plan_district(cfg, geometry_ref, lon, lat):
    """Point-in-polygon against a PRIOR plan's district geojson (repo convention:
    property `district` = the bare number, e.g. '1'..'7'; falls back to digits in a
    'DIST'/'District' field). Returns the bare district number or None."""
    import json
    path = os.path.join(cfg.city_dir, geometry_ref)
    with open(path) as f:
        gj = json.load(f)
    for feat in gj.get("features", []):
        if _point_in_geojson_geom(lon, lat, feat["geometry"]):
            props = feat.get("properties", {})
            for key in ("district", "DIST", "District"):
                val = props.get(key)
                if val is not None and str(val).strip():
                    digits = "".join(ch for ch in str(val) if ch.isdigit())
                    return digits or str(val).strip()
    return None


def representatives_for_address(cfg, address, date, latlon=None, precinct=None):
    """address + date → representatives, wired THROUGH district_versions.

    AT-LARGE city (redistrict is None): resolves the whole city to its single
    district and returns (district_id, all sitting council members + mayor).

    DISTRICT city: resolves the address via geo/address_to_district.py to one
    District N, returns that district's rep on `date` PLUS both citywide members
    and the mayor. Honors district_versions: a date under an unacquired plan is an
    honest GAP (never a fabricated district). Returns a dict.

    PRIOR-PLAN dates (2026-07-19, confidence-gated): a date under the PRIOR plan
    resolves by point-in-polygon against that plan's own geojson ONLY when the
    plan_old `district_versions` row for the HIT district carries a non-blank
    geometry_ref AND confidence high/medium (the gate is data-driven from the
    written district_versions.csv, so per-district confidences — e.g. slc's — gate
    per district: a `low` district NEVER resolves even if its neighbors could).
    A resolved prior-plan hit carries `plan_provenance` (plan id, district,
    geometry confidence, geometry_ref, source_url, adopted_by) so downstream
    output can cite it honestly. Blank-geometry plans keep the original
    "boundaries not acquired" gap verbatim; low-confidence geometry returns an
    explanatory gap (approximate reconstruction — not resolved) — never a
    resolution. Today exactly one city qualifies: millcreek (plan_2016, HIGH —
    the authoritative city-GIS 2017-2022 layer; see scripts/roster_boundary_recon.md).
    Current-plan behavior is byte-identical to before."""
    if cfg.redistrict is None:
        dv = [d for d in load_district_versions(cfg)
              if (not d["effective_start"] or d["effective_start"] <= date)
              and (not d["effective_end"] or d["effective_end"] > date)]
        if not dv:
            return "At-Large", []
        district_id = dv[0]["district_id"]
        reps = [r for r in roster_as_of(cfg, date, body="Council")
                if r["district"] == district_id]
        mayor = roster_as_of(cfg, date, body="Mayor")
        return district_id, reps + mayor

    rd = cfg.redistrict
    dvs = load_district_versions(cfg)
    geo_plan = None
    for dv in dvs:
        if dv["district_id"].startswith("District 1"):
            if (not dv["effective_start"] or dv["effective_start"] <= date) and \
               (not dv["effective_end"] or dv["effective_end"] > date):
                geo_plan = dv["plan_id"]
    result = {"date": date, "plan": geo_plan}
    if geo_plan == rd.plan_old:
        # Confidence-gated PRIOR-PLAN resolution (2026-07-19). Data-driven from the
        # written district_versions.csv plan_old rows — never from config prose.
        prior = {dv["district_id"]: dv for dv in dvs
                 if dv["plan_id"] == rd.plan_old
                 and dv["district_id"].startswith("District")}
        result["district"] = None
        geo_rep = []
        with_geom = {d: dv for d, dv in prior.items()
                     if (dv.get("geometry_ref") or "").strip()}
        gated_ok = {d: dv for d, dv in with_geom.items()
                    if dv.get("confidence") in ("high", "medium")}
        if not with_geom:
            # No prior geometry on disk at all — the original honest gap, verbatim.
            result["gap"] = ("%s boundaries not acquired — cannot resolve the geographic "
                             "district for a pre-%s date without fabricating (honest gap)"
                             % (rd.plan_old, rd.plan_switch[:4]))
        elif not gated_ok:
            # Geometry exists but EVERY district is low-confidence (e.g. the six SLCo
            # current-shape dissolves over renumbered precinct codes) — never resolve.
            result["gap"] = ("%s prior-plan geometry is low-confidence (approximate "
                             "reconstruction — see district_versions note) — not "
                             "resolved (honest gap)" % rd.plan_old)
        else:
            pt = _latlon_for_address(cfg, address, latlon)
            if pt is None:
                result["method"] = "unresolved (no coordinates for prior-plan lookup)"
            else:
                lon, lat = pt
                geometry_ref = next(iter(gated_ok.values()))["geometry_ref"]
                dist = _prior_plan_district(cfg, geometry_ref, lon, lat)
                if dist is None:
                    result["method"] = ("prior-plan point-in-polygon (%s): point outside "
                                        "every district polygon" % geometry_ref)
                else:
                    label = "District " + dist
                    dv = prior.get(label)
                    conf = dv.get("confidence") if dv else None
                    if dv is None or conf not in ("high", "medium"):
                        # Per-district gate: the HIT district is low/unlisted — an honest
                        # gap even when neighboring districts could have resolved.
                        result["gap"] = ("%s %s geometry is %s-confidence (approximate "
                                         "reconstruction — see district_versions note) — "
                                         "not resolved (honest gap)"
                                         % (rd.plan_old, label, conf or "unknown"))
                    else:
                        result["district"] = dist
                        result["precinct"] = None
                        result["method"] = ("prior-plan point-in-polygon (%s)"
                                            % dv["geometry_ref"])
                        result["plan_provenance"] = {
                            "plan_id": rd.plan_old,
                            "district_id": label,
                            "geometry_confidence": conf,
                            "geometry_ref": dv["geometry_ref"],
                            "source_url": dv.get("source_url", ""),
                            "adopted_by": dv.get("adopted_by", ""),
                        }
                        seat = rd.geo_seat_prefix + dist
                        geo_rep = [r for r in roster_as_of(cfg, date, body="Council")
                                   if r["seat_id"] == seat]
    else:
        dist, prec, method = _resolve_address_to_district(cfg, address, latlon, precinct)
        result["district"], result["precinct"], result["method"] = dist, prec, method
        seat = rd.geo_seat_prefix + str(dist) if dist else None
        geo_rep = [r for r in roster_as_of(cfg, date, body="Council")
                   if r["seat_id"] == seat]
    citywide = [r for r in roster_as_of(cfg, date, body="Council")
                if r["seat_id"] in rd.citywide_seats]
    mayor = roster_as_of(cfg, date, body="Mayor")
    result["reps"] = geo_rep + citywide + mayor
    return result


def precinct_crosscheck(cfg, verbose=True):
    """District city: group precinct votes by the district_precincts (plan_new)
    assignment and confirm the winner matches the roster. Pre-switch cycles fall
    under plan_old (old precinct numbering) → reported as an honest GAP."""
    rd = cfg.redistrict
    p2d = {}
    with open(cfg.precinct_map_path, newline="") as f:
        for r in csv.DictReader(f):
            p2d[r["precinct"]] = r["district"]
    terms = load_terms(cfg)
    results = []
    by = defaultdict(lambda: defaultdict(int))
    skipped = 0
    with open(cfg.precincts_byprecinct_path, newline="") as f:
        for r in csv.DictReader(f):
            if r["election_type"] != "municipal general" or r["office"] != "Council":
                continue
            if r["district"] not in rd.crosscheck_districts:
                continue
            # blank / suppressed / non-numeric vote guard — a canonical by-precinct file may carry
            # voter-privacy-suppressed rows (a `suppressed` column) and empty/non-numeric vote cells.
            # Honoring both here replaces the per-city _precinct_votes sidecar entirely.
            if (r.get("suppressed") or "").strip().lower() == "true":
                skipped += 1
                continue
            v = (r.get("votes") or "").strip()
            try:
                votes = int(float(v))
            except (ValueError, TypeError):
                skipped += 1
                continue
            prec = r["precinct"].strip()
            prec25 = prec if prec.startswith(rd.precinct_prefix) else rd.precinct_prefix + prec
            mapped = p2d.get(prec25)
            by[(r["year"], r["district"])][r["candidate"]] += votes
            if mapped and mapped != r["district"] and r["year"] in _hi_srcs(rd):
                results.append(("MISMATCH", r["year"], r["district"], prec25, mapped))
    if verbose and skipped:
        print("  [precinct cross-check] skipped %d blank/non-numeric vote cell(s)" % skipped)
    for (year, dist), tally in sorted(by.items()):
        plan = rd.plan_new if year >= rd.plan_switch_year else rd.plan_old
        winner = max(tally, key=tally.get).title()
        seat = rd.geo_seat_prefix + dist
        roster_winner = next((t["person_name"] for t in terms
                              if t["seat_id"] == seat and t["election_year"] == year
                              and t["start_event"] in ("elected", "reelected")), None)
        if plan == rd.plan_old:
            status = "GAP (%s old precinct numbering; composition not acquired)" % rd.plan_old
            ok = None
        else:
            ok = _winner_matches(cfg, max(tally, key=tally.get), roster_winner)
            status = "RECONCILES" if ok else "DISCREPANCY"
        if verbose:
            tot = sum(tally.values())
            print("  %s %s%s [%s] %s" % (year, rd.geo_seat_prefix, dist, plan, status))
            for c, v in sorted(tally.items(), key=lambda x: -x[1]):
                print("       %-22s%6d (%.1f%%)" % (c, v, 100 * v / tot))
            print("       precinct-sum winner=%s  roster winner=%s" % (winner, roster_winner))
        results.append((status, year, dist, winner, roster_winner))
    return results
