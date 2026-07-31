#!/usr/bin/env python3
"""Convert Murray CivicPlus raw minutes PDFs -> clean markdown + minutes_index.csv.

Deterministic: pdftotext -layout on each retained raw/ PDF, wrap with the standard
provenance header, file under minutes/<year>/<week-monday>/<date>_<slug>.md, and
emit minutes_index.csv per SCHEMA_SPEC §3. Byte-identical source duplicates (the
city posts the same doc under two ADIDs) are collapsed to one, logged to
convert_dropped_dupes.csv. Resumable: skips markdown already written.

Usage: python3 convert_minutes.py <raw_manifest.csv> <dataset_dir> <body>
  body = council | pc
"""
import sys, os, csv, re, subprocess, datetime, hashlib

def slugify(title, body):
    t = title.lower()
    base = "planning-commission" if body == "pc" else "city-council"
    if "work" in t:            kind = "work-session"
    elif "study" in t:         kind = "study-session"
    elif "special" in t:       kind = "special-meeting"
    elif "canvass" in t:       kind = "canvass"
    elif body == "pc":         kind = "meeting"
    else:                      kind = "meeting"
    return f"{base}-{kind}"

def week_monday(d):
    return (d - datetime.timedelta(days=d.weekday())).isoformat()

def pdftotext(path):
    r = subprocess.run(["pdftotext", "-layout", path, "-"],
                       capture_output=True)
    return r.stdout.decode("utf-8", "replace")

def main():
    manifest, ds_dir, body = sys.argv[1], sys.argv[2], sys.argv[3]
    raw_dir = os.path.join(ds_dir, "raw")
    rows = list(csv.DictReader(open(manifest)))
    rows.sort(key=lambda r: (r["date"], r["adid"]))
    seen_hash, index, dropped, used_paths = {}, [], [], set()
    for r in rows:
        h = r["sha256"]
        if h in seen_hash:
            dropped.append({**r, "dup_of": seen_hash[h]})
            continue
        seen_hash[h] = r["filename"]
        d = datetime.date.fromisoformat(r["date"])
        slug = slugify(r["title"], body)
        rel = f"minutes/{d.year}/{week_monday(d)}/{r['date']}_{slug}.md"
        # collision: distinct docs, same date+slug -> disambiguate with adid
        if rel in used_paths:
            rel = f"minutes/{d.year}/{week_monday(d)}/{r['date']}_{slug}-adid{r['adid']}.md"
        used_paths.add(rel)
        out = os.path.join(ds_dir, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        if not os.path.exists(out):
            text = pdftotext(os.path.join(raw_dir, r["filename"]))
            title = re.sub(r"\s+", " ", r["title"]).strip()
            hdr = (f"# {title}\n"
                   f"> Source: {r['url']}\n"
                   f"> Meeting date: {r['date']}\n"
                   f"> Format: pdf-text (CivicPlus Archive, born-digital)\n\n---\n\n")
            open(out, "w", encoding="utf-8").write(hdr + text)
        index.append(dict(date=r["date"], year=d.year, title=r["title"],
                          slug=slug, path=rel, source="civicplus",
                          source_url=r["url"], format="pdf-text"))
    index.sort(key=lambda x: (x["date"], x["path"]))
    with open(os.path.join(ds_dir, "minutes_index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date","year","title","slug","path",
                                          "source","source_url","format"])
        w.writeheader(); w.writerows(index)
    if dropped:
        with open(os.path.join(ds_dir, "convert_dropped_dupes.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(dropped[0].keys()))
            w.writeheader(); w.writerows(dropped)
    print(f"{body}: {len(index)} minutes docs indexed, "
          f"{len(dropped)} byte-identical dupes collapsed")

if __name__ == "__main__":
    main()
