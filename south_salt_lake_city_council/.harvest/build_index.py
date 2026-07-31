#!/usr/bin/env python3
"""Build minutes_index.csv (from the markdown tree) + minutes_unrecovered.csv (from the
harvest logs' UNRECOVERED lines) for a dataset dir. Deterministic, idempotent."""
import csv, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HDR = re.compile(r"<!--\s*(.*?)\s*-->", re.S)

def meta_of(md):
    m = HDR.search(md.read_text(encoding="utf-8", errors="replace")[:600])
    d = {}
    if m:
        for p in m.group(1).split("|"):
            if ":" in p:
                k, v = p.split(":", 1); d[k.strip()] = v.strip()
    return d

def build(ds_dir, log_streams):
    ds = REPO / ds_dir
    rows = []
    for md in sorted((ds / "minutes").rglob("*.md")):
        m = meta_of(md)
        date = m.get("date", "")
        rows.append([date, date[:4], f"{m.get('body','')} {m.get('meeting_kind','')} Meeting {date}".strip(),
                     md.stem, str(md.relative_to(ds)), "pmn", m.get("source_url", ""),
                     "pdf-text", m.get("body", ""), m.get("meeting_kind", ""), m.get("pmn_file", "")])
    rows.sort()
    with (ds / "minutes_index.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "year", "title", "slug", "path", "source", "source_url",
                    "format", "body", "meeting_kind", "pmn_file"])
        w.writerows(rows)
    # unrecovered from logs (use every log_<stream>*.txt; keep last-seen reason per key)
    seen = {}
    for st in log_streams:
        for log in sorted((REPO / ".harvest").glob(f"log_{st}*.txt")):
            for ln in log.read_text().splitlines():
                m = re.match(r"\s*\[(\w+)\]\s+(\d{4}-\d\d-\d\d)\s+(\w+):\s+UNRECOVERED\s+\((.*)\)\s*$", ln)
                if m:
                    body = {"council": "Council", "rda": "RDA", "pc": "PlanningCommission"}[m.group(1)]
                    seen[(m.group(2), body, m.group(3))] = m.group(4)
    unrec = sorted([k[0], k[1], k[2], v] for k, v in seen.items())
    with (ds / "minutes_unrecovered.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "body", "meeting_kind", "reason"])
        w.writerows(unrec)
    print(f"{ds_dir}: index={len(rows)} unrecovered={len(unrec)}")

if __name__ == "__main__":
    build("meeting_minutes", ["council", "rda"])
    build("planning_commission", ["pc"])
