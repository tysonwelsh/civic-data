#!/usr/bin/env python3
"""rebuild_derived.py — run the full derived chain in the right order (REFACTOR_PLAN 4.5).

    python3 scripts/rebuild_derived.py <slug> [<slug> ...]   # named cities
    python3 scripts/rebuild_derived.py --all                 # every registry city
    python3 scripts/rebuild_derived.py --repo-only           # repo-level steps only

Per city (in order):     db/build_db.py → db/build_referrals.py → build_weeks.py →
                         scripts/normalize_motions.py <slug> →
                         scripts/build_sources_index.py <slug> →
                         scripts/validate_city.py <dir> (must exit 0)
Repo-level (once, last): scripts/build_coverage.py → scripts/build_cities_db.py
                         (which itself runs build_search_layer.py)

Fail-loud: the first non-zero step aborts the run (nothing downstream of a broken
step is rebuilt). This wrapper only ever regenerates derived layers — it never
touches canonical CSVs, minutes, or raw/. Run it after any change to a city's
extractor output, override files, or flat CSVs.

TRAP (from REMEDIATION_PLAN 5): db/referral_overrides.csv pins application_ids that
can SHIFT when applications appear/disappear — if build_referrals.py fails or the
referral count changes unexpectedly, remap the overrides via stable
(source_file, motion_no) keys before rerunning.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cities import CITIES, DIRS, SLUGS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")


def run(cmd, cwd, label):
    print(f"→ {label}: {' '.join(os.path.relpath(c, ROOT) if os.path.isabs(c) else c for c in cmd)}")
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0:
        sys.exit(f"ABORT — {label} exited {r.returncode}; nothing downstream was rebuilt")


def rebuild_city(slug):
    cdir = os.path.join(ROOT, DIRS[slug])
    db_dir = os.path.join(cdir, "db")
    run([sys.executable, "build_db.py"], db_dir, f"{slug} db")
    run([sys.executable, "build_referrals.py"], db_dir, f"{slug} referrals")
    run([sys.executable, "build_weeks.py"], cdir, f"{slug} weeks")
    run([sys.executable, os.path.join(SCRIPTS, "normalize_motions.py"), slug],
        ROOT, f"{slug} motions_std")
    run([sys.executable, os.path.join(SCRIPTS, "build_sources_index.py"), slug],
        ROOT, f"{slug} sources")
    run([sys.executable, os.path.join(SCRIPTS, "validate_city.py"), cdir, "--quiet"],
        ROOT, f"{slug} validate")


def rebuild_repo():
    run([sys.executable, os.path.join(SCRIPTS, "build_coverage.py")], ROOT, "coverage.json")
    run([sys.executable, os.path.join(SCRIPTS, "build_cities_db.py")], ROOT,
        "cities.db (+ search layer)")


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if "--repo-only" in args:
        rebuild_repo()
        return
    slugs = SLUGS if "--all" in args else args
    unknown = [s for s in slugs if s not in DIRS]
    if unknown:
        sys.exit(f"unknown city slug(s): {unknown} — see scripts/cities.py")
    for slug in slugs:
        print(f"===== {slug} =====")
        rebuild_city(slug)
    rebuild_repo()
    print("Derived chain rebuilt: %s + repo level." % ", ".join(slugs))


if __name__ == "__main__":
    main()
