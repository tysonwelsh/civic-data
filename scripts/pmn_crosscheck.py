#!/usr/bin/env python3
"""pmn_crosscheck.py — mandatory-refresh PMN cross-check engine (TODO plan, owner-
approved 2026-07-13; built 2026-07-17).

City-agnostic, READ-ONLY vs the repo's datasets, REPORT-ONLY output (constraint (a):
flag-and-review, NEVER auto-ingest — PMN carries drafts, mislabeled attachments,
wrong event dates, body misfilings). One-directional diff (constraint (d)): PMN-has /
repo-lacks only — PMN purges history (kearns/magna/copperton 2017-18), so PMN absence
means nothing.

Per-city config (seeded from each pmn_backfill/CLAUDE.md):
  pmn_backfill/pmn_bodies.csv
      entity_id,body_id,body_name,crawl,repo_datasets,repo_body,date_mode,floor,notes
      - floor: ISO date; PMN dates BEFORE it are out of scope (PMN history reaches
        2008 for some bodies — far below the repo's deliberate data floors; herriman
        pattern). Counted as pre_floor in the report, never flagged.
      - crawl: yes|no (no = inventoried-only body, still watched by the body-list diff)
      - repo_datasets: ';'-joined dataset dirs whose minutes_index.csv dates count as
        "repo has it" (e.g. "meeting_minutes" or "meeting_minutes;planning_commission"
        for cross-filing cities like herriman — a match in ANY listed dataset clears
        the flag; the verifying agent determines the true body)
      - repo_body: optional body-column filter within those datasets ('' = all rows)
      - date_mode: exact | pm4  (constraint (e): exact where the city's PMN event
        dates are reliable, +/-4 days elsewhere)
  pmn_backfill/pmn_exceptions.csv   (constraint (b): the per-city exception ledger)
      date,body_id,kind,reason,verified_date
      kind: mislabel|duplicate|draft|wrong_date|not_minutes|other — a flag whose
      (date,body_id) matches a ledger row is SUPPRESSED (reported in the suppressed
      tally, never re-surfaced).

Output (into <city>_city_council/pmn_backfill/):
  crosscheck_flags.csv         current run's flags (machine-readable)
  crosscheck_report.md         human summary for the review gate
  _crosscheck/history/<date>_flags.csv    dated archive (constraint/step 6: successive
                               files measure each city's real PMN attachment lag)
  _crosscheck/cache/           the fetched HTML (evidence for the verifying agent)

Flag classes:
  missing_minutes    PMN holds a minutes attachment for a date the repo has no
                     minutes doc for (known_unrecovered=yes when the date is already
                     in minutes_unrecovered.csv -> a live recovery lead)
  count_mismatch     PMN carries MORE minutes files on a matched date than the repo
                     has docs (multi-doc days; catches split/second bodies)
  agenda_only_gap    a non-cancelled PMN meeting date the repo has NO record of at
                     all (no minutes, no unrecovered row) - lower confidence; the
                     draper-TnT-specials pattern
  new_body           the live publicBodies list has an id absent from pmn_bodies.csv
                     (constraint (c): bodies re-register - draper 379->5555 - and new
                     bodies appear; a frozen map silently goes blind)
  renamed_body       a configured id whose live name no longer matches

Trailing exclusion window (constraint (f)): flags within --window days of today
(default 60) are counted as pending-adoption noise, not emitted (minutes attach to
PMN only after adoption, ~2-6 wks).

Usage:
  python3 scripts/pmn_crosscheck.py bluffdale            # one city
  python3 scripts/pmn_crosscheck.py --all                # every city with a config
  python3 scripts/pmn_crosscheck.py murray --window 90 --cached
      --cached reuses _crosscheck/cache/ instead of refetching (dev/verification)

Polite: single utah.gov host, >=1.0 s between GETs, browser-ish UA, GET-only.
stdlib-only.
"""
import argparse
import csv
import datetime as dt
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from entities import ENTITIES  # registry-driven entity list

BASE = "https://www.utah.gov"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 civic-data-archive/1.0 "
      "(+public records research)")
DELAY = 1.0
_last_fetch = [0.0]

RE_ROW = re.compile(
    r'<tr class="(?:on|off)">\s*<td>\s*'
    r'<a href="/pmn/sitemap/notice/(\d+)\.html">(.*?)</a>\s*</td>\s*'
    r'<td>(\d{4}/\d{2}/\d{2})[^<]*</td>\s*<td>(.*?)</td>\s*</tr>', re.S)
