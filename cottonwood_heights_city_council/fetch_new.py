#!/usr/bin/env python3
"""
Cottonwood Heights incremental refresh — PROBE (read-only) + APPEND-ONLY INGEST.

Cottonwood Heights minutes are published on a **Granicus / CivicEngage Central** portal
(www.cottonwoodheights.utah.gov) whose rolling window has DECAYED (the 2022 portal column
is down to 4 docs), so the canonical corpus UNIONs the portal with **Utah Public Notice**
(entity 111; body **Council 2147**, **PC 2148**). This driver reuses `fetch_minutes.py`'s
live harvesters (`harvest_portal`, `harvest_pmn`) — same browser header set (the site 403s
bare UAs behind an Akamai-style edge) and same PMN body ids — so probe/ingest reflect
exactly what the portal serves.

    python3 fetch_new.py                 # PROBE (default, read-only) — both datasets
    python3 fetch_new.py --probe         # same
    python3 fetch_new.py --json          # machine-readable probe result
    python3 fetch_new.py --ingest        # APPEND-ONLY refresh: fetch genuinely-new docs
                                         #   and APPEND index rows (never regenerates)
    python3 fetch_new.py --dataset planning_commission --ingest   # one dataset

APPEND-ONLY INGEST (the routine refresh step) — how it stays non-destructive:
  * diffs the LIVE portal+PMN harvest against the EXISTING minutes_index.csv by target
    on-disk PATH; only docs whose path is not already indexed are candidates;
  * honors the removal ledger (_removed_duplicates/): a candidate whose target basename
    was deliberately removed is NEVER re-added (kills the 2024-01-02 resurrection class);
  * a file already on disk but absent from the index is LEFT ALONE (a curated/recovered
    row a human manages — never silently re-added);
  * fetches ONLY genuinely-new docs, converts + gates them (looks_like_minutes), writes
    the markdown, and APPENDS rows via refresh_lib.append_index_rows (which preserves the
    existing file + header, dedupes by path, and logs retrieved_date to fetch_log.csv).
  It never rewrites or drops an existing row. After an ingest that added docs, rebuild the
  derived layers: `python3 meeting_minutes/extract_votes.py` (+ PC) ·
  `python3 db/build_db.py && python3 db/build_referrals.py` · `python3 build_weeks.py` ·
  `python3 ../scripts/build_cities_db.py`.

  ⚠️ `--fetch` is the OLD destructive full re-acquisition (regenerates minutes_index.csv
  from scratch — it dropped 3 council + 39 PC recovered rows and resurrected the removed
  2024-01-02 duplicate on 2026-07-19). It is now GUARDED: it refuses without
  --force-full-rebuild and writes a timestamped index backup first. Use --ingest for
  routine refresh; --fetch only for a deliberate full rebuild.
"""
import argparse
import csv
import datetime
import json
import subprocess
import sys
import time
from pathlib import Path

CITY = Path(__file__).resolve().parent
sys.path.insert(0, str(CITY))
sys.path.insert(0, str(CITY.parent / "scripts"))
import fetch_minutes as fm  # noqa: E402  (reuse the live harvesters + BODIES config)
import refresh_lib          # noqa: E402  (shared append_index_rows / conventions)


# ------------------------------------------------------------------ index state

def indexed(ds):
    """Return (max_date_or_None, {dates already known}). Known = index dates ∪
    honestly-unrecovered dates (so an unrecovered meeting never re-surfaces as new)."""
    idx = CITY / ds / "minutes_index.csv"
    dates = set()
    if idx.exists():
        for r in csv.DictReader(idx.open()):
            if r.get("date"):
                dates.add(r["date"])
    unrec = CITY / ds / "minutes_unrecovered.csv"
    if unrec.exists():
        for r in csv.DictReader(unrec.open()):
            if r.get("date"):
                dates.add(r["date"])
    return (max(dates) if dates else None), dates


