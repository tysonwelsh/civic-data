#!/usr/bin/env python3
"""Summit County Council — extract minutes + motions/tally-votes from the Granicus
MinutesViewer HTML (view_id=1), the county's born-digital minutes source (2023-01 →
present). Reads the retained raw HTML in raw/granicus/<clip>.html and the meeting catalog
council_meetings.json (clip_id -> date/type, scraped from the Granicus ViewPublisher
archive). Writes:

  minutes/<year>/<date>_council_<clip>.md   one markdown file per meeting (provenance
                                            front-matter + full minutes text + motions)
  minutes_index.csv                         one row per minutes document (SCHEMA_SPEC §3)
  all_votes.csv                             the 13+1-col vote schema (SCHEMA_SPEC §2)
  ../db/staging/{meetings,motions,votes}.csv  prose staging for db/build_db.py

THE RECORDING CEILING (honest, final): Summit's minutes are TALLY-PRIMARY. Unanimous
motions print only a tally ("all voted in favor, (5-0)") — members are NOT named, so those
rows are tally-only (blank member/vote, names_recorded=0). Named member votes appear ONLY
when a division is called ("Roger Armstrong voted AYE ... Christopher Robinson voted NAY").
Summit has NO Legistar, so there is no API to recover named rolls — this ceiling cannot be
lifted. Mover/seconder ARE named on every motion. Never fabricated.

DERIVED + idempotent. Rerun after refreshing raw/granicus/. Never hand-edit the outputs.
"""
import csv, html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw", "granicus")
STG = os.path.join(HERE, "..", "db", "staging")
META = json.load(open(os.path.join(HERE, "council_meetings.json")))

VMAP = {'AYE': 'Aye', 'YES': 'Aye', 'NAY': 'Nay', 'NO': 'Nay', 'ABSTAIN': 'Abstain',
        'ABSTAINED': 'Abstain', 'RECUSE': 'Recuse', 'RECUSED': 'Recuse',
        'ABSENT': 'Absent', 'EXCUSED': 'Excused'}
MONTHS = 'January February March April May June July August September October November December'.split()

# Council roster (2023-2026), resolved by unique surname. Mover/seconder are attributed by
# surname because the born-digital minutes frequently run the motion action and the seconder
# clause together without a sentence period (e.g. "...Board of Equalization Malena Stevens
# seconded"), so a literal left-to-right parse of the seconder is unreliable. The token
# immediately before "seconded" is always the seconder's surname; we map it to the canonical
# full name. Verbatim prose is preserved in the motion text and the minutes markdown.
ROSTER = {'armstrong': 'Roger Armstrong', 'robinson': 'Christopher Robinson',
          'harte': 'Canice Harte', 'hanson': 'Tonja B Hanson', 'stevens': 'Malena Stevens',
          'mckenna': 'Megan McKenna', 'poll': 'Stephanie Poll'}


def resolve(name):
    """Canonicalize a mover/seconder name to the roster by surname (unifies Chris/Christopher
    Robinson, Tonja/Tonja B Hanson, and repairs run-on parse artifacts)."""
    if not name:
        return None
    last = re.sub(r"[^A-Za-z]", "", name.split()[-1]).lower()
    return ROSTER.get(last, name.strip())


def clean(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s).replace('\xa0', ' ')
    return re.sub(r'[ \t\n]+', ' ', s).strip()


def slugify(s):
    return re.sub(r'[^a-z0-9]+', '_', (s or '').lower()).strip('_')