RE_ATT = re.compile(
    r'<a href="(/pmn/files/[^"]+)"[^>]*>([^<]+)</a>\s*(?:&nbsp;)?\(([^)]+)\)', re.S)
RE_BODY_ROW = re.compile(
    r'<a href="/pmn/list/notices\.html\?id=(\d+)[^"]*">([^<]+)</a>')
# 'reschedul' added Q3-2026: the "Meeting Rescheduled" notice family (st_george ×5)
# is a non-meeting the same way a cancellation is
RE_CANCEL = re.compile(r'cancel|postpone|reschedul', re.I)
RE_MINUTES_LABEL = re.compile(r'meeting minutes', re.I)
# word-boundary required — bare r'minut' matched "Minuteman Project" (H-C3, draper)
RE_MINUTES_FNAME = re.compile(r'minutes?\b', re.I)
# minutes attachments must be documents — an .mp3 under a "(Meeting Minutes)" label
# is audio, not a text record (taylorsville 2023-04-25)
RE_DOC_EXT = re.compile(r'\.(pdf|docx?|rtf|txt)(\W|$)', re.I)
# agenda_only_gap fires only for MEETING-shaped notices (hardening #1, bluffdale
# pilot 2026-07-17: bodies carry bid requests / quorum notices / proclamations /
# annual schedules — none are meetings the repo could hold minutes for)
RE_MEETINGISH = re.compile(r'meeting|agenda|work session|special session|hearing', re.I)
RE_NOT_MEETING = re.compile(
    r'request for bids?|invitation to bid|\brfp\b|notice of (?:potential )?quorum|'
    r'proclamation|meetings?\s+schedule|meetings\s*-\s*\d{4}|schedule of .{0,30}meetings|'
    r'annual (?:notice|meeting notice)|\d{4}\s+regular\s+meetings|surplus|'
    r'determination of risk|meeting rescheduled|oath of office ceremony|'
    r'anchor location renewal|budget notice|disposition of real property', re.I)
# title-date rescue (hardening #2, same pilot: PMN event dates can be WRONG —
# "Special Meeting Agenda - May 29, 2020" filed under event date 2020-04-29; if a
# date printed in the TITLE matches the repo, the flag is noise)
RE_TITLE_DATES = re.compile(
    r'(January|February|March|April|May|June|July|August|September|October|'
    r'November|December)\s+(\d{1,2}),?\s+(\d{4})|(\d{1,2})[-/](\d{1,2})[-/](\d{4})')
_MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"])}


def title_dates(title):
    out = []
    for m in RE_TITLE_DATES.finditer(title):
        try:
            if m.group(1):
                out.append(dt.date(int(m.group(3)), _MONTHS[m.group(1)],
                                   int(m.group(2))).isoformat())
            else:
                out.append(dt.date(int(m.group(6)), int(m.group(4)),
                                   int(m.group(5))).isoformat())
        except ValueError:
            continue
    return out


# filename-date rescue (hardening 2026-07-17, 17 instances across 7 cities): a
# minutes attachment whose FILENAME encodes a date is usually a PRIOR meeting's
# minutes riding a later approval notice. Forms: M-D-YYYY, M.D.YYYY, M_D_YYYY,
# YYYY-MM-DD, MMDDYY(YY) runs. Month-name-only filenames ("July minutes.pdf")
# are NOT extractable — those stay review-gate material by design.
RE_FNAME_DATES = re.compile(
    r'(\d{4})[-._](\d{1,2})[-._](\d{1,2})|'          # YYYY-M-D
    r'(\d{1,2})[-._](\d{1,2})[-._](\d{4}|\d{2})|'    # M-D-YYYY / M-D-YY
    r'(?<!\d)(\d{2})(\d{2})(\d{2})(?!\d)')           # MMDDYY run


def fname_dates(fnames):
    out = []
    for fn in fnames:
        for m in RE_FNAME_DATES.finditer(fn):
            try:
                if m.group(1):
                    out.append(dt.date(int(m.group(1)), int(m.group(2)),
                                       int(m.group(3))).isoformat())
                elif m.group(4):
                    y = int(m.group(6))
                    y += 2000 if y < 100 else 0
                    out.append(dt.date(y, int(m.group(4)),
                                       int(m.group(5))).isoformat())
                else:
                    mm, dd, yy = int(m.group(7)), int(m.group(8)), int(m.group(9))
                    if 1 <= mm <= 12 and 1 <= dd <= 31:
                        out.append(dt.date(2000 + yy, mm, dd).isoformat())
            except ValueError:
                continue
    return out