def indexed_paths(ds):
    """Set of on-disk paths already in minutes_index.csv (the append-only diff key)."""
    idx = CITY / ds / "minutes_index.csv"
    if not idx.exists():
        return set()
    return {r["path"] for r in csv.DictReader(idx.open()) if r.get("path")}


def removal_ledger():
    """Basenames of deliberately-removed duplicates (_removed_duplicates/*.md). A
    candidate whose target basename is in this set must NEVER be re-added."""
    d = CITY / "_removed_duplicates"
    return {p.name for p in d.glob("*.md")} if d.exists() else set()


def rel_path(it):
    """Target on-disk rel path for a harvested item — identical formula to
    fetch_minutes.build_body (so the diff compares like for like)."""
    iso, slug = it["date"], it["type"]
    return f"minutes/{iso[:4]}/{fm.week_monday(iso)}/{iso}_{slug}.md"


def harvest_union(cfg):
    """Live portal ∪ PMN harvest, unioned by (date, type) with the born-digital
    portal doc winning a collision — the same union fetch_minutes.build_body forms."""
    merged = {}
    for harvest in (fm.harvest_pmn, fm.harvest_portal):   # portal last -> overrides pmn
        try:
            for it in harvest(cfg):
                merged[(it["date"], it["type"])] = it
        except Exception as e:  # noqa: BLE001
            print(f"  ! harvest {harvest.__name__} failed: {e}", file=sys.stderr)
    return sorted(merged.values(), key=lambda x: (x["date"], x["type"]))


# --------------------------------------------------------------------- probe

def probe_body(ds, cfg):
    max_date, known = indexed(ds)
    cands = {}
    for harvest in (fm.harvest_portal, fm.harvest_pmn):
        try:
            for it in harvest(cfg):
                if it["date"] in known:
                    continue
                if max_date and it["date"] <= max_date:
                    it = dict(it, gap="below-max-not-indexed")
                k = it["date"]
                if k not in cands or (it["source"] == "civicplus" and cands[k]["source"] == "pmn"):
                    cands[k] = it
        except Exception as e:  # noqa: BLE001
            print(f"  ! {ds}: {harvest.__name__} probe failed: {e}", file=sys.stderr)
    new = sorted(cands.values(), key=lambda x: x["date"])
    return {"dataset": ds, "index_max": max_date, "indexed_docs": len(known),
            "candidates": new}


# ----------------------------------------------------------- append-only ingest

def diff_new(ds, cfg):
    """Genuinely-new docs to ingest, plus what the ledger/on-disk filters blocked.
    Returns (new_items, blocked_ledger, on_disk_untouched)."""
    idx_paths = indexed_paths(ds)
    ledger = removal_ledger()
    new, blocked, on_disk = [], [], []
    for it in harvest_union(cfg):
        rel = rel_path(it)
        base = Path(rel).name
        if rel in idx_paths:                 # already indexed -> never touch (append-only)
            continue
        if base in ledger:                   # deliberately-removed duplicate -> never re-add
            blocked.append({**it, "path": rel})
            continue
        if (CITY / ds / rel).exists():        # on disk, not indexed -> human-managed row; leave it
            on_disk.append({**it, "path": rel})
            continue
        new.append(it)
    return new, blocked, on_disk