def parse_motion(div_html):
    """div_html = inner HTML of one bold motion block. Returns a motion dict or None."""
    votes = []
    for sub in re.findall(r'<div>(.*?)</div>', div_html, re.S):
        txt = clean(sub)
        for name, val in re.findall(
                r"([A-Za-z][A-Za-z .'\-]+?)\s+voted\s+(AYE|NAY|ABSTAINED|ABSTAIN|RECUSED|RECUSE|ABSENT|EXCUSED)",
                txt, re.I):
            vv = VMAP.get(val.upper(), '')
            if vv:
                votes.append((name.strip(), vv))
    full = clean(div_html)
    sentence = re.split(
        r"[A-Za-z][A-Za-z .'\-]+?\s+voted\s+(?:AYE|NAY|ABSTAIN|RECUSE|ABSENT|EXCUSED)",
        full)[0].strip()
    if 'made a motion' not in sentence.lower() and 'moved' not in sentence.lower():
        return None
    mover = None
    m = re.match(r"(.+?)\s+made a motion", sentence)
    if m:
        mover = resolve(m.group(1).strip(' .'))
    lack = bool(re.search(r'lack(ed)? (of )?a second|no second|died for lack', sentence, re.I))
    sec = None
    ms = re.search(r"\bseconded\b", sentence)
    if ms and not lack:
        pre = sentence[:ms.start()].rstrip(' ,.')
        if pre.split():
            sec = resolve(pre.split()[-1])
            if sec and re.sub(r"[^A-Za-z]", "", sec.split()[-1]).lower() not in ROSTER:
                sec = None   # trailing token isn't a known member surname → don't guess
    if sec in ('0', '', None) or (sec and sec.lower() in ('and', 'the')):
        sec = None
    tally = re.findall(r'\((\d+)\s*-\s*(\d+)(?:\s*-\s*(\d+))?\)', sentence)
    aye = nay = None
    if tally:
        aye, nay = int(tally[-1][0]), int(tally[-1][1])
    result = ''
    mo = re.search(
        r'((?:and\s+)?(?:all voted in favor|the motion (?:carried|failed|passed|did not carry)'
        r'|passed unanimously|carried unanimously|motion carried|motion failed|failed for|died)[^.]*?)(?:\.|$)',
        sentence, re.I)
    if mo:
        result = re.sub(r'^and\s+', '', mo.group(1), flags=re.I).strip(' ,')
        if tally and not re.search(r'\(\s*\d+\s*-\s*\d+', result):
            result += f", ({aye}-{nay})"
    elif tally:
        result = f"({aye}-{nay})"
    elif lack:
        result = 'died for lack of a second'
    low = (result + ' ' + sentence).lower()
    if re.search(r'fail|did not carry|died|withdrawn', low) and 'carried' not in low and 'in favor' not in low:
        outcome = 'Fail'
    elif re.search(r'carried|in favor|passed|unanimous|adopted|approved', low):
        outcome = 'Pass'
    elif aye is not None:
        outcome = 'Pass' if aye > (nay or 0) else 'Fail'
    else:
        outcome = 'Unknown'
    return dict(mover=mover, seconder=sec, result=result, outcome=outcome,
                aye=aye, nay=nay, votes=votes, motion_text=sentence)


def motion_type(text):
    """City-native motion category from verbatim motion prose."""
    t = text.lower()
    if re.search(r'closed session|open session|recess|adjourn|convene as|dismiss as|reconvene', t):
        return 'Procedural/Administrative'
    if re.search(r'ordinance|rezone|zoning|general plan|development|plat|subdivision|conditional use|code amendment', t):
        return 'Land-Use/Zoning'
    if re.search(r'resolution', t):
        return 'Resolution'
    if re.search(r'contract|agreement|purchase|bid|award|budget|appropriat|grant|fund', t):
        return 'Financial/Contract'
    if re.search(r'appoint|reappoint', t):
        return 'Appointment'
    if re.search(r'board of equalization|appeal|stipulation|exemption', t):
        return 'Board of Equalization'
    return 'Other'


def full_text(h):
    """Readable minutes text (agenda + roll + motion prose) for the FTS corpus."""
    b = re.sub(r'<script.*?</script>', '', h, flags=re.S)
    b = re.sub(r'<style.*?</style>', '', b, flags=re.S)
    b = re.sub(r'<head.*?</head>', '', b, flags=re.S)
    b = re.sub(r'<!--.*?-->', '', b, flags=re.S)
    b = re.sub(r'<br\s*/?>', '\n', b)
    b = re.sub(r'</(div|p|tr|li|h[1-6]|blockquote|td)>', '\n', b)
    b = re.sub(r'<[^>]+>', ' ', b)
    b = html.unescape(b).replace('\xa0', ' ')
    lines = [re.sub(r'[ \t]+', ' ', l).strip() for l in b.split('\n')]
    out, prev = [], None
    for l in lines:
        if not l or l == prev:
            continue
        out.append(l)
        prev = l
    return '\n'.join(out)


