#!/usr/bin/env python3
"""Cache County campaign finance — module-local STATED-TOTALS builder.

DERIVED layer. Regenerate with:
    python3 cache_county/campaign_finance/build_finance.py

Reads two curated inputs and one derived one:
  index.csv                      the filing ledger (itself DERIVED — run build_index.py first)
  vision/<key>.json              CURATED vision transcriptions of the cover page + the
                                 filing's own printed STATED TOTALS (schema cache_cf_totals_v1;
                                 see CLAUDE.md "The vision transcription layer")
  text/<file>.txt                the pdftotext sidecars — the 2025/2026 DocuSign-generated
                                 filings carry a real text layer whose Summary page parses
                                 exactly, so those are read from TEXT, not from an image

Emits:
  filing_totals.csv          one row per index.csv filing — SCHEMA.md §4 column contract EXACTLY
  contributions.csv          §2 — the BORN-DIGITAL itemized layer (TRANCHE 3 Phase A, below)
  expenditures.csv           §3 — ditto
  filing_stated_detail.csv   MODULE-LOCAL companion: every stated figure VERBATIM as printed,
                             both the This-Period and the Year-to-Date column, plus the cover
                             fields and the per-filing incremental/cumulative determination.
                             (filing_totals.csv's column list is fixed by the shared contract,
                             so the verbatim + two-column detail cannot live there.)

Why a module-local builder and not the shared engine's `driver.run()`: 201 of 239 filings
are the handwritten **Carr Printing 5-5-PG county form** whose figures exist ONLY as vision
transcriptions, and `driver.run()` would rewrite all three CSVs from one parse pass. The
module therefore keeps its own totals builder and calls the REGISTERED `cache_cfd` family for
the born-digital subset, through the same shared normalization + reconciliation primitives the
driver uses. The COLUMN CONTRACT of SCHEMA.md is honored exactly (incl. the optional trailing
`geometry` column, §2a).

THE ITEMIZED LAYER (TRANCHE 3 Phase A, 2026-08-02) — born-digital 2022+ CFD only.
  A filing enters the itemized pass ONLY when this module's own `parse_summary_text()` finds a
  genuine Summary-page text layer (the same born-digital test the totals path uses — content,
  never a filename). Those filings are parsed by the registered `cache_cfd` family and each
  side is RECONCILIATION-GATED: rows ship only when they sum EXACTLY (±$0.01) to the stated
  total this module already publishes. A side that does not reconcile emits NOTHING plus a
  reason in `notes`. Stated totals are NEVER recomputed from the itemization.
  Parsing is keyed on `sha256`, so a cross-channel byte-duplicate is parsed ONCE and the same
  rows are applied to every index row that shares those bytes.
  The handwritten Carr era stays itemization-free: an empty side there means NOT TRANSCRIBED,
  never "no donors", which is why its `reconciles_*` stay blank (unknown) and never False.

CARDINAL RULES honored here:
  * nothing is computed from the filer's figures — no sums, no derived balances. A blank stays
    blank; a printed word ("NA", "None", "-0-") is preserved verbatim in filing_stated_detail
    and only mapped to a decimal in filing_totals when the word IS a stated zero.
  * DERIVED — never hand-edit these CSVs. Corrections go in vision/<key>.json.
"""
import csv, decimal, hashlib, json, os, re, sys, glob
from dataclasses import replace as _dc_replace

CF_LIB = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      '..', '..', 'scripts', 'campaign_finance'))
sys.path[:0] = [CF_LIB, os.path.join(CF_LIB, 'families')]
import common            # noqa: E402  shared row model + money/geometry primitives
import normalize_donors  # noqa: E402  tier-1 donor/vendor normalization + donor_type
import reconcile         # noqa: E402  the $0.01 printed-total test
import registry          # noqa: E402  form-family dispatch

FAMILY_ID = 'cache_cfd'

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda *p: os.path.join(HERE, *p)
ENTITY = "cache_county"

TOTALS_HEADER = ['candidate', 'office', 'election_year', 'filing_date', 'reporting_period',
                 'filing_type', 'stated_total_contributions', 'stated_total_expenditures',
                 'stated_beginning_balance', 'stated_ending_balance', 'itemized_contrib_sum',
                 'itemized_expend_sum', 'reconciles_contrib', 'reconciles_expend',
                 'recon_delta_contrib', 'recon_delta_expend', 'self_funded_amount',
                 'n_contrib_rows', 'n_expend_rows', 'source_filing', 'document_id',
                 'extraction_confidence', 'notes']
CONTRIB_HEADER = ['candidate', 'office', 'seat', 'election_year', 'filing_date',
                  'reporting_period', 'date', 'donor_raw', 'donor_normalized', 'donor_type',
                  'donor_city', 'donor_state', 'donor_district', 'amount', 'in_kind',
                  'is_incremental', 'source_filing', 'document_id', 'line_no',
                  'extraction_confidence', 'extract_method', 'needs_review']
EXPEND_HEADER = ['candidate', 'office', 'seat', 'election_year', 'filing_date',
                 'reporting_period', 'date', 'vendor_raw', 'vendor_normalized', 'purpose',
                 'amount', 'in_kind', 'is_incremental', 'source_filing', 'document_id',
                 'line_no', 'extraction_confidence', 'extract_method', 'needs_review']

# Words a filer writes INSTEAD of a figure. "none"/"-0-"/"n/a" are the filer's own statement,
# not our inference — but only the explicit-zero words become a decimal 0; "NA"/"N/A" means
# "not applicable", which is NOT a number and stays blank.
ZERO_WORDS = {'none', 'nond', '-0-', '—0–', '—o—', '-o-', '0', '$0', '0.00', '$0.00',
              '0.0', '$-0-'}
NOT_A_NUMBER = {'na', 'n/a', 'n.a.', 'x', '--', '-', '—', 'blank'}


def money(s):
    """Decimal or None. Never guesses: a string that is not cleanly numeric returns None."""
    if s is None:
        return None
    t = str(s).strip()
    if t == '':
        return None
    low = t.lower().replace(' ', '')
    if low in NOT_A_NUMBER:
        return None
    if low in ZERO_WORDS:
        return decimal.Decimal(0)
    t = t.replace('$', '').replace(',', '').replace(' ', '')
    neg = False
    if t.startswith('(') and t.endswith(')'):
        neg, t = True, t[1:-1]
    if t.startswith('-'):
        neg, t = True, t[1:]
    if not re.fullmatch(r'\d+(\.\d{1,2})?', t):
        return None
    v = decimal.Decimal(t)
    return -v if neg else v