def fetch(url, cache_path, cached):
    if cached and os.path.exists(cache_path):
        return open(cache_path, encoding="utf-8", errors="replace").read()
    wait = DELAY - (time.time() - _last_fetch[0])
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        html = r.read().decode("utf-8", "replace")
    _last_fetch[0] = time.time()
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def repo_dates(city_dir, datasets, repo_body):
    """(dates_with_docs, per-date doc counts, unrecovered dates) across the
    configured datasets. pmn_backfill's own recovered index counts as repo-has."""
    have, counts, unrec = set(), {}, set()
    for ds in datasets:
        for r in read_csv(os.path.join(city_dir, ds, "minutes_index.csv")):
            if repo_body and (r.get("body") or "") != repo_body:
                continue
            d = (r.get("date") or "")[:10]
            if d:
                have.add(d)
                counts[d] = counts.get(d, 0) + 1
        for r in read_csv(os.path.join(city_dir, ds, "minutes_unrecovered.csv")):
            d = (r.get("date") or "")[:10]
            if d:
                unrec.add(d)
    for r in read_csv(os.path.join(city_dir, "pmn_backfill", "index.csv")):
        d = (r.get("date") or "")[:10]
        if d:
            have.add(d)
            counts[d] = counts.get(d, 0) + 1
    return have, counts, unrec


def near(date, dates, tol):
    """date (ISO) matches any of dates within +/-tol days."""
    if tol == 0:
        return date in dates
    d0 = dt.date.fromisoformat(date)
    for d in dates:
        try:
            if abs((dt.date.fromisoformat(d) - d0).days) <= tol:
                return True
        except ValueError:
            continue
    return False


