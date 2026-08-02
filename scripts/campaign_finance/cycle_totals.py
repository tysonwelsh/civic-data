#!/usr/bin/env python3
"""Canonical per-candidate CYCLE-TOTAL rollup for the structured campaign-finance layer.

WHY THIS EXISTS
---------------
`filing_totals.csv` is one row PER FILING, not per candidate-cycle. Candidates file
several reports per cycle (interim reports + a year-end summary/final), in mixed
incremental / cumulative styles — and the style can vary BY CANDIDATE within one city
(Logan: 7 incremental + 2 cumulative filers; Orem: interims + a cumulative year-end
summary). Naively summing a candidate's filings therefore DOUBLE-COUNTS. This module
encodes the correct dedup once so no downstream query has to (and can't get it wrong):

  cycle total per (candidate, election_year) =
     • if the candidate filed a SUMMARY / FINAL report → the LATEST such report's stated
       total (a summary is cumulative-to-date: it already contains the interims); else
     • the SUM of the candidate's interim reports (pure per-period chain); else
     • the single filing's stated total.
  Superseded filings (amendments / exact re-files, flagged in filing_totals.notes) are
  dropped first.

MIXED-STYLE HAZARD (the Orem case): if a candidate has BOTH interims and a summary AND
the summed interims MATERIALLY EXCEED the latest summary, the summary is NOT a true
cumulative-of-everything — the classification or extraction is suspect. We do NOT guess:
we take the summary (conservative) and set `review_flag` so it surfaces for a human.

`basis` vocabulary (2026-07-19, truthful-label pass): `summary` (both figures are the
latest summary's), `sum-interim` (both are the summed/cumulative-last interims), `single`
(one filing), `max-mixed` (the max() rule took raised from one source and spent from the
other — a genuinely split pair, previously mislabeled by the spent side alone), `override`
(cycle_overrides.csv), `none`.

REGIME FILTER (2026-07-19): rows whose trailing `filing_regime` column is a non-empty
value other than `election_cycle` (Taylorsville's `annual` March-1 statements) are
EXCLUDED before grouping — mandatory annual financial statements are a parallel statutory
stream and must never enter race totals. Cities without the column are unaffected.

Reads existing dataset outputs only (filing_totals.csv + index.csv for office/seat);
never rebuilds. Regenerate after any `build_finance.py` run.

Usage:
  python3 scripts/campaign_finance/cycle_totals.py <city>          # writes <city>/campaign_finance/cycle_totals.csv
  python3 scripts/campaign_finance/cycle_totals.py --all           # every city that has a structured layer
  python3 scripts/campaign_finance/cycle_totals.py --all --races   # also print a top-races-by-spend ranking
"""
import csv, os, re, sys, glob

SUMMARY_TYPES = {"summary", "final", "year-end", "yearend", "annual", "combined"}
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from entities import ENTITIES, by_slug  # noqa: E402  (registry resolution, 2026-08-01)


def _cf_dir(slug):
    """campaign_finance dir for any entity slug. Cities resolve to the SAME
    <slug>_city_council path as the pre-2026-08-01 hardcode (by_slug('lehi').dir ==
    'lehi_city_council'), so city behavior is unchanged by construction; county/other
    entities resolve through the registry (county-CF federation, 2026-08-01)."""
    try:
        e = by_slug(slug)
        if e.dir:
            return os.path.join(REPO, e.dir, "campaign_finance")
    except KeyError:
        pass
    return os.path.join(REPO, f"{slug}_city_council", "campaign_finance")


def _norm(n):
    t = re.sub(r"[^A-Za-z ]", "", (n or "").upper()).split()
    return (t[0], t[-1]) if t else ("", "")


def _f(x):
    try:
        return float((x or "").replace(",", "").replace("$", ""))
    except Exception:
        return None


def _load_index(p):
    idx = {}
    fp = os.path.join(p, "index.csv")
    if os.path.exists(fp):
        for r in csv.DictReader(open(fp)):
            idx[(_norm(r.get("candidate", "")), r.get("election_year", ""))] = r
    return idx


def _load_overrides(p):
    """Optional <city>/campaign_finance/cycle_overrides.csv — the documented correction
    mechanism for candidate-cycles whose incremental-vs-cumulative shape the generic rules
    cannot classify but a human has verified against the filings (e.g. a per-period filer
    whose 'final' report is itself a period, so neither max() branch is right). Columns:
    candidate,election_year,raised,spent,reason,added — values REPLACE the computed ones,
    basis becomes 'override', review_flag carries the reason."""
    fp = os.path.join(p, "cycle_overrides.csv")
    if not os.path.exists(fp):
        return {}
    return {(_norm(r["candidate"]), r["election_year"].strip()): r
            for r in csv.DictReader(open(fp))}


