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


def load_adjudications(rec_dir):
    """Optional `adjudications.csv` beside the records dir: COORDINATOR-level corrections to a
    transcribed stated total, each carrying its evidence.

    WHY THIS EXISTS, and why it is not a licence to edit values. A filer can print a figure
    whose GLYPHS are unambiguous and whose VALUE the same page then disproves — the utah Smith
    2014 case (`$3446` printed, proved to be 34.46 by the line-5 subtotal, the line-7 closure and
    the prior report's line 7) and, in this wave, Goodfellow 2015 line 7 printed `173634` where
    line 5 prints the identical six digits WITH a decimal point, line 6 is `0`, and the form's
    own instruction reads "Subtract Line 6 from Line 5". Publishing `173634` as dollars is a
    100x error; blanking it discards a value the document proves. GOTCHAS is explicit that the
    document's own ARITHMETIC outranks any glyph reading, so the arithmetic governs.

    Discipline: the transcriber's verbatim string is NEVER lost — it is preserved in
    `<field>_verbatim` on the cache and named in `_meta.adjudications`. Every row must state the
    evidence. Nothing here may invent a value the page does not prove; a figure that is merely
    doubtful is left exactly as transcribed.

    Columns: index_path, field, transcribed, published, evidence.
    """
    p = os.path.join(rec_dir, "adjudications.csv")
    if not os.path.exists(p):
        return {}
    import csv
    out = {}
    with open(p, newline="") as fh:
        for r in csv.DictReader(fh):
            if not r.get("index_path") or not r.get("field"):
                continue
            out.setdefault(r["index_path"], []).append(r)
    return out


def build_cache(rec, idx_row, transcribed_by=None, transcribed_date=None, adjud=()):
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
    applied = []
    for a in adjud:
        f = a["field"]
        if f not in TOTAL_FIELDS and f not in AGG_FIELDS:
            raise SystemExit(f"adjudication names an unknown field: {f!r}")
        cur = cache[f] if f in TOTAL_FIELDS else cache["aggregate"][f]
        if (cur or "") != a["transcribed"]:
            raise SystemExit(
                f"adjudication STALE for {rec['index_path']} {f}: the cache holds {cur!r}, the "
                f"adjudication expected {a['transcribed']!r}. Re-verify at the page.")
        # The verbatim string is preserved BESIDE the published one, never overwritten.
        cache.setdefault("totals_verbatim", {})[f] = a["transcribed"]
        if f in TOTAL_FIELDS:
            cache[f] = a["published"]
        else:
            cache["aggregate"][f] = a["published"]
        applied.append(f"{f}: printed {a['transcribed']!r} -> published "
                       f"{a['published']!r} ({a['evidence']})")
    if applied:
        cache["_meta"]["adjudications"] = applied
    return cache


def _easyvote_api_docids():
    """The UNGATED set of document ids the EasyVote advanced-search API carries any rows for.

    Wave W2 (2026-08-24) uses it to define the new tranche era: an EasyVote filing outside
    the 2022 cycle with NO API rows at all. Ungated on purpose — a school-board filing whose
    rows exist but fail the county-office gate (Fife-Jepperson) is excluded from the county
    worklist here, which is exactly the owner ruling."""
    out = set()
    api = os.path.join(HERE, "raw", "easyvote_api")
    for name in ("advancedsearch_contributions.json", "advancedsearch_distributions.json"):
        p = os.path.join(api, name)
        if not os.path.exists(p):
            continue
        for r in json.load(open(p)):
            fid = (r.get("DocumentFilingId") or "").replace("_Redacted", "").upper()
            if fid:
                out.add(fid)
    return out