def crosscheck_city(slug, window, page, cached):
    ent = {e.slug: e for e in ENTITIES}.get(slug)
    if not ent:
        print(f"{slug}: not in registry — skipped")
        return None
    city_dir = os.path.join(ROOT, ent.dir)
    pb = os.path.join(city_dir, "pmn_backfill")
    bodies = read_csv(os.path.join(pb, "pmn_bodies.csv"))
    if not bodies:
        print(f"{slug}: no pmn_bodies.csv — seed it first (rollout step 3)")
        return None
    exceptions = {((r.get("date") or "")[:10], r.get("body_id") or ""): r
                  for r in read_csv(os.path.join(pb, "pmn_exceptions.csv"))}
    cache_dir = os.path.join(pb, "_crosscheck", "cache")
    today = dt.date.today()
    cutoff = (today - dt.timedelta(days=window)).isoformat()
    flags, suppressed, pending = [], 0, 0

    # --- constraint (c): live body-list diff -------------------------------
    entity_ids = sorted({r["entity_id"] for r in bodies if r.get("entity_id")})
    known_ids = {r["body_id"]: r for r in bodies}
    for eid in entity_ids:
        html = fetch(f"{BASE}/pmn/list/publicBodies.html?id={eid}",
                     os.path.join(cache_dir, f"publicBodies_{eid}.html"), cached)
        for bid, bname in RE_BODY_ROW.findall(html):
            bname = bname.strip()
            if bid not in known_ids:
                flags.append(dict(body_id=bid, body_name=bname, date="",
                                  flag_class="new_body",
                                  evidence_url=f"{BASE}/pmn/list/notices.html?id={bid}",
                                  pmn_title="", pmn_files="", known_unrecovered="",
                                  note="unconfigured live body — inventory it"))
            elif known_ids[bid].get("body_name") and \
                    known_ids[bid]["body_name"].strip().lower() != bname.lower():
                flags.append(dict(body_id=bid, body_name=bname, date="",
                                  flag_class="renamed_body",
                                  evidence_url=f"{BASE}/pmn/list/notices.html?id={bid}",
                                  pmn_title="", pmn_files="", known_unrecovered="",
                                  note=f"config name: {known_ids[bid]['body_name']}"))

    # --- per-body notice crawl + one-directional diff ----------------------
    per_body_stats = []
    # Q3-2026 hardening: dedup date-bearing flags across bodies that map to the
    # SAME repo datasets (logan's RDA body re-flagged every council-body date —
    # the RDA rides the same combined doc). Key = (date, class, dataset-set).
    seen_flag_keys = set()
    n_body_cancelled = 0
    for b in bodies:
        if (b.get("crawl") or "yes").lower() != "yes":
            continue
        bid = b["body_id"]
        datasets = [d for d in (b.get("repo_datasets") or "").split(";") if d]
        tol = 4 if (b.get("date_mode") or "pm4") == "pm4" else 0
        floor = (b.get("floor") or "").strip()
        have, counts, unrec = repo_dates(city_dir, datasets, b.get("repo_body") or "")
        html = fetch(f"{BASE}/pmn/list/notices.html?id={bid}&page={page}",
                     os.path.join(cache_dir, f"notices_{bid}.html"), cached)
        # per-date aggregation across this body's notices
        dates = {}  # date -> dict(minutes_files=[], titles=[], cancelled, notice_ids)
        for nid, title, d, att_html in RE_ROW.findall(html):
            d = d.replace("/", "-")
            rec = dates.setdefault(d, dict(minutes=[], titles=[], notice_ids=[],
                                           cancelled=False))
            rec["titles"].append(re.sub(r"\s+", " ", title).strip())
            rec["notice_ids"].append(nid)
            if RE_CANCEL.search(title):
                rec["cancelled"] = True
            for href, fname, label in RE_ATT.findall(att_html):
                # cancellation notices sometimes live only in the ATTACHMENT
                # filename (magna CRA 2026-02-10; copperton 2022-01-11)
                if RE_CANCEL.search(fname):
                    rec["cancelled"] = True
                    continue
                if not (RE_DOC_EXT.search(fname) or RE_DOC_EXT.search(href)):
                    continue  # audio/video under a minutes label is not a record
                if RE_MINUTES_LABEL.search(label) or RE_MINUTES_FNAME.search(fname):
                    rec["minutes"].append(fname.strip())
        n_min_dates = 0
        pre_floor = sum(1 for d in dates if floor and d < floor)
        for d, rec in sorted(dates.items()):
            if floor and d < floor:
                continue
            ev = f"{BASE}/pmn/sitemap/notice/{rec['notice_ids'][0]}.html"
            common = dict(body_id=bid, body_name=b.get("body_name", ""),
                          date=d, evidence_url=ev,
                          pmn_title=rec["titles"][0][:120],
                          pmn_files="; ".join(rec["minutes"])[:200])
            if rec["minutes"]:
                n_min_dates += 1
                if d >= cutoff:
                    pending += 1
                    continue
                if not near(d, have, tol):
                    # filename-date rescue: if every extractable date in the
                    # minutes filenames is already repo-held (or pre-floor),
                    # this is a prior meeting's minutes on a later notice
                    fdates = fname_dates(rec["minutes"])
                    if fdates and all(
                            near(fd, have, tol) or (floor and fd < floor)
                            for fd in fdates):
                        suppressed += 1
                        continue
                    ku = "yes" if near(d, unrec, max(tol, 4)) else ""
                    f = dict(common, flag_class="missing_minutes",
                             known_unrecovered=ku,
                             note="recovery lead (date already logged unrecovered)"
                                  if ku else "")
                    if (d, bid) in exceptions:
                        suppressed += 1
                    else:
                        flags.append(f)
                elif tol == 0 and len(rec["minutes"]) > counts.get(d, 0):
                    f = dict(common, flag_class="count_mismatch",
                             known_unrecovered="",
                             note=f"PMN {len(rec['minutes'])} minutes files vs "
                                  f"repo {counts.get(d, 0)} docs")
                    if (d, bid) in exceptions:
                        suppressed += 1
                    else:
                        flags.append(f)
            else:
                if d >= cutoff or rec["cancelled"]:
                    continue
                # meeting-shaped notices only (hardening #1)
                joined = " | ".join(rec["titles"])
                if not RE_MEETINGISH.search(joined) or RE_NOT_MEETING.search(joined):
                    continue
                if not near(d, have, max(tol, 4)) and not near(d, unrec, max(tol, 4)):
                    # title-date rescue (hardening #2): a date printed in the title
                    # that the repo DOES hold means the PMN event date is wrong
                    if any(near(td, have, tol) for td in title_dates(joined)):
                        continue
                    if (d, bid) in exceptions:
                        suppressed += 1
                        continue
                    # cross-body dedup (Q3-2026): same date + same dataset mapping
                    # already flagged by a sibling body → one flag is enough
                    fkey = (d, "agenda_only_gap", tuple(sorted(datasets)))
                    if fkey in seen_flag_keys:
                        suppressed += 1
                        continue
                    # notice-body cancellation check (Q3-2026, 6 confirmations:
                    # taylorsville/logan/midvale/WJ/riverton title-less + nephi's
                    # DESCRIPTION-field cancellations): before emitting, fetch the
                    # notice DETAIL page(s) — only for would-be flags, so the cost
                    # is a handful of polite requests per city — and scan the full
                    # page text (description + body prose) for cancel language.
                    body_cancelled = False
                    for nid in rec["notice_ids"][:3]:
                        detail = fetch(
                            f"{BASE}/pmn/sitemap/notice/{nid}.html",
                            os.path.join(cache_dir, f"notice_{nid}.html"), cached)
                        if RE_CANCEL.search(re.sub(r"<[^>]+>", " ", detail)):
                            body_cancelled = True
                            break
                    if body_cancelled:
                        n_body_cancelled += 1
                        continue
                    seen_flag_keys.add(fkey)
                    flags.append(dict(common, flag_class="agenda_only_gap",
                                      known_unrecovered="",
                                      note="no repo record of this meeting date "
                                           "at all (lower confidence)"))
        per_body_stats.append((bid, b.get("body_name", ""), len(dates), n_min_dates,
                               pre_floor))

    # --- outputs (report-only; never touches datasets) ---------------------
    os.makedirs(os.path.join(pb, "_crosscheck", "history"), exist_ok=True)
    cols = ["body_id", "body_name", "date", "flag_class", "evidence_url",
            "pmn_title", "pmn_files", "known_unrecovered", "note"]
    flags.sort(key=lambda f: (f["flag_class"], f["date"]))
    for path in (os.path.join(pb, "crosscheck_flags.csv"),
                 os.path.join(pb, "_crosscheck", "history",
                              f"{today.isoformat()}_flags.csv")):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(flags)
    by_class = {}
    for f in flags:
        by_class[f["flag_class"]] = by_class.get(f["flag_class"], 0) + 1
    with open(os.path.join(pb, "crosscheck_report.md"), "w", encoding="utf-8") as f:
        f.write(f"# PMN cross-check — {slug} — {today.isoformat()}\n\n")
        f.write("Flag-and-review output only (NEVER auto-ingest — verify every flag "
                "at source; verified false positives go to pmn_exceptions.csv).\n\n")
        f.write(f"- flags: **{len(flags)}** ({', '.join(f'{k} {v}' for k, v in sorted(by_class.items())) or 'none'})\n")
        f.write(f"- suppressed by exception ledger / cross-body dedup: {suppressed}\n")
        if n_body_cancelled:
            f.write(f"- auto-suppressed as cancelled (notice-body/description text): "
                    f"{n_body_cancelled}\n")
        f.write(f"- pending-adoption (inside {window}-day window, not flagged): {pending}\n\n")
        f.write("| body | name | PMN dates | minutes dates | pre-floor (skipped) |\n"
                "|---|---|---|---|---|\n")
        for bid, name, nd, nm, pf in per_body_stats:
            f.write(f"| {bid} | {name} | {nd} | {nm} | {pf} |\n")
        if flags:
            f.write("\n| class | body | date | note | evidence |\n|---|---|---|---|---|\n")
            for fl in flags:
                f.write(f"| {fl['flag_class']} | {fl['body_id']} | {fl['date']} | "
                        f"{(fl['note'] or fl['pmn_title'])[:80]} | {fl['evidence_url']} |\n")
    print(f"{slug}: {len(flags)} flags "
          f"({', '.join(f'{k} {v}' for k, v in sorted(by_class.items())) or 'clean'}); "
          f"{suppressed} suppressed; {pending} pending-adoption")
    return flags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cities", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--window", type=int, default=60)
    ap.add_argument("--page", type=int, default=300)
    ap.add_argument("--cached", action="store_true",
                    help="reuse _crosscheck/cache/ HTML instead of refetching")
    a = ap.parse_args()
    slugs = a.cities
    if a.all:
        slugs = [e.slug for e in ENTITIES if e.level == "city" and os.path.exists(
            os.path.join(ROOT, e.dir, "pmn_backfill", "pmn_bodies.csv"))]
    if not slugs:
        ap.error("name cities or use --all")
    for s in slugs:
        crosscheck_city(s, a.window, a.page, a.cached)


if __name__ == "__main__":
    main()