def cycle_totals(city):
    """Return a list of per-candidate-cycle dicts for one city."""
    p = _cf_dir(city)
    ftp = os.path.join(p, "filing_totals.csv")
    if not os.path.exists(ftp):
        return []
    idx = _load_index(p)
    overrides = _load_overrides(p)
    by = {}  # (cand, year) -> list of filing dicts
    excluded_regime = 0
    for r in csv.DictReader(open(ftp)):
        # REGIME FILTER (2026-07-19): a filing_totals.csv MAY carry a trailing
        # `filing_regime` column (Taylorsville: `annual` mandatory March-1 statements vs
        # `election_cycle` C&E disclosures). Only the election_cycle stream belongs in a
        # race total — an annual statement is a parallel statutory instrument, never part
        # of a campaign cycle. Blank/absent regime (single-regime cities) is unaffected.
        regime = (r.get("filing_regime") or "").strip()
        if regime and regime != "election_cycle":
            excluded_regime += 1
            continue
        key = (r.get("candidate", ""), r.get("election_year", ""))
        by.setdefault(key, []).append(r)
    if excluded_regime:
        print(f"  [{city}] {excluded_regime} non-election_cycle filing(s) "
              f"(filing_regime!='election_cycle') excluded from cycle totals")

    def is_superseded(notes):
        """A filing is dropped ONLY when a structured note ENTRY begins with
        'superseded' (the driver's markers: 'superseded (cumulative snapshot…',
        'superseded by amendment…'). The old anywhere-substring match dropped a
        bluffdale filing whose free-text note merely MENTIONED supersession
        (Q3-2026 finding; that build carries a keep-the-word-out comment as a
        workaround — this fix makes the marker structural instead)."""
        return any(seg.strip().lower().startswith("superseded")
                   for seg in (notes or "").split(";"))

    out = []
    for (cand, year), filings in by.items():
        live = [f for f in filings if not is_superseded(f.get("notes", ""))]
        if not live:
            live = filings
        def totals(f):
            c = _f(f.get("stated_total_contributions", "")) or _f(f.get("itemized_contrib_sum", "")) or 0.0
            e = _f(f.get("stated_total_expenditures", "")) or _f(f.get("itemized_expend_sum", "")) or 0.0
            return c, e
        summaries = [f for f in live if (f.get("filing_type", "") or "").lower().strip() in SUMMARY_TYPES]
        interims = [f for f in live if (f.get("filing_type", "") or "").lower().strip() not in SUMMARY_TYPES]
        review = ""
        # A "summary/final" report is cumulative-to-date IN PRINCIPLE, but in practice some
        # filers leave the year-end form near-empty and keep the money in the interims
        # (verified in Orem: McKell's summary is the true $59.5k cumulative, but Mecham's is
        # $750 while his interims sum to ~$25k). So per candidate take whichever is larger —
        # max(latest summary, summed interims) — and flag when they diverge materially.
        s_raised = s_spent = i_raised = i_spent = 0.0
        if summaries:
            latest = max(summaries, key=lambda f: (f.get("filing_date", ""), totals(f)[1]))
            s_raised, s_spent = totals(latest)
        if interims:
            # Interims are USUALLY per-period (→ sum), but some filers file *cumulative*
            # interims that each restate cycle-to-date (→ summing 6× overcounts, e.g. Orem
            # Dave Young: 6 interims ≈ $22k each summing to $132k). Detect a cumulative chain
            # by a non-decreasing stated-total sequence in filing-date order and take the last
            # instead of the sum.
            iord = sorted(interims, key=lambda f: f.get("filing_date", ""))
            def _cumulative(getter):
                vals = [getter(totals(f)) for f in iord]
                return len(vals) >= 3 and all(b >= a - 1 for a, b in zip(vals, vals[1:])) and vals[-1] > 0
            i_raised = totals(iord[-1])[0] if _cumulative(lambda t: t[0]) else sum(totals(f)[0] for f in interims)
            i_spent = totals(iord[-1])[1] if _cumulative(lambda t: t[1]) else sum(totals(f)[1] for f in interims)
        if summaries and interims:
            # Cumulative-restatement detection (West Valley, Buhler 2021): some filers'
            # interim reports each restate cycle-to-date (the general filing photocopies the
            # primary's schedules) and the summary repeats the last interim's figures, so
            # summing interims double-counts. Proof from the data itself: the latest
            # interim's stated raised equals the summary's (±$1) while its spent does not
            # exceed the summary's — then the summary IS the cycle.
            iord2 = sorted(interims, key=lambda f: f.get("filing_date", ""))
            li_raised, li_spent = totals(iord2[-1])
            if (len(interims) > 1 and s_raised > 0
                    and abs(li_raised - s_raised) <= 1.0 and li_spent <= s_spent + 1.0):
                raised, spent, basis = s_raised, s_spent, "summary"
            else:
                raised = max(s_raised, i_raised)
                spent = max(s_spent, i_spent)
                # TRUTHFUL basis label (2026-07-19): this branch takes max() PER SIDE, so
                # the pair of figures may not come from one source. "summary" is claimed
                # ONLY when both figures are the summary's, "sum-interim" only when both
                # are the interim sums; a genuinely split pair (raised from one source,
                # spent from the other) is labeled "max-mixed" — the old code stamped it
                # "summary"/"sum-interim" by the spent side alone, which was a lie about
                # the raised figure's provenance. Ties count as either source.
                if s_raised >= i_raised and s_spent >= i_spent:
                    basis = "summary"
                elif i_raised >= s_raised and i_spent >= s_spent:
                    basis = "sum-interim"
                else:
                    basis = "max-mixed"
                # Flag only genuinely ambiguous cases: BOTH the summary and the interim-sum are
                # substantial yet disagree (a near-empty year-end form vs real interims is the
                # clear-cut case where interims win, not worth flagging).
                if min(s_spent, i_spent) > 1000 and abs(s_spent - i_spent) > 0.25 * max(s_spent, i_spent):
                    review = (f"MIXED: latest summary ${s_spent:,.0f} vs summed interims ${i_spent:,.0f} spent "
                              f"— took the larger; verify per-candidate incremental-vs-cumulative")
        elif summaries:
            raised, spent, basis = s_raised, s_spent, "summary"
        elif interims:
            raised, spent = i_raised, i_spent
            basis = "sum-interim" if len(interims) > 1 else "single"
        else:
            raised = spent = 0.0
            basis = "none"
        ov = overrides.get((_norm(cand), year))
        if ov:
            raised, spent = float(ov["raised"]), float(ov["spent"])
            basis = "override"
            review = f"OVERRIDE: {ov.get('reason', '')}".strip()
        meta = idx.get((_norm(cand), year), {})
        office = (meta.get("office", "") or filings[0].get("office", "") or "").strip()
        seat = (meta.get("seat", "") or meta.get("district", "") or "").strip()
        out.append({
            "city": city, "candidate": cand.strip(), "election_year": year,
            "office": office, "seat": seat,
            "raised": round(raised, 2), "spent": round(spent, 2),
            "n_filings": len(filings), "n_live": len(live), "basis": basis,
            "review_flag": review,
        })
    out.sort(key=lambda d: (d["election_year"], d["office"], d["seat"], -d["spent"]))
    return out


