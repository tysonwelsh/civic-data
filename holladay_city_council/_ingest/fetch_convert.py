#!/usr/bin/env python3
"""Download the 197 PMN minutes PDFs -> <ds>/raw/, convert with pdftotext -layout ->
markdown (provenance header) under <ds>/minutes/<year>/<week-monday>/, verify each PDF's
header says HOLLADAY, and write minutes_index.csv rows. Resumable (skip on-disk)."""
import json, os, re, subprocess, urllib.request, datetime, sys, csv

REPO = "/Users/tysonwelsh/civic-data/holladay_city_council"
SC = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
manifest = json.load(open(f"{SC}/minutes_manifest.json"))

def iso_from_event(ev):
    m = re.match(r'(\d{4})/(\d{2})/(\d{2})', ev)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None

def week_monday(iso):
    d = datetime.date.fromisoformat(iso)
    return (d - datetime.timedelta(days=d.weekday())).isoformat()

def slug_for(body, title):
    t = title.lower()
    if body == "PlanningCommission":
        return "planning-commission"
    if body == "RDA":
        return "rda-meeting"
    if "work" in t or "joint" in t or "jt " in t:
        return "city-council-work-meeting"
    return "city-council-meeting"

def title_for(body, title):
    return {"PlanningCommission": "Planning Commission Meeting",
            "RDA": "Redevelopment Agency (RDA) Meeting"}.get(body, "City Council Meeting")

def ds_dir(body):
    return "planning_commission" if body == "PlanningCommission" else "meeting_minutes"

def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    data = urllib.request.urlopen(req, timeout=120).read()
    if not data[:4] == b"%PDF":
        return False
    open(dest, "wb").write(data)
    return True

index_rows = {"meeting_minutes": [], "planning_commission": []}
skipped = []
n_new = 0
for r in manifest:
    body = r["body"]
    iso = iso_from_event(r["event_date"])
    if not iso:
        skipped.append((r["file_id"], "no-date", r["event_date"])); continue
    ds = ds_dir(body)
    slug = slug_for(body, r["title"])
    raw_name = f"{iso}_{slug}_{r['file_id']}.pdf"
    raw_path = f"{REPO}/{ds}/raw/{raw_name}"
    rel_md = f"minutes/{iso[:4]}/{week_monday(iso)}/{iso}_{slug}_{r['file_id']}.md"
    md_path = f"{REPO}/{ds}/{rel_md}"
    src_url = f"https://www.utah.gov/pmn/files/{r['file_id']}.pdf"
    row = {"date": iso, "year": iso[:4], "title": title_for(body, r["title"]),
           "slug": slug, "path": rel_md, "source": "pmn", "source_url": src_url,
           "format": "pdf-text", "body": body, "file_id": r["file_id"]}
    index_rows[ds].append(row)
    if os.path.exists(md_path) and os.path.getsize(md_path) > 200:
        continue
    if not os.path.exists(raw_path):
        try:
            if not download(src_url, raw_path):
                skipped.append((r["file_id"], "not-pdf", src_url)); continue
        except Exception as e:
            skipped.append((r["file_id"], f"dlerr:{e}", src_url)); continue
    # convert
    txt = subprocess.run(["pdftotext", "-layout", raw_path, "-"],
                         capture_output=True, text=True).stdout
    if "HOLLADAY" not in txt.upper():
        skipped.append((r["file_id"], "NOT-HOLLADAY", raw_path)); continue
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    hdr = (f"# {title_for(body, r['title'])} — {iso}\n"
           f"> Source: {src_url}\n> Meeting date: {iso}\n"
           f"> Public body: {body} (PMN body {r['pb_id']})\n"
           f"> Retrieved: 2026-07-12 from Utah Public Notice (utah.gov/pmn)\n\n---\n\n")
    open(md_path, "w").write(hdr + txt)
    n_new += 1
    if n_new % 25 == 0:
        print(f"  converted {n_new}", file=sys.stderr)

# write minutes_index.csv per dataset
COLS = ["date", "year", "title", "slug", "path", "source", "source_url", "format", "body"]
for ds, rows in index_rows.items():
    rows.sort(key=lambda x: (x["date"], x["slug"]))
    with open(f"{REPO}/{ds}/minutes_index.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for row in rows:
            w.writerow({k: row[k] for k in COLS})
print(f"NEW converted: {n_new}")
print(f"meeting_minutes index rows: {len(index_rows['meeting_minutes'])}")
print(f"planning_commission index rows: {len(index_rows['planning_commission'])}")
print(f"skipped: {len(skipped)}")
for s in skipped[:40]:
    print("  SKIP", s)
json.dump(skipped, open(f"{SC}/fetch_skipped.json", "w"), indent=1)
