#!/usr/bin/env python3
"""
build_comments.py — canonical builder for Millcreek public_comments/all_comments_clean.csv.

Merges the two IN-PACKETS harvest channels into one deduped SLC-schema table:

  1. RETAINED Minutes-view packets  -> extract_packet_comments.py (raw/packet_txt/)   = 9 letters
  2. Large ?packet=true land-use packets -> extract_packet_true_comments.py            (fetched
     by harvest_packet_true.py into raw/packet_true_txt/, binaries discarded per §9)

Dedup is CONTENT-based (date_normalized + normalized comment prefix) so a letter that appears
in BOTH a Minutes-view doc and a ?packet=true packet — or under a slightly different display
name (e.g. "ClinicalTeam" vs "Clinical Team") — is ingested once, never doubled.  The
Minutes-view row wins ties (it was the first-audited).

Deterministic, no network.  Run harvest_packet_true.py first (it needs the network); this
merge only reads the extracted text.  Rebuild weeks/ afterward only if comments feed them
(they currently do not — build_weeks.py has no comment stage).
"""
import csv, os, re, glob, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
CLEAN = os.path.join(HERE, "all_comments_clean.csv")
PKT_TRUE = os.path.join(HERE, "all_comments_packet_true.csv")
PT_TXT = os.path.join(HERE, "raw", "packet_true_txt")

SLC_COLS = ['date', 'contact_name', 'subject', 'topic', 'comment', 'district', 'source',
            'has_attachment', 'source_file', 'page_numbers', 'period_start', 'period_end',
            'date_normalized', 'quality_flag']


def content_key(r):
    c = re.sub(r'\s+', ' ', r['comment']).strip().lower()
    return (r.get('date_normalized', ''), c[:70])


def main():
    # 1. regenerate both channels from their extracted text (idempotent, no network)
    importlib.import_module('extract_packet_comments').main()   # -> all_comments_clean.csv (9)
    importlib.import_module('extract_packet_true_comments').main()  # -> all_comments_packet_true.csv

    minutes_rows = list(csv.DictReader(open(CLEAN, encoding='utf-8')))       # Minutes-view (win ties)
    pkt_rows = list(csv.DictReader(open(PKT_TRUE, encoding='utf-8'))) if os.path.exists(PKT_TRUE) else []

    seen, merged, dup = set(), [], 0
    for r in minutes_rows + pkt_rows:      # Minutes-view first => it wins any content tie
        k = content_key(r)
        if k in seen:
            dup += 1
            continue
        seen.add(k)
        merged.append({c: r.get(c, '') for c in SLC_COLS})

    merged.sort(key=lambda r: (r['date_normalized'] or '', r['contact_name'].lower()))
    with open(CLEAN, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=SLC_COLS)
        w.writeheader()
        w.writerows(merged)

    # Retain packet_true_txt sidecars ONLY for comment-bearing packets (the convention of
    # harvest_packets.py) — every fetch is already logged in packet_true_fetch.csv, so the
    # non-comment-bearing 350 MB of pdftotext is not kept in-repo (re-derivable by re-running
    # harvest_packet_true.py, which re-fetches + re-extracts).
    keep = {os.path.basename(r['source_file']) for r in pkt_rows
            if 'packet_true_txt' in r['source_file']}
    pruned = 0
    for p in glob.glob(os.path.join(PT_TXT, 'packet_*.txt')):
        if os.path.basename(p) not in keep:
            os.remove(p)
            pruned += 1
    if pruned:
        print(f"pruned {pruned} non-comment-bearing packet_true_txt sidecars "
              f"(kept {len(keep)} comment-bearing)")

    from collections import Counter
    print(f"\nMinutes-view: {len(minutes_rows)}  +  packet=true: {len(pkt_rows)}  "
          f"-  {dup} content-duplicate(s)  =  {len(merged)} canonical comments")
    print("by year:", dict(Counter((r['date_normalized'] or '?')[:4] for r in merged)))
    print("by channel flag:", dict(Counter(
        ('web_form' if 'web_form' in r['quality_flag'] else
         'letter_appendix' if 'letter_appendix' in r['quality_flag'] else
         'email_block' if 'email_block' in r['quality_flag'] else 'minutes_view')
        for r in merged)))


if __name__ == '__main__':
    main()
