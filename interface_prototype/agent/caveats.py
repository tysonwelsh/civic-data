"""Attach gov.db's measurement ceilings to every result set.

This is the mechanism the whole design rests on (CHAT_PLAN.md §2.1). After a
query runs, the executor scans the SQL *and* the returned rows for entity and
dataset signals, looks up the matching rows in gov.db's ``caveat`` table, and
appends them to the tool result. **Claude cannot receive data without also
receiving its limits.**

The distinction that matters: this is not "the model remembered to mention the
caveat", it is "the caveat was structurally impossible to omit". It converts
the caveat table from documentation into a runtime component.

Two products come out of here:

``caveats``  — rows from the ``caveat`` table, selected by (entity, dataset).
``notes``    — query-shape warnings for the documented traps that no caveat row
               covers, because they are properties of the *question* rather
               than of an entity: summing overlapping cf_filing dollars,
               applying the city-tier provenance filter across tiers, and so on.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from . import config, guard


# --------------------------------------------------------------------------
# the index, loaded once from the database
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Caveat:
    city: str
    dataset: str
    code: str
    text: str

    def to_dict(self, entity_name: str | None = None) -> dict:
        return {
            "entity": self.city,
            "entity_name": entity_name,
            "dataset": self.dataset,
            "code": self.code,
            "caveat": self.text,
        }


class Index:
    """Slugs, display names, datasets and caveat rows, read from gov.db."""

    def __init__(self) -> None:
        _, rows = guard.query_rows(
            "SELECT slug, name, level, dir, db_rel_path FROM entity ORDER BY slug"
        )
        self.entities: dict[str, dict] = {
            slug: {"slug": slug, "name": name, "level": level,
                   "dir": dir_, "db_rel_path": db_rel or ""}
            for slug, name, level, dir_, db_rel in rows
        }
        # Longest names first so "Salt Lake City" wins over "Salt Lake County"
        # never being reached; both are present, matching is exact anyway.
        self.by_name: dict[str, str] = {
            e["name"].lower(): slug for slug, e in self.entities.items() if e["name"]
        }

        _, crows = guard.query_rows("SELECT city, dataset, code, caveat FROM caveat")
        self.caveats: list[Caveat] = [Caveat(*r) for r in crows]
        self.datasets: set[str] = {c.dataset for c in self.caveats} - {"*"}

        # \b works for every slug in the registry (all are [a-z_]+).
        self._slug_re = re.compile(
            r"\b(" + "|".join(re.escape(s) for s in sorted(self.entities, key=len, reverse=True)) + r")\b"
        )
        self._dataset_re = re.compile(
            r"\b(" + "|".join(re.escape(d) for d in sorted(self.datasets, key=len, reverse=True)) + r")\b"
        )

    def name_of(self, slug: str) -> str | None:
        entity = self.entities.get(slug)
        return entity["name"] if entity else None

    def level_of(self, slug: str) -> str | None:
        entity = self.entities.get(slug)
        return entity["level"] if entity else None


_INDEX: Index | None = None


def index() -> Index:
    global _INDEX
    if _INDEX is None:
        _INDEX = Index()
    return _INDEX


def reset() -> None:
    """Drop the cached index — used by tests and after a federation rebuild."""
    global _INDEX
    _INDEX = None


# --------------------------------------------------------------------------
# table -> dataset inference
#
# A query naming no dataset still tells us which measurement axis it sits on,
# because the table it reads implies one. `legislative` / `land_use` are the
# NON-CITY dataset vocabulary (body-derived at federation), and in the live
# caveat table only the four city='*' rows use them.
# --------------------------------------------------------------------------

_VOTE_SPINE = ("meeting_minutes", "planning_commission")
_NONCITY_MOTION = ("legislative", "land_use")

TABLE_DATASETS: dict[str, tuple[str, ...]] = {
    # vote spine
    "motion": _VOTE_SPINE + _NONCITY_MOTION,
    "motion_std": _VOTE_SPINE + _NONCITY_MOTION,
    "vote": _VOTE_SPINE + _NONCITY_MOTION,
    "meeting": _VOTE_SPINE,
    "body": _VOTE_SPINE,
    "role": _VOTE_SPINE,
    "person": _VOTE_SPINE,
    "referral": _VOTE_SPINE,
    "application": _VOTE_SPINE,
    "ordinance": _VOTE_SPINE,
    "fts_minutes": _VOTE_SPINE,
    "fts_motion": _VOTE_SPINE + _NONCITY_MOTION,
    "fts_ordinance": _VOTE_SPINE,
    "fts_packet": _VOTE_SPINE,
    "v_contested_all": _VOTE_SPINE + _NONCITY_MOTION,
    "v_member_record_all": _VOTE_SPINE + _NONCITY_MOTION,
    "v_landuse_outcomes": _VOTE_SPINE + _NONCITY_MOTION,
    "v_pc_divergence": _VOTE_SPINE,
    "v_coverage": _VOTE_SPINE + _NONCITY_MOTION,
    # comments
    "comment": ("public_comments",),
    "fts_comment": ("public_comments",),
    # elections
    "election_race": ("election_results",),
    "election_result": ("election_results",),
    "v_election_city": ("election_results",),
    # campaign finance
    "cf_filing": ("campaign_finance",),
    "cf_contribution": ("campaign_finance",),
    "cf_expenditure": ("campaign_finance",),
    "cf_cycle": ("campaign_finance",),
    "cf_candidate_person": ("campaign_finance",),
    # regional lifecycle
    "project_vintage": ("project_vintage",),
    "project_history": ("project_history",),
}

_TABLE_RE = re.compile(
    r"\b(?:from|join)\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE
)


def tables_in(scrubbed_sql: str) -> set[str]:
    """Table/view names following FROM or JOIN, lowercased."""
    return {m.group(1).lower() for m in _TABLE_RE.finditer(scrubbed_sql)}


# --------------------------------------------------------------------------
# detection
# --------------------------------------------------------------------------

def _cell_strings(columns: list[str], rows: Iterable[Iterable[Any]]) -> set[str]:
    """Distinct short string values in the result — where slugs show up."""
    seen: set[str] = set()
    for row in rows:
        for value in row:
            if isinstance(value, str) and 0 < len(value) <= 64:
                seen.add(value)
    return seen


def detect(sql: str, columns: list[str] | None = None,
           rows: Iterable[Iterable[Any]] | None = None) -> tuple[set[str], set[str], set[str]]:
    """Return ``(entities, datasets, tables)`` implicated by a query + result.

    Entities are found three ways, because any one alone has a blind spot:
    a slug written in the SQL (``WHERE city='nephi'`` — a result that is just a
    COUNT carries no slug at all), a slug appearing in a returned cell (a
    ``GROUP BY city`` sweep names them only in the rows), and a display name in
    a string literal (``WHERE name='Salt Lake City'``).
    """
    idx = index()
    scrubbed = guard.scrub(sql)
    lowered = sql.lower()

    entities = set(idx._slug_re.findall(lowered))
    datasets = set(idx._dataset_re.findall(lowered))

    for literal in guard.string_literals(sql):
        slug = idx.by_name.get(literal.strip().lower())
        if slug:
            entities.add(slug)

    if columns is not None and rows is not None:
        for value in _cell_strings(columns, rows):
            if value in idx.entities:
                entities.add(value)
            elif value.lower() in idx.by_name:
                entities.add(idx.by_name[value.lower()])
            if value in idx.datasets:
                datasets.add(value)

    tables = tables_in(scrubbed)
    for table in tables:
        datasets.update(TABLE_DATASETS.get(table, ()))

    return entities, datasets, tables


# --------------------------------------------------------------------------
# selection
# --------------------------------------------------------------------------

# A 31-city sweep can implicate more caveats than fit in a tool result. When
# the list has to be cut, cut it from the bottom of THIS ranking rather than
# from the end of the alphabet: a recording ceiling changes whether two cities
# may be compared at all, and must survive truncation.
_PRIORITY: dict[str, int] = {
    # 0 — comparability-breaking: the number means something different here
    "tally-only": 0, "tally-only-partial": 0, "dissent-only": 0,
    "vote-ceiling": 0, "vote-format-note": 0, "mayor-vote": 0,
    "mayor-nonvote": 0, "rcv": 0, "disjoint-persons": 0,
    # 1 — coverage floors and honest zeros: the denominator is not what it seems
    "coverage-floor": 1, "coverage-note": 1, "body-gap": 1,
    "elections-2019-floor": 1, "elections-coverage": 1, "cf-coverage": 1,
    "cf-honest-zero": 1, "cf-unstructured": 1, "cf-partial-structured": 1,
    "cf-totals-tier": 1, "cf-blocked-cycles": 1, "cf-county-eras": 1,
    "comments-honest-zero": 1, "comments-two-cities": 1, "comments-in-packets": 1,
    "disposition-coverage": 1, "motion-std-computed-tier": 1,
    "motion-std-classification-ceiling": 1, "motion-std-deferred": 1,
    "landuse-undercount": 1, "outcome-unknown": 1, "county-canvass": 1,
    "county-office-suppression": 1, "county-primary-nominees": 1,
    "regional-model-note": 1,
}
_DEFAULT_PRIORITY = 2


def _rank(caveat: Caveat) -> tuple:
    return (_PRIORITY.get(caveat.code, _DEFAULT_PRIORITY), caveat.city,
            caveat.dataset, caveat.code)


def applicable(sql: str, columns: list[str] | None = None,
               rows: Iterable[Iterable[Any]] | None = None,
               max_caveats: int = config.MAX_CAVEATS) -> dict:
    """The caveat rows that govern how this result may be read."""
    idx = index()
    rows = list(rows) if rows is not None else None
    entities, datasets, tables = detect(sql, columns, rows)

    # `legislative` / `land_use` are the NON-CITY dataset vocabulary (body-derived
    # at federation). If every entity in scope is a city, those axes cannot apply
    # and their caveats would be noise on an otherwise clean city answer.
    if entities and all(idx.level_of(e) == "city" for e in entities):
        datasets -= set(_NONCITY_MOTION)

    def dataset_matches(caveat: Caveat) -> bool:
        if caveat.dataset == "*":
            return True
        if not datasets:
            # No dataset signal at all: an entity's ceilings all still apply.
            return True
        return caveat.dataset in datasets

    entity_hits: list[Caveat] = []
    wildcard_hits: list[Caveat] = []
    for caveat in idx.caveats:
        if not dataset_matches(caveat):
            continue
        if caveat.city == "*":
            # Repo-wide rows only make sense when a dataset actually put them
            # in scope; otherwise every query would drag all eight along.
            if caveat.dataset in datasets:
                wildcard_hits.append(caveat)
        elif caveat.city in entities:
            entity_hits.append(caveat)

    entity_hits.sort(key=_rank)
    wildcard_hits.sort(key=_rank)

    # A repo-wide caveat registered under both non-city dataset axes is one
    # caveat, not two — collapse identical text so the model sees it once.
    seen_text: set[tuple[str, str]] = set()
    deduped: list[Caveat] = []
    for caveat in wildcard_hits:
        key = (caveat.code, caveat.text)
        if key in seen_text:
            continue
        seen_text.add(key)
        deduped.append(caveat)
    selected = entity_hits + deduped

    truncated = len(selected) > max_caveats
    shown = selected[:max_caveats]
    dropped = selected[max_caveats:]

    return {
        "caveats": [c.to_dict(idx.name_of(c.city)) for c in shown],
        "caveat_count": len(selected),
        "caveats_truncated": truncated,
        "caveats_omitted": [f"{c.city}/{c.dataset}: {c.code}" for c in dropped],
        "entities_detected": sorted(entities),
        "datasets_detected": sorted(datasets),
        "notes": notes(sql, entities, datasets, tables, columns, rows),
    }


# --------------------------------------------------------------------------
# query-shape notes — the traps no caveat row can carry
# --------------------------------------------------------------------------

RCV_CITIES = {"millcreek", "draper", "bluffdale"}
MPO_SLUGS = {"wfrc_mpo", "mag_mpo"}

_AGG_RE = re.compile(r"\b(sum|total|avg)\s*\(", re.IGNORECASE)
_GROUP_RE = re.compile(r"\bgroup\s+by\b", re.IGNORECASE)
_CF_AMOUNT_RE = re.compile(
    r"\b(sum|total)\s*\(\s*(distinct\s+)?[A-Za-z_.]*"
    r"(amount|total|contribution|expenditure|receipt|balance|raised|spent)",
    re.IGNORECASE,
)
# Matched against the RAW sql, not the scrubbed copy: the value it looks for
# lives inside a string literal, which scrub() blanks by design.
_PROVENANCE_MINUTES_RE = re.compile(
    r"provenance\s*(?:=|==|\bin\s*\()\s*'minutes'", re.IGNORECASE
)
_NATIVE_LABEL_RE = re.compile(r"\b(result_raw|motion_type|motion_type_native)\b", re.IGNORECASE)


def notes(sql: str, entities: set[str], datasets: set[str], tables: set[str],
          columns: list[str] | None = None,
          rows: list[list[Any]] | None = None) -> list[str]:
    """Warnings triggered by the *shape* of the query, not by an entity."""
    idx = index()
    scrubbed = guard.scrub(sql)
    out: list[str] = []
    levels = {idx.level_of(e) for e in entities}
    counties = {e for e in entities if idx.level_of(e) == "county"}
    cities = {e for e in entities if idx.level_of(e) == "city"}

    if "cf_filing" in tables and _CF_AMOUNT_RE.search(scrubbed):
        out.append(
            "NEVER sum cf_filing dollar columns — filings overlap (interim + summary "
            "reports restate the same money). cf_cycle carries the only sanctioned "
            "per-candidate totals, and cf_cycle is CITY-ONLY; no county rollups exist."
        )

    if _PROVENANCE_MINUTES_RE.search(sql) and "gov_level" not in sql.lower():
        out.append(
            "provenance has TWO vocabularies by tier. On the city tier 'minutes' means "
            "audited primary; on the county/regional/state tier the column holds "
            "EXTRACTOR names (tesseract, county_portal, legistar, …). A bare "
            "provenance='minutes' filter silently drops ~84% of county motions. "
            "Add gov_level='city' if the city-tier meaning is what you want."
        )

    if _NATIVE_LABEL_RE.search(scrubbed) and (_GROUP_RE.search(scrubbed) or _AGG_RE.search(scrubbed)):
        if len(entities) != 1:
            out.append(
                "result_raw / motion_type are VERBATIM city-native labels — each entity "
                "has its own vocabulary (8–33 distinct result strings; Ogden files rezones "
                "under 'Ordinance', Lehi under 'Land-Use/Zoning'). Never aggregate them "
                "across entities. Use motion_std (motion_type_std / action_class / outcome) "
                "or the crosswalk tables instead."
            )

    if counties and tables & {"cf_contribution", "cf_expenditure"}:
        out.append(
            "County ITEMIZED campaign finance is largely NOT TRANSCRIBED. Outside Salt "
            "Lake County's EasyVote era, the born-digital parser sweep, and the completed "
            "SLCo clerk-legacy vision queue, the counties' scanned filings carry STATED "
            "TOTALS only (in cf_filing). An empty itemized result means NOT TRANSCRIBED — "
            "never report it as 'no donors'."
        )

    if "ut_state" in entities and (cities or counties) and tables & {"person", "vote", "role"}:
        out.append(
            "State legislators are a DISJOINT person population (222 persons). Never join "
            "or match them to municipal or county officials by surname — the repo keeps "
            "them separate deliberately."
        )

    if entities & MPO_SLUGS and tables & {"vote", "v_member_record_all", "v_contested_all"}:
        out.append(
            "MPO vote tables are empty BY SOURCE, not by omission: WFRC and MAG minutes "
            "are tally-only and never print a roll call. The MPO analytic surface is "
            "regional_project and projection, not votes. Reporting zero votes as a gap "
            "would be wrong."
        )

    if entities & RCV_CITIES and tables & {"election_result"}:
        rcv = ", ".join(sorted(entities & RCV_CITIES))
        out.append(
            f"Ranked-choice pilot city in scope ({rcv}): election_result.rank_in_contest is "
            "PLURALITY order (stored first-choice tallies), not the RCV final round. Take "
            "winners and margins from election_race, which is authoritative."
        )

    lowered = scrubbed.lower()
    if "disposition" in lowered and "outcome" not in lowered:
        out.append(
            "disposition (approve/deny/continue/table/procedural) and outcome (did the "
            "MOTION carry) are ORTHOGONAL — compose them: disposition='deny' AND "
            "outcome='Pass' means the matter was DENIED. Note also that every non-city "
            "motion carries NULL disposition; it has not been computed for those tiers."
        )

    if re.search(r"\bd(ocument)?\.path\b|\bdocument\b.*\bpath\b", lowered) and "text_path" not in lowered:
        out.append(
            "document.path resolves only in a full local build — 34% of rows point into "
            "the gitignored raw/ tree. Use text_path to read and source_url to re-fetch."
        )

    if "cf_cycle" in tables and counties:
        out.append(
            "cf_cycle is CITY-ONLY by design — county rollups were deliberately not "
            "derived. A county filtered against cf_cycle returns nothing, and that "
            "absence is a design decision, not missing money."
        )

    return out


# --------------------------------------------------------------------------
# convenience: full caveat set for one entity (used by resolve_entity/coverage)
# --------------------------------------------------------------------------

def for_entity(slug: str) -> list[dict]:
    idx = index()
    hits = [c for c in idx.caveats if c.city == slug]
    hits.sort(key=lambda c: (c.dataset, c.code))
    return [c.to_dict(idx.name_of(c.city)) for c in hits]
