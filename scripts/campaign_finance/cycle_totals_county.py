#!/usr/bin/env python3
"""COUNTY per-candidate-cycle campaign-finance reducer — the county-tier sibling of
`cycle_totals.py`.

Build spec: `scripts/campaign_finance/COUNTY_CYCLE_REDUCER_SPEC.md` (owner-approved
2026-08-23). Read it before changing a rule; every section reference below points into it.

WHY A SEPARATE REDUCER AND A SEPARATE TABLE
-------------------------------------------
`cycle_totals.py` computes `max(latest summary, summed interims)` of stated totals. That
rule is WRONG for every county corpus:

  * the county filing regimes differ per COUNTY and, in three counties, per CANDIDATE
    (washington's template is per-period but a minority of filers fill it cumulatively;
    wasatch's 2024 period sheet has three cumulative restaters; cache varies per filing);
  * summit / juab / weber file CUMULATIVE snapshots — summing them multiplies the truth
    (summit `David R. Brickey` 2014: two filings stating 15,600.00 then 16,800.00; the
    city reducer answers 32,400.00, the truth is 16,800.00);
  * officeholder CARRYOVER opens many county cycles with a large balance that a naive
    cumulative read silently converts into "money raised" (SLCo `Winder Newton, Aimee`
    2022 opens at 215,160.87 having raised 61,084.62 in the cycle);
  * `filing_regime` carries TWO INCOMPATIBLE VOCABULARIES at the county tier — a statutory
    stream (`election_cycle`/`annual`, the city meaning) in juab/washington, and an
    arithmetic basis (`per-period`/`cumulative`/`period`) in utah/weber/wasatch. The city
    rule `regime != 'election_cycle' -> drop` silently drops ALL of utah, weber and wasatch.
    This module reads `filing_regime` for EXACTLY ONE THING — the non-cycle stream filter
    (`annual`) — and NEVER as the arithmetic basis (spec §0.1).

THE METHOD (spec §3)
--------------------
Stated totals from `filing_totals.csv` are PRIMARY (the filer's own printed figures —
cardinal rule 2 — and the only substrate that spans all 8 counties back to 2006). The
BALANCE CHAIN is the resolver; itemized sums are an ADVISORY cross-check that never gates.

  1. scope filter        drop `filing_regime == 'annual'` and blank `election_year` (§3.1)
  2. supersede pre-filter marker-driven, conservative; a group is never all-superseded (§3.2)
  3. per-filing signature period_sig = |BB + C - E - EB| <= 0.51
                           cumul_sig  = |C - E - EB|      <= 0.51        (§3.3)
  4. BALANCE CHAIN        link filing n -> n+1 when |BB(n+1) - EB(n)| <= 0.51; longest wins.
     CHAIN-CLOSURE PROOF  |BB(first) + SUM C - SUM E - EB(last)| <= 0.51                (§3.4)
  5. regime classification, first match wins; the COUNTY PRIOR is a TIE-BREAK ONLY and can
     only ever CONFIRM, never decide (§3.5)

Every published figure is REPRODUCIBLE from the filings named in `governing_filings` and
nothing else (gate G1). A candidate-cycle whose total cannot be established from the
filings' own printed arithmetic emits a GAP ROW — blank figures + `gap_reason` — never an
estimate (cardinal rule 1).

OWNER RULINGS (2026-08-23, on the spec's two blocking questions)
  B1  `raised_net_of_carryover` is NOT computed for cumulative-regime cycles; it stays
      blank there. Gross totals + `carryover_opening` as its own column publish on every
      row. Carryover is NEVER silently subtracted anywhere.
  B2  tier-C floor rows DO publish, flagged `is_floor=1` — a provable lower bound ships as
      a flagged floor, never as an unflagged total.

DERIVED LAYER — regenerate, never hand-edit:
    python3 scripts/campaign_finance/cycle_totals_county.py --all
after any county `build_finance.py` run. Corrections go through
`<county>/campaign_finance/cycle_overrides_county.csv` (cardinal rules 2 and 3).

Usage:
  cycle_totals_county.py <slug>        write one county's cycle_totals_county.csv
  cycle_totals_county.py --all         all 8 counties
  cycle_totals_county.py --report      print the tier / regime / carryover report (no write)
  cycle_totals_county.py --validate    run gates G1-G7 against the emitted CSVs
  cycle_totals_county.py --all --report --validate     the full close-out run
"""
import csv
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from entities import ENTITIES, by_slug  # noqa: E402

TOL = 0.51   # spec §3.3: every documented filer-arithmetic delta in these corpora is >= $1,
             # so this absorbs whole-dollar/rounding variance without manufacturing closures.

# Non-cycle STATUTORY streams (spec §3.1). This is the ONLY use of `filing_regime` in this
# module — never as the arithmetic basis (§0.1).
NONCYCLE_REGIMES = {"annual"}

# COUNTY FORM PRIOR (spec §3.5) — quoted from each county's own `cf-*` caveat row /
# CLAUDE.md. TIE-BREAK ONLY: it fires in rule 1 and rule 6 and can only ever CONFIRM a
# reading the filings' own arithmetic cannot settle. A `mixed` prior NEVER fires rule 6 —
# those counties must settle each cycle on its own arithmetic or emit a gap.
COUNTY_PRIOR = {
    "utah_county":       "per-period",   # caveat: "regime is PER-PERIOD and INVERTED"
    "salt_lake_county":  "per-period",   # caveat: per-period column; 2 filers deviate
    "weber_county":      "cumulative",   # caveat: "cycle figure = latest non-superseded report, never a sum"
    "summit_county":     "cumulative",   # caveat: "CUMULATIVE snapshots - never sum a candidate's filings"
    "juab_county":       "cumulative",   # caveat: "these forms are cumulative"
    "wasatch_county":    "mixed",        # caveat: "regime is per CANDIDATE, not per form"
    "cache_county":      "mixed",        # caveat: "is_incremental varies PER FILING"
    "washington_county": "mixed",        # CLAUDE.md: template per-period, minority cumulative
}

