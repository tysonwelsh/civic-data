#!/usr/bin/env python3
"""
harvest_packets.py — Millcreek IN-PACKETS public-comment harvest (Provo pattern).

Millcreek publishes genuine verbatim resident comments ONLY bundled inside its
Planning Commission agenda/minutes packets (there is no standalone comments page /
eComment archive — see AVAILABILITY.md).  This driver walks EVERY retained PC packet
PDF pinned by ../packets/index.csv (packet_kind=full_packet, body=PlanningCommission,
stored_locally=yes — the combined docs already on disk under
planning_commission/raw/), runs `pdftotext -layout`, and scans each for genuine
resident-comment blocks.

What counts as a genuine comment block (the bar, mirrors Provo / SLC):
  a forwarded/attached resident EMAIL block — "From: <name>\n(Sent|To|Subject|Date):…"
  whose sender is NOT city staff / the applicant / a consultant and whose body is
  substantive resident input.  (Clerk third-person speaker paraphrase in the minutes
  narrative — "X, a resident, stated…" — is NOT a written comment and is NOT harvested
  here; it is a meeting-record speaker log.)

COVERAGE, HONESTLY (read AVAILABILITY.md addendum):
  The RETAINED PDFs are the AgendaCenter *Minutes-view* documents (ViewFile/Minutes/…),
  which for some meetings embed the forwarded-correspondence pages and for others are
  minutes-only.  The very large `?packet=true` land-use packets whose staff reports
  append standalone "Public Comments from Residents" letters are a DIFFERENT (much
  larger) PDF that is NOT retained on disk — recovering those is the documented ceiling
  (a live re-fetch pass), not attempted here.  Every packet scanned is logged to
  packets_scanned.csv so coverage is provable.

Outputs:
  raw/packet_txt/packet_<date>.txt   pdftotext -layout, ONLY for comment-bearing packets
  packets_scanned.csv                one row per PC packet scanned (full-coverage audit)

Resumable: re-runs are deterministic (re-scans from the on-disk PDFs; overwrites the
kept .txt + the audit log).  No network.  Run extract_packet_comments.py afterward.
"""
import csv, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY = os.path.dirname(HERE)
INDEX = os.path.join(CITY, "packets", "index.csv")
TXT_DIR = os.path.join(HERE, "raw", "packet_txt")
SCAN_LOG = os.path.join(HERE, "packets_scanned.csv")

# A candidate resident email block: a From: line followed by ≥1 header line.
BLOCK_RE = re.compile(
    r'^[ \t\x0c]*From:[ \t]*(?P<from>[A-Za-z][^\n]*?)\n'
    r'(?P<mid>(?:[ \t\x0c]*(?:Sent|To|Cc|Subject|Date|Re):[^\n]*\n)+)', re.M)

# City-staff / internal / applicant senders that FORWARD or route resident mail — a
# block from one of these is not itself a public comment (the resident's own inner
# block is captured separately).  Reviewed across all comment-bearing packets.
STAFF_SENDER_RE = re.compile(
    r'(@millcreek\.us|@millcreekut\.gov|planning\s+commission|planning\s+division|'
    r'city\s+recorder|community\s+development|staff|department|director|coordinator|'
    r'no-?reply|notification)', re.I)
STAFF_NAMES = {
    "elyse sullivan",     # Millcreek staff (forwards FW: resident mail)
    "carlos estudillo",   # Millcreek planning staff (forwards resident mail)
    "shawn lamar",        # PC Chair (forwards FW: resident mail)
    "brad sanderson",     # Millcreek staff (forwards resident mail)
    "francis lilly",      # Planning Director
    "sean murray",        # planning staff
}


def clean_sender(raw):
    raw = re.sub(r'<[^>]*>', '', raw)
    raw = re.sub(r'\[[^\]]*\]', '', raw)
    raw = re.sub(r'\b[\w.\-]+@[\w.\-]+\b', '', raw)
    return re.sub(r'\s+', ' ', raw).strip(' ,;>')


def count_genuine_blocks(text):
    """How many blocks look like genuine (non-staff) resident comments with a body."""
    starts = list(BLOCK_RE.finditer(text))
    n = 0
    for i, m in enumerate(starts):
        sender_raw = m.group('from')
        frm = clean_sender(sender_raw)
        if STAFF_SENDER_RE.search(sender_raw) or frm.lower() in STAFF_NAMES:
            continue
        body_end = starts[i + 1].start() if i + 1 < len(starts) else min(len(text), m.end() + 6000)
        body = re.sub(r'\s+', ' ', text[m.end():body_end]).strip()
        if len(body) >= 40:
            n += 1
    return n


def pdftotext(pdf_path):
    return subprocess.run(["pdftotext", "-layout", pdf_path, "-"],
                          capture_output=True, text=True, errors="replace").stdout


def main():
    os.makedirs(TXT_DIR, exist_ok=True)
    rows = [r for r in csv.DictReader(open(INDEX, encoding="utf-8"))
            if r["body"] == "PlanningCommission"
            and r["packet_kind"] == "full_packet"
            and r["stored_locally"] == "yes"]
    rows.sort(key=lambda r: r["date"])
    log = []
    kept = 0
    for r in rows:
        pdf = os.path.join(CITY, r["path"])
        if not os.path.exists(pdf):
            log.append(dict(date=r["date"], docid=r["docid"], path=r["path"],
                            pages="", size_bytes=r.get("content_length_bytes", ""),
                            n_email_blocks="", n_genuine="", had_comments="MISSING",
                            note="retained PDF absent"))
            continue
        text = pdftotext(pdf)
        pages = text.count("\x0c") + 1
        n_blocks = len(BLOCK_RE.findall(text))
        n_genuine = count_genuine_blocks(text)
        had = "yes" if n_genuine else "no"
        if n_genuine:
            with open(os.path.join(TXT_DIR, f"packet_{r['date']}.txt"), "w",
                      encoding="utf-8") as f:
                f.write(text)
            kept += 1
        log.append(dict(date=r["date"], docid=r["docid"], path=r["path"],
                        pages=pages, size_bytes=r.get("content_length_bytes", ""),
                        n_email_blocks=n_blocks, n_genuine=n_genuine, had_comments=had,
                        note=""))
    cols = ["date", "docid", "path", "pages", "size_bytes",
            "n_email_blocks", "n_genuine", "had_comments", "note"]
    with open(SCAN_LOG, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(log)
    print(f"scanned {len(rows)} PC packets; {kept} comment-bearing -> raw/packet_txt/")
    print(f"audit -> {SCAN_LOG}")


if __name__ == "__main__":
    main()
