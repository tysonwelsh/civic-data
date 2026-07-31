#!/usr/bin/env python3
"""Date every LIVE PC (body 1562) minutes attachment the sweep found that is NOT already a
repo file_id, then classify vs the repo's planning_commission index + unrecovered list.

Buckets:
  DUP      -> meeting date already covered by an index row (alternate upload/version)
  RECOVERY -> meeting date is in minutes_unrecovered.csv (a real gap this could fill)
  NEW      -> meeting date not in index and not in unrecovered (also a recovery)

Downloads each candidate once (throwaway scratch), extracts the meeting date from the PDF
body (born-digital text or OCR fallback), and prints the classification. GET-only, throttled.
"""
import csv, os, re, subprocess, sys, time, urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
HERE = os.path.dirname(os.path.abspath(__file__))
CITY = os.path.abspath(os.path.join(HERE, "..", ".."))
SCRATCH = os.path.join(HERE, "_pc_scratch")
os.makedirs(SCRATCH, exist_ok=True)

MON = {m: i for i, m in enumerate(
    ["january","february","march","april","may","june","july","august",
     "september","october","november","december"], 1)}
DATE_TXT = re.compile(
    r"(january|february|march|april|may|june|july|august|september|october|november|december)"
    r"\.?\s+(\d{1,2}),?\s*(\d{4})", re.I)


def repo_dates():
    idx = set(r["date"] for r in csv.DictReader(
        open(os.path.join(CITY, "planning_commission", "minutes_index.csv"))))
    unrec = {}
    for r in csv.DictReader(open(os.path.join(CITY, "planning_commission", "minutes_unrecovered.csv"))):
        unrec[r["date"]] = r["reason"]
    return idx, unrec


def fetch(fid):
    url = f"https://www.utah.gov/pmn/files/{fid}.pdf"
    p = os.path.join(SCRATCH, f"{fid}.pdf")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        open(p, "wb").write(r.read())
    return p


def extract_date(p):
    txt = subprocess.run(["pdftotext", "-layout", "-l", "2", p, "-"],
                         capture_output=True, timeout=40).stdout.decode("utf-8", "replace")
    if len(txt.strip()) < 40:  # image-only -> OCR page 1
        try:
            subprocess.run(["pdftoppm", "-f", "1", "-l", "1", "-r", "130", "-png",
                            p, p + "_pg"], capture_output=True, timeout=60)
            png = p + "_pg-1.png"
            if os.path.exists(png):
                txt = subprocess.run(["tesseract", png, "-"], capture_output=True,
                                     timeout=90).stdout.decode("utf-8", "replace")
        except Exception:
            pass
    m = DATE_TXT.search(txt)
    if m:
        try:
            return f"{int(m.group(3)):04d}-{MON[m.group(1).lower()]:02d}-{int(m.group(2)):02d}", "ok"
        except Exception:
            return "", "parsefail"
    return "", "nodate"


def main():
    idx, unrec = repo_dates()
    repo_fids = set(r["pmn_file_id"] for r in csv.DictReader(
        open(os.path.join(CITY, "planning_commission", "minutes_index.csv"))))
    sw = list(csv.DictReader(open(os.path.join(HERE, "ec_pmn_sweep_1562.csv"))))
    cand = [r for r in sw if r["kind"] == "minutes" and r["minutes_probe"] == "200"
            and r["is_pdf"] == "1" and r["file_id"] not in repo_fids]
    print(f"{len(cand)} candidate LIVE non-repo PC minutes to date\n")
    out = []
    for r in cand:
        fid = r["file_id"]
        try:
            p = fetch(fid)
            d, why = extract_date(p)
        except Exception as e:
            d, why = "", f"err:{str(e)[:30]}"
        if d and d in idx:
            bucket = "DUP"
        elif d and d in unrec:
            bucket = "RECOVERY(unrec)"
        elif d:
            bucket = "NEW"
        else:
            bucket = "UNDATED"
        print(f"  {bucket:16s} fid={fid} date={d or '??'} ({why}) label={r['label'][:32]!r}")
        out.append({**r, "meeting_date": d, "bucket": bucket, "date_src": why})
        # remove non-recovery scratch to save disk
        if bucket in ("DUP",):
            try: os.remove(p)
            except OSError: pass
        time.sleep(0.6)
    with open(os.path.join(HERE, "ec_pc_recovery_candidates.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    from collections import Counter
    print("\nsummary:", dict(Counter(r["bucket"] for r in out)))


if __name__ == "__main__":
    main()
