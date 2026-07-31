#!/usr/bin/env python3
"""Dump every minutes-labeled attachment from a cumulative notices-list HTML:
notice_id, notice_event_date, file_id, ext, filename, label.
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kearns_pmn_parse import parse_notices

rows = parse_notices(sys.argv[1])
for r in rows:
    for a in r["attachments"]:
        lab = a["label"].lower(); fn = a["filename"].lower()
        if "minute" in (lab + " " + fn) and "agenda" not in fn:
            fid = a["file"].rsplit(".", 1)[0]
            ev = r["event_date"].split()[0] if r["event_date"] else ""
            print(f"{ev}\t{r['notice_id']}\t{fid}\t{a['filename']}\t[{a['label']}]")
