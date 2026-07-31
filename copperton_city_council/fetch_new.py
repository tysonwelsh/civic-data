#!/usr/bin/env python3
"""fetch_new.py — Copperton incremental-refresh probe.

Read-only by default. Enumerates candidate NEW meeting dates from BOTH portals and diffs them
against what the repo already has, so a refresh knows exactly what to acquire:

  * Town GoDaddy site  copperton.utah.gov/<YEAR>-agendas...   (2023+; docs on img1.wsimg.com)
  * Utah Public Notice notices list  utah.gov/pmn/list/notices.html?id=<BODY>
        council body 5831  ·  planning-commission body 1560

Both are fetched with `curl -k` + a browser UA (the GoDaddy cert covers secureserversites.net,
not copperton.utah.gov, so a plain WebFetch fails — verified 2026-07-12). Candidate dates already
present in the dataset's minutes_index.csv, or logged in its minutes_unrecovered.csv, are
excluded. NOTE: PMN attachments older than ~mid-2018 are 404-purged (the honest
2017-02→2018-06 gap) — those notices are reported as `[purged]`, never as recoverable.

Usage:
    python3 fetch_new.py            # == --probe ; read-only; prints candidate new dates
    python3 fetch_new.py --probe
    python3 fetch_new.py --json     # machine-readable probe result

Actual acquisition is intentionally NOT automated here: hand the reported dates to
meeting_minutes/fetch_minutes.py (which downloads -> verifies -> OCR-aware markdown -> index),
then re-run extract_votes.py + validate_votes.py and rebuild db/ + weeks/.
"""
import os, re, sys, csv, json, subprocess, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36')

# Shared refresh plumbing — used ONLY to emit the standard machine-readable probe
# JSON (<city>/refresh_probe.json) that scripts/refresh_status.py consumes; the
# stdout report below is unchanged. No fetching happens here.
sys.path.insert(0, os.path.join(HERE, os.pardir, "scripts"))
import refresh_lib as rl  # noqa: E402

# GoDaddy Agendas-&-Minutes year-page slugs (they are NOT uniform — harvested from recon.md).
GODADDY_YEAR_PAGES = {
    2023: "https://copperton.utah.gov/2023-agendas-%26-minutes",
    2024: "https://copperton.utah.gov/2024-agendas-%26-minutes-1",
    2025: "https://copperton.utah.gov/2025-agendas-%26-minutes-1",
    2026: "https://copperton.utah.gov/2026-agendas-%26-minutes",
}
PMN_BODIES = {"meeting_minutes": 5831, "planning_commission": 1560}
PMN_PURGE_CUTOFF = datetime.date(2018, 7, 1)   # attachments older than ~this are 404 on PMN


