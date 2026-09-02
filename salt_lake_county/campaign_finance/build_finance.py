#!/usr/bin/env python3
"""Build the STRUCTURED campaign-finance layer for Salt Lake County COUNTY offices from the
EasyVote portal's ITEMIZED advanced-search JSON (the genuinely-structured source — not PDF
text). Writes contributions.csv / expenditures.csv / filing_totals.csv per
scripts/campaign_finance/SCHEMA.md.

Source of truth: raw/easyvote_api/advancedsearch_{contributions,distributions}.json
(itemized per-transaction rows straight from the county EasyVote API), joined to
documentsearch.json (filer + filing metadata) and the downloaded redacted PDFs (raw/easyvote/).

Design notes (honest caveats, see CLAUDE.md):
- The API exposes NO in-kind flag and NO donor address -> in_kind=False for all rows;
  donor_city/state/district blank. Extraction is `high` (structured API, not OCR).
- The API does NOT return each filing's PRINTED (stated) totals; those live only in the
  image-only redacted PDFs. So filing_totals carries itemized sums with BLANK stated_* and
  BLANK reconciles_* (unknown, never a fabricated mismatch). The integrity signal here is
  "authoritative structured itemized source", documented in notes.
- election_year is the EVEN-year proxy (build_lib.election_year_from_date).

SECOND, ADDITIVE PATH (2026-08-01 vision totals tranche) — `build_totals_tranche()`:
the two NON-STRUCTURED eras (the ~2006-2015 clerk legacy PDFs and the 2022 EasyVote cycle)
have no itemized source at all, so their filings are given **stated-totals-only**
filing_totals rows read off each filing's own cover + Summary Page by Read-tool vision
(caches in `vision/`, schema documented in CLAUDE.md). Those rows are APPENDED after the
EasyVote-JSON rows, which are emitted first and unchanged — the 2024/2026 structured layer
is byte-identical across this change. No contributions/expenditures rows are produced for
these eras this tranche (itemization deferred), so their `itemized_*` / `reconciles_*` stay
BLANK: the honest "unknown" state, never a fabricated reconciliation.
"""
import json, os, sys, csv, re
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "scripts", "campaign_finance")))
import build_lib as BL
import vision_lib as VL
import common
from common import (ContribRow, ExpendRow, FilingTotals, CONTRIB_HEADER, EXPEND_HEADER,
                    TOTALS_HEADER, GEOMETRY_COL, OCCUPATION_COL, money_str, row_to_dict)
from normalize_donors import tier1, classify_donor_type, normalize_contrib, normalize_vendor, load_aliases

API = os.path.join(HERE, "raw", "easyvote_api")
VISION = os.path.join(HERE, "vision")


def load_json(name):
    return json.load(open(os.path.join(API, name)))


# =====================================================================================
# VISION TOTALS TRANCHE (2026-08-01) — the two non-structured eras
# =====================================================================================
# Salt Lake County ran ONE county C&E form from 2006 through 2022 (page 1 = cover with
# candidate / Office Sought / the checked "Type of Report" box; page 2 = "Summary Page"
# with Column A "Total this Period" + Column B "Sum Total to Date"). Both non-structured
# eras — the clerk legacy PDFs and the 2022 EasyVote cycle — print that form and nothing
# machine-readable, so the stated totals are transcribed by Read-tool vision into
# `vision/<sha1(index path)[:8]>.json` (the repo-standard key, vision_lib.cache_key).
#
# Discipline (SCHEMA.md §4/§6 + the repo cardinal rules):
#   * every value is the form's own PRINTED figure, verbatim — nothing is computed here
#     (Line 7 is never derived from Lines 5-6, Column B is never filled from Column A);
#   * the cache's three-state convention is preserved: a string = printed, "" = the filer
#     left the cell blank, null = printed but ILLEGIBLE -> stays blank + drops confidence;
#   * `reporting_period` prefers the FORM's own checked report-type label over the clerk
#     listing-page label (GOTCHAS: portal/listing labels lie); the listing label is kept in
#     `notes` whenever the two disagree;
#   * interim and summary/final filings OVERLAP by design — `filing_type` records which is
#     which so cycle_totals.py can dedup. NEVER sum these rows for a candidate-cycle total.

# The interim deadlines the county form has printed across its versions (April 5 · June 20 /
# June 21 / "seven days before a primary" · September 15 · October 31 / "seven days before a
# general"), matched tolerantly because the transcriber records the checkbox label VERBATIM
# and the wording drifted between form years ("Sept 15", "Nov 1"). Checked only AFTER the
# summary / final / year-end tests, so "January 31" can never fall through to a month match.
_INTERIM_RE = re.compile(r"(?i)\b(apr|jun|jul|aug|sep|oct|nov|dec|seven days|interim|primary|general)")
_CONF_NAME = {3: "high", 2: "medium", 1: "low"}
_CONF_RANK = {"high": 3, "medium": 2, "low": 1}


def filing_type_from_report_type(report_type):
    """The form's OWN checked 'Type of Report' label -> the `filing_type` vocabulary
    cycle_totals.py reads (its SUMMARY_TYPES = summary|final|year-end|yearend|annual|
    combined; anything else is treated as an interim). The verbatim label itself is kept
    in `reporting_period`. Unchecked / unreadable -> '' (honest unknown, never guessed)."""
    s = (report_type or "").strip().lower()
    if not s:
        return ""
    if "dissolution" in s or "final" in s:
        return "final"
    if "january 31" in s or "year-end" in s or "year end" in s:
        return "year-end"
    if "summary" in s:
        return "summary"
    if _INTERIM_RE.search(s):
        return "interim"
    return ""


def tranche_confidence(cache):
    """Filing-level confidence for a vision-transcribed totals row.

    CAPPED AT `medium`: SCHEMA §6 reserves `high` for a born-digital / structured source,
    and this era is a page image read by vision (the same tier as OCR). A stated total that
    came back ILLEGIBLE (null), or that the transcriber flagged `low`, drops the filing to
    `low`. A cell the filer left BLANK ("") is not a confidence problem. No Summary Page
    found (or no cache) -> '' (not attempted / nothing to grade)."""
    if not cache or not cache.get("_meta", {}).get("summary_page_found"):
        return ""
    conf = cache.get("confidence") or {}
    ranks = []
    for f in ("total_contributions", "total_expenditures"):
        v = cache.get(f)
        if v is None:
            ranks.append(1)                       # printed but illegible
        else:
            ranks.append(min(2, _CONF_RANK.get(str(conf.get(f, "medium")).lower(), 2)))
    return _CONF_NAME[min(ranks)] if ranks else ""


def verbatim_money(printed):
    """A VERBATIM printed figure from a vision cache -> (decimal string, repaired_flag).

    Handwritten county forms use a decimal COMMA often enough to matter ("1920,00" for
    $1,920.00, seen on the 2006 Morgan amendment). Read naively that becomes $192,000 — a
    100x fabrication. So the figure is run through the SHARED, whitelisted currency repair
    (`common.repair_money_line`: final-comma-as-decimal, dot-as-thousands) before parsing;
    a 3-digit trailing group ("2,500") is still read as thousands, and anything the repair
    cannot make unambiguous stays BLANK. Repaired values are flagged so the filing's note
    records it (SCHEMA §6: every repaired value is marked)."""
    if printed is None or str(printed).strip() == "":
        return "", False
    raw = str(printed).strip()
    # repair_money_line only rewrites $-prefixed tokens, so add a `$` when the printed
    # figure has none — but never in front of a parenthesised negative ("(11,592.46)",
    # the accounting-style negative the 2022 forms print for an overdrawn balance) or a
    # value that already carries one.
    tok = raw if ("$" in raw or raw.startswith(("-", "("))) else "$" + raw
    fixed, changed = common.repair_money_line(tok)
    val = VL.vmoney(fixed)
    if val is None:
        return "", False
    return money_str(val), (changed and VL.vmoney(tok) != val)


