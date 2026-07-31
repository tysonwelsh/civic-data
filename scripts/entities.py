"""The entity registry — the single source of truth for every government entity.

Generalizes the former city-only registry (scripts/cities.py, now a back-compat
shim over this module) to the full civic-data entity model:

    level ∈ {city, county, regional, state}   state ∈ {ut, ...}  (multi-state ready)

Identity is FLAT and stable — a slug never encodes its parent, so annexation /
redistricting / boundary changes never move a folder. Geography lives in DATA:
registry/relationships.csv is a many-to-many graph (within / member_of / overlaps /
succeeds) — this is what lets an MPO span several counties and a city straddle two
counties without lying about a single parent.

FEDERATION OFFSETS ARE LOAD-BEARING. build_cities_db.py namespaces federated ids as
    federated_id = source_id + fed_index * 10,000,000        fed_index = id // 10,000,000
`fed_index` is stored explicitly per entity (registry/entities.csv) and is APPEND-ONLY:
never renumber a published index. Non-overlapping bands are reserved per level so a new
tier can be added without disturbing the 1..16 city offsets that are already published
(cities_db_SCHEMA.md):

    city 1–99 (16 used) · county 101–199 · regional 201–299 · state 301–999

Usage:
    from entities import ENTITIES, by_level, by_slug, fed_offset, related, RELATIONSHIPS
    from cities import CITIES, SLUGS, city_dir, db_path      # the city-only shim
"""

import csv
import os
from collections import namedtuple

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENTITIES_CSV = os.path.join(_REPO, "registry", "entities.csv")
_RELATIONSHIPS_CSV = os.path.join(_REPO, "registry", "relationships.csv")

LEVELS = ("city", "county", "regional", "state")
RELATIONS = ("within", "member_of", "overlaps", "succeeds")

# Reserved federation-offset bands (inclusive) by level — non-overlapping.
OFFSET_BANDS = {
    "city":     (1, 99),
    "county":   (101, 199),
    "regional": (201, 299),
    "state":    (301, 999),
}

Entity = namedtuple("Entity", [
    "slug", "name", "level", "state", "dir", "db_rel_path",
    "fed_index", "fips", "portal", "gov_form", "notes",
])
Relationship = namedtuple("Relationship", ["a", "relation", "b", "confidence", "note"])


def _load_entities():
    ents = []
    with open(_ENTITIES_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ents.append(Entity(
                slug=row["slug"].strip(),
                name=row["name"].strip(),
                level=row["level"].strip(),
                state=row["state"].strip(),
                dir=row["dir"].strip(),
                db_rel_path=row["db_rel_path"].strip(),
                fed_index=int(row["fed_index"]),
                fips=row["fips"].strip(),
                portal=row["portal"].strip(),
                gov_form=row["gov_form"].strip(),
                notes=row["notes"].strip(),
            ))
    return ents


def _load_relationships(valid_slugs):
    rels = []
    with open(_RELATIONSHIPS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            r = Relationship(
                a=row["entity_a"].strip(),
                relation=row["relation"].strip(),
                b=row["entity_b"].strip(),
                confidence=row["confidence"].strip(),
                note=row["note"].strip(),
            )
            assert r.relation in RELATIONS, f"unknown relation {r.relation!r}"
            assert r.a in valid_slugs, f"relationship references unknown entity {r.a!r}"
            assert r.b in valid_slugs, f"relationship references unknown entity {r.b!r}"
            rels.append(r)
    return rels


ENTITIES = _load_entities()

# --- integrity asserts (fail loud at import; the registry is load-bearing) ---
_slugs = [e.slug for e in ENTITIES]
assert len(_slugs) == len(set(_slugs)), "duplicate entity slug in registry/entities.csv"
_seen_index = {}
for _e in ENTITIES:
    assert _e.level in LEVELS, f"{_e.slug}: bad level {_e.level!r}"
    _lo, _hi = OFFSET_BANDS[_e.level]
    assert _lo <= _e.fed_index <= _hi, (
        f"{_e.slug}: fed_index {_e.fed_index} outside {_e.level} band {_lo}-{_hi}")
    assert _e.fed_index not in _seen_index, (
        f"fed_index {_e.fed_index} reused by {_e.slug} and {_seen_index[_e.fed_index]}")
    _seen_index[_e.fed_index] = _e.slug

RELATIONSHIPS = _load_relationships(set(_slugs))

_BY_SLUG = {e.slug: e for e in ENTITIES}


def by_slug(slug):
    """The Entity for a slug (KeyError if unknown)."""
    return _BY_SLUG[slug]


def by_level(level):
    """All entities of a level, in fed_index order."""
    return sorted((e for e in ENTITIES if e.level == level), key=lambda e: e.fed_index)


def fed_offset(entity_or_slug):
    """The published federation id offset (fed_index * 10,000,000) for an entity."""
    e = entity_or_slug if isinstance(entity_or_slug, Entity) else _BY_SLUG[entity_or_slug]
    return e.fed_index * 10_000_000


def related(slug, relation=None, forward=True):
    """Slugs related to `slug`. forward=True → edges where slug is entity_a
    (e.g. related('slc','within') → ['salt_lake_county']); forward=False → the
    reverse (e.g. related('salt_lake_county','within',forward=False) → member cities).
    """
    out = []
    for r in RELATIONSHIPS:
        if relation and r.relation != relation:
            continue
        if forward and r.a == slug:
            out.append(r.b)
        elif not forward and r.b == slug:
            out.append(r.a)
    return out
