#!/usr/bin/env python3
"""Build transcripts/index.csv for Midvale from the yt-dlp channel enumerations.

Reads raw/_enum_streams.tsv + raw/_enum_videos.tsv (yt-dlp --print, which emits a
LITERAL two-char '\\t' between fields, NOT a real tab), dedupes by video id,
classifies each video's body, parses a meeting date from the title (titles-first;
release_timestamp fallback recorded separately in raw/_timestamps.tsv), and writes the
SCHEMA_SPEC §9 transcripts contract index. Sample caption files that were downloaded
(raw/<id>.en.vtt) are renamed to raw/<date>.en.vtt and get format=caption; all other
meetings are enumerated with format=na (caption available on source, not fetched —
sample-only dataset).

Idempotent. Run from the transcripts/ dir.
"""
import csv, os, re, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
RETRIEVED = "2026-07-13"
CHANNEL = "https://www.youtube.com/channel/UCLDszK2kMUHuc3-bV-BBslQ"

MONTHS = {m.lower(): i for i, m in enumerate(
    ["", "January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}
MONTHS.update({"sept": 9, "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
               "jul": 7, "aug": 8, "oct": 10, "nov": 11, "dec": 12,
               "sep": 9})


def load_tsv(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\\t")  # literal backslash-t
            vid = parts[0]
            title = parts[1] if len(parts) > 1 else ""
            ts = parts[2] if len(parts) > 2 else "NA"
            rows.append((vid, title, ts))
    return rows


def parse_date(title):
    """Return ISO date or '' from a meeting title. Titles-first."""
    t = title
    # 1) MM/DD/YYYY or MM-DD-YYYY (also M/D/YY)
    m = re.search(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})', t)
    if m:
        mo, da, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if yr < 100:
            yr += 2000
        if 1 <= mo <= 12 and 1 <= da <= 31 and 2000 <= yr <= 2030:
            return f"{yr:04d}-{mo:02d}-{da:02d}"
    # 2) MonthName D(th/st/nd/rd), YYYY  (also with stray commas: "August, 11, 2020")
    m = re.search(r'([A-Za-z]{3,9})\.?,?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})', t)
    if m and m.group(1).lower() in MONTHS:
        mo = MONTHS[m.group(1).lower()]
        da, yr = int(m.group(2)), int(m.group(3))
        if 1 <= da <= 31:
            return f"{yr:04d}-{mo:02d}-{da:02d}"
    return ""


NONMEETING = re.compile(
    r'harvest days|food truck|art house|main street|chief elf|holiday|holidays|'
    r'interview|police seeking|manager .*retire|memorial|meet the candidates|'
    r'^test$|test city council|matthew pierce|transportation master plan|our vision',
    re.I)


def classify_body(title):
    t = title.lower()
    if NONMEETING.search(title):
        return None  # not a governing-body meeting
    if re.search(r'planning|zoning', t):
        return "PlanningCommission"
    if re.search(r'redevelopment|\brda\b', t):
        return "RDA"
    if re.search(r'council|budget retreat|legislative meeting|work session|study session', t):
        return "Council"
    return None


def main():
    streams = load_tsv(os.path.join(RAW, "_enum_streams.tsv"))
    videos = load_tsv(os.path.join(RAW, "_enum_videos.tsv"))
    # dedupe by id; streams take precedence (that's the meeting archive)
    seen = {}
    for vid, title, ts in streams + videos:
        if vid not in seen:
            seen[vid] = (title, ts)

    # optional timestamp fallback map: id -> ISO date (America/Denver already applied upstream)
    tsmap = {}
    tspath = os.path.join(RAW, "_timestamps.tsv")
    if os.path.exists(tspath):
        with open(tspath) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                p = line.split("\t")
                if len(p) >= 2 and p[1]:
                    tsmap[p[0]] = p[1]

    # Sampled video ids are recorded in raw/_sample_ids.txt (persistent — the caption
    # files themselves get renamed id->date on first run, so we can't re-detect by
    # filename). A caption row is emitted when raw/<date>.en.vtt exists for that id.
    sample_ids = set()
    sipath = os.path.join(RAW, "_sample_ids.txt")
    if os.path.exists(sipath):
        with open(sipath) as f:
            sample_ids = {ln.strip() for ln in f if ln.strip()}
    # also catch any freshly-downloaded id-named vtts not yet recorded
    for fn in os.listdir(RAW):
        m = re.match(r'([A-Za-z0-9_\-]{11})\.en\.vtt$', fn)
        if m:
            sample_ids.add(m.group(1))

    rows = []
    nonmeeting = 0
    undated = []
    for vid, (title, ts) in seen.items():
        body = classify_body(title)
        if body is None:
            nonmeeting += 1
            continue
        date = parse_date(title)
        date_source = "title"
        if not date and vid in tsmap:
            date = tsmap[vid]
            date_source = "release_timestamp"
        if not date:
            undated.append((vid, title))
        rows.append({
            "vid": vid, "title": title, "body": body, "date": date,
            "date_source": date_source,
        })

    # sort by date (blank last), then body
    rows.sort(key=lambda r: (r["date"] == "", r["date"], r["body"]))

    # rename sample vtts id->date and build final rows
    out = []
    for r in rows:
        vid = r["vid"]
        date = r["date"]
        video_url = f"https://www.youtube.com/watch?v={vid}"
        is_sample = vid in sample_ids and date
        path = ""
        fmt = "na"
        extraction = "enumerated"
        if is_sample:
            src = os.path.join(RAW, f"{vid}.en.vtt")
            dst_name = f"{date}.en.vtt"
            dst = os.path.join(RAW, dst_name)
            # date-collision guard: if the date file already belongs to another id,
            # disambiguate with the id suffix
            if os.path.exists(src):
                if os.path.exists(dst):
                    dst_name = f"{date}_{vid}.en.vtt"
                    dst = os.path.join(RAW, dst_name)
                os.rename(src, dst)
            path = f"raw/{dst_name}"
            fmt = "caption"
            extraction = "yt-dlp --write-auto-sub (en ASR)"
        out.append({
            "date": date,
            "title": r["title"],
            "body": r["body"],
            "video_url": video_url,
            "video_id": vid,
            "caption_type": "asr",
            "source_url": video_url,
            "retrieved_date": RETRIEVED,
            "format": fmt,
            "extraction_method": extraction,
            "path": path,
            "date_source": r["date_source"],
        })

    cols = ["date", "title", "body", "video_url", "video_id", "caption_type",
            "source_url", "retrieved_date", "format", "extraction_method", "path",
            "date_source"]
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)

    n_sample = sum(1 for r in out if r["format"] == "caption")
    print(f"meetings indexed : {len(out)}")
    print(f"  by body        : Council={sum(1 for r in out if r['body']=='Council')} "
          f"PlanningCommission={sum(1 for r in out if r['body']=='PlanningCommission')} "
          f"RDA={sum(1 for r in out if r['body']=='RDA')}")
    print(f"  sample captions: {n_sample}")
    print(f"  undated (need ts fallback): {len(undated)}")
    for vid, title in undated:
        print(f"    {vid}  {title}")
    print(f"non-meeting videos excluded: {nonmeeting}")
    dated = [r['date'] for r in out if r['date']]
    if dated:
        print(f"date range: {min(dated)} .. {max(dated)}")


if __name__ == "__main__":
    main()