def dstr(v):
    return '' if v is None else str(v)


# ---------------------------------------------------------------- born-digital text parsing
def parse_summary_text(txt):
    """Positional parse of the Summary page of the 2025/2026 DocuSign-generated
    `cache_cfd_combined` filings. Returns {'A'..'F', 'closing'} of VERBATIM strings, or None.

    Only applied when the Summary section carries real layout whitespace (a run of >=10
    spaces between glyphs) — i.e. a genuine text layer. Scanner-embedded OCR text is NOT
    parsed here; those filings go through the vision layer instead, because an OCR
    misreading of a handwritten figure is exactly the failure mode this module must not have.
    """
    i = txt.rfind('Summary Page')
    if i < 0:
        return None
    s = txt[i:]
    j = s.find('Audit Trail')
    if j > 0:
        s = s[:j]
    if not re.search(r'\S {10,}\S', s):
        return None
    L = s.splitlines()
    out = {}
    k = 0
    while k < len(L):
        l, st = L[k], L[k].strip()
        if re.fullmatch(r'[A-F]', st):
            out.setdefault(st, (L[k + 1].strip() if k + 1 < len(L) else ''))
            k += 1
            continue
        letters = re.findall(r'(?<![A-Za-z0-9])([A-F])(?![A-Za-z0-9])', l)
        if len(letters) == 2 and not st.replace(letters[0], '').replace(letters[1], '').strip():
            if k + 1 < len(L):
                m1 = re.search(r'\b([A-F])\b', l)
                m2 = re.search(r'\b([A-F])\b', l[m1.start(1) + 1:])
                cb = m1.start(1) + 1 + m2.start(1)
                nxt = L[k + 1]
                out.setdefault(m1.group(1), nxt[:cb].strip())
                out.setdefault(m2.group(1), nxt[cb:].strip())
                k += 2
                continue
        m = re.match(r'^\s*([A-F])\s+(\S.*)$', l)
        if m:
            rest = m.group(2)
            m2 = re.search(r'\s{2,}([A-F])\s+(\S.*)$', rest)
            if m2:
                out.setdefault(m.group(1), rest[:m2.start()].strip())
                out.setdefault(m2.group(1), m2.group(2).strip())
            else:
                out.setdefault(m.group(1), rest.strip())
        k += 1
    for k, l in enumerate(L):
        if 'Balance at Close' in l:
            for n in L[k + 1:k + 4]:
                if n.strip():
                    out['closing'] = n.strip()
                    break
            break
    if not all(out.get(x) for x in 'BCDE'):
        return None
    return out


def load_vision():
    """vision/<sha1(canonical_path)[:8]>.json, keyed to EVERY index path it applies to.

    Cache is written ONCE per distinct document (sha256) under the lexicographically first
    of its index paths, and its `applies_to` list names every index row it covers — the
    41 cross-channel byte-duplicates are transcribed once and applied to both rows.
    """
    out, files = {}, sorted(glob.glob(D('vision', '*.json')))
    for fn in files:
        with open(fn) as fh:
            j = json.load(fh)
        j['_key'] = os.path.basename(fn)[:-5]
        for p in (j.get('applies_to') or [j.get('canonical_path')]):
            if p:
                out[p] = j
    return out, len(files)


def vv(node):
    """{'v':..,'c':..} -> (value, confidence). Tolerates a bare string."""
    if node is None:
        return '', ''
    if isinstance(node, dict):
        return (node.get('v') or '').strip(), (node.get('c') or '')
    return str(node).strip(), ''


CONF_RANK = {'high': 0, 'medium': 1, 'low': 2, '': 1}


def worst(*cs):
    cs = [c for c in cs if c]
    return max(cs, key=lambda c: CONF_RANK.get(c, 1)) if cs else ''


# ---------------------------------------------------------------- the FIELD-SHIFT screen
# A form family reads a ledger by COLUMN GRAMMAR. Where a filing writes its dates in a shape
# the family's date regex does not know ("17 Jan 2026", "1.2.26", "5May26"), the date token
# lands in the NAME column and the real name slides into the next field — the amounts still
# sum to the printed total, so reconciliation alone cannot catch it. Two detectable shapes:
#   * a name field that IS a date token;
#   * a name/purpose field with no letters at all (an OCR artifact like "|" or "---").
# POLICY (uniform across this sweep, and the reason it is not one rule):
#   * >= 50% of a side's rows suspect  -> the family did not understand that section's column
#     grammar, so the WHOLE SIDE is WITHHELD with a reason (a systematically mis-columned
#     ledger is a wrong value, not a rough one);
#   * < 50%  -> an ISOLATED defect, almost always a filer's own malformed date on an otherwise
#     correctly parsed section; the rows are KEPT and flagged `needs_review=1`.
# Either way the finding is a FAMILY LIMITATION, documented not patched (the shared engine is
# frozen this phase) and queued for Phase B.
_DATEISH = re.compile(
    r"^\d{1,2}\s*[/.\-]{1,2}\s*\d{1,2}\s*[/.\-]{0,2}\s*\d{0,4}$"          # 5/20.14  1.2.26
    r"|^\d{1,2}\s*[A-Za-z]{3,9}\.?\s*,?\s*\d{2,4}$"                        # 17 Jan 2026  5May26
    r"|^[A-Za-z]{3,9}\.?\s*\d{1,2}\s*,?\s*\d{2,4}$")                       # Jan 17, 2026
_SHIFT_CUTOFF = 0.5


def _has_alpha(s):
    return any(ch.isalpha() for ch in s or "")