def load_cache(index_path):
    p = os.path.join(VISION, VL.cache_key(index_path) + ".json")
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        return json.load(fh)


def _tranche_era(r, api_docids):
    """Which vision-tranche era an index.csv row belongs to, or None. MIRRORS the era test
    inside `build_totals_tranche` — the two must not drift, or a filing gets two rows.

    The 2026-08-24 wave-W2 addition: an EasyVote filing OUTSIDE the 2022 cycle whose
    `document_id` has NO rows in the advanced-search API at all (the UNGATED set — a
    school-board filing whose rows exist but are gated out, like Fife-Jepperson's, is
    excluded here too, which is exactly the owner ruling: never publish a county-office row
    for a school-board filing). Those are the 143 filings (all 2024 + all 2026 of the
    row-less residue) whose covers W2 reads. An EasyVote filing the API DOES itemize stays
    in the structured block, byte-identical."""
    if r["source"] == "clerk_legacy":
        return "clerk_legacy"
    if r["source"] == "globalassets":
        return "globalassets_2015_2021"
    if r["source"] == "easyvote" and r["path"] not in _OUT_OF_SCOPE_PATHS:
        if r["election_year"] == "2022":
            return "easyvote_2022"
        if (r["document_id"] or "").upper() not in (api_docids or set()):
            return "easyvote_2024_2026"
    return None


# Eras processed in the ORIGINAL loop order — their filing_totals rows and itemized rows
# keep their pre-W2 positions. W2-era rows (and the W2 itemized halves of easyvote_2022
# caches) are APPENDED after them, so the wave is additive in all three CSVs.
_LEGACY_ERAS = ("clerk_legacy", "easyvote_2022", "globalassets_2015_2021")
_W2_ERA = "easyvote_2024_2026"

# OUT OF SCOPE (owner ruling: school-board filings are never transcribed under a county
# label — classify by the office line INSIDE the form). These two documents sit inside the
# EasyVote row-less residue cohort with no API rows, so the era test would otherwise emit
# county FilingTotals rows for them. Both covers were read at the page on 2026-08-24 (wave
# W2, chunk_17) and read "Office Sought: Salt Lake School Board, District 2" — the audit
# (`_audits/2026-08-20-easyvote-residue/README.md` item 3) flagged the same mislabel. They
# are ledgered as out-of-scope records in the wave's records, exactly like the other five
# Fife-Jepperson filings (which carry school-board API rows and likewise get no county row).
_OUT_OF_SCOPE_PATHS = {
    "raw/easyvote/FIFE-JEPPERSON-CHARLOTTE__AE07FEF8.pdf",
    "raw/easyvote/FIFE-JEPPERSON-CHARLOTTE__D20522DA.pdf",
}


def tranche_document_ids(api_docids=None):
    """The `document_id`s `build_totals_tranche` emits a FilingTotals row for."""
    with open(os.path.join(HERE, "index.csv"), newline="") as fh:
        return {r["document_id"] for r in csv.DictReader(fh)
                if r["document_id"] and _tranche_era(r, api_docids)}