def build_doc(ds, cfg, it):
    """Fetch + convert + gate one genuinely-new doc. Returns (index_row, None) on
    success or (None, reason) if it's a stub / non-doc (-> minutes_unrecovered)."""
    ds_dir = CITY / ds
    (ds_dir / "raw").mkdir(parents=True, exist_ok=True)
    rel = rel_path(it)
    out = ds_dir / rel
    time.sleep(0.6)                                   # be polite between GETs
    try:
        data = fm.http_get(it["url"], binary=True)
    except Exception as e:  # noqa: BLE001
        return None, f"fetch error: {e}"
    if data.startswith(b"%PDF"):
        ext = ".pdf"
    elif data.startswith(b"PK\x03\x04"):
        ext = ".docx"                                 # CivicEngage sometimes serves Word
    else:
        return None, "not a PDF/DOCX (portal returned HTML/stub)"
    raw = ds_dir / "raw" / f"{it['source']}_{it['date']}_{it['type']}{ext}"
    raw.write_bytes(data)                             # raw retention
    txt, fmt = fm.convert(raw)
    if not fm.looks_like_minutes(txt):
        return None, f"doc too short / not minutes prose ({len(txt.strip())} chars)"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        fm.md_header(cfg["title"], it["date"], it["url"], fmt, it["source"]) + txt.rstrip() + "\n",
        encoding="utf-8")
    title = f"{cfg['title']} — {it['desc'][:80]}".rstrip()
    row = {"date": it["date"], "year": it["date"][:4], "title": title, "slug": it["type"],
           "path": rel, "source": it["source"], "source_url": it["url"], "format": fmt}
    print(f"  built {rel} [{it['source']}/{fmt}]")
    return row, None


def append_unrecovered(ds, new_rows):
    """Append (never regenerate) stub/non-doc rows to minutes_unrecovered.csv,
    de-duped against what's already there."""
    if not new_rows:
        return 0
    up = CITY / ds / "minutes_unrecovered.csv"
    cols = ["date", "year", "description", "reason", "source_url"]
    seen, existing = set(), []
    if up.exists():
        existing = list(csv.DictReader(up.open()))
        seen = {(r["date"], r.get("reason", "")) for r in existing}
    added = 0
    for r in new_rows:
        key = (r["date"], r["reason"])
        if key in seen:
            continue
        seen.add(key)
        existing.append(r)
        added += 1
    if added:
        with up.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(sorted(existing, key=lambda r: (r["date"], r.get("reason", ""))))
    return added


def ingest(selected):
    total_added = 0
    for ds, cfg in selected.items():
        max_date, _ = indexed(ds)
        print(f"\n== {ds}  (portal + PMN body {cfg['pmn_body']}) ==")
        print(f"   indexed max date {max_date}")
        new, blocked, on_disk = diff_new(ds, cfg)
        for b in blocked:
            print(f"   SKIP  {b['date']}  {Path(b['path']).name}  "
                  f"[removal-ledger: deliberately-removed duplicate, not re-added]")
        for o in on_disk:
            print(f"   SKIP  {o['date']}  {Path(o['path']).name}  "
                  f"[on disk, not indexed — human-managed row, left untouched]")
        if not new:
            print("   no genuinely-new docs — index unchanged (append-only no-op).")
            continue
        rows, unrec = [], []
        for it in new:
            row, reason = build_doc(ds, cfg, it)
            if row:
                rows.append(row)
            else:
                print(f"   UNREC {it['date']}  {it['type']}: {reason}")
                unrec.append({"date": it["date"], "year": it["date"][:4],
                              "description": it["desc"], "reason": reason,
                              "source_url": it["url"]})
        if rows:
            n = refresh_lib.append_index_rows(CITY / ds, rows)
            total_added += n
            print(f"   APPENDED {n} row(s) to {ds}/minutes_index.csv")
        append_unrecovered(ds, unrec)
    if total_added:
        print(f"\n{total_added} new doc(s) appended. Rebuild the derived layers:\n"
              "  python3 meeting_minutes/extract_votes.py   (+ planning_commission)\n"
              "  python3 db/build_db.py && python3 db/build_referrals.py\n"
              "  python3 build_weeks.py\n"
              "  python3 ../scripts/normalize_motions.py --all    (motions_std refresh)\n"
              "  python3 ../scripts/build_cities_db.py       (federation)")
    else:
        print("\nNo new docs ingested — nothing to rebuild.")
    return total_added