def curl(url, tries=2):
    for _ in range(tries):
        r = subprocess.run(["curl", "-k", "-sL", "--max-time", "60", "-A", UA, url],
                           capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout.decode("utf-8", "replace")
    return ""


def known_dates(dataset):
    """Dates already indexed OR logged unrecovered for this dataset."""
    base = os.path.join(HERE, dataset)
    have = set()
    for fn, col in (("minutes_index.csv", "date"), ("minutes_unrecovered.csv", "date")):
        p = os.path.join(base, fn)
        if not os.path.exists(p):
            continue
        with open(p, newline="") as f:
            for row in csv.DictReader(f):
                d = (row.get(col) or "").strip()
                if re.match(r"\d{4}-\d{2}-\d{2}", d):
                    have.add(d[:10])
    return have


def index_max(dataset):
    p = os.path.join(HERE, dataset, "minutes_index.csv")
    ds = []
    if os.path.exists(p):
        with open(p, newline="") as f:
            ds = [r["date"][:10] for r in csv.DictReader(f)
                  if re.match(r"\d{4}-\d{2}-\d{2}", r.get("date", ""))]
    return max(ds) if ds else "0000-00-00"


# ---- GoDaddy: harvest doc anchors, read the date out of each filename -------------------------
_MDY = re.compile(r'(\d{2})[-_](\d{2})[-_](20\d{2})')  # 07-16-2025 in the wsimg filename

def probe_godaddy(known):
    """Return sorted list of (date, note) candidate NEW council meetings from the town site."""
    found = {}
    for year, url in GODADDY_YEAR_PAGES.items():
        html = curl(url)
        if not html:
            found.setdefault("_error", []).append(f"{year}: fetch failed")
            continue
        for m in re.finditer(r'https://img1\.wsimg\.com/blobby/go/[^"\'<> ]+', html):
            frag = m.group(0)
            dm = _MDY.search(frag)
            if not dm:
                continue
            mm, dd, yyyy = dm.groups()
            try:
                iso = datetime.date(int(yyyy), int(mm), int(dd)).isoformat()
            except ValueError:
                continue
            low = frag.lower()
            if "minute" not in low:        # skip agenda / supporting-doc anchors
                continue
            if iso not in known:
                found[iso] = "godaddy: minutes doc present"
    return sorted((d, n) for d, n in found.items() if d != "_error")


# ---- PMN: parse the cumulative notices list --------------------------------------------------
_ROW = re.compile(r'<tr class="[^"]*">(.*?)</tr>', re.S)
_DATE = re.compile(r'<td>(\d{4})/(\d{2})/(\d{2})')          # e.g. 0025/07/16 -> 2025-07-16
_ATT = re.compile(r'/pmn/files/(\d+\.\w+)')                 # attachment file references in a row
_DOC_EXT = (".pdf", ".docx", ".doc")                        # a minutes doc is one of these

def probe_pmn(body_id, known, deep_pages=(1, 20, 48)):
    """Return sorted (date, note) candidate meetings from a PMN body's notices list.

    The list is cumulative per page; page 48 reaches the oldest rows (later pages just repeat),
    so we union a few page depths. For each meeting date we look at the attachment file-refs in
    the row and keep only DOC attachments (.pdf/.docx) — audio-only rows (.mp3/.wav agendas) are
    dropped, which is what removes the bulk of false positives. A candidate is still only a
    NOTICE-level lead: PMN routinely attaches an agenda PDF (not minutes), so the reported doc
    must be opened to confirm it is the minutes before ingesting."""
    seen = {}   # iso -> set of attachment filenames (doc-type only)
    for pg in deep_pages:
        html = curl(f"https://www.utah.gov/pmn/list/notices.html?id={body_id}&page={pg}")
        for row in _ROW.findall(html):
            d = _DATE.search(row)
            if not d:
                continue
            yy = "20" + d.group(1)[2:]          # 0025 -> 2025 ; 0017 -> 2017
            try:
                iso = datetime.date(int(yy), int(d.group(2)), int(d.group(3))).isoformat()
            except ValueError:
                continue
            docs = {a for a in _ATT.findall(row) if a.lower().endswith(_DOC_EXT)}
            seen.setdefault(iso, set()).update(docs)
    out = []
    for iso, docs in seen.items():
        if iso in known:
            continue
        d = datetime.date.fromisoformat(iso)
        if d < PMN_PURGE_CUTOFF:
            # pre-mid-2018 attachments are 404 even when the row lists file-ids (retention purge)
            out.append((iso, "pmn: attachment 404-purged (retention) — NOT recoverable"))
        elif docs:
            out.append((iso, f"pmn body {body_id}: {len(docs)} doc attachment(s) "
                             f"{sorted(docs)} — open to confirm it is MINUTES (may be an agenda)"))
        # rows with only audio (or no) attachments are not surfaced as doc candidates
    return sorted(out)


def main():
    args = set(sys.argv[1:])
    as_json = "--json" in args
    if args - {"--probe", "--json"}:
        print(__doc__)
        return 2

    result = {"generated": datetime.date.today().isoformat(), "datasets": {}}

    # Council: GoDaddy (2023+) + PMN 5831
    known_c = known_dates("meeting_minutes")
    result["datasets"]["meeting_minutes"] = {
        "index_max": index_max("meeting_minutes"),
        "godaddy_candidates": probe_godaddy(known_c),
        "pmn_candidates": probe_pmn(PMN_BODIES["meeting_minutes"], known_c),
    }
    # Planning Commission: PMN 1560 only
    known_p = known_dates("planning_commission")
    result["datasets"]["planning_commission"] = {
        "index_max": index_max("planning_commission"),
        "pmn_candidates": probe_pmn(PMN_BODIES["planning_commission"], known_p),
    }

    # Emit the standard machine-readable probe JSON for scripts/refresh_status.py.
    # new_count = genuine (non-404-purged) candidate meeting dates across both portals.
    for ds, info in result["datasets"].items():
        gd = info.get("godaddy_candidates", []) or []
        pmn_real = [(d, n) for d, n in info["pmn_candidates"] if "404-purged" not in n]
        purged = [1 for d, n in info["pmn_candidates"] if "404-purged" in n]
        new_dates = sorted({d for d, _ in gd} | {d for d, _ in pmn_real})
        mx, nrows = rl.index_max_date(os.path.join(HERE, ds))
        rl.write_probe(HERE, ds, {
            "probe_date": rl.today(),
            "portal": "godaddy+pmn" if ds == "meeting_minutes" else "pmn",
            "index_max_date": mx, "index_rows": nrows, "status": "ok",
            "new_count": len(new_dates),
            "new_items": [{"date": d, "title": "Copperton meeting", "url": ""}
                          for d in new_dates],
            "notes": (f"PMN body {PMN_BODIES[ds]}"
                      + (f" + GoDaddy town site" if ds == "meeting_minutes" else "")
                      + f"; {len(new_dates)} candidate new meeting date(s)"
                      + (f"; {len(purged)} pre-2018-07 notices 404-purged (honest gap)"
                         if purged else "")
                      + ". Open each doc to confirm minutes vs agenda before ingesting."),
            "fetch_cmd": "feed real NEW dates to meeting_minutes/fetch_minutes.py",
        })

    if as_json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"Copperton refresh probe — {result['generated']} (read-only)\n")
    for ds, info in result["datasets"].items():
        print(f"== {ds} == (index max {info['index_max']})")
        gd = info.get("godaddy_candidates", [])
        if "godaddy_candidates" in info:
            if gd:
                print("  GoDaddy town-site NEW minutes:")
                for d, n in gd:
                    print(f"    {d}  {n}")
            else:
                print("  GoDaddy: no new minutes docs (or all already indexed)")
        pmn = [(d, n) for d, n in info["pmn_candidates"] if "404-purged" not in n]
        purged = [(d, n) for d, n in info["pmn_candidates"] if "404-purged" in n]
        if pmn:
            print("  PMN NEW / candidate meetings:")
            for d, n in pmn:
                print(f"    {d}  {n}")
        else:
            print("  PMN: no new recoverable meetings")
        if purged:
            print(f"  PMN: {len(purged)} pre-2018-07 notices are 404-purged (honest gap; see "
                  f"minutes_unrecovered.csv)")
        if ds == "planning_commission" and pmn:
            print("  NOTE: Copperton's PC cancels most scheduled meetings — sampling (2026-07-12) "
                  "found the great majority of these PC notices are ~150-word CANCELLATION "
                  "agendas, not minutes. Confirm each doc is genuine minutes before ingesting.")
        print()
    print("Next: feed any real NEW dates to meeting_minutes/fetch_minutes.py, then re-run "
          "extract_votes.py + validate_votes.py and rebuild db/ + weeks/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