def extract_motions(h):
    motions = []
    # 2026-07-25: Granicus also wraps a motion in a MediaPlayer deep-link —
    # `<div><a href=...MediaPlayer.php?...><strong>X made a motion to ...`
    # The old pattern required <strong> to follow <div> directly, so every linked motion was
    # invisible: 2026-06-03 published 10 tallies and yielded 2 motions, 2026-04-22 14 → 11.
    OPEN = r'(?:<div style="font-weight: bold;">|<div>\s*(?:<a [^>]*>\s*)?<strong>)'
    found = []                                   # (position, parsed motion)
    for m in re.finditer(
            OPEN + r'(.*?)'
            r'(?=</div>\s*<br>|' + OPEN + r'|<blockquote)',
            h, re.S):
        pm = parse_motion(m.group(1))
        if pm:
            found.append((m.start(), pm))
    # 2026-07-25 second pass: Granicus leaves some motions — notably the closed-session
    # ones opening a meeting — in a PLAIN <div> with no bold/strong at all
    # (2026-04-22 lost 3 that way). Loosening the markup match would sweep in every div,
    # so key on the motion GRAMMAR instead: a mover, the verb, and a printed tally.
    GRAMMAR = re.compile(r'made\s+a\s+motion\b.*?\(\s*\d+\s*[-–]\s*\d+\s*\)', re.S)
    seen = {re.sub(r'\W+', '', (pm.get('motion_text') or ''))[:80] for _p, pm in found}
    for m in re.finditer(r'<div>((?!<strong)(?:(?!</?div).)*?)</div>', h, re.S):
        seg = m.group(1)
        if not GRAMMAR.search(seg):
            continue
        pm = parse_motion(seg)
        if not pm:
            continue
        key = re.sub(r'\W+', '', (pm.get('motion_text') or ''))[:80]
        if key in seen:
            continue
        seen.add(key)
        found.append((m.start(), pm))
    found.sort(key=lambda x: x[0])               # keep document order
    motions = [pm for _p, pm in found]
    return motions