def build_totals_tranche(api_itemized=None, api_docids=None):
    """FilingTotals rows for the clerk-legacy (~2006-2015) + EasyVote-2022 eras, from the
    `vision/` caches. Returns (rows, crows, erows, stats, warnings). One row per index.csv
    filing in those eras — including filings with NO cache, which are emitted as honest
    acquired-but-not-transcribed inventory rows (all stated_* blank).

    Since wave B2 the same pass ALSO emits each cache's itemized Schedule A/B rows and fills
    that filing's itemized/reconciliation half (see the tranche header above). A cache whose
    row lists are still empty behaves exactly as before — the two tranches compose.

    `api_itemized` (2026-08-20 office-gate repair) maps `document_id` -> the RAW EasyVote
    advanced-search rows for that filing, for the EasyVote-2022 filings whose itemized data
    exists in the structured API but which are ALSO in this tranche (their stated totals live
    only on the image-only PDF). Those filings get ONE row — this one — with the vision-read
    `stated_*` untouched and the itemized half filled from the API. A filing that already has
    a VISION itemization keeps it (the transcribed, geometry-anchored layer wins; the API set
    is not merged on top) and says so in `notes`."""
    with open(os.path.join(HERE, "index.csv"), newline="") as fh:
        idx = list(csv.DictReader(fh))
    aliases = load_aliases(os.path.join(HERE, "donor_aliases.csv"))
    rows, all_c, all_e, warnings, stats = [], [], [], [], Counter()
    # Wave W2 (2026-08-24): ordering discipline. FilingTotals rows for the LEGACY eras keep
    # their pre-W2 positions; the new `easyvote_2024_2026` rows APPEND at the end. ITEMIZED
    # rows from any EasyVote vision cache (the W2-itemized 2022 row-less filings AND the new
    # era) likewise APPEND after the pre-existing vision blocks — inserting the 2022 W2 rows
    # between clerk-legacy and globalassets would shift every globalassets row and break the
    # frozen-block proof. The 26 API-routed 2022 filings keep their historical position
    # (the `elif api:` branch below extends all_c/all_e directly, as before).
    w2_crows, w2_erows = [], []
    ordered = []
    for r in idx:
        era = _tranche_era(r, api_docids)
        if era:
            ordered.append((r, era))
    ordered.sort(key=lambda t: 0 if t[1] in _LEGACY_ERAS else 1)   # stable within groups
    for r, era in ordered:
        stats[era] += 1
        cache = load_cache(r["path"])
        meta = (cache or {}).get("_meta", {})
        cover = (cache or {}).get("cover", {}) or {}
        notes = []

        # --- office: the form's own "Office Sought" outranks the clerk listing-page header,
        # but only where the listing label did not already normalize to a county office.
        office = r["office"]
        if office not in BL.COUNTY_OFFICE_SET and cover.get("office_sought"):
            o2, _ = BL.normalize_office(cover["office_sought"])
            if o2 in BL.COUNTY_OFFICE_SET:
                notes.append(f"office read from the form's own 'Office Sought' "
                             f"({cover['office_sought']!r}); clerk listing said {office!r}")
                office = o2
                stats["office_from_form"] += 1

        # --- election_year / filing_date: FILL ONLY WHERE index.csv is blank (never
        # overwrite an acquisition-time value). Source = the form's own signature date /
        # title year, then the same EVEN-year proxy the rest of this module uses.
        eyear, fdate = r["election_year"], r["date"]
        form_iso = VL.vdate(cover.get("report_date") or "")
        if not fdate and form_iso:
            fdate = form_iso
            stats["filing_date_from_form"] += 1
        if not eyear:
            ey = (BL.election_year_from_date(form_iso)
                  or BL.election_year_from_date(cover.get("form_year") or ""))
            if ey:
                eyear = ey
                notes.append("election_year absent from the clerk listing; derived from the "
                             "form's own date/title year via the EVEN-year proxy")
                stats["election_year_from_form"] += 1

        # --- reporting_period: the form's checked label wins; keep the listing label when
        # the two disagree (a label is evidence, not truth).
        rp_form = (cover.get("report_type") or "").strip() if cover.get("report_type") else ""
        rp = rp_form or r["reporting_period"]
        if rp_form and r["reporting_period"] and rp_form.lower() not in r["reporting_period"].lower():
            notes.append(f"clerk listing label: {r['reporting_period']}")
        ftype = filing_type_from_report_type(rp_form)

        if str(cover.get("is_amendment") or "").strip().lower().startswith("y"):
            of = (cover.get("amendment_of") or "").strip()
            notes.append("the form marks this an AMENDMENT" + (f" of {of}" if of else ""))
            stats["amendment"] += 1

        # --- stated figures (verbatim printed -> decimal string; illegible stays blank)
        repaired = []

        def m(field):
            if not cache:
                return ""
            v, fixed = verbatim_money(cache.get(field))
            if fixed:
                repaired.append(f"{field}={cache.get(field)!r}")
            return v
        s_c, s_e = m("total_contributions"), m("total_expenditures")
        s_b, s_end = m("beginning_balance"), m("ending_balance")
        if repaired:
            notes.append("whitelisted currency repair applied to the verbatim printed figure "
                         "(decimal-comma / dot-thousands): " + ", ".join(repaired))
            stats["currency_repair"] += 1

        if cache is None:
            notes.append("ACQUIRED, NOT TRANSCRIBED — no vision cache for this filing")
            stats["no_cache"] += 1
        elif not meta.get("summary_page_found"):
            notes.append("no Summary Page found in this document — stated totals unavailable")
            stats["no_summary_page"] += 1
        else:
            stats["transcribed"] += 1
            for field, label in (("total_contributions", "Total Contributions Received"),
                                 ("total_expenditures", "Total Expenditures Made")):
                if cache.get(field) is None:
                    notes.append(f"{label} printed but ILLEGIBLE — left blank, never guessed")
                    stats["illegible_total"] += 1
            agg = cache.get("aggregate") or {}
            colb = [f"{k}={v}" for k, v in (("contrib", agg.get("total_contributions_to_date")),
                                            ("expend", agg.get("total_expenditures_to_date")))
                    if v]
            if colb:
                notes.append("Column B sum-to-date as printed: " + ", ".join(colb))
        if cache and cache.get("_meta", {}).get("notes"):
            notes.append("transcriber: " + str(cache["_meta"]["notes"]))

        # --- itemized half (wave B2). Absent cache / empty lists => unchanged totals-only row.
        it_meta = ((cache or {}).get("_meta") or {}).get("itemized") or {}
        api = (api_itemized or {}).get(r["document_id"] or "")
        crows, erows, sides, it = ([], [], {}, {})
        if it_meta:
            # SCHEMA 2/3: an itemized ROW carries `candidate` / `election_year` / `filing_date`
            # VERBATIM FROM index.csv, not re-derived. The form-derived election_year and
            # filing_date this tranche computes are a FILING-level enrichment and stay on the
            # FilingTotals row (with the note that says where they came from). Pushing the
            # derived year onto the rows broke referential integrity for the seven Corroon
            # legacy filings whose index `election_year` is blank — validate_finance checks
            # every row's `(candidate, election_year)` against index.csv, and rightly failed.
            crows, erows, sides, it = itemized_rows_for(
                cache, r, office, r["seat"], r["election_year"], r["date"], rp, aliases,
                "vision-itemized/" + (it_meta.get("wave") or "claude-opus-5"))

        if it_meta:
            if era == "clerk_legacy":
                # The 496 clerk-legacy rows carry this EXACT historical wording — it is a
                # close-out gate that they stay byte-identical.
                item_head = ("; itemized Schedule A/B rows VISION-TRANSCRIBED "
                             "(2026-08-02 wave B2)")
            else:
                # Every other era reads the wave stamp from the cache's own `_meta` — the
                # eras were transcribed by DIFFERENT waves (W1 globalassets; W2 EasyVote
                # residue 2022 + 2024/2026), and the stamp is published provenance.
                item_head = ("; itemized Schedule A/B rows VISION-TRANSCRIBED ("
                             + (it_meta.get("wave") or "2026-08-02 wave B2") + ")")
        elif api:
            item_head = ("; itemized rows from the EasyVote STRUCTURED API "
                         "(advancedsearch, 2026-08-20 office-gate repair) — the stated totals "
                         "above stay the vision read of this filing's own Summary Page")
        else:
            item_head = "; itemized layer NOT built for this filing -> reconciliation unknown"
        tranche_stamp = ("Read-tool, $0 API; 2026-08-23 wave W1 (2015-2021 paper slice)"
                         if era == "globalassets_2015_2021"
                         else "ReadMediaFile vision (Kimi K3); 2026-08-24 wave W2 "
                              "(EasyVote residue)"
                         if era == _W2_ERA
                         else "Read-tool, $0 API; 2026-08-01 totals tranche")
        head = ("stated totals VISION-TRANSCRIBED from the filing's own cover + Summary Page "
                f"({tranche_stamp})"
                + item_head
                + f" [{era}]")
        ft = FilingTotals(
            candidate=r["candidate"], office=office, election_year=eyear,
            filing_date=fdate, reporting_period=rp, filing_type=ftype,
            stated_total_contributions=s_c, stated_total_expenditures=s_e,
            stated_beginning_balance=s_b, stated_ending_balance=s_end,
            itemized_contrib_sum="", itemized_expend_sum="",
            reconciles_contrib="", reconciles_expend="",
            recon_delta_contrib="", recon_delta_expend="", self_funded_amount="",
            n_contrib_rows="0", n_expend_rows="0",
            source_filing=r["path"],
            document_id=r["document_id"] or VL.cache_key(r["path"]),
            extraction_confidence=tranche_confidence(cache),
            notes="")
        if it_meta:
            warnings.extend(apply_itemized(ft, crows, erows, sides, it, notes))
            if era in ("clerk_legacy", "globalassets_2015_2021"):
                all_c.extend(crows)          # pre-W2 positions, frozen-block proof holds
                all_e.extend(erows)
            else:
                w2_crows.extend(crows)       # EasyVote vision rows are ALL wave-W2 additions:
                w2_erows.extend(erows)       # appended after every pre-existing block
            stats["itemized_filings"] += 1
            stats["itemized_contrib_rows"] += len(crows)
            stats["itemized_expend_rows"] += len(erows)
            for side in ("contributions", "expenditures"):
                stats["side_" + (sides.get(side) or "none")] += 1
            if api:
                notes.append("this filing ALSO has itemized rows in the EasyVote structured "
                             "API; the VISION transcription above is what is published (the "
                             "two are not merged — that would double-count the same schedule)")
                stats["api_itemized_yielded_to_vision"] += 1
        elif api:
            acrows, aerows = api_itemized_rows_for(api, r, office, r["seat"], rp, aliases)
            apply_api_itemized(ft, acrows, aerows, notes)
            all_c.extend(acrows)
            all_e.extend(aerows)
            stats["api_itemized_filings"] += 1
            stats["api_itemized_contrib_rows"] += len(acrows)
            stats["api_itemized_expend_rows"] += len(aerows)
        ft.notes = "; ".join([head] + notes)
        rows.append(ft)
    all_c.extend(w2_crows)
    all_e.extend(w2_erows)
    return rows, all_c, all_e, stats, warnings


