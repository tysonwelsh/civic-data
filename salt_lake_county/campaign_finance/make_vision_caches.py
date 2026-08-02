#!/usr/bin/env python3
"""make_vision_caches.py — materialize `vision/<key>.json` stated-totals caches from the
raw Read-tool transcription records produced by the 2026-08-01 vision wave.

WHY A SEPARATE STEP. The transcription agents wrote ONE JSON list per chunk (raw records:
`key`, `cover`, `totals`, `confidence`, `notes`) instead of 670 individual cache files, so
that (a) no agent ever writes inside the repo, and (b) the `_meta` provenance stamp and the
cache schema are applied in exactly ONE place — here. This script is a pure, idempotent
transform: it renames/nests fields and stamps provenance. **It never invents a value** — a
`null` (printed but illegible) and a `""` (the filer left the cell blank) both survive the
transform intact, and the two states stay distinguishable in the cache.

Cache key: `vision/<sha1(index.csv path)[:8]>.json` — the repo-standard key
(`scripts/campaign_finance/vision_lib.cache_key`). Cache body is a SUPERSET of the standard
vision cache (`contributions`/`expenditures`/`total_*`/`*_balance`/`_meta`), so a later
itemization tranche can fill the two empty row lists in place without a schema change.

Usage:
    python3 make_vision_caches.py <chunk_dir> [--dry-run]
                                  [--transcribed-by STR] [--transcribed-date YYYY-MM-DD]

The two stamp flags exist because the tranche ran in WAVES: the 2026-08-01 wave transcribed
114 filings and the 2026-08-02 continuation wave the remaining 556. Each wave stamps its own
`_meta.transcribed_by` / `_meta.transcribed_date` so a cache always says which pass produced
it. Defaults reproduce the FIRST wave's stamp, so re-running the original records is a no-op.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "scripts", "campaign_finance")))
import vision_lib as VL  # noqa: E402

VISION = os.path.join(HERE, "vision")
TRANSCRIBED_BY = "vision-transcribed(claude-opus-5; 2026-08-01 totals tranche)"
TRANSCRIBED_DATE = "2026-08-01"
RENDER = "pdftoppm -jpeg -r 150"   # default; a record may declare its own (the
                                   # orchestrator's own batch rendered at -r 110)

TOTAL_FIELDS = ("total_contributions", "total_expenditures",
                "beginning_balance", "ending_balance")
AGG_FIELDS = ("total_contributions_to_date", "total_expenditures_to_date", "line5_subtotal")
COVER_FIELDS = ("candidate", "party", "office_sought", "district_number", "report_type",
                "is_amendment", "amendment_of", "report_date", "form_year")


def _keep(v):
    """Preserve the transcriber's THREE states verbatim: a string (printed), "" (blank on
    the form), None/null (printed but illegible). Never coerce one into another."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return str(v)
    return v


def build_cache(rec, idx_row, transcribed_by=None, transcribed_date=None):
    tot = rec.get("totals") or {}
    cover = rec.get("cover") or {}
    cache = {
        "contributions": [],          # itemization NOT built in this tranche
        "expenditures": [],
    }
    for f in TOTAL_FIELDS:
        cache[f] = _keep(tot.get(f))
    cache["aggregate"] = {f: _keep(tot.get(f)) for f in AGG_FIELDS}
    cache["cover"] = {f: _keep(cover.get(f)) for f in COVER_FIELDS}
    cache["confidence"] = {k: v for k, v in (rec.get("confidence") or {}).items() if v}
    cache["_meta"] = {
        "index_path": rec["index_path"],
        "era": idx_row["era"],
        "tranche": "stated-totals (cover + Summary Page); itemization deferred",
        "candidate": idx_row["candidate"],
        "office": idx_row["office"],
        "election_year": idx_row["election_year"],
        "source_pdf": rec["index_path"],
        "pages_read": rec.get("pages_read") or [],
        "render": rec.get("render") or RENDER,
        "summary_page_found": bool(rec.get("summary_page_found")),
        "transcription_method": "read-tool-vision (Claude Code allotment, $0 API)",
        "transcribed_by": transcribed_by or TRANSCRIBED_BY,
        "transcribed_date": transcribed_date or TRANSCRIBED_DATE,
        "notes": rec.get("notes") or "",
    }
    return cache


def tranche_worklist():
    """The filings this tranche covers, straight from index.csv (no curated side-file):
    every clerk-legacy filing + the whole 2022 EasyVote cycle."""
    import csv
    out = {}
    with open(os.path.join(HERE, "index.csv"), newline="") as fh:
        for r in csv.DictReader(fh):
            if r["source"] == "clerk_legacy":
                era = "clerk_legacy"
            elif r["source"] == "easyvote" and r["election_year"] == "2022":
                era = "easyvote_2022"
            else:
                continue
            out[r["path"]] = dict(era=era, candidate=r["candidate"], office=r["office"],
                                  election_year=r["election_year"])
    return out


def main(chunk_dir, dry=False, transcribed_by=None, transcribed_date=None):
    worklist = tranche_worklist()
    os.makedirs(VISION, exist_ok=True)
    written, seen = 0, set()
    for name in sorted(os.listdir(chunk_dir)):
        if not name.endswith(".json"):
            continue
        recs = json.load(open(os.path.join(chunk_dir, name)))
        for rec in recs:
            ip = rec["index_path"]
            key = VL.cache_key(ip)
            if rec.get("key") and rec["key"] != key:
                raise SystemExit(f"{name}: key mismatch for {ip}: {rec['key']} != {key}")
            if key in seen:
                raise SystemExit(f"{name}: duplicate record for {ip}")
            seen.add(key)
            cache = build_cache(rec, worklist[ip], transcribed_by, transcribed_date)
            if not dry:
                with open(os.path.join(VISION, key + ".json"), "w") as fh:
                    json.dump(cache, fh, indent=1, sort_keys=False)
                    fh.write("\n")
            written += 1
    print(f"{'would write' if dry else 'wrote'} {written} caches to vision/ "
          f"(worklist has {len(worklist)} filings)")
    missing = set(worklist) - {w for w in worklist if VL.cache_key(w) in seen}
    if missing:
        print(f"NOT TRANSCRIBED ({len(missing)}): honest gap, emitted as inventory-only rows")
        for m in sorted(missing)[:20]:
            print("   ", m)


def _opt(name):
    """--name VALUE or --name=VALUE from argv; None if absent."""
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith(name + "="):
            return a.split("=", 1)[1]
    return None


if __name__ == "__main__":
    _flagvals = {v for n in ("--transcribed-by", "--transcribed-date")
                 for v in ([_opt(n)] if _opt(n) else [])}
    args = [a for a in sys.argv[1:] if not a.startswith("--") and a not in _flagvals]
    if not args:
        print(__doc__)
        sys.exit(2)
    main(args[0], dry="--dry-run" in sys.argv,
         transcribed_by=_opt("--transcribed-by"),
         transcribed_date=_opt("--transcribed-date"))
