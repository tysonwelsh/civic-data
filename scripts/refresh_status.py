#!/usr/bin/env python3
"""
refresh_status — generate the repo-root refresh_status.md dashboard.

For every city x dataset it reports:
  * the index's max(date) + row count (measured live from minutes_index.csv,
    falling back to all_votes.csv where a dataset has no index — sandy PC)
  * the last portal probe (date, ok/fail, new-items-available count, notes)
    read from each city's refresh_probe.json (written by fetch_new.py --probe)
  * the fetch command to run when new items exist.

Usage:
    python3 scripts/refresh_status.py          # rewrite refresh_status.md
Run each city's `python3 fetch_new.py --probe` first to refresh the probe data.
Stdlib-only; never mutates data.
"""

import csv
import datetime
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "refresh_status.md"

# City list comes from the shared registry (scripts/cities.py). Before
# 2026-07-06 this file hardcoded 13 slugs and silently omitted the three
# 2026-07-06 cities (millcreek, south_jordan, taylorsville) from the dashboard.
from cities import SLUGS as CITIES
CORE_DATASETS = ["meeting_minutes", "planning_commission"]


def measured_max(city_dir, dataset):
    """(max date, n rows) measured from the dataset's own files."""
    for fname, count_rows in (("minutes_index.csv", True), ("all_votes.csv", False)):
        p = city_dir / dataset / fname
        if not p.exists():
            continue
        with open(p, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        dates = sorted(r.get("date", "") for r in rows if r.get("date"))
        if fname == "all_votes.csv":
            # votes CSV: rows are member-votes, count distinct meetings instead
            n = len({(r.get("date"), r.get("title")) for r in rows})
            return (dates[-1] if dates else None), n, "all_votes.csv"
        return (dates[-1] if dates else None), len(rows), fname
    return None, 0, None


# --- probe-shape normalization (Q3-2026 hardening) ---------------------------
# The 2026-07 wave cities' fetch_new.py probes write differently-shaped JSON
# (SSL: {council:{index_max,new_meeting_dates,…}}; bluffdale/white_city:
# standard keys), and several cities print results to stdout without writing
# refresh_probe.json at all. Normalize the shapes; label print-only cities
# honestly instead of "no probe".
DS_ALIASES = {"council": "meeting_minutes", "minutes": "meeting_minutes",
              "pc": "planning_commission"}
# rda rides the same combined council doc in these cities — fold its count in
DS_FOLD_INTO = {"rda": "meeting_minutes"}
STDOUT_ONLY = {  # cities whose --probe prints results without writing the json
    # herriman gained a standard read-only --probe 2026-07-19 (removed from this set)
    "kearns": "probe prints to stdout only",
    "magna": "probe prints to stdout only",
    "copperton": "probe prints to stdout only",
    "emigration_canyon": "probe prints to stdout only",
    "cottonwood_heights": "probe prints to stdout only",
    "riverton": "probe prints to stdout only",
    "alta": "probe prints to stdout only",
}


def normalize_probes(raw):
    norm = {}
    for k, v in raw.items():
        if not isinstance(v, dict):
            continue
        ds = DS_FOLD_INTO.get(k) or DS_ALIASES.get(k, k)
        q = dict(v)
        if "index_max_date" not in q and "index_max" in q:
            q["index_max_date"] = q["index_max"]
        if "new_count" not in q:
            for alt in ("new_meeting_dates", "new_dates", "new"):
                if alt in q:
                    val = q[alt]
                    q["new_count"] = len(val) if isinstance(val, list) else val
                    break
        if "status" not in q and (q.get("probe_date") or q.get("index_max_date")):
            q["status"] = "ok"
        q.setdefault("probe_date", "(json, undated)")
        if ds in norm:  # e.g. SSL council+rda both fold into meeting_minutes
            try:
                norm[ds]["new_count"] = (int(norm[ds].get("new_count") or 0)
                                         + int(q.get("new_count") or 0))
            except (TypeError, ValueError):
                pass
        else:
            norm[ds] = q
    return norm


def main():
    today = datetime.date.today().isoformat()
    lines = [
        f"# Refresh status — {len(CITIES)}-city portal probe dashboard",
        "",
        f"Generated {today} by `scripts/refresh_status.py`. Probe data comes from each",
        "city's `fetch_new.py --probe` run (stored in `<city>_city_council/refresh_probe.json`);",
        "index max dates are measured live from the dataset files.",
        "",
        "| City | Dataset | Portal | Index max date | Rows | Probed | Probe result | New on portal | Fetch command |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    notes_block = []
    for city in CITIES:
        cdir = REPO / f"{city}_city_council"
        probe_file = cdir / "refresh_probe.json"
        probes = {}
        if probe_file.exists():
            try:
                probes = normalize_probes(json.loads(probe_file.read_text()))
            except json.JSONDecodeError:
                probes = {}
        datasets = list(CORE_DATASETS) + [d for d in probes if d not in CORE_DATASETS]
        for ds in datasets:
            p = probes.get(ds, {})
            mx, n, src = measured_max(cdir, ds)
            if mx is None:
                mx, n = p.get("index_max_date"), p.get("index_rows", "")
            portal = p.get("portal", "?")
            probed = p.get("probe_date", "never")
            if p.get("status") == "ok":
                res = "ok"
                new = str(p.get("new_count"))
                if p.get("notes"):
                    notes_block.append(f"- **{city} / {ds}**: {p['notes']}")
            elif p.get("status") == "fail":
                res = "**FAIL**"
                new = "?"
                notes_block.append(f"- **{city} / {ds}** PROBE FAIL: {p.get('error', '')}")
            elif city in STDOUT_ONLY:
                res, new = "stdout-only", "?"
                if ds == datasets[0]:
                    notes_block.append(f"- **{city}**: {STDOUT_ONLY[city]}")
            else:
                res, new = "no probe", "?"
            fetch_cmd = p.get("fetch_cmd", f"python3 fetch_new.py --fetch --dataset {ds}")
            star = "" if src != "all_votes.csv" else " *"
            lines.append(
                f"| {city} | {ds} | {portal} | {mx}{star} | {n} | {probed} | {res} | {new} | `cd {city}_city_council && {fetch_cmd}` |")
    lines += [
        "",
        "`*` = dataset has no minutes_index.csv; max date measured from all_votes.csv",
        "(rows = distinct meetings). \"New on portal\" counts documents newer than the",
        "index max that the portal actually serves (meetings held but not yet posted",
        "are excluded — they appear in the notes).",
        "",
        "## Probe notes & failures",
        "",
    ]
    lines += notes_block or ["- none"]
    lines += [
        "",
        "## Quarterly refresh routine",
        "",
        "Suggested cadence: the first week of Jan / Apr / Jul / Oct (minutes are",
        "approved 2–6 weeks after a meeting, so a quarterly pass catches everything).",
        "",
        "1. **Probe everything** (read-only, ~5 min):",
        "   `for c in *_city_council; do (cd $c && python3 fetch_new.py --probe); done`",
        "2. **Regenerate this dashboard**: `python3 scripts/refresh_status.py`",
        "3. **Fetch per city where new items exist**: `cd <city>_city_council &&",
        "   python3 fetch_new.py --fetch` (downloads raw docs, converts to markdown,",
        "   appends index rows, runs that city's extract_votes.py + validate_votes.py).",
        "   SLC public comments delegate to `public_comments/check_new_comments.py`",
        "   (then vision_extract.py + clean_comments.py).",
        "4. **Rebuild derived layers** in each touched city: `python3 db/build_db.py`",
        "   (+ `db/build_referrals.py` where present), `python3 build_weeks.py`, and",
        "   `python3 scripts/normalize_motions.py --all` from the repo root for motions_std.",
        "5. **Validate**: `python3 scripts/validate_city.py <city>_city_council` must",
        "   stay at 0 FAIL; investigate any new WARN before committing.",
        "6. If a probe FAILs (portal moved/auth wall), re-recon that vendor section in",
        "   the city's recon.md and update its fetch_new.py — never fake availability.",
        "",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