GAP_REASONS = {"no-stated-total", "chain-broken", "regime-conflict",
               "mixed-county-no-evidence", "neither-basis", "superseded-only"}

COLS = ["city", "candidate", "election_year", "office", "seat",
        "regime", "regime_basis",
        "raised_gross", "spent_gross",
        "carryover_opening", "carryover_basis", "raised_net_of_carryover",
        "ending_balance", "chain_closes",
        "n_filings", "n_live", "n_governing", "chain_len",
        "is_floor", "in_kind_basis", "confidence",
        "governing_filings", "excluded_filings", "gap_reason",
        "itemized_check_raised", "itemized_check_spent", "itemized_check_note",
        "review_flag"]

# index.csv seat column, per county. Blank elsewhere means "the county does not publish a
# seat", NOT unknown-by-omission (spec §2.2 col 5).
SEAT_COL = {"summit_county": "seat", "wasatch_county": "seat",
            "salt_lake_county": "seat", "cache_county": "council_seat"}


# ---------------------------------------------------------------- primitives

def money(x):
    """Parse a printed money token. Returns None for anything unparseable.

    A BLANK IS NEVER 0 (washington's standing rule) — a nil mark is not a numeral, and the
    ZERO-GLYPH RULING (GOTCHAS, owner 2026-08-02) already converted every glyph that DENOTES
    zero into a literal 0 upstream. Anything still blank/dash/N-A here is an absent figure.
    """
    if x is None:
        return None
    s = str(x).replace(",", "").replace("$", "").strip()
    if s.startswith("(") and s.endswith(")"):     # accounting negative
        s = "-" + s[1:-1]
    if s in ("", "-", "--", "None", "N/A", "n/a", "NA"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def is_superseded(notes):
    """Conservative, MARKER-DRIVEN supersede test (spec §3.2).

    Two accepted markers:
      * a `;`-separated note ENTRY that begins with 'superseded' — the existing structural
        convention, reused verbatim from `cycle_totals.py::is_superseded`. (Do NOT go back
        to the anywhere-substring test: it once dropped a bluffdale filing whose free text
        merely MENTIONED supersession.)
      * the literal 'SUPERSEDED by' / 'is SUPERSEDED' — weber's wave-B2 wording.

    Deliberately incomplete: SLCo's overlapping April-5 amendment trio carries no marker at
    all. The balance chain (§3.4) resolves those without one.
    """
    n = notes or ""
    if any(seg.strip().lower().startswith("superseded") for seg in n.split(";")):
        return True
    return "SUPERSEDED by" in n or "is SUPERSEDED" in n


def signatures(f):
    """Attach the two arithmetic booleans of spec §3.3 to a filing dict.

    `both` (period and cumulative) is the FIRST-REPORT case: when BB = 0 the two are
    algebraically identical. That is utah's documented `cumulative-exact` state, not an
    ambiguity to resolve at the filing level — it resolves at the cycle level in step 4.
    """
    bb, c, e, eb = f["bb"], f["c"], f["e"], f["eb"]
    f["period_sig"] = (bb is not None and None not in (c, e, eb)
                       and abs(bb + c - e - eb) <= TOL)
    f["cumul_sig"] = (None not in (c, e, eb) and abs(c - e - eb) <= TOL)
    f["testable"] = None not in (c, e, eb)
    return f


def longest_chain(rows):
    """The BALANCE CHAIN (spec §3.4). Link filing n -> n+1 when |BB(n+1) - EB(n)| <= TOL.

    Try every start; prefer the later-dated candidate on ties; each filing used at most
    once. O(n^2) over groups that never exceed ~15 filings — no optimization warranted.

    Among chains of EQUAL length prefer one whose closure proof is TESTABLE (its first
    filing prints a beginning balance): an equally long chain that cannot be proved is
    strictly less evidence, and the proof is this reducer's spine. Length still dominates.
    """
    best = []
    best_key = (-1, -1)
    for s in range(len(rows)):
        used = {s}
        ch = [rows[s]]
        while True:
            tail = ch[-1]
            if tail["eb"] is None:
                break
            cand = [j for j in range(len(rows))
                    if j not in used and rows[j]["bb"] is not None
                    and abs(rows[j]["bb"] - tail["eb"]) <= TOL]
            if not cand:
                break
            j = max(cand, key=lambda k: (rows[k]["filing_date"] or "", k))
            used.add(j)
            ch.append(rows[j])
        key = (len(ch), 1 if ch[0]["bb"] is not None else 0)
        if key > best_key:
            best_key, best = key, ch
    return best


def collapse_restatements(live):
    """LAST-RESORT restatement collapse. Returns (kept, dropped).

    Two per-period filings that print the SAME beginning balance for the SAME reporting
    period cannot be consecutive periods — a subsequent period opens at the prior period's
    ENDING balance. By the documents' own balance arithmetic they are RESTATEMENTS of one
    report, so the later-dated one (tie-break: the larger contributions figure) governs and
    the rest are `duplicate-restatement`. This is an inference from printed figures, not a
    heuristic about filer behaviour.

    Applied ONLY when the ordinary ladder has already produced a GAP, so it can never
    disturb a cycle that resolves on its own — it is monotone by construction (it can turn
    a gap into a published row, never the reverse). The specimen is SLCo `Ben McAdams` 2014:
    a year-end report and a file literally named `...-2014-year-end-amendment` that share
    BB 43,181.28 and expenditures 180,904.12 and differ only in contributions
    (268,232.00 -> 274,232.00); neither carries a supersede marker, and because they open
    from the SAME balance no chain can link them.
    """
    buckets = defaultdict(list)
    for f in live:
        if f["bb"] is None or not f["reporting_period"]:
            buckets[id(f)].append(f)
        else:
            buckets[(round(f["bb"], 2), f["reporting_period"].strip().lower())].append(f)
    kept, dropped = [], []
    for _, fl in buckets.items():
        if len(fl) == 1:
            kept.append(fl[0])
            continue
        g = max(fl, key=lambda f: (f["filing_date"] or "", f["c"] if f["c"] is not None else -1))
        kept.append(g)
        dropped += [f for f in fl if f is not g]
    kept.sort(key=lambda f: (f["filing_date"] or "", f["source_filing"] or ""))
    return kept, dropped


def chain_proof(ch):
    """CHAIN-CLOSURE PROOF: BB(first) + SUM C - SUM E == EB(last), within TOL.

    Returns True / False / None (None = untestable, a required figure is not printed).
    """
    if not ch or ch[0]["bb"] is None or ch[-1]["eb"] is None:
        return None
    if any(r["c"] is None or r["e"] is None for r in ch):
        return None
    return abs(ch[0]["bb"] + sum(r["c"] for r in ch)
               - sum(r["e"] for r in ch) - ch[-1]["eb"]) <= TOL


# ---------------------------------------------------------------- I/O helpers

def cf_dir(slug):
    e = by_slug(slug)
    return os.path.join(REPO, e.dir, "campaign_finance")


def county_slugs():
    """Every NON-CITY entity with a structured filing_totals.csv.

    Mirror image of `cycle_totals.py::all_cities()`, which is city-only. The two lists are
    disjoint BY CONSTRUCTION so neither reducer can ever write into the other's table.
    """
    return sorted(e.slug for e in ENTITIES
                  if e.dir and e.level != "city" and os.path.exists(
                      os.path.join(REPO, e.dir, "campaign_finance", "filing_totals.csv")))


def _read(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_index(slug):
    """(candidate, election_year) -> index row, for `office` and (4 counties) `seat`."""
    idx = {}
    for r in _read(os.path.join(cf_dir(slug), "index.csv")):
        idx.setdefault(((r.get("candidate") or "").strip(),
                        (r.get("election_year") or "").strip()), r)
    return idx


def load_overrides(slug):
    """Optional `cycle_overrides_county.csv` (spec §5.6) — the documented correction
    mechanism. Values REPLACE the computed ones, `regime_basis` becomes 'override' and
    `review_flag` carries the reason. Ships absent: an override is a human verification of
    a specific cycle against its filings, never a build step."""
    return {((r["candidate"] or "").strip(), (r["election_year"] or "").strip()): r
            for r in _read(os.path.join(cf_dir(slug), "cycle_overrides_county.csv"))}


def load_itemized(slug):
    """Itemized rows keyed by source_filing, for the ADVISORY cross-check (§5.4)."""
    con, exp = defaultdict(list), defaultdict(list)
    for r in _read(os.path.join(cf_dir(slug), "contributions.csv")):
        con[(r.get("source_filing") or "").strip()].append(r)
    for r in _read(os.path.join(cf_dir(slug), "expenditures.csv")):
        exp[(r.get("source_filing") or "").strip()].append(r)
    return con, exp


# ---------------------------------------------------------------- in-kind

def in_kind_from_notes(gov):
    """`in_kind_basis` (spec §4.5): `included` / `excluded` ONLY where the county's
    build_finance.py already settled it PER FILING from that filing's own arithmetic and
    recorded it in `notes`. NEVER inferred from cycle, form family or county — the
    owner-ratified 2026-08-17 per-filer in-kind finding.

    The stated totals this layer publishes are the filer's own printed figures, so whatever
    the filer did with in-kind is already inside them: this column DOCUMENTS the convention,
    it never adjusts a number."""
    seen = set()
    for f in gov:
        n = (f["notes"] or "").lower()
        if "in-kind" not in n and "in kind" not in n:
            continue
        if "excludes in-kind" in n or "in-kind excluded" in n or "exclude in-kind" in n:
            seen.add("excluded")
        elif "includes in-kind" in n or "in-kind included" in n or "include in-kind" in n:
            seen.add("included")
    if len(seen) == 1:
        return seen.pop()
    return "unknown"


# ---------------------------------------------------------------- itemized cross-check

def itemized_check(gov, con, exp, regime):
    """ADVISORY cross-check (spec §5.4). NEVER gates, NEVER corrects a stated total.

    Scope = the GOVERNING filings only, so the check compares like with like: the same
    filings that produced `raised_gross`.
      * every row `is_incremental='True'`  -> SUM (periods are disjoint)
      * every row `is_incremental='False'` -> the LATEST governing filing's ledger only
        (the ledger RESTATES the cycle — washington's 1,518 rows are 676 distinct donations)
      * MIXED within one cycle -> not comparable; figures left blank.
    """
    def side(rows_by_sf):
        rows, flags, withrows = [], set(), 0
        for f in gov:
            got = rows_by_sf.get(f["source_filing"], [])
            if got:
                withrows += 1
            for r in got:
                rows.append((f, r))
                flags.add((r.get("is_incremental") or "").strip())
        if not rows:
            return None, "none"
        if withrows < len(gov):
            # PARTIAL itemized coverage of the governing filings. Comparing an itemized sum
            # over 1 of 5 filings against a stated total built from all 5 manufactures a
            # false disagreement, so the check declares itself not comparable and prints the
            # coverage. Empty itemized = NOT TRANSCRIBED, never "no donors".
            return None, f"partial:{withrows}/{len(gov)}"
        if flags - {"True"} == set():
            return sum(money(r.get("amount")) or 0.0 for _, r in rows), "sum-incremental"
        if flags - {"False"} == set():
            last = gov[-1]["source_filing"]
            sel = [r for f, r in rows if f["source_filing"] == last]
            if not sel:
                return None, "none"
            return sum(money(r.get("amount")) or 0.0 for r in sel), "latest-ledger"
        return None, "mixed"

    ir, mr = side(con)
    ie, me = side(exp)
    if mr == "mixed" or me == "mixed":
        return "", "", "not-comparable: mixed is_incremental within cycle"
    if mr == "none" and me == "none":
        return "", "", "no itemized layer"
    if mr.startswith("partial") or me.startswith("partial"):
        cov = mr if mr.startswith("partial") else me
        return "", "", (f"not-comparable: itemized rows exist for only "
                        f"{cov.split(':')[1]} governing filings")
    note = mr if mr != "none" else me
    if regime.startswith("cumulative") and note == "sum-incremental":
        note = ("not-comparable: ledger is period-scoped (is_incremental=True) while the "
                "stated total is cumulative")
        return (f"{ir:.2f}" if ir is not None else "",
                f"{ie:.2f}" if ie is not None else "", note)
    return (f"{ir:.2f}" if ir is not None else "",
            f"{ie:.2f}" if ie is not None else "", note)


# ---------------------------------------------------------------- the reducer

def classify(live, prior, fallback):
    """The DECISION PROCEDURE of spec §3.3-§3.5 over one candidate-cycle's live filings.

    Pure: takes the live filing dicts, returns everything the row needs. Kept as ONE
    importable classifier (spec §7.1 "keep exactly one classifier") so a future
    federation-time path cannot drift from the on-disk one.
    """
    excluded = []
    nper = sum(1 for f in live if f["period_sig"] and not f["cumul_sig"])
    ncum = sum(1 for f in live if f["cumul_sig"] and not f["period_sig"])
    nboth = sum(1 for f in live if f["period_sig"] and f["cumul_sig"])
    ncoherent = nper + ncum + nboth
    ch = longest_chain(live) if len(live) > 1 else list(live)
    # A one-filing "chain" is not a chain: report the closure proof only where a real link
    # was made, so `chain_closes` can never read True beside `chain_len` 0 or 1.
    chain_len = len(ch) if len(live) > 1 else 0
    proof = chain_proof(ch) if chain_len >= 2 else None

    regime = regime_basis = ""
    raised = spent = carry = endbal = None
    carry_basis = ""
    gov = []
    gap = ""
    # ---- spec §3.5, first match wins
    if len(live) == 1:
        # SINGLE-FILING CYCLE — spec §3.5 rules 1-3, with two documented refinements
        # the spec's own text requires (both recorded in CLOSEOUT.md):
        #
        # (a) THE FILING'S OWN ARITHMETIC OUTRANKS THE COUNTY PRIOR. The spec writes
        #     rule 1 as "prior is cumulative OR the filing is cumulative-only" ahead of
        #     rule 2, which would let a cumulative prior overrule a filing that closes
        #     ONLY on the per-period reading — contradicting §3.5's own governing
        #     sentence, "the county prior is a TIE-BREAK ONLY and is never allowed to
        #     overrule a filing's own arithmetic." Testing the exclusive signatures
        #     first restores that. Affects exactly ONE cycle in the corpus
        #     (weber_county `Terry Thompson` 2014); summit/wasatch/juab print no
        #     beginning balance at all, so `period_sig` is never true there.
        #
        # (b) THE `both` FIRST-REPORT CASE IS RESOLVED, NOT DROPPED. When BB = 0 the two
        #     signatures are algebraically identical, which §3.3 states plainly is "the
        #     first-report case ... not ambiguity to be resolved at the filing level."
        #     Rules 1 and 2 as written both demand exclusivity, so a single `both`
        #     filing fell through to rule 3 and became a GAP — 102 cycles of it, incl.
        #     53 utah and 31 salt_lake. That is a hole, not a finding: `C` is the
        #     filer's own printed figure and is a LOWER BOUND under EITHER reading
        #     (a period total or a cycle-to-date total is <= the cycle total), so it
        #     publishes as a flagged floor (owner ruling B2), never as a total. The
        #     prior breaks the tie where it has one — which is precisely a tie-break's
        #     job, and is what rule 1 already does for the cumulative side.
        f = live[0]
        gov = [f]
        if f["period_sig"] and not f["cumul_sig"]:
            regime, regime_basis = "per-period-single", "single-filing"    # rule 2
        elif f["cumul_sig"] and not f["period_sig"]:
            regime, regime_basis = "cumulative-single", "single-filing"    # rule 1
        elif f["period_sig"] and f["cumul_sig"]:                           # `both`
            regime = {"cumulative": "cumulative-single",
                      "per-period": "per-period-single"}.get(prior, "undetermined")
            regime_basis = "single-filing"
        elif prior == "cumulative":                          # rule 1, prior tie-break
            regime, regime_basis = "cumulative-single", "single-filing"
        else:
            regime, regime_basis = "undetermined", "none"                  # rule 3
        if regime_basis == "single-filing" and f["c"] is not None:
            raised, spent, carry, endbal = f["c"], f["e"], f["bb"], f["eb"]
            carry_basis = "governing-report-bb" if carry is not None else ""
    elif proof and chain_len >= 2 and nper >= ncum:                        # rule 4
        regime, regime_basis = "per-period", "chain-closure"
        gov = list(ch)
        raised = sum(f["c"] for f in ch)
        spent = sum(f["e"] for f in ch)
        carry, endbal = ch[0]["bb"], ch[-1]["eb"]
        carry_basis = "chain-first-bb" if carry is not None else ""
        for f in live:
            if f not in ch:
                excluded.append((f["key"], "orphan-not-chained"))
    elif ncum > 0 and nper == 0:                                           # rule 5
        cands = [f for f in live if f["c"] is not None]
        if cands:
            regime, regime_basis = "cumulative", "filing-arithmetic"
            g = max(cands, key=lambda f: (f["filing_date"] or "", f["c"]))
            gov = [g]
            raised, spent, endbal = g["c"], g["e"], g["eb"]
            carry = live[0]["bb"]
            carry_basis = "chain-first-bb" if carry is not None else ""
            for f in live:
                if f is not g:
                    excluded.append((f["key"], "duplicate-restatement"))
    elif (prior == "cumulative" and nper == 0                              # rule 6
          and all(f["c"] is not None for f in live)):
        # `nper == 0` is the spec's own governing sentence made operative: "the county prior
        # is a TIE-BREAK ONLY and is never allowed to overrule a filing's own arithmetic."
        # A live filing that closes ONLY on the per-period reading is evidence AGAINST the
        # cumulative prior, so the prior may not decide over it — the cycle falls through to
        # a gap instead. (Without this, the synthesized weber swapped-cover pair of §7.2 T12
        # would be answered with the LATER cover's figure, which is the "silent fallback"
        # §3.4 forbids.)
        regime, regime_basis = "cumulative", "county-prior"
        g = max(live, key=lambda f: (f["filing_date"] or "", f["c"]))
        gov = [g]
        raised, spent, endbal = g["c"], g["e"], g["eb"]
        carry = live[0]["bb"]
        carry_basis = "chain-first-bb" if carry is not None else ""
        for f in live:
            if f is not g:
                excluded.append((f["key"], "duplicate-restatement"))
    else:                                                                  # rule 7
        regime, regime_basis = "undetermined", "none"

    # ---- gap classification (spec §5.5). A gap is a ROW, never an estimate.
    if raised is None:
        gov = []
        carry = endbal = spent = None
        carry_basis = ""
        if not any(f["c"] is not None for f in live):
            gap = ("no-stated-total: no live filing prints a parseable "
                   "total-contributions figure")
        elif fallback:
            gap = ("superseded-only: every filing carries a supersede marker and the "
                   "restored fallback set still cannot be settled")
        elif nper > 0 and ncum > 0:
            gap = ("regime-conflict: period-only and cumulative-only filings coexist "
                   "and no chain resolves them")
        elif len(live) > 1 and chain_len >= 2 and proof is False:
            gap = (f"chain-broken: the longest balance chain ({chain_len} of "
                   f"{len(live)} live filings) does not close")
        elif len(live) > 1 and ncoherent > 0:
            # The filings' own arithmetic is coherent but NO balance chain links them,
            # so the periods cannot be proved disjoint. Summing them here is exactly
            # the fallback §3.4 forbids ("it does NOT silently fall back to a sum") —
            # two unlinked filings may be an unmarked restatement as easily as two
            # disjoint periods, and summing a restatement double-counts.
            gap = (f"chain-broken: {ncoherent} of {len(live)} live filings close on "
                   f"their own arithmetic, but their balances do not link into a "
                   f"chain (longest chain {chain_len}), so the periods cannot be "
                   f"proved disjoint and are never summed")
        elif any(f["testable"] for f in live):
            gap = ("neither-basis: the filer's own arithmetic closes on neither the "
                   "per-period nor the cumulative reading")
        elif prior == "mixed":
            gap = ("mixed-county-no-evidence: this county's regime varies per filer and "
                   "the cycle's own arithmetic is silent (a required printed figure is "
                   "blank on every live filing)")
        else:
            gap = ("neither-basis: arithmetic untestable — a required printed figure "
                   "(expenditures or ending balance) is blank on every live filing")

    return {"regime": regime, "regime_basis": regime_basis, "raised": raised,
            "spent": spent, "carry": carry, "carry_basis": carry_basis,
            "endbal": endbal, "gov": gov, "gap": gap, "proof": proof,
            "chain_len": chain_len, "chain": ch, "excluded": excluded, "live": live,
            "nper": nper, "ncum": ncum}


def scope_filter(rows):
    """Spec §3.1 — drop the non-cycle STATUTORY streams, then shape each surviving row.

    Returns (filings, dropped). NOT the city rule (`filing_regime != 'election_cycle'`),
    which would drop every utah / weber / wasatch filing (§0.1).
    """
    filings, dropped = [], []
    for r in rows:
        cand = (r.get("candidate") or "").strip()
        year = (r.get("election_year") or "").strip()
        if (r.get("filing_regime") or "").strip().lower() in NONCYCLE_REGIMES:
            dropped.append((cand, year, r.get("source_filing"), "non-cycle-stream"))
            continue
        if not year:
            dropped.append((cand, year, r.get("source_filing"), "blank-election-year"))
            continue
        filings.append(signatures({
            "candidate": cand, "election_year": year,
            "office": (r.get("office") or "").strip(),
            "filing_date": (r.get("filing_date") or "").strip(),
            "reporting_period": (r.get("reporting_period") or "").strip(),
            "filing_type": (r.get("filing_type") or "").strip(),
            "source_filing": (r.get("source_filing") or "").strip(),
            "notes": r.get("notes") or "",
            "bb": money(r.get("stated_beginning_balance")),
            "c": money(r.get("stated_total_contributions")),
            "e": money(r.get("stated_total_expenditures")),
            "eb": money(r.get("stated_ending_balance")),
        }))
    return filings, dropped


def reduce_group(slug, cand, year, filings, prior=None, idx=None, seat_col=None,
                 con=None, exp=None, overrides=None):
    """Reduce ONE candidate-cycle's shaped filings to its output row.

    The single entry point used by both the CSV writer and the test suite, so a test can
    never exercise a different code path from the one that ships (spec §7.1).
    """
    prior = prior if prior is not None else COUNTY_PRIOR.get(slug, "mixed")
    idx = idx or {}
    con = con if con is not None else {}
    exp = exp if exp is not None else {}
    overrides = overrides or {}
    if True:   # (indentation preserved from the per-group loop this was extracted from)
        filings = list(filings)
        filings.sort(key=lambda f: (f["filing_date"] or "", f["source_filing"] or ""))
        # REPRODUCIBILITY KEY (gate G1): `source_filing` is NOT unique inside every group —
        # 9 county groups hold two filings carved out of ONE combined PDF (utah 2, weber 7;
        # utah `Jeffrey R. Buhman` 2014 is the documented specimen). Where a group repeats a
        # source_filing, EVERY occurrence gets a 1-based `#N` ordinal in filing-date order so
        # `governing_filings` names exactly one row. Unique paths are emitted bare, so the
        # column reads as the spec's plain `;`-joined source_filing list everywhere else.
        seen = defaultdict(int)
        dupes = {sf for sf, n in
                 ((sf, sum(1 for g in filings if g["source_filing"] == sf))
                  for sf in {g["source_filing"] for g in filings}) if n > 1}
        for f in filings:
            seen[f["source_filing"]] += 1
            f["key"] = (f"{f['source_filing']}#{seen[f['source_filing']]}"
                        if f["source_filing"] in dupes else f["source_filing"])

        live = [f for f in filings if not is_superseded(f["notes"])]
        fallback = not live          # a group is never all-superseded (spec §3.2)
        if fallback:
            live = list(filings)
        excluded = [(f["key"], "superseded-note") for f in filings if f not in live]

        res = classify(live, prior, fallback)
        if res["raised"] is None:
            # LAST-RESORT restatement collapse (see collapse_restatements). Runs ONLY on a
            # cycle the ordinary ladder already gapped, so it is monotone by construction.
            kept, coll = collapse_restatements(live)
            if coll:
                res2 = classify(kept, prior, fallback)
                if res2["raised"] is not None:
                    res = res2
                    res["excluded"] = ([(f["key"], "duplicate-restatement") for f in coll]
                                       + res["excluded"])
        excluded += res["excluded"]
        regime, regime_basis = res["regime"], res["regime_basis"]
        raised, spent = res["raised"], res["spent"]
        carry, carry_basis, endbal = res["carry"], res["carry_basis"], res["endbal"]
        gov, gap = res["gov"], res["gap"]
        proof, chain_len, ch = res["proof"], res["chain_len"], res["chain"]
        live = res["live"]
        # ---- is_floor (spec §4.4, owner ruling B2: floors PUBLISH, flagged)
        is_floor = ""
        if raised is not None:
            if regime in ("per-period-single", "undetermined"):
                # per-period-single: one period was filed or survives, so the cycle total
                # is at least this. `undetermined`: a lone `both`-signature filing in a
                # MIXED-prior county — nothing settles the regime, but C is a lower bound
                # on either reading, so it publishes as a floor and never as a total.
                is_floor = "1"
            elif regime == "per-period" and chain_len < len(live):
                # §4.4: a floor when "money exists in a filing the chain could not place."
                # An unchained filing that reports a period the CHAIN ALREADY COVERS is an
                # amendment/restatement of money already counted, not unplaced money — that
                # is the whole point of the A-superseded tier, and the spec's own canonical
                # specimen (SLCo `Rivera, Rosie` 2022) is presented there as a resolved
                # total, not a bound: all four of her orphans restate an April-5 or a
                # September-15 report the chain contains. So the floor fires only where an
                # unchained non-zero filing covers a period the chain does NOT.
                covered = {(f["reporting_period"] or "").strip().lower() for f in ch}
                if any(f not in ch and f["c"] not in (None, 0.0)
                       and (f["reporting_period"] or "").strip().lower() not in covered
                       for f in live):
                    is_floor = "1"

        # ---- confidence tier (spec §5)
        if raised is None:
            conf = ""
        elif regime == "per-period" and proof and chain_len == len(live):
            conf = "A"
        elif regime == "per-period" and proof:
            conf = "A-superseded"
        elif regime.startswith("cumulative"):
            conf = "B"
        else:
            conf = "C"

        # ---- carryover. NEVER silently folded (spec §4.3; owner ruling B1).
        # per-period: the chain's periods are disjoint, so nothing is subtracted and the net
        # figure EQUALS the gross BY CONSTRUCTION. cumulative: BLANK — weber proves the
        # opening-balance column's semantics is not stable across filings (Froerer 2022's
        # cumulative contributions cell equals BB + this-period, 31,415.05 = 7,815.05 +
        # 23,600.00, while his 2018 final carries a last-report CONTRIBUTIONS figure of
        # 73,634 beside a BALANCE BB of 9,976.05), so one blanket subtraction is wrong on one
        # of them.
        net = raised if (raised is not None and regime.startswith("per-period")) else None

        meta = idx.get((cand, year), {})
        office = (meta.get("office") or (filings[0]["office"] if filings else "") or "").strip()
        seat = (meta.get(seat_col) or "").strip() if seat_col else ""

        ir = ie = inote = ""
        if gov:
            ir, ie, inote = itemized_check(gov, con, exp, regime)
        review = ""

        # ---- documented human override (spec §5.6)
        ov = overrides.get((cand, year))
        if ov:
            if money(ov.get("raised_gross")) is not None:
                raised = money(ov["raised_gross"])
            if money(ov.get("spent_gross")) is not None:
                spent = money(ov["spent_gross"])
            if money(ov.get("carryover_opening")) is not None:
                carry = money(ov["carryover_opening"])
            if (ov.get("regime") or "").strip():
                regime = ov["regime"].strip()
            regime_basis = "override"
            gap = "" if raised is not None else gap
            conf = conf or "C"
            review = f"OVERRIDE: {ov.get('reason', '')} [{ov.get('evidence', '')}]".strip()

        def dec(v):
            return "" if v is None else f"{v:.2f}"

        return {
            "city": slug, "candidate": cand, "election_year": year,
            "office": office, "seat": seat,
            "regime": regime, "regime_basis": regime_basis,
            "raised_gross": dec(raised), "spent_gross": dec(spent),
            "carryover_opening": dec(carry), "carryover_basis": carry_basis,
            "raised_net_of_carryover": dec(net),
            "ending_balance": dec(endbal),
            "chain_closes": "" if proof is None else str(proof),
            "n_filings": len(filings), "n_live": len(live), "n_governing": len(gov),
            "chain_len": chain_len,
            "is_floor": is_floor,
            "in_kind_basis": in_kind_from_notes(gov) if gov else "unknown",
            "confidence": conf,
            "governing_filings": ";".join(f["key"] for f in gov),
            "excluded_filings": ";".join(f"{k}={r}" for k, r in excluded),
            "gap_reason": gap,
            "itemized_check_raised": ir, "itemized_check_spent": ie,
            "itemized_check_note": inote,
            "review_flag": review,
        }


def cycle_totals_county(slug, itemized=True):
    """Return (rows, dropped) — the per-candidate-cycle rows for one county."""
    prior = COUNTY_PRIOR.get(slug, "mixed")
    idx = load_index(slug)
    overrides = load_overrides(slug)
    seat_col = SEAT_COL.get(slug)
    con, exp = load_itemized(slug) if itemized else ({}, {})
    filings, dropped = scope_filter(_read(os.path.join(cf_dir(slug), "filing_totals.csv")))
    groups = defaultdict(list)
    for f in filings:
        groups[(f["candidate"], f["election_year"])].append(f)
    out = [reduce_group(slug, cand, year, fl, prior, idx, seat_col, con, exp, overrides)
           for (cand, year), fl in sorted(groups.items())]
    out.sort(key=lambda d: (d["election_year"], d["office"], d["seat"], d["candidate"]))
    return out, dropped


def write_county(slug):
    rows, dropped = cycle_totals_county(slug)
    path = os.path.join(cf_dir(slug), "cycle_totals_county.csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    return rows, dropped


# ---------------------------------------------------------------- gates

def _regroup(slug):
    """Re-read filing_totals.csv into {key: filing} for the G1 re-derivation."""
    by = {}
    groups = defaultdict(list)
    for r in _read(os.path.join(cf_dir(slug), "filing_totals.csv")):
        cand = (r.get("candidate") or "").strip()
        year = (r.get("election_year") or "").strip()
        groups[(cand, year)].append(r)
    for (cand, year), fl in groups.items():
        fl.sort(key=lambda r: ((r.get("filing_date") or ""), (r.get("source_filing") or "")))
        seen = defaultdict(int)
        counts = defaultdict(int)
        for r in fl:
            counts[(r.get("source_filing") or "").strip()] += 1
        for r in fl:
            sf = (r.get("source_filing") or "").strip()
            seen[sf] += 1
            key = f"{sf}#{seen[sf]}" if counts[sf] > 1 else sf
            by[(cand, year, key)] = r
    return by


def validate(slugs, verbose=True):
    """Gates G1-G7 (spec §6). Returns (failures, report_lines)."""
    fails, lines = 0, []
    tot = defaultdict(int)
    for slug in slugs:
        ft = os.path.join(cf_dir(slug), "filing_totals.csv")
        cyc = os.path.join(cf_dir(slug), "cycle_totals_county.csv")
        # STALENESS (spec §7.1): a county rebuild must not leave a stale derived CSV.
        if not os.path.exists(cyc):
            lines.append(f"FAIL [{slug}] cycle_totals_county.csv missing — run --all")
            fails += 1
            continue
        if os.path.getmtime(ft) > os.path.getmtime(cyc):
            lines.append(f"FAIL [{slug}] STALE: filing_totals.csv is newer than "
                         f"cycle_totals_county.csv — re-run the reducer")
            fails += 1
        rows = _read(cyc)
        src = _regroup(slug)
        g1 = g5 = g6 = 0
        closure_num = closure_den = 0
        for r in rows:
            gov = [g for g in (r["governing_filings"] or "").split(";") if g]
            # -- G1 reproducibility: re-derive from the NAMED filings and nothing else
            if r["raised_gross"]:
                if r["regime_basis"] == "override":
                    pass
                else:
                    got = [src.get((r["candidate"], r["election_year"], k)) for k in gov]
                    if any(x is None for x in got):
                        lines.append(f"FAIL G1 [{slug}] {r['candidate']} {r['election_year']}: "
                                     f"governing filing not found: {gov}")
                        g1 += 1
                    else:
                        if r["regime"].startswith("per-period") and len(got) > 1:
                            rr = sum(money(x["stated_total_contributions"]) for x in got)
                            ss = sum(money(x["stated_total_expenditures"]) for x in got)
                        else:
                            rr = money(got[-1]["stated_total_contributions"])
                            ss = money(got[-1]["stated_total_expenditures"])
                        if abs(rr - float(r["raised_gross"])) > 0.005 or (
                                r["spent_gross"] and ss is not None
                                and abs(ss - float(r["spent_gross"])) > 0.005):
                            lines.append(
                                f"FAIL G1 [{slug}] {r['candidate']} {r['election_year']}: "
                                f"re-derived {rr}/{ss} vs published "
                                f"{r['raised_gross']}/{r['spent_gross']}")
                            g1 += 1
            # -- G2 chain-closure proof on tier A rows
            if r["confidence"] in ("A", "A-superseded") and r["chain_closes"] != "True":
                lines.append(f"FAIL G2 [{slug}] {r['candidate']} {r['election_year']}: "
                             f"tier {r['confidence']} without chain_closes=True")
                fails += 1
            if int(r["n_live"]) > 1:
                closure_den += 1
                if r["chain_closes"] == "True":
                    closure_num += 1
            # -- G5 no fabrication
            if r["raised_gross"]:
                ok = any((src.get((r["candidate"], r["election_year"], k)) or {})
                         .get("stated_total_contributions") not in (None, "")
                         for k in gov)
                if not ok or not gov:
                    lines.append(f"FAIL G5 [{slug}] {r['candidate']} {r['election_year']}: "
                                 f"published figure with no parseable governing total")
                    g5 += 1
                if r["gap_reason"]:
                    lines.append(f"FAIL G5 [{slug}] {r['candidate']} {r['election_year']}: "
                                 f"published figure AND a gap_reason")
                    g5 += 1
            else:
                code = (r["gap_reason"] or "").split(":")[0].strip()
                if code not in GAP_REASONS:
                    lines.append(f"FAIL G5 [{slug}] {r['candidate']} {r['election_year']}: "
                                 f"blank figure with gap_reason {r['gap_reason']!r}")
                    g5 += 1
            # -- G6 carryover never silently folded
            n = r["raised_net_of_carryover"]
            if n and not (r["regime"].startswith("per-period") and n == r["raised_gross"]) \
                    and r["regime_basis"] != "override":
                lines.append(f"FAIL G6 [{slug}] {r['candidate']} {r['election_year']}: "
                             f"net {n} on regime {r['regime']}")
                g6 += 1
        fails += g1 + g5 + g6
        rate = f"{100.0 * closure_num / closure_den:.1f}%" if closure_den else "n/a"
        lines.append(f"  [{slug}] {len(rows)} cycles · G1 {'PASS' if not g1 else f'{g1} FAIL'}"
                     f" · G5 {'PASS' if not g5 else f'{g5} FAIL'}"
                     f" · G6 {'PASS' if not g6 else f'{g6} FAIL'}"
                     f" · chain closure {closure_num}/{closure_den} ({rate}) of "
                     f"multi-filing cycles")
        tot["cycles"] += len(rows)
        tot["closure_num"] += closure_num
        tot["closure_den"] += closure_den
    lines.append(f"  ALL: {tot['cycles']} cycles · chain closure "
                 f"{tot['closure_num']}/{tot['closure_den']}")
    if verbose:
        print("\n".join(lines))
    return fails, lines


def report(slugs):
    """The tier / regime / carryover / itemized-agreement run record (gates G2, G7)."""
    allrows = []
    dropped_all = []
    for slug in slugs:
        rows, dropped = cycle_totals_county(slug)
        allrows += rows
        dropped_all += [(slug,) + d for d in dropped]
    tiers = ["A", "A-superseded", "B", "C", ""]
    lab = {"": "GAP"}
    print("=== TIER DISTRIBUTION (spec §5) ===")
    print(f"{'county':20s}" + "".join(f"{lab.get(t, t):>14s}" for t in tiers)
          + f"{'TOTAL':>8s}{'PUBLISHES':>11s}")
    per = defaultdict(lambda: defaultdict(int))
    for r in allrows:
        per[r["city"]][r["confidence"]] += 1
    grand = defaultdict(int)
    for c in sorted(per):
        row = per[c]
        for t in tiers:
            grand[t] += row[t]
        pub = sum(row[t] for t in tiers if t != "")
        print(f"{c:20s}" + "".join(f"{row[t]:14d}" for t in tiers)
              + f"{sum(row.values()):8d}{pub:11d}")
    pub = sum(grand[t] for t in tiers if t != "")
    print(f"{'ALL':20s}" + "".join(f"{grand[t]:14d}" for t in tiers)
          + f"{sum(grand.values()):8d}{pub:11d}")

    print("\n=== REGIME MIX ===")
    rm = defaultdict(int)
    for r in allrows:
        rm[r["regime"]] += 1
    for k in sorted(rm, key=lambda k: -rm[k]):
        print(f"  {k:24s} {rm[k]}")

    print("\n=== GAP REASONS ===")
    gr = defaultdict(int)
    for r in allrows:
        if r["gap_reason"]:
            gr[r["gap_reason"].split(":")[0]] += 1
    for k in sorted(gr, key=lambda k: -gr[k]):
        print(f"  {k:28s} {gr[k]}")

    print("\n=== EXCLUDED FILINGS (non-cycle statutory stream / blank election_year) ===")
    dd = defaultdict(int)
    for slug, cand, yr, sf, reason in dropped_all:
        dd[(slug, reason)] += 1
    for k in sorted(dd):
        print(f"  {k[0]:20s} {k[1]:22s} {dd[k]}")

    print("\n=== IS_FLOOR (published LOWER BOUNDS, owner ruling B2) ===")
    fl = defaultdict(int)
    for r in allrows:
        if r["is_floor"]:
            fl[r["city"]] += 1
    print(f"  {sum(fl.values())} of {pub} published cycles: "
          + ", ".join(f"{k} {v}" for k, v in sorted(fl.items())))

    print("\n=== CARRYOVER (reported in its own column; NEVER subtracted) ===")
    cz = [r for r in allrows if r["carryover_opening"]
          and float(r["carryover_opening"]) > 0.5 and r["raised_gross"]]
    print(f"  {len(cz)} of {pub} published cycles open with a non-zero balance; "
          f"total ${sum(float(r['carryover_opening']) for r in cz):,.2f}")
    for r in sorted(cz, key=lambda r: -float(r["carryover_opening"]))[:8]:
        print(f"    {r['city']:18s} {r['candidate'][:26]:26s} {r['election_year']}  "
              f"carry ${float(r['carryover_opening']):>12,.2f}  "
              f"raised ${float(r['raised_gross']):>12,.2f}  {r['regime']}")

    print("\n=== G7 ITEMIZED CROSS-CHECK (ADVISORY — never gates) ===")
    agg = defaultdict(lambda: [0, 0])
    diffs = []
    for r in allrows:
        if not r["itemized_check_raised"] or not r["raised_gross"]:
            continue
        if r["itemized_check_note"].startswith("not-comparable"):
            continue
        agg[r["city"]][1] += 1
        d = float(r["itemized_check_raised"]) - float(r["raised_gross"])
        if abs(d) <= 0.51:
            agg[r["city"]][0] += 1
        else:
            diffs.append((abs(d), r, d))
    for c in sorted(agg):
        ok, n = agg[c]
        print(f"  {c:20s} comparable {n:4d}  agree {ok:4d}  "
              f"({100.0 * ok / n:.1f}%)" if n else f"  {c:20s} none")
    print("  top disagreements:")
    for _, r, d in sorted(diffs, key=lambda t: -t[0])[:10]:
        print(f"    {r['city']:18s} {r['candidate'][:24]:24s} {r['election_year']}  "
              f"stated {float(r['raised_gross']):>12,.2f}  itemized "
              f"{float(r['itemized_check_raised']):>12,.2f}  delta {d:>+12,.2f}")
    return allrows


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    slugs = county_slugs() if "--all" in sys.argv else args
    if not slugs:
        slugs = county_slugs()
    if "--report" in sys.argv:
        report(slugs)
    elif "--validate" in sys.argv:
        n, _ = validate(slugs)
        print(f"\n{'ALL GATES PASS' if not n else f'{n} FAILURE(S)'}")
        sys.exit(1 if n else 0)
    else:
        for s in slugs:
            rows, dropped = write_county(s)
            pub = sum(1 for r in rows if r["raised_gross"])
            print(f"  {s}: {len(rows)} candidate-cycles ({pub} publish a figure, "
                  f"{len(rows) - pub} honest gaps; {len(dropped)} filing(s) outside the "
                  f"cycle stream) -> cycle_totals_county.csv")