# --------------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(
        description="Cottonwood Heights refresh — read-only probe (default) + append-only ingest.")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--probe", action="store_true", help="list new meeting dates (default, read-only)")
    g.add_argument("--ingest", action="store_true",
                   help="APPEND-ONLY: fetch genuinely-new docs and APPEND index rows (routine refresh)")
    g.add_argument("--fetch", action="store_true",
                   help="DESTRUCTIVE full re-acquisition (regenerates the index) — GUARDED, "
                        "needs --force-full-rebuild; prefer --ingest")
    ap.add_argument("--force-full-rebuild", action="store_true",
                    help="required to actually run the destructive --fetch full rebuild")
    ap.add_argument("--dataset", choices=list(fm.BODIES), help="limit to one dataset")
    ap.add_argument("--json", action="store_true", help="machine-readable probe output")
    args = ap.parse_args()

    selected = ({args.dataset: fm.BODIES[args.dataset]} if args.dataset else dict(fm.BODIES))

    # ---- append-only ingest (the routine refresh step) --------------------
    if args.ingest:
        print(f"Cottonwood Heights APPEND-ONLY ingest  (portal={fm.HOST}  PMN entity 111)")
        ingest(selected)
        return

    # ---- guarded destructive full rebuild ---------------------------------
    if args.fetch:
        if not args.force_full_rebuild:
            sys.stderr.write(fm.DESTRUCTIVE_WARNING)
            sys.stderr.write(
                "\n(Invoked via fetch_new.py --fetch. Use `python3 fetch_new.py --ingest` "
                "for routine refresh, or add --force-full-rebuild to force the rebuild.)\n")
            sys.exit(2)
        cmd = [sys.executable, str(CITY / "fetch_minutes.py"), "--force-full-rebuild"]
        if args.dataset:
            cmd.insert(2, args.dataset)
        print("DESTRUCTIVE full rebuild (a timestamped index backup is written first) ...")
        subprocess.run(cmd, check=True)
        print("\nNow rebuild derived layers: extract_votes.py (both) · db/build_db.py + "
              "build_referrals.py · build_weeks.py · ../scripts/build_cities_db.py")
        return

    # ---- probe (default, read-only) ---------------------------------------
    results = [probe_body(ds, cfg) for ds, cfg in selected.items()]
    # emit the standard machine-readable probe JSON that scripts/refresh_status.py
    # consumes (in addition to the stdout report + optional --json dump below)
    for r in results:
        cfg = fm.BODIES[r["dataset"]]
        refresh_lib.write_probe(CITY, r["dataset"], {
            "probe_date": str(datetime.date.today()), "portal": "civicplus+pmn",
            "index_max_date": r["index_max"], "index_rows": r["indexed_docs"],
            "status": "ok", "new_count": len(r["candidates"]),
            "new_items": [{"date": c["date"], "title": c.get("type", ""),
                           "url": c.get("url", "")} for c in r["candidates"]],
            "notes": (f"portal (CivicEngage) ∪ PMN body {cfg['pmn_body']}; "
                      f"{len(r['candidates'])} candidate meeting(s). Routine refresh is "
                      f"--ingest (append-only)."),
            "fetch_cmd": f"python3 fetch_new.py --ingest --dataset {r['dataset']}",
        })
    if args.json:
        print(json.dumps({"probed": fm.TODAY, "today": str(datetime.date.today()),
                          "results": results}, indent=2))
        return

    print(f"Cottonwood Heights refresh probe  (portal={fm.HOST}  PMN entity 111)")
    total = 0
    for r in results:
        cfg = fm.BODIES[r["dataset"]]
        print(f"\n== {r['dataset']}  (portal + PMN body {cfg['pmn_body']}) ==")
        print(f"   indexed: {r['indexed_docs']} docs, max date {r['index_max']}")
        if not r["candidates"]:
            print("   no new meetings found.")
            continue
        for c in r["candidates"]:
            total += 1
            flag = f"  [{c['gap']}]" if c.get("gap") else ""
            print(f"   NEW {c['date']}  {c['type']:32s}  src={c['source']:9s}{flag}")
            print(f"        {c['url']}")
    print(f"\n{total} candidate meeting(s). Review, then INGEST (append-only): "
          "python3 fetch_new.py --ingest")


if __name__ == "__main__":
    main()