COLS = ["city", "candidate", "election_year", "office", "seat",
        "raised", "spent", "n_filings", "n_live", "basis", "review_flag"]


def write_city(city):
    rows = cycle_totals(city)
    if not rows:
        return 0, 0
    outp = os.path.join(_cf_dir(city), "cycle_totals.csv")
    with open(outp, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    flags = sum(1 for r in rows if r["review_flag"])
    return len(rows), flags


def all_cities():
    # every registry entity with a structured layer (cities AND counties since
    # 2026-08-01); registry order is stable, sort keeps the historical output order
    return sorted(e.slug for e in ENTITIES if e.dir and os.path.exists(
        os.path.join(REPO, e.dir, "campaign_finance", "filing_totals.csv")))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    do_all = "--all" in sys.argv
    do_races = "--races" in sys.argv
    cities = all_cities() if do_all else args
    everything = []
    for c in cities:
        n, flags = write_city(c)
        everything.extend(cycle_totals(c))
        fl = f" — {flags} review-flag(s)" if flags else ""
        print(f"  {c}: {n} candidate-cycles -> cycle_totals.csv{fl}")
    if do_races:
        from collections import defaultdict
        races = defaultdict(dict)
        for r in everything:
            if "mayor" in (r["office"] + " " + r["seat"]).lower():
                continue
            m = re.search(r"district\s*([1-9])", (r["office"] + " " + r["seat"]).lower())
            seat = f"District {m.group(1)}" if m else (r["seat"] or "at-large")
            key = (r["city"], r["election_year"], seat)
            races[key][r["candidate"]] = max(r["spent"], races[key].get(r["candidate"], 0))
        ranked = []
        for k, cands in races.items():
            if len(cands) < 2:
                continue
            top2 = sorted(cands.items(), key=lambda x: -x[1])[:2]
            ranked.append((sum(s for _, s in top2), k, top2))
        ranked.sort(reverse=True)
        print("\nMost expensive council races (top-2 combined spent):")
        for total, (city, yr, seat), top2 in ranked[:10]:
            who = " + ".join(f"{c} ${s:,.0f}" for c, s in top2)
            print(f"  ${total:>10,.0f}  {city} {yr} {seat}: {who}")
