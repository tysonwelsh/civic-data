"""The city registry — BACK-COMPAT SHIM over the general entity registry.

Since 2026-07-11 the single source of truth is registry/entities.csv, loaded by
scripts/entities.py (cities, counties, regional bodies, the state — multi-state
ready). Cities are the rows with level=='city'. This module re-exposes them under
the exact historical interface (CITIES / SLUGS / DIRS / city_dir / db_path) so every
pre-existing importer keeps working unchanged.

ORDER IS LOAD-BEARING. The city fed_index (1..16 in registry/entities.csv — first 13
alphabetical, the 2026-07-06 additions appended) IS the published federation offset
namespacing (build_cities_db.py: fed_index * 10,000,000). NEVER reorder or renumber;
new cities are appended in entities.csv. To edit the roster, edit registry/entities.csv,
not this file.

Usage (unchanged):
    from cities import CITIES, SLUGS, city_dir, db_path
"""

from collections import namedtuple

from entities import by_level

# Historical shape: (slug, city dir, per-city db path relative to the city dir).
City = namedtuple("City", ["slug", "dir", "db_rel_path"])

# level=='city' entities in fed_index order == the historical 1..16 order.
CITIES = [City(e.slug, e.dir, e.db_rel_path) for e in by_level("city")]

SLUGS = [c.slug for c in CITIES]
DIRS = {c.slug: c.dir for c in CITIES}

_BY_SLUG = {c.slug: c for c in CITIES}


def city_dir(slug):
    """City directory name (relative to the repo root) for a slug."""
    return _BY_SLUG[slug].dir


def db_path(slug):
    """Per-city SQLite path relative to the city dir (filename is not uniform)."""
    return _BY_SLUG[slug].db_rel_path