# =====================================================================================
# VISION ITEMIZED TRANCHE (2026-08-02, wave B2) — Schedule A/B donor + vendor lines
# =====================================================================================
# The totals tranche above answers "how much"; this one answers "FROM WHOM". Same caches,
# same discipline, one more layer: `vision/<key>.json` now carries populated
# `contributions` / `expenditures` lists (materialized by `make_itemized_caches.py`, which
# is also where geometry becomes `pct:` and the wave stamp is applied).
#
# Discipline (SCHEMA.md 2/3/4/6 + the cardinal rules):
#   * A WITHHELD side emits ZERO rows and leaves `itemized_*` / `reconciles_*` BLANK. A
#     withheld side is NOT a zero: "we did not finish reading it" and "the filer spent
#     nothing" are different facts and the CSV must not conflate them.
#   * `stated_*` is NEVER recomputed from the rows. Where both exist, the delta is reported
#     (`recon_delta_* = itemized - stated`, signed) and BOTH figures stay. A non-zero delta
#     is the FILER's arithmetic, retained verbatim and named in `notes` — three of the
#     pilot's 24 filings carry one (McAdams -0.02, Allen +89.00, Jensen +600.00), each
#     traced to an internal inconsistency printed on the filing itself.
#   * The reconciliation VERDICT is recomputed here mechanically (|delta| <= $0.01) and
#     cross-checked against the transcriber's own recorded verdict; a disagreement is
#     printed loudly at build time rather than silently resolved.
#   * In-kind rows COUNT toward the printed total on this form (verified at the page:
#     Noyce 2012 prints 12 in-kind $35.00 rows + $100.00 = the printed $520.00), so
#     reconciliation sums ALL rows — this family is not one of the cash-only families.
#   * `is_incremental=True` is STRUCTURAL here, not assumed: the form's Column A is headed
#     "Total this Period" and Schedule A/B itemize that period. (Two filers put cumulative
#     figures in Column A — CLAUDE.md finding 12 — and those filings say so in `notes`.)

def _money(v):
    """A verbatim transcribed amount -> float, via the SAME whitelisted repair the totals
    tranche uses. Unparseable stays None (blank + needs_review), never guessed."""
    s, _ = verbatim_money(v)
    return float(s) if s else None


def _occupation(row):
    """The published `donor_occupation` for one transcribed contribution row.

    The county's own Schedule A prints ONE cell headed `Occupation/Employer`, and filers fill
    it as one string ("POLICY ADVISOR / SL COUNTY" written on two lines of the same cell). But
    three filings in this slice attach the filer's own spreadsheet, and that spreadsheet SPLITS
    the field into two columns. Both halves are kept verbatim in the cache; here they compose
    back into the single field the form defines, joined with " / " — the same separator the
    handwritten cells already use. Nothing is invented: if only one half exists, only that half
    is published, and if neither does the value is blank (with the cache row's note recording
    WHY it is blank — no such column, filer left it empty, or redacted at source)."""
    occ = (row.get("occupation") or "").strip()
    emp = (row.get("employer") or "").strip()
    if occ and emp:
        return f"{occ} / {emp}"
    return occ or emp


def itemized_rows_for(cache, r, office, seat, eyear, fdate, rp, aliases, method):
    """(ContribRow[], ExpendRow[], stats) for ONE filing's vision cache."""
    it = (cache.get("_meta") or {}).get("itemized") or {}
    sides = it.get("sides") or {}
    crows, erows = [], []
    for i, row in enumerate(cache.get("contributions") or [], 1):
        amt = _money(row.get("amount"))
        donor = (row.get("donor_raw") or "").strip()
        cr = ContribRow(
            candidate=r["candidate"], office=office, seat=seat, election_year=eyear,
            filing_date=fdate, reporting_period=rp,
            date=row.get("date", ""), donor_raw=donor,
            donor_city=row.get("donor_city", ""), donor_state=row.get("donor_state", ""),
            donor_district="",
            amount=(money_str(amt) if amt is not None else ""),
            in_kind=("True" if row.get("in_kind") else "False"),
            is_incremental="True",
            source_filing=r["path"], document_id=r["document_id"] or VL.cache_key(r["path"]),
            line_no=str(row.get("line_no", i)),
            extraction_confidence=(row.get("confidence") or "medium"),
            extract_method=method,
            needs_review=("1" if (amt is None or not donor or row.get("needs_review")) else "0"),
            geometry=row.get("geometry", ""),
            # Occupation/Employer, VERBATIM as the filer wrote it (owner decision
            # 2026-08-20). Blank means one of three DIFFERENT things, and the row's note in
            # the cache says which: the form has no such column (every pre-2015 filing), the
            # column exists and the filer left it empty, or the county's redaction bar covers
            # it. Never inferred from the donor name and never normalized.
            donor_occupation=_occupation(row))
        normalize_contrib(cr, r["candidate"], aliases)
        crows.append(cr)
    for i, row in enumerate(cache.get("expenditures") or [], 1):
        amt = _money(row.get("amount"))
        er = ExpendRow(
            candidate=r["candidate"], office=office, seat=seat, election_year=eyear,
            filing_date=fdate, reporting_period=rp,
            date=row.get("date", ""), vendor_raw=(row.get("vendor_raw") or "").strip(),
            purpose=row.get("purpose", ""),
            amount=(money_str(amt) if amt is not None else ""),
            in_kind=("True" if row.get("in_kind") else "False"),
            is_incremental="True",
            source_filing=r["path"], document_id=r["document_id"] or VL.cache_key(r["path"]),
            line_no=str(row.get("line_no", i)),
            extraction_confidence=(row.get("confidence") or "medium"),
            extract_method=method,
            needs_review=("1" if (amt is None or row.get("needs_review")) else "0"),
            geometry=row.get("geometry", ""))
        normalize_vendor(er)
        erows.append(er)
    return crows, erows, sides, it