def screen_side(rows, name_field, side_label, notes, family_id):
    """Return the rows that may ship (possibly []). Appends every finding to `notes`."""
    if not rows:
        return rows
    suspect = []
    for x in rows:
        nm = (getattr(x, name_field, "") or "").strip()
        extra = (getattr(x, "purpose", "") or "").strip()
        why = None
        if _DATEISH.match(nm):
            why = "%s reads %r, a DATE token" % (name_field, nm)
        elif nm and not _has_alpha(nm):
            why = "%s reads %r, which carries no letters" % (name_field, nm)
        elif extra and not _has_alpha(extra):
            why = "purpose reads %r, which carries no letters" % extra
        if why:
            suspect.append((x, why))
    if not suspect:
        return rows
    frac = len(suspect) / len(rows)
    if frac >= _SHIFT_CUTOFF:
        notes.append(
            "ITEMIZED %s WITHHELD (FIELD SHIFT): %d of %d parsed row(s) are mis-columned — "
            "e.g. line %s: %s. The `%s` family did not recognise this filing's date format, so "
            "the date landed in the name column and the real name slid into the next field; "
            "the amounts still sum to the printed total, which is exactly why reconciliation "
            "cannot catch it. A systematically mis-columned ledger is a WRONG VALUE, so the "
            "whole side emits NOTHING. FAMILY LIMITATION, documented not patched — queued for "
            "Phase B."
            % (side_label, len(suspect), len(rows), suspect[0][0].line_no, suspect[0][1],
               family_id))
        return []
    for x, why in suspect:
        x.needs_review = "1"
    notes.append(
        "FIELD SHIFT (isolated, %d of %d rows KEPT and flagged needs_review=1): %s. The filer's "
        "own malformed date is not in the `%s` date grammar, so the token slid into the name "
        "column; the amount is unaffected and the side still reconciles. FAMILY LIMITATION, "
        "documented not patched."
        % (len(suspect), len(rows),
           "; ".join("line %s: %s" % (x.line_no, w) for x, w in suspect[:4]), family_id))
    return rows


def itemize(r, text, stated_c, stated_e, aliases, parsed_by_sha, period_basis,
            module_incremental):
    """Parse ONE born-digital CFD filing with the registered family and RECONCILIATION-GATE
    each side against the stated total this module already publishes.

    Returns (contrib_rows, expend_rows, ft_patch, notes). `parsed_by_sha` memoizes the parse
    per sha256 so the cross-channel byte-duplicates are parsed ONCE (their rows are then
    re-stamped with each index row's own candidate/office/source_filing).
    """
    notes = []
    fam = registry.get(FAMILY_ID)
    meta = dict(candidate=r['candidate'], office=r['office'],
                seat=r.get('council_seat', ''), election_year=r['election_year'],
                filing_date=r['date'], reporting_period=r['reporting_period'],
                source_filing=r['path'], document_id='',
                extract_method=FAMILY_ID + '/text', is_scanned=False)
    sha = r['sha256']
    if sha not in parsed_by_sha:
        parsed_by_sha[sha] = fam.parse(text, meta)
    res = parsed_by_sha[sha]

    # The per-filing REGIME. This module already reads it off Box B vs Box C
    # (`_cfd_totals`), which is the same face the family reads; the module's published
    # determination wins, and the family's declaration is the fallback where the filer
    # left one column blank (period_only / ytd_only / neither -> module value is '').
    incr = module_incremental or res.get('is_incremental') or 'False'

    def stamp(row):
        return _dc_replace(row, candidate=meta['candidate'], office=meta['office'],
                           seat=meta['seat'], election_year=meta['election_year'],
                           filing_date=meta['filing_date'],
                           reporting_period=meta['reporting_period'],
                           source_filing=meta['source_filing'],
                           document_id=meta['document_id'], is_incremental=incr)

    crows = [stamp(x) for x in res['contrib_rows']]
    erows = [stamp(x) for x in res['expend_rows']]
    for x in crows:
        normalize_donors.normalize_contrib(x, meta['candidate'], aliases)
    for x in erows:
        normalize_donors.normalize_vendor(x)

    crows = screen_side(crows, 'donor_raw', 'contributions', notes, FAMILY_ID)
    erows = screen_side(erows, 'vendor_raw', 'expenditures', notes, FAMILY_ID)

    patch = {}
    keep = {'contrib': crows, 'expend': erows}
    for side, stated in (('contrib', stated_c), ('expend', stated_e)):
        rows_ = keep[side]
        if not rows_:
            if stated is not None and abs(float(stated)) > 0.005:
                notes.append('%s: the born-digital face states a total but itemizes no row '
                             'this family can read cleanly — reconciliation UNKNOWN, never a '
                             'fabricated mismatch' % side)
            continue
        ssum = round(sum(float(x.amount) for x in rows_ if x.amount), 2)
        rec, delta = reconcile.reconciles(ssum, None if stated is None else float(stated))
        if rec is not True:
            notes.append('ITEMIZED %s WITHHELD: %d parsed row(s) sum to %.2f against a stated '
                         '%s — the side does not reconcile, so NOTHING is emitted '
                         '(SCHEMA.md §6)'
                         % (side, len(rows_), ssum,
                            'blank total' if stated is None else '%.2f' % float(stated)))
            keep[side] = []
            continue
        patch['itemized_%s_sum' % side] = str(ssum)
        patch['reconciles_%s' % side] = 'True'
        patch['recon_delta_%s' % side] = '%.2f' % delta

    crows, erows = keep['contrib'], keep['expend']
    for x in crows + erows:
        x.extraction_confidence = 'high'
        x.needs_review = x.needs_review or '0'
    if crows or erows:
        patch['n_contrib_rows'] = len(crows)
        patch['n_expend_rows'] = len(erows)
        patch['self_funded_amount'] = common.money_str(round(sum(
            float(x.amount) for x in crows
            if x.donor_type in ('candidate-self', 'loan') and x.amount), 2))
        notes.append('ITEMIZED LAYER: %d contribution / %d expenditure row(s) parsed by the '
                     'registered `%s` family from the born-digital text layer, each side '
                     'reconciled EXACTLY to the stated total; period_basis=%s '
                     '(is_incremental=%s); per-row `geometry` records the amount cell read'
                     % (len(crows), len(erows), FAMILY_ID, period_basis or 'unknown', incr))
    return crows, erows, patch, notes


# ------------------------------------------------ the HANDWRITTEN era: vision itemization
# PHASE B FINAL WAVE, 2026-08-23. The pre-2022 Carr form and the image-faced 2022+ CFD scans are
# handwriting/scans no text pipeline can read; their donor/vendor lines were transcribed from
# page images into `vision_itemized/<key>.json` (schema cf_vision_itemized_v1, ONE per DISTINCT
# DOCUMENT, `applies_to` naming every index row that shares those bytes). It is a NEW sibling
# directory on purpose: the 171 stated-totals caches in `vision/` are hand transcriptions that
# are never regenerated and stay byte-identical through this wave.
#
# THE ANCHOR LADDER, and why it is ordered rather than a single test:
#   * Form "A" / Schedule A itemizes ONLY contributions OVER $50 on the Carr form; the cover's
#     line 2 aggregate of $50-and-under is NEVER itemized, and `stated_total_contributions`
#     publishes line 1 + line 2. Scoring the ledger against that sum manufactures a false
#     mismatch on every filing with a small-donor aggregate.
#   * `is_incremental` VARIES PER FILING here (CLAUDE.md), so the scope is decided by WHICH
#     printed cell the rows equal -- never by form family. A side that equals the figure this
#     module PUBLISHES is `reconciles_*=True`; a side that equals a different printed cell is
#     published with `reconciles_*` left BLANK and the basis named (a different SCOPE is not a
#     delta); a side matching nothing printed is a `delta`, published verbatim.
SIDE_STATES = ('transcribed', 'none', 'withheld', 'out-of-scope')


