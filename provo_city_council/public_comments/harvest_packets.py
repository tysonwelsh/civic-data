#!/usr/bin/env python3
"""
FULL agenda-packet public-comment harvest for Provo (documentType=5).

Iterates ALL Council Regular-Meeting packet_url rows in
meeting_minutes/minutes_index.csv (~138), downloads each packet PDF to a work
dir, runs `pdftotext -layout`, and scans the text for genuine resident written
comments (email blocks: From:/Sent:/To:/Subject: + body).

Disk policy:
  - If a packet yields >= 1 GENUINE comment, keep:
        raw/packets/<date>_packet.pdf   (renamed)
        raw/packet_txt/packet_<date>.txt
    so every extracted row has retrievable provenance.
  - If a packet yields 0 genuine comments, the PDF is deleted (not hoarded).
    A txt copy is kept ONLY if it had any From: blocks at all (for audit);
    otherwise nothing is kept. Either way it is logged in packets_scanned.csv.

Resumable: skips any date already present in packets_scanned.csv.

This script ONLY scans/downloads and updates packets_scanned.csv. The clean CSV
is rebuilt deterministically by extract_packet_comments.py from raw/packet_txt/.
"""
import csv, os, re, sys, subprocess, glob
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
INDEX = os.path.join(REPO, 'meeting_minutes', 'minutes_index.csv')
PACKETS_DIR = os.path.join(HERE, 'raw', 'packets')
TXT_DIR = os.path.join(HERE, 'raw', 'packet_txt')
SCANNED = os.path.join(HERE, 'packets_scanned.csv')
WORK = os.environ.get('PACKET_WORK',
    '/private/tmp/claude-501/-Users-tysonwelsh-Sites/'
    'cd2d1a4b-f0f4-479f-b78d-4c9686e9389b/scratchpad/packetwork')

os.makedirs(PACKETS_DIR, exist_ok=True)
os.makedirs(TXT_DIR, exist_ok=True)
os.makedirs(WORK, exist_ok=True)

# --- comment-detection: reuse the same parser the clean CSV is built from -----
sys.path.insert(0, HERE)
import extract_packet_comments as epc

SCAN_COLS = ['date', 'packet_url', 'had_comments', 'n_comments', 'pages',
             'size_bytes', 'from_blocks', 'note']


def load_scanned():
    done = {}
    if os.path.exists(SCANNED):
        for r in csv.DictReader(open(SCANNED)):
            done[r['date']] = r
    return done


def write_scanned(rows):
    rows = sorted(rows.values(), key=lambda r: r['date'])
    with open(SCANNED, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=SCAN_COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in SCAN_COLS})


def regular_packets():
    out = []
    seen = set()
    for r in csv.DictReader(open(INDEX)):
        if r['title'].strip().lower() != 'council regular meeting':
            continue
        url = r['packet_url'].strip()
        if not url:
            continue
        d = r['date'].strip()
        if d in seen:           # one packet per meeting date
            continue
        seen.add(d)
        out.append((d, url))
    return sorted(out)


def main():
    pkts = regular_packets()
    done = load_scanned()
    total = len(pkts)
    print(f"Regular-meeting packets: {total}; already scanned: {len(done)}")
    for i, (date, url) in enumerate(pkts, 1):
        if date in done:
            continue
        pdf = os.path.join(WORK, f'{date}.pdf')
        txt = os.path.join(WORK, f'{date}.txt')
        note = ''
        try:
            rc = subprocess.run(['curl', '-sL', '--max-time', '180', url,
                                 '-o', pdf], capture_output=True)
            size = os.path.getsize(pdf) if os.path.exists(pdf) else 0
            if size < 1000:
                note = 'download_failed_or_tiny'
                done[date] = dict(date=date, packet_url=url, had_comments='false',
                                  n_comments=0, pages='', size_bytes=size,
                                  from_blocks=0, note=note)
                print(f"[{i}/{total}] {date}  DL FAIL ({size}b)")
                write_scanned(done)
                if os.path.exists(pdf):
                    os.remove(pdf)
                continue
            pages = ''
            pi = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True)
            mp = re.search(r'Pages:\s+(\d+)', pi.stdout)
            if mp:
                pages = mp.group(1)
            subprocess.run(['pdftotext', '-layout', pdf, txt],
                           capture_output=True, timeout=300)
        except subprocess.TimeoutExpired:
            note = 'pdftotext_timeout'
            done[date] = dict(date=date, packet_url=url, had_comments='false',
                              n_comments=0, pages=pages, size_bytes=size,
                              from_blocks=0, note=note)
            print(f"[{i}/{total}] {date}  TIMEOUT")
            write_scanned(done)
            for p in (pdf, txt):
                if os.path.exists(p):
                    os.remove(p)
            continue
        except Exception as e:
            note = f'error:{type(e).__name__}'
            done[date] = dict(date=date, packet_url=url, had_comments='false',
                              n_comments=0, pages=pages if 'pages' in dir() else '',
                              size_bytes=size if 'size' in dir() else 0,
                              from_blocks=0, note=note)
            print(f"[{i}/{total}] {date}  ERROR {e}")
            write_scanned(done)
            for p in (pdf, txt):
                if os.path.exists(p):
                    os.remove(p)
            continue

        # count raw From: blocks (audit) and run the genuine-comment parser
        text = open(txt, encoding='utf-8', errors='replace').read() if os.path.exists(txt) else ''
        from_blocks = len(epc.BLOCK_RE.findall(text))
        dropped = []
        # parse_packet keys off filename packet_<date>.txt for date fallback;
        # stage the txt under that name in WORK for the parser to read.
        staged = os.path.join(WORK, f'packet_{date}.txt')
        if text:
            with open(staged, 'w') as f:
                f.write(text)
            rows = epc.parse_packet(staged, dropped)
        else:
            rows = []
        n = len(rows)

        if n >= 1:
            # KEEP: rename pdf + persist txt under canonical name
            keep_pdf = os.path.join(PACKETS_DIR, f'{date}_packet.pdf')
            keep_txt = os.path.join(TXT_DIR, f'packet_{date}.txt')
            os.replace(pdf, keep_pdf)
            with open(keep_txt, 'w') as f:
                f.write(text)
            had = 'true'
            print(f"[{i}/{total}] {date}  KEEP  {n} comments ({pages}p, {size//1024}KB, {from_blocks} from-blocks)")
        else:
            had = 'false'
            if os.path.exists(pdf):
                os.remove(pdf)
            print(f"[{i}/{total}] {date}  ---   0 comments ({pages}p, {size//1024}KB, {from_blocks} from-blocks)")
        # cleanup work txts
        for p in (txt, staged):
            if os.path.exists(p):
                os.remove(p)

        done[date] = dict(date=date, packet_url=url, had_comments=had,
                          n_comments=n, pages=pages, size_bytes=size,
                          from_blocks=from_blocks, note=note)
        write_scanned(done)

    # summary
    done = load_scanned()
    kept = [r for r in done.values() if r['had_comments'] == 'true']
    print(f"\n=== scanned {len(done)}/{total} ; packets with comments: {len(kept)} ===")
    print("kept dates:", sorted(r['date'] for r in kept))


if __name__ == '__main__':
    main()