def apply_itemized(ft, crows, erows, sides, it, notes):
    """Fill the itemized/reconciliation half of a vision FilingTotals row, in place.

    Returns a list of build-time WARNINGS (verdict disagreements), never raising: a
    disagreement between our arithmetic and the transcriber's recorded verdict is a thing
    to SHOW, not to resolve silently."""
    warn = []
    recon = {k: ({"result": v} if isinstance(v, str) else (v or {}))
             for k, v in (it.get("recon") or {}).items()}   # tolerate a bare-string verdict
    self_funded = sum(float(c.amount) for c in crows
                      if c.amount and c.donor_type in ("candidate-self", "loan"))
    if self_funded:
        ft.self_funded_amount = money_str(self_funded)
    for side, rows, stated_attr, sum_attr, rec_attr, delta_attr, n_attr in (
            ("contributions", crows, "stated_total_contributions", "itemized_contrib_sum",
             "reconciles_contrib", "recon_delta_contrib", "n_contrib_rows"),
            ("expenditures", erows, "stated_total_expenditures", "itemized_expend_sum",
             "reconciles_expend", "recon_delta_expend", "n_expend_rows")):
        state = sides.get(side, "")
        if state == "withheld":
            reason = (it.get("withheld_reason") or {}).get(side, "reason not recorded")
            notes.append(f"{side} side WITHHELD (no rows emitted, no sum claimed): {reason}")
            continue
        if state != "transcribed":
            continue
        total = sum(float(x.amount) for x in rows if x.amount)
        setattr(ft, n_attr, str(len(rows)))
        blanks = sum(1 for x in rows if not x.amount)
        if blanks:
            notes.append(f"{blanks} {side} row(s) have an ILLEGIBLE amount — left blank and "
                         f"EXCLUDED from the itemized sum, so this side is a floor")
        stated = getattr(ft, stated_attr)
        if not stated:
            setattr(ft, sum_attr, money_str(total))
            notes.append(f"{side}: itemized rows transcribed but the form states no total for "
                         f"this side — reconciliation UNKNOWN, never assumed")
            continue

        # ---- THE RECONCILIATION-BASIS RULE (owner-ratified 2026-08-17), enforced in code.
        # A wave-W1 record NAMES the printed figure it reconciled against (`recon.<side>.basis`)
        # and carries that figure in `recon.<side>.schedule_total`. Where that anchor is NOT the
        # Summary line this module publishes as `stated_*`, the two figures HAVE DIFFERENT
        # SCOPES and subtracting one from the other is a basis error, not a delta.
        #
        # Snelgrove April-2016 is the proof and the reason this branch exists. His Schedule B
        # footer prints 3,161.02 (5 rows, in-kind INCLUDED — the schedule's own SUBTOTAL and
        # TOTAL both equal it) while Summary line 2 prints 501.02 (the 4 cash rows, in-kind
        # EXCLUDED). Both are correct; they measure different things, and the difference is
        # exactly the one $2,660.00 in-kind row. Comparing the transcribed rows to `stated_*`
        # would publish `reconciles_expend=False` with a **manufactured +2,660.00 delta** on a
        # filing that closes exactly against both of its own printed figures.
        #
        # So: publish the itemized sum, publish the stated figure verbatim, and assert NO
        # VERDICT — `reconciles_*` and `recon_delta_*` stay BLANK (unknown). This is the same
        # answer utah's `cumulative-exact` sides get, for the same reason, and it needs no
        # weakening of validate_finance.py (a blank verdict is always legal). Legacy wave-B2
        # caches carry no `basis` key at all and are untouched by this branch, which is what
        # keeps the 496 clerk-legacy filings byte-identical.
        # The trigger is a MEASURED disagreement, not the label. A transcriber may reconcile
        # against the schedule's grand total and that total may simply EQUAL the Summary figure
        # (most filings: one scope, two printed copies of it). Blanking the verdict there would
        # discard a real reconciliation — it did, on 3 of the first 7 rows this branch caught,
        # where stated and itemized agreed to the cent. So the scope-split treatment applies
        # ONLY where the declared anchor and the published stated figure actually differ.
        # THREE conditions, and the third is the one that keeps this honest. A non-summary
        # anchor that DISAGREES with the stated figure has two possible causes, and they get
        # opposite treatments:
        #
        #   * DIFFERENT SCOPES (transcriber verdict `exact`) — the rows match the anchor
        #     exactly, and the anchor differs from `stated_*` because the two printed figures
        #     measure different things (Snelgrove: in-kind included vs excluded). No verdict
        #     can be asserted; blank it. This branch.
        #   * SAME SCOPE, FILER DISAGREES WITH HIMSELF (verdict `delta`) — Evershed's 20 rows
        #     equal the attachment total AND the county stub total AND Summary line 6, while
        #     Summary line 2 prints $14.05 less. Nothing about scope explains it; it is the
        #     filer's own arithmetic inside his own Summary Page. That is a REAL delta and the
        #     repo's rule is to publish it verbatim with the trace — so it falls through to the
        #     ordinary path below.
        #
        # The transcriber, who had the page in hand, records which it is. The build does not
        # guess: absent an explicit `exact`, the ordinary stated-total comparison applies.
        # The anchor is compared to THE LINE THIS MODULE PUBLISHES for this side — line 1 for
        # contributions, line 2 for expenditures — because that is what `stated_*` holds. Any
        # OTHER declared basis means the rows were reconciled against a different figure.
        #
        # ⚠ `summary-line-4` / `summary-line-6` ARE such a case, and missing that would have
        # been catastrophic. DeBry's 2021 year-end (chunk 24) runs the inversion one level
        # deeper than his earlier filings: the schedule grand total is cumulative AND Summary
        # line 1 Column A is *also* cumulative (it prints the PRIOR cycle total, 64,893.50,
        # byte-identical to his 2018 year-end's schedule grand total). The period figure exists
        # ONLY at lines 4 and 6 — 7,350.00 / 80.00 — which is exactly what the page subtotals
        # match. The transcriber reconciled against `summary-line-4`, deliberately left
        # `schedule_total` EMPTY so no wrong-scope anchor could be adopted, and flagged it.
        # An earlier version of this branch required `anchor is not None`, so it fell through
        # to the ordinary path and would have published a **-57,543.50 delta** on a side that
        # closes exactly — undoing the transcriber's care with a mechanical comparison.
        #
        # So: an absent anchor is not a reason to compare against `stated_*`. It is a reason
        # NOT to, because the record has already said the rows do not answer to that figure.
        # TWO independent tests, either sufficient. Both ask the same question — *do the rows
        # answer to the figure this module publishes as `stated_*`?* — but they detect the two
        # different ways a record can say no.
        #
        # (a) THE RECORD ANCHORED ON A DIFFERENT FIGURE ENTIRELY. `recon.<side>.stated` is the
        #     figure the transcriber reconciled against; `stated_*` is Summary Column A. When
        #     they differ, the transcriber's verdict is about something else. Evershed's
        #     2018 year-end is the case: his attachment totals equal Summary **Column B**
        #     (cumulative, 75,405.83 / 33,613.31) while Column A is the period (29,053.68 /
        #     26,175.09), and his own note says the schedules run from 8/2017. His contributions
        #     verdict is `delta` (a 2-cent spreadsheet slip against HIS anchor), so a
        #     verdict-only test would have fallen through to the ordinary path and published a
        #     **+46,352.17** delta — the exact fabrication this whole branch exists to prevent.
        #
        # (b) THE RECORD ANCHORED ON A DIFFERENT *LINE* while quoting the same `stated`.
        #     Snelgrove: `recon.stated` is 501.02 (= ours) but the rows were gated on the
        #     schedule's own 3,161.02, which includes the in-kind row Summary line 2 excludes.
        #
        # And the case that must NOT trip either test — Evershed's OTHER filing, where the
        # attachment total equals Summary line 6 AND the county stub total, and only line 2
        # disagrees by $14.05. Same scope, filer's own arithmetic: `recon.stated` equals ours
        # and the verdict is `delta`, so it falls through and the real delta is published.
        published_line = ("summary-line-1" if side == "contributions" else "summary-line-2")
        basis = (recon.get(side) or {}).get("basis", "")
        verdict = (recon.get(side) or {}).get("result", "")
        anchor = _money((recon.get(side) or {}).get("schedule_total"))
        rec_stated = _money((recon.get(side) or {}).get("stated"))
        anchored_elsewhere = (rec_stated is not None
                              and abs(rec_stated - float(stated)) > 0.01)
        different_line = (basis and basis != published_line and verdict == "exact"
                          and (anchor is None or abs(anchor - float(stated)) > 0.01))
        scope_split = anchored_elsewhere or different_line
        if scope_split:
            setattr(ft, sum_attr, money_str(total))
            gap = (round(anchor - float(stated), 2)
                   if anchor is not None else None)
            notes.append(
                f"SCHEDULE-SCOPE SPLIT ({side}) — "
                f"{side} RECONCILIATION BASIS = {basis!r}: the rows were reconciled against "
                f"the filing's own printed schedule total"
                + (f" ({money_str(anchor)})" if anchor is not None else "")
                + (f", which is a DIFFERENT SCOPE from the Summary-Page figure this module "
                   f"publishes as stated ({stated})" if anchor is not None else
                   f" rather than against the Summary-Page figure this module publishes as "
                   f"stated ({stated}); the record deliberately states NO schedule figure here, "
                   f"so no anchor of that scope exists to compare")
                + (f" — the two differ by {money_str(gap)}" if gap else "")
                + ". Both printed figures are retained verbatim and NEITHER is recomputed; "
                f"`reconciles_{side[:6]}` and `recon_delta_{side[:6]}` are left BLANK because "
                f"comparing figures of different scope is a basis error, not a delta"
                + (f". The record reconciled against {money_str(rec_stated)}"
                   if anchored_elsewhere else "")
                + (f"; the transcriber's own verdict against THAT figure was {verdict!r}"
                   if anchored_elsewhere and verdict else "")
                + (f". Transcriber: {(recon.get(side) or {}).get('detail', '')}"
                   if (recon.get(side) or {}).get("detail") else ""))
            continue
        # SIGN CONVENTION. A few filers attach a register/QuickBooks export that prints every
        # amount NEGATIVE — accounting parentheses ("($745.00)") or a leading minus. SCHEMA
        # reads those as negative and the rows keep the printed sign VERBATIM, so a signed sum
        # lands at exactly -1x the form's printed (positive) total. Comparing signed against
        # stated there manufactures a mismatch of twice the total out of a filing that is
        # correct to the cent. So: when a side's amounts are uniformly non-positive AND their
        # MAGNITUDE reconciles, reconcile on magnitude and say so loudly. Never applied to a
        # mixed-sign side (a genuine refund/adjustment line stays a signed outlier).
        amts = [float(x.amount) for x in rows if x.amount]
        signflip = (bool(amts) and all(a <= 0 for a in amts) and any(a < 0 for a in amts)
                    and abs(abs(total) - float(stated)) <= 0.01)
        if signflip:
            notes.append(f"{side}: this filing prints EVERY amount of this side as a NEGATIVE "
                         f"(accounting parentheses / register export). Rows keep the printed "
                         f"sign verbatim, so `itemized_{side[:6]}_sum` is negative; "
                         f"reconciliation is on MAGNITUDE — |{money_str(total)}| = {stated}. A "
                         f"consumer summing this side must take the absolute value")
            total = -total
        # `itemized_*` is written in the SAME orientation as `stated_*` so the pair is
        # comparable and `reconciles_*` is self-consistent (validate_finance checks exactly
        # that). The individual rows keep the printed negative VERBATIM; only this aggregate
        # is stated positive, and the note above says so.
        setattr(ft, sum_attr, money_str(total))
        delta = round(total - float(stated), 2)
        setattr(ft, delta_attr, money_str(delta))
        setattr(ft, rec_attr, "True" if abs(delta) <= 0.01 else "False")
        said = (recon.get(side) or {}).get("result", "")
        mine = "exact" if abs(delta) <= 0.01 else "delta"
        if said and said != mine:
            warn.append(f"{ft.source_filing} {side}: transcriber said {said!r}, "
                        f"arithmetic says {mine} (delta {money_str(delta)})")
        if abs(delta) > 0.01:
            detail = (recon.get(side) or {}).get("detail", "")
            notes.append(f"{side} RECONCILIATION DELTA {money_str(delta)} (itemized {money_str(total)} "
                         f"vs the form's printed {stated}) — the FILER's own arithmetic, retained "
                         f"verbatim, never adjusted" + (f": {detail}" if detail else ""))
    if it.get("page_subtotal_gates"):
        notes.append("page-subtotal gate: " + str(it["page_subtotal_gates"]))
    if it.get("notes"):
        notes.append("itemizer: " + str(it["notes"]))
    return warn