def row_money(printed):
    """A VERBATIM printed amount from a vision row -> (Decimal|None, applied_note).

    ⚠ `money()` CANNOT BE USED ON A HANDWRITTEN CELL. It strips commas and spaces, so `300,00`
    parses as 30000 and `63 75` as 6375 — both 100x FABRICATIONS found on real pages of this
    programme. `common.parse_vision_amount` is the shared reader for handwritten cells.
    """
    return common.parse_vision_amount(printed)


def load_vision_itemized():
    """index path -> the itemization cache that covers it (one per distinct document)."""
    out = {}
    for fn in sorted(glob.glob(D('vision_itemized', '*.json'))):
        with open(fn, encoding='utf-8') as fh:
            j = json.load(fh)
        for p in (j.get('applies_to') or [j.get('index_path')]):
            if p:
                out[p] = j
    return out


# A whole-dollar figure written with the cents position struck rather than filled: `7,200.`,
# `1,000.-`, `326-`. The transcription contract already rules this for ROW amounts ("a trailing
# dash after whole dollars means no cents"), and these filers use the same hand on the COVER.
# ⚠ USED FOR RECONCILIATION ANCHORS ONLY — never to publish a stated total. `money()` returns
# None on `7,200.`, so this module's published `stated_total_contributions` for that filing stays
# exactly what it has always been; without the tolerant read here the anchor ladder would see NO
# parseable figure and score a side that closes EXACTLY to the printed cover line as a `delta`.
# Fabricating a delta out of an unparsed anchor is a worse error than the one it replaces.
_NIL_CENTS = re.compile(r'^-?\d+(?:\.|-|\.-|\.–)$')


def anchor_money(s):
    """(Decimal|None, tolerant_flag). The module's own strict `money()` first; the shared
    handwritten-cell reader only as a FALLBACK, and the flag says when that happened."""
    v = money(s)
    if v is not None:
        return v, False
    v2, _note = common.parse_vision_amount(s)
    return (v2, v2 is not None)


def _anchors(detail, stated_basis, side):
    """[(label, Decimal|None, tolerant_flag)] in the order a match should be reported.

    `tolerant_flag` marks a figure the strict reader could not parse and the nil-cents
    fallback could (`7,200.`), so the note can say the anchor came from a form this module's
    published `stated_*` had to leave blank."""
    def A(lab, cell):
        v, tol = anchor_money(cell)
        return (lab, v, tol)

    if stated_basis == 'carr_three_column':
        if side == 'contrib':
            return [A("the cover's line 1 (contributions over $50), CUMULATIVE column",
                      detail['contrib_over_50_cum']),
                    A("the cover's line 1 (contributions over $50), THIS-REPORT column",
                      detail['contrib_over_50_this'])]
        return [A("the cover's line 3 (total campaign expenses), CUMULATIVE column",
                  detail['total_expenses_cum']),
                A("the cover's line 3 (total campaign expenses), THIS-REPORT column",
                  detail['total_expenses_this'])]
    if side == 'contrib':
        return [A("Summary Page Box B (contributions received THIS PERIOD)",
                  detail['box_B_contrib_this_period']),
                A("Summary Page Box C (contributions received YEAR-TO-DATE)",
                  detail['box_C_contrib_ytd']),
                A("the printed Schedule A total (sum of all Schedule A pages)",
                  detail['schedA_total_contributions'])]
    return [A("Summary Page Box D (expenditures made THIS PERIOD)",
              detail['box_D_expend_this_period']),
            A("Summary Page Box E (expenditures made YEAR-TO-DATE)",
              detail['box_E_expend_ytd']),
            A("the printed Schedule B total (sum of all Schedule B pages)",
              detail['schedB_total_expenditures'])]