def main():
    os.makedirs(STG, exist_ok=True)
    idx_rows, vote_rows = [], []
    stg_meet, stg_motion, stg_vote = [], [], []
    clips = sorted(META, key=lambda c: (META[c]['date'] or '', int(c)))
    n_meet = n_motion = n_named = n_tallyonly = n_div = 0
    pdf_stub = []
    for cid in clips:
        info = META[cid]
        date = info['date']
        h = open(os.path.join(RAW, cid + '.html'), encoding='utf-8', errors='replace').read()
        if 'Redirecting' in h or len(h) < 2000:
            pdf_stub.append(cid)          # uploaded-PDF minutes (7 Jan–Feb 2023 special sessions)
            continue
        draft = 'draft' in info['title'].lower()
        year = date[:4]
        slug = f"{date}_council_{cid}"
        rel = f"minutes/{year}/{slug}.md"
        outp = os.path.join(HERE, "minutes", year, slug + ".md")
        os.makedirs(os.path.dirname(outp), exist_ok=True)
        motions = extract_motions(h)
        body_text = full_text(h)
        title = f"Summit County Council — {info['type']}"
        # markdown with provenance front-matter
        fm = [
            "---",
            f"body: County Council",
            f"date: {date}",
            f"title: {title}",
            f"meeting_type: {info['type']}",
            f"source: granicus",
            f"source_url: https://summitcounty.granicus.com/MinutesViewer.php?view_id=1&clip_id={cid}",
            f"clip_id: {cid}",
            f"minutes_status: {'draft' if draft else 'final'}",
            f"format: text",
            f"provenance: minutes",
            f"n_motions: {len(motions)}",
            "---",
            "",
            f"# {title}",
            f"**{date}**  ·  clip {cid}  ·  source: Granicus MinutesViewer",
            "",
        ]
        md = "\n".join(fm) + body_text + "\n"
        if motions:
            md += "\n\n## Motions (extracted)\n\n"
            for i, mo in enumerate(motions, 1):
                tally = f"{mo['aye']}-{mo['nay']}" if mo['aye'] is not None else "tally-only/none"
                md += (f"{i}. **{mo['outcome']}** — {mo['motion_text']}\n"
                       f"   - mover: {mo['mover'] or ''}; seconder: {mo['seconder'] or ''}; "
                       f"result: {mo['result'] or ''} ({tally})\n")
                if mo['votes']:
                    md += "   - named: " + "; ".join(f"{n} {v}" for n, v in mo['votes']) + "\n"
        open(outp, "w").write(md)
        n_meet += 1
        idx_rows.append([date, year, title, slug, rel, "granicus",
                         f"https://summitcounty.granicus.com/MinutesViewer.php?view_id=1&clip_id={cid}",
                         "text"])
        stg_meet.append([cid, date, "County Council", info['type'], rel,
                         'draft' if draft else 'final'])
        for mno, mo in enumerate(motions, 1):
            n_motion += 1
            names_recorded = 1 if mo['votes'] else 0
            if names_recorded:
                n_named += 1
            else:
                n_tallyonly += 1
            if mo['votes']:
                n_div += 1
            mtype = motion_type(mo['motion_text'])
            stg_motion.append([cid, date, "County Council", mno, mo['motion_text'], mtype,
                               mo['result'], mo['outcome'], mo['mover'] or '', mo['seconder'] or '',
                               mo['aye'] if mo['aye'] is not None else '',
                               mo['nay'] if mo['nay'] is not None else '', names_recorded, rel])
            if mo['votes']:
                for name, val in mo['votes']:
                    stg_vote.append([cid, mno, name, val])
                    vote_rows.append([date, year, title, "Council", mno, mo['motion_text'],
                                      mtype, mo['result'], mo['mover'] or '', mo['seconder'] or '',
                                      name, val, rel, "minutes"])
            else:
                # tally-only placeholder row (blank member/vote) — the recording ceiling
                vote_rows.append([date, year, title, "Council", mno, mo['motion_text'],
                                  mtype, mo['result'], mo['mover'] or '', mo['seconder'] or '',
                                  "", "", rel, "minutes"])

    # write minutes_index.csv
    with open(os.path.join(HERE, "minutes_index.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "year", "title", "slug", "path", "source", "source_url", "format"])
        w.writerows(sorted(idx_rows))
    # write all_votes.csv (13 std cols + trailing provenance)
    with open(os.path.join(HERE, "all_votes.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "year", "title", "body", "motion_no", "motion", "motion_type",
                    "result", "mover", "seconder", "member", "vote", "source", "provenance"])
        w.writerows(vote_rows)
    # write db staging
    with open(os.path.join(STG, "meetings.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["clip_id", "date", "body", "meeting_type", "source_file", "minutes_status"])
        w.writerows(stg_meet)
    with open(os.path.join(STG, "motions.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["clip_id", "date", "body", "motion_no", "motion_text", "motion_type",
                    "result_raw", "outcome", "mover", "seconder", "aye", "nay",
                    "names_recorded", "source_file"])
        w.writerows(stg_motion)
    with open(os.path.join(STG, "votes.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["clip_id", "motion_no", "member", "vote_value"])
        w.writerows(stg_vote)

    print(f"meetings written: {n_meet} (+{len(pdf_stub)} uploaded-PDF special sessions logged as unrecovered)")
    print(f"motions: {n_motion}  |  divided/named motions: {n_div}  |  tally-only: {n_tallyonly}")
    print(f"named vote rows: {len(stg_vote)}")
    print(f"pdf-stub clips (Granicus DocumentViewer, text pending): {pdf_stub}")


if __name__ == "__main__":
    main()