# =====================================================================================
# API ITEMIZATION ATTACHED TO A VISION TOTALS ROW (2026-08-20 office-gate repair)
# =====================================================================================
# The EasyVote-2022 filings are BOTH in the vision totals tranche (their printed totals live
# only on an image-only PDF) and in the structured advanced-search API (their itemized rows
# are born-digital). Before the office-gate repair the API half was silently dropped for
# every filing whose OfficeGuid is absent from `offices.json`, so these filings carried
# stated totals with a blank itemized half. Now the two halves meet on ONE row: `stated_*`
# stays the verbatim vision read, the itemized half comes from the API, and the delta between
# them is reported — never nudged.

def api_itemized_rows_for(api, r, office, seat, rp, aliases):
    """(ContribRow[], ExpendRow[]) for ONE filing's RAW EasyVote advanced-search rows.

    SCHEMA 2/3 (and the wave-B2 precedent in `itemized_rows_for`): an itemized row carries
    `candidate` / `election_year` / `filing_date` VERBATIM FROM index.csv — validate_finance
    checks every row's `(candidate, election_year)` against the manifest — so this builds
    those from `r`, not from the API's own filer metadata. Amounts, dates and party names are
    the API's, verbatim. PRIVACY: the advanced-search payload carries NO address field of any
    kind (verified 2026-08-20 over both files: no street/city/state/zip key exists), so
    donor_city / donor_state / donor_district stay blank — an honest absence, not a redaction.
    """
    crows, erows = [], []
    for i, row in enumerate(sorted(api.get("c", []),
                                   key=lambda x: (x.get("ContributionDate") or "",
                                                  x.get("ContributionAmount") or 0)), 1):
        donor = BL.contributor_raw(row)
        amt = row.get("ContributionAmount")
        cr = ContribRow(candidate=r["candidate"], office=office, seat=seat,
                        election_year=r["election_year"], filing_date=r["date"],
                        reporting_period=rp,
                        date=(row.get("ContributionDate") or "")[:10], donor_raw=donor,
                        donor_city="", donor_state="", donor_district="",
                        amount=money_str(amt), in_kind="False", is_incremental="True",
                        source_filing=r["path"], document_id=r["document_id"],
                        line_no=str(i), extraction_confidence="high",
                        extract_method="easyvote_api/json",
                        needs_review=("1" if (amt is None or not donor) else "0"))
        normalize_contrib(cr, r["candidate"], aliases)
        crows.append(cr)
    for i, row in enumerate(sorted(api.get("e", []),
                                   key=lambda x: (x.get("DistributionDate") or "",
                                                  x.get("DistributionAmount") or 0)), 1):
        amt = row.get("DistributionAmount")
        er = ExpendRow(candidate=r["candidate"], office=office, seat=seat,
                       election_year=r["election_year"], filing_date=r["date"],
                       reporting_period=rp,
                       date=(row.get("DistributionDate") or "")[:10],
                       vendor_raw=BL.payee_raw(row), purpose="",
                       amount=money_str(amt), in_kind="False", is_incremental="True",
                       source_filing=r["path"], document_id=r["document_id"],
                       line_no=str(i), extraction_confidence="high",
                       extract_method="easyvote_api/json",
                       needs_review=("1" if amt is None else "0"))
        normalize_vendor(er)
        erows.append(er)
    return crows, erows