def itemize_vision(r, vi, detail, stated_basis, stated_c, stated_e, aliases, doc_id):
    """Emit the vision-transcribed itemized rows of ONE handwritten / scanned filing.

    Returns (crows, erows, patch, notes)."""
    notes, patch, out = [], {}, {'contrib': [], 'expend': []}
    sides = vi.get('sides') or {}
    withheld = vi.get('withheld_reason') or {}
    recon = vi.get('recon') or {}
    shapes = vi.get('shape') or {}
    verdicts = {}

    for side, key, label in (('contrib', 'contributions', 'A'),
                             ('expend', 'expenditures', 'B')):
        state = sides.get(key, '')
        raw = vi.get(key) or []
        if state not in SIDE_STATES:
            notes.append('ITEMIZED %s: unknown side state %r in the transcription; nothing '
                         'emitted' % (key, state))
            verdicts[side] = 'unknown-state'
            continue
        if state == 'out-of-scope':
            verdicts[side] = 'out-of-scope'
            notes.append('ITEMIZED %s OUT OF SCOPE: %s' % (key, withheld.get(key, '')))
            continue
        if state == 'withheld':
            verdicts[side] = 'withheld'
            notes.append('ITEMIZED %s WITHHELD by the transcription (NOTHING emitted, no sum '
                         'claimed): %s' % (key, withheld.get(key, 'no reason recorded')))
            continue
        if state == 'none':
            verdicts[side] = 'no-schedule-page'
            notes.append('ITEMIZED %s: the document carries NO Form "%s" / Schedule %s page at '
                         'all -- an honest absence, NOT a zero (%s)'
                         % (key, label, label, (recon.get(key) or {}).get('detail', '')))
            continue
        if not raw:
            verdicts[side] = 'empty-schedule'
            notes.append('ITEMIZED %s: the Form "%s" / Schedule %s page exists and prints NO '
                         'lines (read from the page image) -- an empty schedule, never "no '
                         'donors"' % (key, label, label))
            continue

        rows_, total, n_blank, n_repaired = [], decimal.Decimal(0), 0, 0
        for i, x in enumerate(sorted(raw, key=lambda y: int(y.get('line_no', 0) or 0)), 1):
            amt, amt_note = row_money(x.get('amount'))
            n_repaired += 1 if amt_note else 0
            if amt is None:
                n_blank += 1
            else:
                total += amt
            kw = dict(candidate=r['candidate'], office=r['office'],
                      seat=r.get('council_seat', ''), election_year=r['election_year'],
                      filing_date=r['date'], reporting_period=r['reporting_period'],
                      date=x.get('date', ''), amount='' if amt is None else str(amt),
                      in_kind='True' if x.get('in_kind') else 'False',
                      source_filing=r['path'], document_id=doc_id, line_no=str(i),
                      # A VISION read is capped at the OCR tier; a transcriber's
                      # own `high` is downgraded, never up.
                      extraction_confidence=('medium' if x.get('confidence') in ('', None, 'high')
                                             else x.get('confidence')),
                      extract_method='vision/' + (vi.get('shape', {}).get(key) or 'page-image'),
                      needs_review='1' if str(x.get('needs_review')) == '1' else '0',
                      geometry=x.get('geometry', ''))
            rows_.append(common.ContribRow(donor_raw=x.get('donor_raw', ''),
                                           donor_city=x.get('donor_city', ''),
                                           donor_state=x.get('donor_state', ''), **kw)
                         if side == 'contrib' else
                         common.ExpendRow(vendor_raw=x.get('vendor_raw', ''),
                                          purpose=x.get('purpose', ''), **kw))
        if n_repaired:
            notes.append('ITEMIZED %s: the SHARED WHITELISTED currency repair (decimal-comma / '
                         'dot-as-thousands, common.repair_money_line) was applied to %d printed '
                         'amount(s) — read naively a decimal comma is a 100x error (SCHEMA §6: '
                         'every repaired value is marked)' % (key, n_repaired))
        if n_blank:
            notes.append('ITEMIZED %s: %d row(s) carry NO amount (illegible on the page and never '
                         'guessed), so the side\'s sum is a FLOOR, not a total' % (key, n_blank))

        published = stated_c if side == 'contrib' else stated_e
        anchors = _anchors(detail, stated_basis, side)
        hit = next(((lab, val, tol) for lab, val, tol in anchors
                    if val is not None and abs(total - val) <= decimal.Decimal('0.01')), None)
        patch['itemized_%s_sum' % side] = str(total)
        if hit is None:
            verdicts[side] = 'delta'
            patch['reconciles_%s' % side] = 'False'
            # A delta side matched NO printed anchor, so the scope is undetermined. The Carr form
            # publishes the CUMULATIVE column, and these ledgers restate the cycle, so the safe
            # flag is False (cumulative) — marking such rows incremental would invite a naive
            # cycle SUM, which is the one arithmetic this corpus must never support.
            for y in rows_:
                y.needs_review = '1'
                y.is_incremental = 'False'
            notes.append(
                'ITEMIZED %s DELTA (published verbatim, NOT adjusted): %d row(s) read from the '
                'page image sum to %s, matching NONE of the figures the document prints (%s). '
                'The residual is the FILER\'s own arithmetic, retained as a fact about the '
                'document; every row on the side carries needs_review=1. recon_delta_%s is left '
                'BLANK because the competing figures may be different SCOPES.'
                % (key, len(rows_), total,
                   '; '.join('%s = %s' % (lab, 'blank' if val is None else val)
                             for lab, val, _tol in anchors), side))
        else:
            lab, val, tolerant = hit
            if tolerant:
                notes.append(
                    'ITEMIZED %s ANCHOR READ WITH THE NIL-CENTS TOLERANCE: the printed figure is '
                    'written with its cents position struck rather than filled, which this '
                    'module\'s strict money reader leaves unparsed — so the published '
                    'stated_total_* for this filing does NOT carry it, and it is used here as a '
                    'RECONCILIATION ANCHOR ONLY. No published stated figure was changed.' % key)
            same_scope = (published is not None
                          and abs(val - published) <= decimal.Decimal('0.01'))
            verdicts[side] = 'stated-exact' if same_scope else 'other-scope-exact'
            if same_scope:
                patch['reconciles_%s' % side] = 'True'
                patch['recon_delta_%s' % side] = '0.00'
                notes.append('ITEMIZED %s EXACT: %d row(s) sum to %s = %s = the figure this '
                             'module publishes in stated_total_%s'
                             % (key, len(rows_), total, lab,
                                'contributions' if side == 'contrib' else 'expenditures'))
            else:
                patch['recon_delta_%s' % side] = '0.00'
                notes.append(
                    'ITEMIZED %s DIFFERENT-SCOPE EXACT: %d row(s) sum EXACTLY to %s = %s, and NOT '
                    'to the %s this module publishes in stated_total_%s. reconciles_%s is left '
                    'BLANK (unknown) rather than True: the two figures are different SCOPES and '
                    'comparing them is a basis error. Both are named here; neither is adjusted.'
                    % (key, len(rows_), total, lab,
                       'blank figure' if published is None else str(published),
                       'contributions' if side == 'contrib' else 'expenditures', side))
            # SCOPE -> the row flag. A ledger matching the THIS-PERIOD / Box-B cell is a genuinely
            # per-period schedule; one matching the CUMULATIVE / YTD cell restates the cycle.
            per_period = ('THIS-REPORT' in lab or 'THIS PERIOD' in lab)
            cum_val = next((v for l2, v, _t in anchors
                            if ('CUMULATIVE' in l2 or 'YEAR-TO-DATE' in l2) and v is not None),
                           None)
            incr = 'True' if (per_period and cum_val is not None
                              and abs(cum_val - val) > decimal.Decimal('0.01')) else 'False'
            for y in rows_:
                y.is_incremental = incr
        if shapes.get(key):
            notes.append('ITEMIZED %s shape: %s' % (key, shapes[key]))
        det = (recon.get(key) or {}).get('detail', '')
        if det:
            notes.append('ITEMIZED %s basis as read: %s' % (key, det))
        out[side] = rows_

    crows, erows = out['contrib'], out['expend']
    for x in crows:
        normalize_donors.normalize_contrib(x, r['candidate'], aliases)
    for x in erows:
        normalize_donors.normalize_vendor(x)
    if crows or erows:
        patch['n_contrib_rows'] = len(crows)
        patch['n_expend_rows'] = len(erows)
        patch['self_funded_amount'] = common.money_str(round(sum(
            float(x.amount) for x in crows
            if x.donor_type in ('candidate-self', 'loan') and x.amount), 2))
        g = vi.get('gates') or {}
        notes.append(
            'ITEMIZED LAYER (VISION, Phase B final wave 2026-08-23): %d contribution / %d '
            'expenditure row(s) read from the page images; verdicts contributions=%s, '
            'expenditures=%s. Gates: %s | %s | %s | %s'
            % (len(crows), len(erows), verdicts.get('contrib', 'none'),
               verdicts.get('expend', 'none'), g.get('page_subtotal', '') or 'no page subtotal',
               g.get('row_count', '') or 'no row-count gate',
               g.get('geometry_proof', '') or 'no geometry proof',
               g.get('balance_chain', '') or 'no balance chain'))
    if vi.get('notes'):
        notes.append('transcription: ' + vi['notes'])
    return crows, erows, patch, notes


