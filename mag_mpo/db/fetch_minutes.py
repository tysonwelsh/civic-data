#!/usr/bin/env python3
"""Harvest MAG MPO Board + MPO TAC minutes from the magutah.gov static tree.

The MPO Board landing page (magutah.gov/mpoboard/) is JS-rendered; the year
accordions populate from an AJAX endpoint:
    GET /sitefiles/minutes-list/?dir=files/committees/<tree>/meetings/<YEAR>/
which returns an HTML fragment listing every file for that year. We enumerate
minute PDFs from that endpoint (NOT the rendered HTML), download the born-digital
PDFs, extract text, and write:
  legislative/raw_pdf/<body>/<year>/<file>.pdf   (raw retention)
  legislative/minutes/<year>/<date>_<bodyslug>.md (front-matter + flowed text)
  legislative/minutes_index.csv

Provenance = magutah_site (primary). PMN (body 8083 current / 1480 older) is a
documented recovery fallback, not harvested — the site is complete to 2014.
DERIVED + idempotent — rerun to refresh; safe to re-run (overwrites in place).
"""
import csv, os, re, sys, time, urllib.parse, urllib.request
import pypdf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # mag_mpo/
LEG = os.path.join(ROOT, "legislative")
BASE = "https://magutah.gov"
UA = {"User-Agent": "Mozilla/5.0 (civic-data harvester)"}

# (body, tree, [(year, subpath)])
YEARS_MAIN = [str(y) for y in range(2020, 2027)]
YEARS_OLD = [str(y) for y in range(2014, 2020)]
BODIES = [
    ("MPO Board", "mpo_board", [(y, y) for y in YEARS_MAIN] + [(y, "Older/" + y) for y in YEARS_OLD]),
    ("MPO TAC", "tac", [(y, y) for y in YEARS_MAIN] + [(y, "Older/" + y) for y in YEARS_OLD]),
]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")


MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def date_from_name(fname):
    """Pull a meeting date out of the filename, if present; else None.
    Handles M.D.YY(YY), M-D-YY(YY), and '<D> <Mon> <YYYY>' (the 2014 era)."""
    m = re.search(r"\b(\d{1,2})[.\-](\d{1,2})[.\-](\d{2,4})\b", fname)
    if m:
        mo, d, y = (int(x) for x in m.groups())
        y = y + 2000 if y < 100 else y
        if 1 <= mo <= 12 and 1 <= d <= 31 and 2010 <= y <= 2030:
            return "%04d-%02d-%02d" % (y, mo, d)
    m = re.search(r"\b(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})\b", fname)
    if m:
        d = int(m.group(1)); mo = MONTHS.get(m.group(2)[:3].lower()); y = int(m.group(3))
        if mo and 1 <= d <= 31 and 2010 <= y <= 2030:
            return "%04d-%02d-%02d" % (y, mo, d)
    return None


def doctype(fname):
    n = fname.lower()
    if "work session" in n:
        return "Work Session"
    if "orientation" in n:
        return "Orientation"
    if re.search(r"\b101\b", n):
        return "Orientation 101"
    return ""


def get(url, binary=False, retries=4):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read() if binary else r.read().decode("utf-8", "ignore")
        except Exception as e:
            if i == retries - 1:
                print("  ! fetch failed", url, e)
                return None
            time.sleep(1.5 * (i + 1))


def list_minutes(tree, subpath):
    url = BASE + "/sitefiles/minutes-list/?" + urllib.parse.urlencode(
        {"dir": "files/committees/%s/meetings/%s/" % (tree, subpath)})
    html = get(url) or ""
    urls = []
    for m in re.finditer(r'href="(/static/files/committees/[^"]*?minute[^"]*?\.pdf)"', html, re.I):
        urls.append(m.group(1))
    return sorted(set(urls))


def flow(txt):
    """Reconstruct born-digital PDF text into flowing paragraphs."""
    txt = txt.replace("\r", "\n")
    txt = re.sub(r"[ \t]*\n[ \t]*", " ", txt)
    txt = re.sub(r"[ \t]{2,}", " ", txt)
    # normalize the ligature the extractor emits for fi/ff
    txt = txt.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("ﬀ", "ff")
    return txt.strip()