def apply_api_itemized(ft, crows, erows, notes):
    """Fill the itemized/reconciliation half of a VISION FilingTotals row from API rows.

    Same discipline as `apply_itemized`: `stated_*` is NEVER recomputed from the rows; where
    both figures exist the signed delta is published (`recon_delta_* = itemized - stated`) and
    BOTH stay; |delta| <= $0.01 is the verdict rule. One extra guard this path needs and the
    vision path does not: the vision cache states per side whether it was `transcribed` or
    `withheld`, but the API just returns rows. Zero rows on a side is only read as a real
    zero when the form ITSELF states $0.00 for that side; otherwise the side is left BLANK
    (unknown), because "the feed returned nothing" and "the filer raised nothing" are
    different facts."""
    self_funded = sum(float(c.amount) for c in crows
                      if c.amount and c.donor_type in ("candidate-self", "loan"))
    if self_funded:
        ft.self_funded_amount = money_str(self_funded)
    for side, rows, stated_attr, sum_attr, rec_attr, delta_attr, n_attr in (
            ("contributions", crows, "stated_total_contributions", "itemized_contrib_sum",
             "reconciles_contrib", "recon_delta_contrib", "n_contrib_rows"),
            ("expenditures", erows, "stated_total_expenditures", "itemized_expend_sum",
             "reconciles_expend", "recon_delta_expend", "n_expend_rows")):
        stated = getattr(ft, stated_attr)
        if not rows and not (stated and abs(float(stated)) <= 0.01):
            notes.append(f"{side}: the structured API returns NO rows for this filing while "
                         f"the form states {stated or 'no total'} — itemization for this side "
                         f"left BLANK (unknown), never read as a zero")
            continue
        setattr(ft, n_attr, str(len(rows)))
        blanks = sum(1 for x in rows if not x.amount)
        if blanks:
            notes.append(f"{blanks} {side} row(s) carry no amount in the API — left blank and "
                         f"EXCLUDED from the itemized sum, so this side is a floor")
        total = sum(float(x.amount) for x in rows if x.amount)
        setattr(ft, sum_attr, money_str(total))
        if not stated:
            notes.append(f"{side}: itemized rows from the structured API but the form states "
                         f"no total for this side — reconciliation UNKNOWN, never assumed")
            continue
        delta = round(total - float(stated), 2) + 0.0
        setattr(ft, delta_attr, money_str(delta))
        setattr(ft, rec_attr, "True" if abs(delta) <= 0.01 else "False")
        if abs(delta) > 0.01:
            notes.append(f"{side} RECONCILIATION DELTA {money_str(delta)} (itemized "
                         f"{money_str(total)} from the EasyVote structured API vs the form's "
                         f"printed {stated}) — published VERBATIM, never adjusted; the two are "
                         f"independent readings of the same filing")