def build(rows):
    vision, n_vision_files = load_vision()
    vis_item = load_vision_itemized()
    tot, det = [], []
    n_from_vision = n_from_text = n_no_totals = 0
    contrib_rows, expend_rows = [], []
    aliases = normalize_donors.load_aliases(D('donor_aliases.csv'))
    parsed_by_sha, n_bd, n_vis = {}, 0, 0

    for r in rows:
        path = r['path']
        doc_id = 'cache_county|%s|%s' % (r['sha256'][:12], path)
        v = vision.get(path)
        src, form_read, conf, notes = '', '', '', []
        cover = {}
        stated_c = stated_e = stated_b = stated_end = None
        detail = dict.fromkeys(
            ['contrib_over_50_last', 'contrib_over_50_this', 'contrib_over_50_cum',
             'contrib_le50_last', 'contrib_le50_this', 'contrib_le50_cum',
             'total_expenses_last', 'total_expenses_this', 'total_expenses_cum',
             'ending_balance_last', 'ending_balance_this', 'ending_balance_cum',
             'box_A_balance_begin', 'box_B_contrib_this_period', 'box_C_contrib_ytd',
             'box_D_expend_this_period', 'box_E_expend_ytd', 'box_F_subtotal',
             'box_closing_balance', 'schedA_total_contributions', 'schedB_total_expenditures'], '')
        period_basis, is_incremental, stated_basis = '', '', ''

        if v:
            src = 'vision'
            form_read = v.get('form_read', '')
            st = v.get('stated') or {}
            stated_basis = st.get('basis', '')
            for f in ('candidate_stated', 'office_verbatim', 'office_district', 'party_verbatim',
                      'residence_city', 'addressee', 'report_type_marked', 'date_signed',
                      'received_stamp'):
                cover[f] = vv((v.get('cover') or {}).get(f))[0]

            if stated_basis == 'carr_three_column':
                n_from_vision += 1
                lines = st.get('lines') or {}
                cs = []
                for key, pref in (('contrib_over_50', 'contrib_over_50'),
                                  ('contrib_50_or_less', 'contrib_le50'),
                                  ('total_expenses', 'total_expenses'),
                                  ('ending_balance', 'ending_balance')):
                    node = lines.get(key) or {}
                    for col, suf in (('last', 'last'), ('this', 'this'), ('cumulative', 'cum')):
                        val, c = vv(node.get(col))
                        detail['%s_%s' % (pref, suf)] = val
                        if val:
                            cs.append(c)
                conf = worst(*cs) or 'high'
                # the Carr form's third column IS the whole-cycle-to-date figure, so the
                # cumulative column is the stated cycle total for this filing.
                gt = money(detail['contrib_over_50_cum'])
                le = money(detail['contrib_le50_cum'])
                parts = [p for p in (gt, le) if p is not None]
                stated_c = sum(parts) if parts else None
                stated_e = money(detail['total_expenses_cum'])
                stated_end = money(detail['ending_balance_cum'])
                period_basis = 'carr_cumulative_column'
                is_incremental = 'False'
                if gt is None and detail['contrib_over_50_cum']:
                    notes.append('contributions >$50 cumulative printed as %r (not a number) — '
                                 'stated total omits it' % detail['contrib_over_50_cum'])
                if le is None and detail['contrib_le50_cum']:
                    notes.append('contributions <=$50 cumulative printed as %r (not a number) — '
                                 'stated total omits it' % detail['contrib_le50_cum'])

            elif stated_basis == 'cfd_period_ytd':
                n_from_vision += 1
                bx = st.get('boxes') or {}
                sch = st.get('schedule_totals') or {}
                m = {'A_balance_begin': 'box_A_balance_begin',
                     'B_contrib_this_period': 'box_B_contrib_this_period',
                     'C_contrib_ytd': 'box_C_contrib_ytd',
                     'D_expend_this_period': 'box_D_expend_this_period',
                     'E_expend_ytd': 'box_E_expend_ytd',
                     'F_subtotal_before_expend': 'box_F_subtotal',
                     'closing_balance': 'box_closing_balance'}
                cs = []
                for k, col in m.items():
                    val, c = vv(bx.get(k))
                    detail[col] = val
                    if val:
                        cs.append(c)
                detail['schedA_total_contributions'] = vv(sch.get('total_contributions_received'))[0]
                detail['schedB_total_expenditures'] = vv(sch.get('total_expenditures_made'))[0]
                conf = worst(*cs) or 'high'
                stated_c, stated_e, stated_b, stated_end, period_basis, is_incremental = \
                    _cfd_totals(detail, notes)
            else:
                n_no_totals += 1
                conf = 'low'
                notes.append('vision read the page but recovered no stated totals '
                             '(form_read=%s)' % (form_read or 'unreadable'))
            if v.get('notes'):
                notes.append(v['notes'])
        else:
            # born-digital text layer (the 2025/2026 DocuSign set)
            tp = D(r['text_path'])
            parsed = parse_summary_text(open(tp, errors='replace').read()) if os.path.exists(tp) else None
            if parsed:
                src, form_read, stated_basis = 'born_digital_text', 'cache_cfd', 'cfd_period_ytd'
                n_from_text += 1
                detail['box_A_balance_begin'] = parsed.get('A', '')
                detail['box_B_contrib_this_period'] = parsed.get('B', '')
                detail['box_C_contrib_ytd'] = parsed.get('C', '')
                detail['box_D_expend_this_period'] = parsed.get('D', '')
                detail['box_E_expend_ytd'] = parsed.get('E', '')
                detail['box_F_subtotal'] = parsed.get('F', '')
                detail['box_closing_balance'] = parsed.get('closing', '')
                cover['office_verbatim'] = r.get('office_stated', '')
                cover['candidate_stated'] = r.get('candidate_stated', '')
                conf = 'high'
                stated_c, stated_e, stated_b, stated_end, period_basis, is_incremental = \
                    _cfd_totals(detail, notes)
            else:
                src = 'none'
                n_no_totals += 1
                conf = ''
                notes.append('no stated totals: the filing is not born-digital and has no '
                             'vision transcription yet')

        # ---- BORN-DIGITAL itemized layer (TRANCHE 3 Phase A). No-op on the handwritten
        # Carr era: the module's own born-digital test gates entry, so those rows/notes/
        # reconciliation columns are byte-unchanged.
        patch = {}
        tp = D(r['text_path']) if r.get('text_path') else ''
        bd_text = None
        if tp and os.path.exists(tp):
            _t = open(tp, errors='replace').read()
            if parse_summary_text(_t) is not None:
                bd_text = _t
        _c = _e = []
        if bd_text is not None:
            n_bd += 1
            _c, _e, patch, _n = itemize(r, bd_text, stated_c, stated_e, aliases,
                                        parsed_by_sha, period_basis, is_incremental)
            contrib_rows.extend(_c)
            expend_rows.extend(_e)
            notes.extend(_n)

        # ---- the VISION itemization (Phase B final wave, 2026-08-23). Runs ONLY where the
        # born-digital family emitted nothing for this filing, so the 2026-08-02 born-digital
        # block is frozen: a filing that already carries parser rows is never re-itemized.
        vi = vis_item.get(path)
        if vi is not None and not (_c or _e):
            n_vis += 1
            _c, _e, vpatch, _n = itemize_vision(
                r, vi, detail, stated_basis, stated_c, stated_e, aliases,
                'cache_county|%s|%s' % (r['sha256'][:12], path))
            contrib_rows.extend(_c)
            expend_rows.extend(_e)
            notes.extend(_n)
            patch.update(vpatch)
            if len(vi.get('applies_to') or []) > 1:
                notes.append('one ITEMIZATION applied to %d index rows (identical bytes) -- group '
                             'on sha256 before summing' % len(vi['applies_to']))

        if 'byte-identical duplicate of' in (r.get('notes') or ''):
            notes.append('cross-channel byte-identical duplicate — group on sha256 before summing')
        if v and len(v.get('applies_to') or []) > 1:
            notes.append('one transcription applied to %d index rows (identical bytes)'
                         % len(v['applies_to']))

        tot.append({
            'candidate': r['candidate'], 'office': r['office'],
            'election_year': r['election_year'], 'filing_date': r['date'],
            'reporting_period': r['reporting_period'], 'filing_type': r['filing_type'],
            'stated_total_contributions': dstr(stated_c),
            'stated_total_expenditures': dstr(stated_e),
            'stated_beginning_balance': dstr(stated_b),
            'stated_ending_balance': dstr(stated_end),
            'itemized_contrib_sum': '', 'itemized_expend_sum': '',
            'reconciles_contrib': '', 'reconciles_expend': '',
            'recon_delta_contrib': '', 'recon_delta_expend': '',
            'self_funded_amount': '', 'n_contrib_rows': 0, 'n_expend_rows': 0,
            'source_filing': path, 'document_id': doc_id,
            'extraction_confidence': conf, 'notes': '; '.join(notes)})
        tot[-1].update(patch)
        for _row in list(_c) + list(_e):
            _row.document_id = doc_id

        det.append(dict(
            source_filing=path, sha256=r['sha256'], candidate=r['candidate'],
            election_year=r['election_year'], office=r['office'],
            scope_status=r['scope_status'], totals_source=src,
            vision_key=(v or {}).get('_key', ''), form_read=form_read,
            stated_basis=stated_basis, period_basis=period_basis,
            is_incremental=is_incremental, extraction_confidence=conf,
            office_verbatim=cover.get('office_verbatim', ''),
            office_district=cover.get('office_district', ''),
            party_verbatim=cover.get('party_verbatim', ''),
            residence_city=cover.get('residence_city', ''),
            filed_to_clerk=cover.get('addressee', ''),
            report_type_marked=cover.get('report_type_marked', ''),
            date_signed=cover.get('date_signed', ''),
            received_stamp=cover.get('received_stamp', ''),
            candidate_stated=cover.get('candidate_stated', ''),
            **detail, notes='; '.join(notes)))

    tot.sort(key=lambda x: (x['election_year'], x['office'], x['candidate'], x['source_filing']))
    det.sort(key=lambda x: (x['election_year'], x['candidate'], x['source_filing']))
    contrib_rows.sort(key=lambda x: (x.source_filing, int(x.line_no or 0)))
    expend_rows.sort(key=lambda x: (x.source_filing, int(x.line_no or 0)))
    return tot, det, contrib_rows, expend_rows, dict(
        vision_files=n_vision_files, from_vision=n_from_vision, from_text=n_from_text,
        no_totals=n_no_totals, born_digital=n_bd, vision_itemized=n_vis,
        vision_itemized_files=len(vis_item))