def main():
    rows = []
    seen_text = set()          # (body, texthash) -> drop exact-duplicate minutes
    used_md = set()            # md rel paths already written this run
    for body, tree, plan in BODIES:
        for year, subpath in plan:
            for path in list_minutes(tree, subpath):
                url = BASE + urllib.parse.quote(path)
                fname = urllib.parse.unquote(path.split("/")[-1])
                # A few files in the mpo_board tree are a DIFFERENT body's minutes
                # attached for reference (e.g. the Utah County Commission's own
                # minutes ratifying an MPO action) — not MPO Board minutes, skip.
                if re.search(r"county commission", fname, re.I):
                    print("  - skip foreign-body doc:", fname); continue
                folder = "%s-%s-%s" % re.search(r"/(\d{4})_(\d{2})_(\d{2})/", path).groups()
                # Prefer a date embedded in the FILENAME (some folders hold a prior
                # meeting's approved minutes, e.g. "5.2.19 minutes" in the 6/6 folder).
                date = date_from_name(fname) or folder
                year = date[:4]
                # doc-type discriminator (work session / orientation / 101) so
                # multiple distinct same-date docs get their own meeting rows.
                dt = doctype(fname)
                # raw retention
                raw_rel = os.path.join("raw_pdf", body, year, fname)
                raw_abs = os.path.join(LEG, raw_rel)
                os.makedirs(os.path.dirname(raw_abs), exist_ok=True)
                if not os.path.exists(raw_abs) or os.path.getsize(raw_abs) == 0:
                    data = get(url, binary=True)
                    if not data:
                        continue
                    open(raw_abs, "wb").write(data)
                    time.sleep(0.05)
                # extract text
                try:
                    reader = pypdf.PdfReader(raw_abs)
                    text = flow("\n".join(p.extract_text() or "" for p in reader.pages))
                    npages = len(reader.pages)
                except Exception as e:
                    print("  ! pdf parse", fname, e); continue
                import hashlib
                th = hashlib.md5(text.encode("utf-8")).hexdigest()
                if (body, th) in seen_text:
                    print("  - dup text, skip:", fname); continue
                seen_text.add((body, th))
                title = text[:120].split("  ")[0].strip()
                if dt:
                    title = title + " [" + dt + "]"
                # unique md name: append doctype / counter on collision
                base = "%s_%s%s" % (date, slug(body), ("_" + slug(dt)) if dt else "")
                md_rel = os.path.join("minutes", year, base + ".md")
                n = 2
                while md_rel in used_md:
                    md_rel = os.path.join("minutes", year, "%s_%d.md" % (base, n)); n += 1
                used_md.add(md_rel)
                md_abs = os.path.join(LEG, md_rel)
                os.makedirs(os.path.dirname(md_abs), exist_ok=True)
                fm = ("---\n"
                      "entity: mag_mpo\n"
                      "body: %s\n"
                      "date: %s\n"
                      "title: %s\n"
                      "source_url: %s\n"
                      "source_pdf: legislative/%s\n"
                      "provenance: magutah_site\n"
                      "pages: %d\n"
                      "retrieved: 2026-07-20\n"
                      "---\n\n" % (body, date, title.replace("\n", " "), url,
                                   raw_rel.replace(os.sep, "/"), npages))
                open(md_abs, "w").write(fm + text + "\n")
                rows.append({"body": body, "date": date, "year": year,
                             "title": title.replace("\n", " "),
                             "minutes_md": "legislative/" + md_rel.replace(os.sep, "/"),
                             "source_pdf": "legislative/" + raw_rel.replace(os.sep, "/"),
                             "source_url": url, "pages": npages,
                             "provenance": "magutah_site"})
                print("  ok %-9s %s  (%dp)" % (body, date, npages))
    rows.sort(key=lambda r: (r["body"], r["date"]))
    idx = os.path.join(LEG, "minutes_index.csv")
    with open(idx, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["body", "date", "year", "title",
                           "minutes_md", "source_pdf", "source_url", "pages", "provenance"])
        w.writeheader(); w.writerows(rows)
    print("\nwrote %d minutes across %d bodies -> %s" %
          (len(rows), len({r["body"] for r in rows}), idx))


if __name__ == "__main__":
    main()
