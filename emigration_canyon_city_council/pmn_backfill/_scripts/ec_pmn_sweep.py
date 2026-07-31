#!/usr/bin/env python3
"""Full-history PMN notice sweep for Emigration Canyon bodies 5809 (Council) + 1562 (PC).

Purpose: independently RE-VERIFY that the audited meeting_minutes/ + planning_commission/
datasets are a SUPERSET of every live PMN minutes attachment, and RE-CONFIRM the 2017 (+
scattered pre-2018-10) purge by probing the actual file ids.

Method (GET-only, ~0.7s/host):
  1. Walk /pmn/list/notices.html?id=<body>&page=N (cumulative) until the notice-id set
     stops growing -> the body's entire notice history.
  2. GET each /pmn/sitemap/notice/<id>.html; extract every /pmn/files/<fid>.<ext> link
     with its visible label; classify (minutes / agenda / audio / cancelled / other) and
     pull the meeting date from the notice title.
  3. For each MINUTES-labeled attachment: HEAD-probe the file id (200 live vs 404 purged).
  4. Emit ec_pmn_sweep_<body>.csv (one row per attachment) + a console summary.

Writes CSVs next to this script. Diff vs the repo is done afterward in the shell.
"""
import csv, os, re, sys, time, urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
HERE = os.path.dirname(os.path.abspath(__file__))
BODIES = {"5809": "Council", "1562": "PlanningCommission"}
DATE_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return None, str(e)[:50]


def head_status(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            # read a little to confirm PDF vs 404 html
            head = r.read(1024)
            return r.status, (b"%PDF" in head[:8])
    except urllib.error.HTTPError as e:
        return e.code, False
    except Exception:
        return None, False


def walk_notices(body):
    seen, page, stale = {}, 0, 0
    while True:
        st, html = get(f"https://www.utah.gov/pmn/list/notices.html?id={body}&page={page}")
        if st != 200:
            time.sleep(1.0);
            st, html = get(f"https://www.utah.gov/pmn/list/notices.html?id={body}&page={page}")
        before = len(seen)
        # notice links + nearby title text
        for m in re.finditer(r'sitemap/notice/(\d+)\.html', html or ""):
            seen.setdefault(m.group(1), True)
        grew = len(seen) - before
        print(f"  body {body} page {page}: total notices={len(seen)} (+{grew})", flush=True)
        if grew == 0:
            stale += 1
            if stale >= 2:
                break
        else:
            stale = 0
        page += 1
        if page > 80:
            break
        time.sleep(0.6)
    return list(seen)


def classify(label):
    l = label.lower()
    if "cancel" in l: return "cancelled"
    if l.endswith(".mp3") or "audio" in l or "recording" in l: return "audio"
    if "minute" in l: return "minutes"
    if "agenda" in l: return "agenda"
    if "packet" in l or "supporting" in l or "attach" in l: return "packet"
    return "other"


def main():
    for body, bname in BODIES.items():
        print(f"=== BODY {body} ({bname}) ===", flush=True)
        nids = walk_notices(body)
        rows = []
        for i, nid in enumerate(sorted(nids, key=int)):
            st, html = get(f"https://www.utah.gov/pmn/sitemap/notice/{nid}.html")
            # notice date from title area
            mdate = ""
            dm = DATE_RE.search(html or "")
            if dm:
                mdate = f"{int(dm.group(3)):04d}-{int(dm.group(1)):02d}-{int(dm.group(2)):02d}"
            for m in re.finditer(r'/pmn/files/(\d+)\.([A-Za-z0-9]+)[\"\x27][^>]*>\s*([^<]{0,60})', html or ""):
                fid, ext, label = m.group(1), m.group(2), m.group(3).strip()
                kind = classify(label)
                probe_status, is_pdf = "", ""
                if kind in ("minutes",):
                    ps, pdf = head_status(f"https://www.utah.gov/pmn/files/{fid}.{ext}")
                    probe_status, is_pdf = str(ps), "1" if pdf else "0"
                    time.sleep(0.5)
                rows.append({"body": body, "bname": bname, "notice_id": nid,
                             "notice_date": mdate, "file_id": fid, "ext": ext,
                             "label": label, "kind": kind,
                             "minutes_probe": probe_status, "is_pdf": is_pdf})
            time.sleep(0.5)
            if (i + 1) % 25 == 0:
                print(f"  ...{i+1}/{len(nids)} notices scanned", flush=True)
        out = os.path.join(HERE, f"ec_pmn_sweep_{body}.csv")
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["body","bname","notice_id","notice_date",
                                              "file_id","ext","label","kind",
                                              "minutes_probe","is_pdf"])
            w.writeheader(); w.writerows(rows)
        mins = [r for r in rows if r["kind"] == "minutes"]
        live = [r for r in mins if r["minutes_probe"] == "200" and r["is_pdf"] == "1"]
        dead = [r for r in mins if r["minutes_probe"] != "200" or r["is_pdf"] != "1"]
        print(f"  body {body}: {len(rows)} attachments, {len(mins)} minutes-labeled "
              f"({len(live)} LIVE / {len(dead)} purged/404). wrote {out}", flush=True)
    print("DONE")


if __name__ == "__main__":
    main()
