#!/usr/bin/env python3
"""Harvest Salt Lake County agenda packets + staff reports (the "why" behind decisions).

Two tiers (Sandy's proven pattern):
  1. Event AGENDA packets (EventAgendaFile) — born-digital, small; downloaded + text-extracted.
  2. Matter STAFF REPORTS / exhibits — via /matters/{id}/attachments. For the LAND-USE
     matters (those behind the development_application pipeline), download the staff-report
     PDFs (searchable) and INDEX every attachment (name + live source_url + matter_id) so the
     rest are catalogued without storing GBs.

Output: salt_lake_county/packets/{raw/, text/, index.csv}. DERIVED + resumable (skips files
already on disk). Text is the searchable layer (fts_packet after federation).
"""
import csv, os, re, sqlite3, time, urllib.request

B = "https://webapi.legistar.com/v1/slco"
HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
STG = os.path.join(HERE, "staging")
PK = os.path.join(COUNTY, "packets")
RAW, TXT = os.path.join(PK, "raw"), os.path.join(PK, "text")
for d in (RAW, TXT):
    os.makedirs(d, exist_ok=True)

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader


def getj(url, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                d = __import__("json").load(r)
            time.sleep(0.05)
            return d
        except Exception as e:
            if i == tries - 1:
                print("  ! api:", repr(e)); return []
            time.sleep(2 * (i + 1))
    return []


def download(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 800:
        return True
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "civic-data/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r, open(dest, "wb") as f:
                f.write(r.read())
            return os.path.getsize(dest) > 800
        except Exception:
            time.sleep(2 * (i + 1))
    return False


def totext(pdf, txt):
    if os.path.exists(txt):
        return True
    try:
        reader = PdfReader(pdf)
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        if len(text) < 40:
            return False
        with open(txt, "w", encoding="utf-8") as f:
            f.write(text)
        return True
    except Exception:
        return False


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")[:50]


def main():
    events = {e["EventId"]: e for e in csv.DictReader(open(os.path.join(STG, "events.csv")))}
    rows = []

    # tier 1 — event agenda packets
    n_ag = 0
    for eid, e in events.items():
        url = (e.get("EventAgendaFile") or "").strip()
        if not url:
            continue
        date = e["EventDate"][:10]
        pdf = os.path.join(RAW, "agenda_%s.pdf" % eid)
        txt = os.path.join(TXT, "agenda_%s.txt" % eid)
        stored = download(url, pdf)
        has_text = totext(pdf, txt) if stored else False
        rows.append({"date": date, "body": e["EventBodyName"], "packet_kind": "agenda",
                     "title": "%s Agenda %s" % (e["EventBodyName"], date), "matter_id": "",
                     "path": os.path.relpath(pdf, COUNTY) if stored else "",
                     "text_path": os.path.relpath(txt, COUNTY) if has_text else "",
                     "format": "pdf", "source_url": url,
                     "stored_locally": "yes" if stored else "no"})
        n_ag += 1
        if n_ag % 50 == 0:
            print("  agendas: %d" % n_ag, flush=True)
    print("agendas done: %d" % n_ag, flush=True)

    # tier 2 — land-use matter staff reports/attachments (matters behind the dev pipeline)
    db = sqlite3.connect(os.path.join(HERE, "salt_lake_county.db"))
    matter_ids = set()
    for (app_key,) in db.execute(
            "SELECT DISTINCT a.app_key FROM application a JOIN motion m "
            "ON m.application_id=a.application_id WHERE a.app_key LIKE 'matter:%' "
            "AND (m.motion_text LIKE '%rezone%' OR m.motion_text LIKE '%zoning%' "
            "OR m.motion_text LIKE '%planned development%' OR m.motion_text LIKE '%subdivision%' "
            "OR m.motion_text LIKE '%annex%' OR m.motion_text LIKE '%general plan%' "
            "OR m.motion_text LIKE '%conditional use%')"):
        matter_ids.add(app_key.split(":", 1)[1])
    print("land-use matters to fetch attachments for: %d" % len(matter_ids), flush=True)
    n_att = n_sr = 0
    for i, mid in enumerate(sorted(matter_ids), 1):
        for a in getj("%s/matters/%s/attachments" % (B, mid)):
            name = (a.get("MatterAttachmentName") or "").strip()
            url = (a.get("MatterAttachmentHyperlink") or "").strip()
            if not url:
                continue
            n_att += 1
            is_sr = "staff report" in name.lower()
            path = text_path = ""; stored = "no"
            if is_sr:   # download + text the staff reports (the analytical prize)
                pdf = os.path.join(RAW, "staffreport_m%s_%s.pdf" % (mid, slug(name)))
                txt = os.path.join(TXT, "staffreport_m%s_%s.txt" % (mid, slug(name)))
                if download(url, pdf):
                    stored = "yes"; path = os.path.relpath(pdf, COUNTY)
                    if totext(pdf, txt):
                        text_path = os.path.relpath(txt, COUNTY); n_sr += 1
            rows.append({"date": "", "body": "", "packet_kind":
                         "staff_report" if is_sr else "matter_attachment", "title": name,
                         "matter_id": mid, "path": path, "text_path": text_path,
                         "format": "pdf", "source_url": url, "stored_locally": stored})
        if i % 25 == 0:
            print("  matters: %d/%d (attachments=%d, staff reports=%d)"
                  % (i, len(matter_ids), n_att, n_sr), flush=True)

    cols = ["date", "body", "packet_kind", "title", "matter_id", "path", "text_path",
            "format", "source_url", "stored_locally"]
    with open(os.path.join(PK, "index.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print("DONE. %d agendas, %d matter attachments (%d staff reports w/ text). index rows=%d"
          % (n_ag, n_att, n_sr, len(rows)), flush=True)


if __name__ == "__main__":
    main()