def tranche_worklist():
    """The filings this tranche covers, straight from index.csv (no curated side-file):
    every clerk-legacy filing + the whole 2022 EasyVote cycle + (since 2026-08-23) the whole
    `globalassets` 2015-2021 paper slice + (since 2026-08-24, wave W2) every EasyVote
    2024/2026 filing the API carries no itemized rows for (the row-less residue)."""
    import csv
    api_docids = None           # computed lazily, only if a non-2022 easyvote row appears
    out = {}
    with open(os.path.join(HERE, "index.csv"), newline="") as fh:
        for r in csv.DictReader(fh):
            if r["source"] == "clerk_legacy":
                era = "clerk_legacy"
            elif r["source"] == "globalassets":
                era = "globalassets_2015_2021"   # wave W1, 2026-08-23 (the paper slice)
            elif r["source"] == "easyvote" and r["election_year"] == "2022":
                era = "easyvote_2022"
            elif r["source"] == "easyvote":
                # Owner ruling (school-board, proven at the cover 2026-08-24, wave W2
                # chunk_17): these two filings are ledgered out-of-scope, never given a
                # county cache — mirrors build_finance._OUT_OF_SCOPE_PATHS.
                if r["path"] in ("raw/easyvote/FIFE-JEPPERSON-CHARLOTTE__AE07FEF8.pdf",
                                 "raw/easyvote/FIFE-JEPPERSON-CHARLOTTE__D20522DA.pdf"):
                    continue
                if api_docids is None:
                    api_docids = _easyvote_api_docids()
                if (r["document_id"] or "").upper() not in api_docids:
                    era = "easyvote_2024_2026"   # wave W2, 2026-08-24 (EasyVote residue)
                else:
                    continue
            else:
                continue
            out[r["path"]] = dict(era=era, candidate=r["candidate"], office=r["office"],
                                  election_year=r["election_year"])
    return out


def main(chunk_dir, dry=False, transcribed_by=None, transcribed_date=None):
    worklist = tranche_worklist()
    adjud = load_adjudications(chunk_dir)
    adj_applied = 0
    os.makedirs(VISION, exist_ok=True)
    written, seen = 0, set()
    skipped_itemization_only = 0
    for name in sorted(os.listdir(chunk_dir)):
        if not name.endswith(".json"):
            continue
        recs = json.load(open(os.path.join(chunk_dir, name)))
        for rec in recs:
            ip = rec["index_path"]
            # Wave W2 (2026-08-24): a record with NO totals half is an ITEMIZATION-ONLY
            # record for a filing whose stated-totals cache already exists (the 97 row-less
            # EasyVote-2022 filings). Building a cache from it would overwrite the good
            # stated totals with nulls — skip it here; `make_itemized_caches.py` is its
            # materializer. Detected structurally: no `totals` and no `cover` key at all.
            if "totals" not in rec and "cover" not in rec:
                skipped_itemization_only += 1
                continue
            key = VL.cache_key(ip)
            if rec.get("key") and rec["key"] != key:
                raise SystemExit(f"{name}: key mismatch for {ip}: {rec['key']} != {key}")
            if key in seen:
                raise SystemExit(f"{name}: duplicate record for {ip}")
            seen.add(key)
            rows = adjud.get(ip, [])
            cache = build_cache(rec, worklist[ip], transcribed_by, transcribed_date, rows)
            adj_applied += len(rows)
            if not dry:
                with open(os.path.join(VISION, key + ".json"), "w") as fh:
                    json.dump(cache, fh, indent=1, sort_keys=False)
                    fh.write("\n")
            written += 1
    print(f"{'would write' if dry else 'wrote'} {written} caches to vision/ "
          f"(worklist has {len(worklist)} filings)")
    if skipped_itemization_only:
        print(f"skipped {skipped_itemization_only} ITEMIZATION-ONLY record(s) "
              f"(no totals half — their caches already exist; make_itemized_caches.py "
              f"is their materializer)")
    if adjud:
        print(f"coordinator adjudications applied: {adj_applied} field(s) across "
              f"{len(adjud)} filing(s) — verbatim preserved in cache['totals_verbatim']")
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