def _cfd_totals(detail, notes):
    """Cache's own county form prints BOTH a 'This Period' and a 'Year-to-Date' column, so
    whether a filing is incremental is a property OF THAT FILING, not of the city. Record
    what the filing itself says; never reconcile the two columns for the filer."""
    b = money(detail['box_B_contrib_this_period'])
    c = money(detail['box_C_contrib_ytd'])
    d = money(detail['box_D_expend_this_period'])
    e = money(detail['box_E_expend_ytd'])
    a = money(detail['box_A_balance_begin'])
    cl = money(detail['box_closing_balance'])
    have_p = b is not None or d is not None
    have_y = c is not None or e is not None
    if have_p and have_y:
        differ = (b is not None and c is not None and b != c) or \
                 (d is not None and e is not None and d != e)
        period_basis = 'period_and_ytd_differ' if differ else 'period_equals_ytd'
        is_incr = 'True' if differ else 'False'
        if not differ:
            notes.append('This-Period and Year-to-Date columns are equal — first/only report '
                         'of the cycle; incremental and cumulative readings coincide')
    elif have_p:
        period_basis, is_incr = 'period_only', ''
        notes.append('only the This-Period column is filled in — cannot tell from the filing '
                     'whether earlier activity exists')
    elif have_y:
        period_basis, is_incr = 'ytd_only', ''
        notes.append('only the Year-to-Date column is filled in — This-Period left blank by '
                     'the filer')
    else:
        period_basis, is_incr = 'neither', ''
    # stated_total_* = the THIS-PERIOD figure (this filing's own reporting period), falling
    # back to the YTD figure when the filer filled only that column. Both stay verbatim in
    # filing_stated_detail.csv.
    sc = b if b is not None else c
    se = d if d is not None else e
    return sc, se, a, cl, period_basis, is_incr


