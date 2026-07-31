#!/usr/bin/env python3
"""Enumerate the MSD (Greater Salt Lake MSD) CivicPlus AgendaCenter by meeting-id (MID).

The ViewFile endpoint keys ONLY on the trailing numeric MID (the _MMDDYYYY- prefix is
cosmetic and ignored): /AgendaCenter/ViewFile/{Minutes,Agenda}/<MID>. MIDs are shared
across every MSD body/category. This script pulls each MID's Minutes and Agenda PDFs to a
throwaway scratch dir, extracts the first-page text, and classifies body + date so we can
find any Emigration Canyon (council or PC) documents — especially purged-2017 minutes PMN
lacks. Discovery only; genuine recoveries are re-fetched into raw/ via polite_fetch.py.

GET-only, ~0.8s/host throttle. Writes ec_msd_catalog.csv next to this script.
"""
import csv, os, re, subprocess, sys, time, urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
BASE = "https://www.msd.utah.gov/AgendaCenter/ViewFile/{kind}/{mid}"
HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.join(HERE, "_scratch")
os.makedirs(SCRATCH, exist_ok=True)
OUT = os.path.join(HERE, "ec_msd_catalog.csv")

MAXMID = int(sys.argv[1]) if len(sys.argv) > 1 else 195

BODY_PATTERNS = [
    ("emigration_canyon", r"emigration\s+canyon"),
    ("emigration_other", r"emigration"),
    ("copperton", r"copperton"),
    ("kearns", r"kearns"),
    ("magna", r"magna"),
    ("white_city", r"white\s*city"),
    ("board_of_trustees", r"board\s+of\s+trustees"),
    ("msd_generic", r"municipal\s+services\s+district"),
]
DATE_RE = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"[a-z]*\.?\s+(\d{1,2}),?\s*(\d{4})", re.I)
PC_RE = re.compile(r"planning\s+commission", re.I)


def fetch(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            ct = r.headers.get("Content-Type", "")
            data = r.read()
        if b"%PDF" not in data[:1024] and "pdf" not in ct:
            return None, ct, len(data)
        with open(path, "wb") as f:
            f.write(data)
        return "pdf", ct, len(data)
    except Exception as e:
        return None, str(e)[:40], 0


def pdftext(path, pages=2):
    try:
        out = subprocess.run(["pdftotext", "-layout", "-l", str(pages), path, "-"],
                             capture_output=True, timeout=30)
        return out.stdout.decode("utf-8", "replace")
    except Exception:
        return ""


def classify(txt):
    head = txt[:1500]
    body = ""
    for name, pat in BODY_PATTERNS:
        if re.search(pat, head, re.I):
            body = name
            break
    is_pc = bool(PC_RE.search(head))
    m = DATE_RE.search(head)
    date = ""
    if m:
        months = {mn.lower(): i for i, mn in enumerate(
            ["", "January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"], 0)}
        mo = None
        for k, v in months.items():
            if k and head[m.start():m.start()+len(k)].lower() == k[:len(k)]:
                pass
        mon = m.group(1).lower()[:3]
        monmap = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,
                  "sep":9,"oct":10,"nov":11,"dec":12}
        try:
            date = f"{int(m.group(3)):04d}-{monmap[mon]:02d}-{int(m.group(2)):02d}"
        except Exception:
            date = ""
    return body, ("PC" if is_pc else "Council/Other"), date


def main():
    rows = []
    for mid in range(1, MAXMID + 1):
        rec = {"mid": mid}
        for kind in ("Minutes", "Agenda"):
            path = os.path.join(SCRATCH, f"{kind.lower()}_{mid}.pdf")
            url = BASE.format(kind=kind, mid=mid)
            got, ct, size = fetch(url, path)
            rec[f"{kind}_ok"] = "1" if got else "0"
            rec[f"{kind}_size"] = size
            if got:
                txt = pdftext(path)
                body, cat, date = classify(txt)
                rec[f"{kind}_body"] = body
                rec[f"{kind}_cat"] = cat
                rec[f"{kind}_date"] = date
                # keep scratch pdf only if emigration; else delete to save disk
                if "emigration" not in (body or ""):
                    try: os.remove(path)
                    except OSError: pass
            else:
                rec[f"{kind}_body"] = ""
                rec[f"{kind}_cat"] = ""
                rec[f"{kind}_date"] = ""
                try: os.remove(path)
                except OSError: pass
            time.sleep(0.8)
        tag = rec.get("Minutes_body") or rec.get("Agenda_body")
        print(f"MID {mid:3d} | min={rec['Minutes_ok']}({rec.get('Minutes_body','')[:18]:18s} {rec.get('Minutes_date','')}) "
              f"| ag={rec['Agenda_ok']}({rec.get('Agenda_body','')[:18]:18s} {rec.get('Agenda_date','')})",
              flush=True)
        rows.append(rec)
        if rec["Minutes_ok"] == "0" and rec["Agenda_ok"] == "0" and mid > 189:
            # past the end
            pass
    cols = ["mid","Minutes_ok","Minutes_size","Minutes_body","Minutes_cat","Minutes_date",
            "Agenda_ok","Agenda_size","Agenda_body","Agenda_cat","Agenda_date"]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    print("\nwrote", OUT)


if __name__ == "__main__":
    main()