def build():
    offices = {o["OfficeId"].upper(): o["OfficeName"] for o in load_json("offices.json")}
    docsearch = load_json("documentsearch.json")
    contribs = load_json("advancedsearch_contributions.json")
    distribs = load_json("advancedsearch_distributions.json")

    # DocumentFilingId (base GUID) -> filer/filing metadata from documentsearch
    doc_meta = {}
    filer_path = {}
    # map documentid -> download path via the easyvote fetch log
    filer_officename = {}
    for line in open(os.path.join(HERE, "raw", "easyvote", "_fetch_log.jsonl")):
        r = json.loads(line)
        if r.get("documentid") and not r.get("error"):
            filer_path[r["documentid"].upper()] = r["path"]
            if r.get("officename"):
                filer_officename[r["documentid"].upper()] = r["officename"]
    for f in docsearch:
        for d in f["documents"]:
            did = (d.get("documentid") or "").upper()
            if not did:
                continue
            doc_meta[did] = {
                "displayname": f["displayname"], "officename": f["officename"],
                "filertype": f["filertype"], "datesubmitted": d.get("datesubmitted"),
                "documentname": d.get("documentname"), "documenttype": d.get("documenttype"),
            }

    aliases = load_aliases(os.path.join(HERE, "donor_aliases.csv"))

    def base_fid(r):
        return (r.get("DocumentFilingId") or "").replace("_Redacted", "").upper()

    # OFFICE RESOLUTION, TWO-STEP (2026-08-20 repair).
    # `offices.json` is a snapshot of CURRENTLY-ACTIVE offices, NOT a complete historical
    # GUID table: 12 distinct OfficeGuids that appear on itemized rows are absent from it.
    # The old gate looked the GUID up, got "", and silently DROPPED the row — taking 1,228
    # provably-county contributions and 479 expenditures with it (Clerk, Sheriff, Auditor,
    # Recorder, Surveyor and four Council seats).
    # So: the ROW's own OfficeGuid wins whenever it resolves, and only when it does NOT does
    # the filing's own metadata (`documentsearch.json`'s filer-level `officename`, mirrored in
    # raw/easyvote/_fetch_log.jsonl) stand in. That ORDER matters and is evidence-based:
    # GOTCHAS' "portal labels lie" holds here too — Charlotte Fife-Jepperson's filer record
    # says "Salt Lake County Council District 2", but her filing's own cover reads
    # "Office Sought: Salt Lake School Board, District 2" (verified at the page, 2026-08-20),
    # and her rows' OfficeGuid correctly resolves to 'Salt Lake School Board'. Trusting the
    # filer label over the GUID would have pulled 73 school-board contributions into a county
    # dataset. GUID-first also makes the change a strict SUPERSET: every row the old gate
    # admitted is admitted on exactly the same string.
    def officename_for(r):
        return (offices.get((r.get("OfficeGuid") or "").upper())
                or doc_meta.get(base_fid(r), {}).get("officename")
                or filer_officename.get(base_fid(r), ""))

    def county_office(r):
        return BL.is_county_officename(officename_for(r))

    def meta_for(fid):
        return doc_meta.get(fid)

    crows, erows = [], []
    # group itemized by filing for line_no + totals
    by_filing_c = defaultdict(list)
    by_filing_e = defaultdict(list)
    for r in contribs:
        if county_office(r):
            by_filing_c[base_fid(r)].append(r)
    for r in distribs:
        if county_office(r):
            by_filing_e[base_fid(r)].append(r)

    all_fids = set(by_filing_c) | set(by_filing_e)
    filing_rows = []
    skipped_no_meta = []

    def filing_common(fid, sample):
        m = meta_for(fid)
        if m:
            cand = m["displayname"]
            office_raw = m["officename"]
            fdate = BL.easyvote_iso(m["datesubmitted"])
            period = m.get("documentname") or ""
        else:
            # itemized-only filing (no documentsearch doc) -> fall back to itemized name
            cand = sample.get("displayrecipientname") or sample.get("displaycandidatename") or ""
            office_raw = officename_for(sample)
            fdate = ""
            period = ""
            skipped_no_meta.append(fid)
        office, seat = BL.normalize_office(office_raw)
        eyear = BL.election_year_from_date(fdate) or BL.election_year_from_date(
            sample.get("ContributionDate") or sample.get("DistributionDate"))
        path = filer_path.get(fid, "")
        return cand, office, seat, eyear, fdate, period, path

    skipped_no_pdf = []
    # A filing whose stated totals come from the VISION tranche (clerk-legacy + EasyVote-2022:
    # image-only PDFs) must end up with exactly ONE filing_totals row. Its API itemization is
    # handed to that tranche instead of being emitted as a second, stated-total-less row.
    # `api_docids` is the UNGATED set of filings the API carries any rows for (2026-08-24,
    # wave W2): the new `easyvote_2024_2026` tranche era is defined as EasyVote filings with
    # NO API rows at all — ungated, so a school-board filing whose rows the county-office
    # gate drops (Fife-Jepperson) is still excluded from the county tranche.
    api_docids = {base_fid(r) for r in contribs} | {base_fid(r) for r in distribs}
    tranche_docids = tranche_document_ids(api_docids)
    api_itemized = {}
    routed_to_tranche = []
    for fid in sorted(all_fids):
        cl = by_filing_c.get(fid, [])
        el = by_filing_e.get(fid, [])
        sample = (cl or el)[0]
        cand, office, seat, eyear, fdate, period, path = filing_common(fid, sample)
        # Skip filings that have no downloaded PDF (itemized-only records with no
        # documentsearch doc — e.g. EasyVote's "Training Candidate" test record). They
        # cannot be keyed to an index.csv path, so they are honestly excluded (logged).
        if not path:
            skipped_no_pdf.append((fid, cand))
            continue
        if fid in tranche_docids:
            api_itemized[fid] = {"c": cl, "e": el}
            routed_to_tranche.append(fid)
            continue
        # contributions
        c_sum = 0.0
        self_funded = 0.0
        for i, r in enumerate(sorted(cl, key=lambda x: (x.get("ContributionDate") or "", x.get("ContributionAmount") or 0)), 1):
            donor = BL.contributor_raw(r)
            amt = r.get("ContributionAmount")
            row = ContribRow(candidate=cand, office=office, seat=seat, election_year=eyear,
                             filing_date=fdate, reporting_period=period,
                             date=(r.get("ContributionDate") or "")[:10], donor_raw=donor,
                             donor_city="", donor_state="", donor_district="",
                             amount=money_str(amt), in_kind="False", is_incremental="True",
                             source_filing=path, document_id=fid, line_no=str(i),
                             extraction_confidence="high", extract_method="easyvote_api/json",
                             needs_review=("1" if (amt is None or not donor) else "0"))
            normalize_contrib(row, cand, aliases)
            crows.append(row)
            if amt:
                c_sum += float(amt)
                if row.donor_type in ("candidate-self", "loan"):
                    self_funded += float(amt)
        # expenditures
        e_sum = 0.0
        for i, r in enumerate(sorted(el, key=lambda x: (x.get("DistributionDate") or "", x.get("DistributionAmount") or 0)), 1):
            vendor = BL.payee_raw(r)
            amt = r.get("DistributionAmount")
            row = ExpendRow(candidate=cand, office=office, seat=seat, election_year=eyear,
                            filing_date=fdate, reporting_period=period,
                            date=(r.get("DistributionDate") or "")[:10], vendor_raw=vendor,
                            purpose="", amount=money_str(amt), in_kind="False",
                            is_incremental="True", source_filing=path, document_id=fid,
                            line_no=str(i), extraction_confidence="high",
                            extract_method="easyvote_api/json",
                            needs_review=("1" if amt is None else "0"))
            normalize_vendor(row)
            erows.append(row)
            if amt:
                e_sum += float(amt)
        ft = FilingTotals(candidate=cand, office=office, election_year=eyear,
                          filing_date=fdate, reporting_period=period,
                          filing_type="interim",
                          stated_total_contributions="", stated_total_expenditures="",
                          stated_beginning_balance="", stated_ending_balance="",
                          itemized_contrib_sum=money_str(c_sum) if cl else "",
                          itemized_expend_sum=money_str(e_sum) if el else "",
                          reconciles_contrib="", reconciles_expend="",
                          recon_delta_contrib="", recon_delta_expend="",
                          self_funded_amount=money_str(self_funded) if self_funded else "",
                          n_contrib_rows=str(len(cl)), n_expend_rows=str(len(el)),
                          source_filing=path, document_id=fid,
                          extraction_confidence="high",
                          notes="itemized from EasyVote structured API; stated totals not in API "
                                "(image-only redacted PDF) -> reconciliation unknown")
        filing_rows.append(ft)

    def write(fname, header, rows):
        with open(os.path.join(HERE, fname), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=header)
            w.writeheader()
            for r in rows:
                d = row_to_dict(r)
                w.writerow({k: d.get(k, "") for k in header})

    # ---- ADDITIVE: the vision tranches for the two non-structured eras.
    # APPENDED AFTER the EasyVote-JSON rows (which are built first, untouched) in ALL THREE
    # CSVs, so the 2024/2026 structured block stays byte-identical row-for-row. Wave B2 adds
    # the trailing optional `geometry` column (SCHEMA 2a) — a ONE-TIME, documented, additive
    # header change; the EasyVote rows' own field values are unchanged.
    n_structured = len(filing_rows)
    n_structured_c, n_structured_e = len(crows), len(erows)
    tranche_rows, t_crows, t_erows, tstats, twarn = build_totals_tranche(api_itemized, api_docids)
    filing_rows = filing_rows + tranche_rows
    crows = crows + t_crows
    erows = erows + t_erows

    geo = any(getattr(r, "geometry", "") for r in crows + erows)
    # `donor_occupation` (2026-08-23, owner decision 2026-08-20) is the SECOND optional
    # trailing column and is emitted only after `geometry`, so the header grows by a suffix
    # and never reorders. Only the 2015-2021 paper slice populates it; if a future rebuild
    # had no such rows the column would simply not be written and the file would revert to
    # the wave-B2 header — the same contract `geometry` itself has.
    occ = any(getattr(r, "donor_occupation", "") for r in crows)
    c_header = CONTRIB_HEADER + ([GEOMETRY_COL] if geo else []) + ([OCCUPATION_COL] if occ else [])
    if occ and not geo:                       # order is fixed; never emit occupation alone
        c_header = CONTRIB_HEADER + [GEOMETRY_COL, OCCUPATION_COL]
    write("contributions.csv", c_header, crows)
    write("expenditures.csv", EXPEND_HEADER + ([GEOMETRY_COL] if geo else []), erows)
    write("filing_totals.csv", TOTALS_HEADER, filing_rows)
    print(f"contributions {len(crows)} (EasyVote {n_structured_c} + vision-itemized {len(t_crows)})"
          f" | expenditures {len(erows)} (EasyVote {n_structured_e} + vision-itemized {len(t_erows)})"
          f" | filings {len(filing_rows)}"
          f" (EasyVote-JSON structured {n_structured} + vision tranche {len(tranche_rows)})")
    print("  vision tranche: " + " | ".join(f"{k}={v}" for k, v in sorted(tstats.items())))
    if twarn:
        print(f"  !! RECONCILIATION VERDICT DISAGREEMENTS ({len(twarn)}) — transcriber vs arithmetic:")
        for w in twarn:
            print("     " + w)
    print(f"API itemization routed onto a vision totals row (one row per filing): "
          f"{len(routed_to_tranche)} filings")
    print(f"itemized-only filings (no documentsearch meta): {len(set(skipped_no_meta))}")
    print(f"excluded (no downloaded PDF, e.g. Training Candidate): {len(skipped_no_pdf)} -> {skipped_no_pdf}")
    tot_c = sum(float(r.amount) for r in crows if r.amount)
    tot_e = sum(float(r.amount) for r in erows if r.amount)
    print(f"total itemized contributions ${tot_c:,.2f} | expenditures ${tot_e:,.2f}")


if __name__ == "__main__":
    build()