def mark_content_duplicates(tot, crows, erows, sha_of):
    """Flag two filings that are the SAME REPORT published twice with DIFFERENT BYTES.

    ⚠ `sha256`-DISTINCT IS NOT DOCUMENT-DISTINCT (GOTCHAS.md, proved on salt_lake_county and
    again here). This module's whole duplicate story is byte-identity — `applies_to` groups the
    42 cross-channel copies — and that machinery is BLIND to a re-scan: the 2026-08-23 wave found
    Buttars 7/16/2012 published through two channels with identical covers, identical schedules
    and different md5s. Both are real publications and both are kept, but summing them
    double-counts the filer, and nothing in the data says so.

    The detector is deliberately CONSERVATIVE and evidence-only: same candidate, same cycle, and
    an IDENTICAL non-empty multiset of (date, name, amount) rows on BOTH sides. Sequential
    reports of one cycle never satisfy that; a re-scan always does. Nothing is dropped — a note
    is added to each filing naming its twin.
    """
    def sig(rows_, name_attr):
        return tuple(sorted((x.date, (getattr(x, name_attr) or '').strip().lower(), x.amount)
                            for x in rows_))
    by_src = {}
    for x in crows:
        by_src.setdefault(x.source_filing, [[], []])[0].append(x)
    for x in erows:
        by_src.setdefault(x.source_filing, [[], []])[1].append(x)
    groups = {}
    for r in tot:
        rows_ = by_src.get(r['source_filing'])
        if not rows_ or not (rows_[0] or rows_[1]):
            continue
        key = (re.sub(r'[^a-z]', '', (r['candidate'] or '').lower()), r['election_year'],
               sig(rows_[0], 'donor_raw'), sig(rows_[1], 'vendor_raw'))
        groups.setdefault(key, []).append(r)
    n = 0
    for key, grp in groups.items():
        if len(grp) < 2:
            continue
        # ⚠ EXCLUDE THE KNOWN BYTE-DUPLICATES. 42 index rows are the same bytes served by a
        # second channel; `applies_to` already groups them and each row already says so. This
        # detector exists ONLY for the case that machinery is blind to — the same report
        # RE-SCANNED, so a group whose members share one sha256 is not news.
        if len({sha_of.get(r['source_filing'], r['source_filing']) for r in grp}) < 2:
            continue
        for r in grp:
            others = '; '.join(o['source_filing'] for o in grp if o is not r)
            r['notes'] += (' | CONTENT-DUPLICATE (NOT a byte duplicate): this filing itemizes an '
                           'IDENTICAL set of contributions and expenditures to %s — the same '
                           'report published through a second channel as a different scan, so the '
                           'sha256 grouping this module uses elsewhere CANNOT see it. Both '
                           'publications are real and both are kept; COUNT THE FILING ONCE and '
                           'never sum the copies.' % others)
            n += 1
    return n


def write(path, rows, header):
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=header, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def write_rows(path, header, geo_header, rows):
    """Same trailing-optional-`geometry` contract as the shared driver (SCHEMA.md §2a):
    the column appears only when a row actually carries positional provenance."""
    use = geo_header if any(getattr(x, common.GEOMETRY_COL, '') for x in rows) else header
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=use, extrasaction='ignore')
        w.writeheader()
        for x in rows:
            w.writerow(common.row_to_dict(x))


def main():
    idx = list(csv.DictReader(open(D('index.csv'))))
    tot, det, crows, erows, stats = build(idx)
    n_dup = mark_content_duplicates(tot, crows, erows,
                                    {r['path']: r['sha256'] for r in idx})
    write(D('filing_totals.csv'), tot, TOTALS_HEADER)
    write_rows(D('contributions.csv'), CONTRIB_HEADER, common.CONTRIB_HEADER_GEO, crows)
    write_rows(D('expenditures.csv'), EXPEND_HEADER, common.EXPEND_HEADER_GEO, erows)
    write(D('filing_stated_detail.csv'), det, list(det[0].keys()) if det else ['source_filing'])
    n_c = sum(1 for r in tot if r['stated_total_contributions'] != '')
    n_e = sum(1 for r in tot if r['stated_total_expenditures'] != '')
    print('filing_totals.csv        %3d rows (one per index.csv filing)' % len(tot))
    print('  stated contributions   %3d rows carry a figure  (%d blank — filer left it blank '
          'or it is unreadable)' % (n_c, len(tot) - n_c))
    print('  stated expenditures    %3d rows carry a figure  (%d blank)' % (n_e, len(tot) - n_e))
    print('  totals source          vision %d / born-digital text %d / none %d'
          % (stats['from_vision'], stats['from_text'], stats['no_totals']))
    print('vision/                  %3d transcription caches read' % stats['vision_files'])
    print('filing_stated_detail.csv %3d rows (verbatim This-Period + Year-to-Date)' % len(det))
    nrc = sum(1 for r in tot if r['reconciles_contrib'] == 'True')
    nre = sum(1 for r in tot if r['reconciles_expend'] == 'True')
    print('born-digital filings handed to `%s`: %3d of %d  (sides reconciling exactly: '
          '%d contrib / %d expend)' % (FAMILY_ID, stats['born_digital'], len(tot), nrc, nre))
    if n_dup:
        print('CONTENT-DUPLICATE filings flagged: %d (same report, DIFFERENT bytes — sha256 '
              'grouping cannot see these; count each report ONCE)' % n_dup)
    print('vision itemization       %3d filings itemized from page images (%d distinct-document '
          'caches in vision_itemized/)'
          % (stats['vision_itemized'], stats['vision_itemized_files']))
    nb = sum(1 for r in tot if 'ITEMIZED LAYER (VISION' in r['notes'])
    nw = sum(1 for r in tot if 'WITHHELD by the transcription' in r['notes'])
    ne_ = sum(1 for r in tot if 'an empty schedule, never' in r['notes'])
    print('  of those: %d carry rows, %d have a withheld side, %d an empty schedule'
          % (nb, nw, ne_))
    print('contributions.csv        %3d rows   expenditures.csv %3d rows  — an empty itemized '
          'side is NOT TRANSCRIBED or an EMPTY SCHEDULE, never "no donors"'
          % (len(crows), len(erows)))


if __name__ == '__main__':
    main()
