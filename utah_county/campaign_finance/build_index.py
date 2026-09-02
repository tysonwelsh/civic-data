#!/usr/bin/env python3
"""build_index.py — regenerate index.csv for utah_county/campaign_finance/.

Reads `batch/manifest.json` (the acquisition manifest: one entry per retained filing, with its
channel provenance and its office evidence) plus the files actually present in `raw/` and
`text/`, applies the curated `office_overrides.csv`, and rewrites `index.csv`.

`office_overrides.csv` has TWO row kinds, distinguished by whether the `path` column is filled:

  * **documentation-only** (blank `path`, keyed on the acquisition `staging_file`) — the
    original 7 rows. They were folded into `batch/manifest.json` at acquisition time and are
    kept here as the audit trail; this script does not re-apply them.
  * **APPLIED** (`path` = the dataset-relative raw path) — added by the 2026-08-01 vision
    tranche. A row with a NON-EMPTY `office` rewrites that filing's `office` (+ `office_source` /
    `office_confidence` / `office_note`) at build time, with per-row logging. Since 2026-08-02
    an APPLIED row may also carry a trailing `candidate` — the name printed on the FILING'S OWN
    FACE, written ONLY into an empty `candidate` cell (the acquisition channel named no filer);
    a non-empty channel label is never overwritten, so a channel/face disagreement stays
    visible. The sentinel
    office `__school__` marks a filing the vision read proved is a LOCAL SCHOOL BOARD filer:
    it is DROPPED from index.csv (out of Package-B scope) and reported, never silently kept.
    A row whose `path` matches no manifest filing is STALE and FAILS the build — the
    vote_overrides discipline (GOTCHAS.md).

Idempotent and NON-DESTRUCTIVE: it never fetches, never edits a raw file, and never invents a
value. A filing whose raw file is missing on disk is DROPPED from index.csv and reported, so the
index can never claim a document the repository does not hold; a sha256 that no longer matches
is reported as a FAIL (the raw layer is verbatim and must not drift).

    python3 utah_county/campaign_finance/build_index.py [--check]

`--check` verifies only (no write) and exits non-zero on any FAIL.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, 'batch', 'manifest.json')
OVERRIDES = os.path.join(HERE, 'office_overrides.csv')
INDEX = os.path.join(HERE, 'index.csv')


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main(argv):
    check_only = '--check' in argv
    man = json.load(open(MANIFEST))
    rows = man['filings']

    ovr_rows = list(csv.DictReader(open(OVERRIDES))) if os.path.exists(OVERRIDES) else []
    applied = {o['path']: o for o in ovr_rows if (o.get('path') or '').strip()}
    n_doc_only = len(ovr_rows) - len(applied)

    kept, missing, mismatched = [], [], []
    for r in rows:
        raw = os.path.join(HERE, r['path'])
        if not os.path.exists(raw):
            missing.append(r['path'])
            continue
        if sha256(raw) != r['sha256']:
            mismatched.append(r['path'])
            continue
        tp = r.get('text_path') or ''
        if tp and not os.path.exists(os.path.join(HERE, tp)):
            r = dict(r, text_path='', extraction_method='none (text sidecar missing)')
        kept.append(r)

    # ---- apply the path-keyed curated office overrides
    manifest_paths = {r['path'] for r in rows}
    stale = sorted(p for p in applied if p not in manifest_paths)
    excluded, changed, noop, promoted = [], [], [], []
    out = []
    for r in kept:
        o = applied.get(r['path'])
        if not o:
            out.append(r)
            continue
        office = (o.get('office') or '').strip()
        if office == '__school__':
            excluded.append((r['path'], o.get('evidence', '')))
            continue
        if not office:
            # CANDIDATE-ONLY override row (2026-08-02): a blank `office` means this row makes no
            # office claim, so the manifest's office/office_source/office_note are left exactly
            # as they are. Only the trailing `candidate` promotion below applies.
            noop.append(r['path'] + ' (candidate-only row; office untouched)')
        else:
            if r.get('office', '') == office:
                noop.append(r['path'])
            else:
                changed.append((r['path'], r.get('office', ''), office))
            r = dict(r, office=office,
                     office_source='filing text (curated override)',
                     office_confidence=(o.get('confidence') or '').strip(),
                     office_note=(o.get('evidence') or '').strip(),
                     needs_review='0' if office else '1')
        # TRAILING OPTIONAL `candidate` column (2026-08-02). index.csv's `candidate` is the
        # ACQUISITION CHANNEL's label, and for a handful of documents the channel named no
        # filer at all (title: 'filer not named by the channel'). Where a curated override row
        # carries a `candidate`, it is the name printed ON THE FILING'S OWN FACE (cited in
        # `evidence`) and it is written into an EMPTY cell only — a non-empty channel label is
        # NEVER overwritten here, because a channel/face disagreement must stay visible.
        # REATTRIBUTION (2026-08-19, Phase B wave). The rule above is right for a mere
        # name-form difference, but this module's own do-nots record that the acquisition
        # channel is SOMETIMES SIMPLY WRONG ABOUT WHO FILED — the county's Strapi record files
        # Paul V. Child's 2020 Recorder filing under Taylor Dayton. Keeping a known-wrong filer
        # in index.csv does not preserve a useful disagreement, it preserves an ERROR, and it
        # blocks that filing's itemized rows (the shared validator requires a contributions
        # row's (candidate, election_year) to exist here).
        #
        # So an override row whose `evidence` begins with the literal token `REATTRIBUTION:`
        # MAY overwrite a non-empty channel label. It is deliberately explicit — the token has
        # to be typed into the curated file — it is logged loudly on every build, and the
        # channel's original label is quoted verbatim in that same `evidence` cell, so the
        # disagreement stays visible where corrections are supposed to live. Anything WITHOUT
        # the token still refuses to overwrite, exactly as before.
        cand = (o.get('candidate') or '').strip()
        chan = (r.get('candidate') or '').strip()
        reattr = (o.get('evidence') or '').lstrip().startswith('REATTRIBUTION:')
        if cand and not chan:
            promoted.append((r['path'], cand))
            r = dict(r, candidate=cand)
        elif cand and reattr and cand != chan:
            print(f'  candidate REATTRIBUTED for {r["path"]}: channel {chan!r} -> page face '
                  f'{cand!r} (explicit REATTRIBUTION: row; channel label retained in evidence)')
            promoted.append((r['path'], cand))
            r = dict(r, candidate=cand)
        elif cand and cand != chan:
            print(f'  candidate override IGNORED for {r["path"]}: the channel already labels '
                  f'this filing {chan!r} (a disagreement must stay visible; an explicit '
                  f'`REATTRIBUTION:` evidence prefix is required to overwrite)')
        out.append(r)
    kept = out

    print(f'manifest filings: {len(rows)} · on disk + sha OK: {len(kept) + len(excluded)} · '
          f'missing: {len(missing)} · sha MISMATCH: {len(mismatched)}')
    print(f'office_overrides.csv: {len(applied)} APPLIED (path-keyed) · '
          f'{n_doc_only} documentation-only (staging_file-keyed, folded in at acquisition) · '
          f'{len(changed)} changed · {len(noop)} no-op · {len(excluded)} excluded as school board')
    for p, old, new in changed:
        print(f'  OVERRIDE  {p}: office {old!r} -> {new!r}')
    for p in noop:
        print(f'  no-op     {p} (already correct in the manifest)')
    for p, cand in promoted:
        print(f'  CANDIDATE {p}: channel named no filer -> {cand!r} (from the page face)')
    for p, ev in excluded:
        print(f'  EXCLUDED  {p} — school-board filer, dropped from index.csv ({ev[:70]})')
    for p in stale:
        print('  FAIL STALE override path (no manifest filing):', p)
    for p in missing:
        print('  MISSING  ', p)
    for p in mismatched:
        print('  FAIL sha ', p)

    if not check_only:
        cols = list(rows[0].keys())
        with open(INDEX, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in sorted(kept, key=lambda x: (int(x['election_year']), x['office'],
                                                 x['candidate'], x['path'])):
                w.writerow({c: r.get(c, '') for c in cols})
        print(f'wrote {INDEX} ({len(kept)} rows)')

    return 1 if (mismatched or stale) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
