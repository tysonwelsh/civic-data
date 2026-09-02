#!/usr/bin/env python3
"""test_cycle_totals_county.py — regression suite for the COUNTY cycle reducer.

Run:  python3 scripts/campaign_finance/tests/test_cycle_totals_county.py

Every case is a specimen named in `COUNTY_CYCLE_REDUCER_SPEC.md` §7.2 (T1-T13). The fixtures
in `fixtures/county_cycle_filings.py` are VERBATIM `filing_totals.csv` rows copied out of the
repo's own county datasets, so a failure here means the reducer stopped reproducing a figure
a human verified against the filing itself. The tests never touch gov.db or the live CSVs.

The two NEGATIVE CONTROLS (T11, T12) are the most important cases in the file: they assert
that the reducer produces NO NUMBER where the documents do not establish one. Producing a
figure there is a test FAILURE, not a nicer answer (cardinal rule 1).
"""
from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(HERE)
sys.path[:0] = [LIB, os.path.join(HERE, "fixtures")]

import cycle_totals_county as R                          # noqa: E402
import cycle_totals                                      # noqa: E402
import county_cycle_filings as F                         # noqa: E402


def run(slug, rows, con=None, exp=None):
    """Reduce one candidate-cycle through the SHIPPING code path."""
    filings, dropped = R.scope_filter(rows)
    assert filings, "fixture produced no in-scope filings"
    cand = filings[0]["candidate"]
    year = filings[0]["election_year"]
    return R.reduce_group(slug, cand, year, filings, con=con, exp=exp)


class T1_Rivera(unittest.TestCase):
    """SLCo `Rivera, Rosie` 2022 — nine filings, five labelled reporting period April 5 with
    mutually inconsistent totals (the 2026-08-02 deferral's $68,605 / $38,236 / $31,019 case).
    The BALANCE CHAIN resolves it with no marker, no heuristic and no guess."""

    def setUp(self):
        self.r = run("salt_lake_county", F.T1_slco_rivera_2022)

    def test_chain_totals(self):
        self.assertEqual(self.r["raised_gross"], "142340.79")
        self.assertEqual(self.r["spent_gross"], "115745.48")
        self.assertEqual(self.r["carryover_opening"], "1341.42")
        self.assertEqual(self.r["ending_balance"], "27936.73")
        self.assertEqual(self.r["chain_closes"], "True")
        self.assertEqual(self.r["confidence"], "A-superseded")
        self.assertEqual(self.r["regime"], "per-period")
        self.assertEqual(self.r["regime_basis"], "chain-closure")
        self.assertEqual(int(self.r["chain_len"]), 5)
        self.assertEqual(int(self.r["n_live"]), 9)

    def test_the_amendment_trio_never_sums(self):
        # the four earlier versions all open from 0.00 and link to nothing
        excl = self.r["excluded_filings"]
        self.assertEqual(excl.count("orphan-not-chained"), 4)
        for h in ("E3F0DBD0", "8108996C", "F9736DDB", "AEDF400A"):
            self.assertIn(h, excl)
        # the naive sum of all nine stated totals, which must never appear
        self.assertNotEqual(self.r["raised_gross"], "376530.29")

    def test_carryover_reported_not_folded(self):
        self.assertEqual(self.r["carryover_basis"], "chain-first-bb")
        self.assertEqual(self.r["raised_net_of_carryover"], self.r["raised_gross"])

    def test_closure_proof_is_exact(self):
        self.assertAlmostEqual(1341.42 + 142340.79 - 115745.48, 27936.73, places=2)


class T2_T3_WeberFroerer(unittest.TestCase):
    """weber `Gage Froerer` — the supersede marker, the cumulative rule, and officeholder
    carryover reported in its own column."""

    def test_t2_supersede_marker_and_no_sum(self):
        r = run("weber_county", F.T2_weber_froerer_2022)
        self.assertIn("superseded-note", r["excluded_filings"])
        self.assertTrue(r["regime"].startswith("cumulative"))
        self.assertEqual(r["raised_gross"], "13895.18")
        self.assertNotEqual(r["raised_gross"], "45310.23")   # the naive sum
        self.assertEqual(r["carryover_opening"], "8895.18")
        # OWNER RULING B1: never computed for a cumulative cycle
        self.assertEqual(r["raised_net_of_carryover"], "")

    def test_t3_officeholder_carryover_is_reported_never_subtracted(self):
        r22 = run("weber_county", F.T2_weber_froerer_2022)
        r18 = run("weber_county", F.T3_weber_froerer_2018)
        # his 2018 final ends at 7,815.05 — the opening balance of his 2022 June report
        self.assertEqual(r18["ending_balance"], "7815.05")
        self.assertNotEqual(r22["carryover_opening"], "")
        # no cross-cycle subtraction is ever attempted
        self.assertEqual(r22["raised_net_of_carryover"], "")
        self.assertEqual(r18["raised_net_of_carryover"], "")

    def test_t3_harvey_2024_opens_from_his_2020_closing(self):
        r20 = run("weber_county", F.T3c_weber_harvey_2020)
        r24 = run("weber_county", F.T3b_weber_harvey_2024)
        self.assertNotEqual(r24["carryover_opening"], "")
        self.assertNotEqual(r20["ending_balance"], "")
        self.assertEqual(r24["carryover_opening"], r20["ending_balance"])


class T4_SummitBrickey(unittest.TestCase):
    """summit `David R. Brickey` 2014 — the specimen that proves the city reducer is wrong
    for a cumulative corpus: two filings stating 15,600.00 then 16,800.00."""

    def test_latest_cumulative_never_the_sum(self):
        r = run("summit_county", F.T4_summit_brickey_2014)
        self.assertEqual(r["raised_gross"], "16800.00")
        self.assertNotEqual(r["raised_gross"], "32400.00")
        self.assertEqual(r["regime"], "cumulative")
        self.assertEqual(r["regime_basis"], "filing-arithmetic")
        self.assertEqual(r["confidence"], "B")
        # summit prints no beginning balance anywhere: 0 of 131 filings
        self.assertEqual(r["carryover_basis"], "")
        self.assertEqual(r["carryover_opening"], "")

    def test_the_printed_arithmetic_backs_the_answer(self):
        self.assertAlmostEqual(16800.00 - 15540.12, 1259.88, places=2)


class T5_UtahBuhman(unittest.TestCase):
    """utah `Jeffrey R. Buhman` 2014 — four filings, TWO OF THEM CARVED FROM ONE PDF, both
    stating 15,209.58. The chain places three and orphans the duplicate."""

    def test_chain_total_matches_the_filer_ytd(self):
        r = run("utah_county", F.T5_utah_buhman_2014)
        self.assertEqual(r["raised_gross"], "15709.58")
        self.assertNotEqual(r["raised_gross"], "30919.16")   # the naive sum of all four
        self.assertEqual(r["confidence"], "A-superseded")
        self.assertEqual(r["chain_closes"], "True")

    def test_duplicate_restatement_excluded_once(self):
        r = run("utah_county", F.T5_utah_buhman_2014)
        self.assertEqual(r["excluded_filings"].count("="), 1)

    def test_one_pdf_two_filings_are_named_distinctly(self):
        # G1 reproducibility: `source_filing` repeats inside this group, so the governing
        # list must disambiguate with an ordinal or the figure is not re-derivable.
        r = run("utah_county", F.T5_utah_buhman_2014)
        gov = r["governing_filings"].split(";")
        self.assertEqual(len(gov), len(set(gov)))
        self.assertTrue(any("#" in g for g in gov + r["excluded_filings"].split(";")))


class T6_UtahCleanPerPeriod(unittest.TestCase):
    """utah `Kris Poulson` 2010 — a clean tier-A per-period cycle, three chained filings."""

    def test_tier_a(self):
        r = run("utah_county", F.T6_utah_poulson_2010)
        self.assertEqual(r["regime"], "per-period")
        self.assertEqual(r["chain_closes"], "True")
        self.assertEqual(r["confidence"], "A")
        self.assertEqual(int(r["chain_len"]), int(r["n_live"]))
        self.assertEqual(r["raised_net_of_carryover"], r["raised_gross"])
        self.assertEqual(r["is_floor"], "")


class T7_WashingtonRestatingLedger(unittest.TestCase):
    """washington `Chris White` 2014 — every itemized row is `is_incremental=False`, i.e. each
    ledger RESTATES the cycle. The advisory cross-check must take the LATEST ledger, never
    the sum, and must not touch the stated-total derivation either way."""

    LEDGERS = {
        "raw/wayback_financialreports/4 4 2014 Contributions - Chris White_04-04-2014.xls":
            [{"amount": "512.82", "is_incremental": "False"}],
        "raw/wayback_financialreports/6 17 2014 Contributions - Chris White_06-17-2014.xls":
            [{"amount": "512.82", "is_incremental": "False"}],
        "raw/wayback_financialreports/10 28 2014 Contributions - Chris White_10-28-2014.xls":
            [{"amount": "512.82", "is_incremental": "False"},
             {"amount": "100.00", "is_incremental": "False"},
             {"amount": "153.09", "is_incremental": "False"},
             {"amount": "50.00", "is_incremental": "False"}],
        "raw/wayback_financialreports/1 5 2015 Contributions - Chris White_01-08-2015.xls":
            [{"amount": "512.82", "is_incremental": "False"},
             {"amount": "100.00", "is_incremental": "False"},
             {"amount": "153.09", "is_incremental": "False"},
             {"amount": "50.00", "is_incremental": "False"}],
    }

    def test_latest_ledger_not_the_sum(self):
        gov = [{"source_filing": p, "reporting_period": "", "filing_date": d, "c": None}
               for p, d in (
                   (list(self.LEDGERS)[0], "2014-04-04"),
                   (list(self.LEDGERS)[3], "2015-01-08"))]
        ir, ie, note = R.itemized_check(gov, self.LEDGERS, {}, "per-period")
        self.assertEqual(ir, "815.91")            # the latest ledger
        self.assertNotEqual(ir, "1328.73")        # never the sum of the two
        self.assertEqual(note, "latest-ledger")

    def test_the_stated_derivation_is_unaffected(self):
        with_items = run("washington_county", F.T8_wash_white_2012, con=self.LEDGERS)
        without = run("washington_county", F.T8_wash_white_2012)
        self.assertEqual(with_items["raised_gross"], without["raised_gross"])
        self.assertEqual(with_items["gap_reason"], without["gap_reason"])


class T8_WashingtonTemplateNeverDecides(unittest.TestCase):
    """washington `Chris White` 2012 — the county's TEMPLATE is per-period, but the template
    never decides. Each cycle settles on its own arithmetic or emits a gap."""

    def test_template_never_decides(self):
        r = run("washington_county", F.T8_wash_white_2012)
        self.assertEqual(R.COUNTY_PRIOR["washington_county"], "mixed")
        # a MIXED prior can never fire the county-prior rule
        self.assertNotEqual(r["regime_basis"], "county-prior")
        # this filer mixes period-only and cumulative-only reports and no chain resolves
        # them, so the honest answer is a gap naming the conflict — not a number
        self.assertEqual(r["raised_gross"], "")
        self.assertTrue(r["gap_reason"].startswith("regime-conflict"))

    def test_filing_regime_is_not_the_basis(self):
        # every fixture row carries filing_regime='election_cycle' (a STATUTORY STREAM),
        # which must never be read as an arithmetic basis
        self.assertTrue(all(x["filing_regime"] == "election_cycle"
                            for x in F.T8_wash_white_2012))


class T9_WasatchPeriodSheetRestater(unittest.TestCase):
    """wasatch `Colleen Bonner` 2024 — filed on the 2024 PERIOD sheet (`filing_regime='period'`)
    but restating cumulatively. Classified from her own arithmetic; the form family and the
    `filing_regime` column are both irrelevant to the basis."""

    def test_cumulative_despite_period_form(self):
        r = run("wasatch_county", F.T9_wasatch_bonner_2024)
        self.assertTrue(all(x["filing_regime"] == "period"
                            for x in F.T9_wasatch_bonner_2024))
        self.assertEqual(r["regime"], "cumulative")
        self.assertEqual(r["regime_basis"], "filing-arithmetic")
        self.assertEqual(r["raised_gross"], "700.00")
        self.assertNotEqual(r["raised_gross"], "5650.00")     # the naive sum
        self.assertNotEqual(r["regime_basis"], "county-prior")


class T10_SLCoDeBry(unittest.TestCase):
    """SLCo `DeBry, Steve` 2022 — the documented filer who put CUMULATIVE figures in SLCo's
    per-period column. Caught from HIS OWN ARITHMETIC, not from the county prior."""

    def test_cumulative_from_own_arithmetic(self):
        r = run("salt_lake_county", F.T10_slco_debry_2022)
        self.assertEqual(R.COUNTY_PRIOR["salt_lake_county"], "per-period")
        self.assertTrue(r["regime"].startswith("cumulative"))
        self.assertNotEqual(r["regime_basis"], "county-prior")
        self.assertEqual(r["carryover_opening"], "46616.34")
        self.assertEqual(r["raised_gross"], "0.00")           # his final/dissolution report
        # never summed as if the four reports were disjoint periods
        self.assertNotEqual(r["raised_gross"], "280355.90")
        self.assertEqual(r["raised_net_of_carryover"], "")


class T11_NegativeControl_NeitherBasis(unittest.TestCase):
    """NEGATIVE CONTROL — washington `Brock R. Belnap` 2010. The filer's arithmetic closes on
    NEITHER reading (500 contributions, 500 expenditures, 500 ending balance, blank opening).
    PRODUCING ANY NUMBER HERE IS A TEST FAILURE."""

    def test_emits_a_gap_row_not_a_figure(self):
        r = run("washington_county", F.T11_wash_belnap_2010)
        self.assertEqual(r["raised_gross"], "")
        self.assertEqual(r["spent_gross"], "")
        self.assertEqual(r["confidence"], "")
        self.assertEqual(r["is_floor"], "")
        self.assertEqual(r["governing_filings"], "")
        self.assertTrue(r["gap_reason"].startswith("neither-basis"))

    def test_a_gap_is_still_a_row(self):
        r = run("washington_county", F.T11_wash_belnap_2010)
        self.assertEqual(r["candidate"], "Brock R. Belnap")
        self.assertEqual(r["election_year"], "2010")
        self.assertEqual(set(r) - set(R.COLS), set())


class T12_NegativeControl_BrokenChain(unittest.TestCase):
    """NEGATIVE CONTROL — the weber swapped-cover class, synthesized per spec §7.2: two
    INTERNALLY CONSISTENT covers filed under each other's key, so each closes on its own
    arithmetic but neither links to the other. NEVER a silent sum."""

    PAIR = [
        {"candidate": "Swapped Cover", "election_year": "2020", "office": "Commission",
         "filing_date": "2020-06-15", "reporting_period": "June", "filing_type": "interim",
         "stated_beginning_balance": "0.00", "stated_total_contributions": "5000.00",
         "stated_total_expenditures": "1000.00", "stated_ending_balance": "4000.00",
         "source_filing": "raw/synthetic/swap_a.pdf", "notes": "", "filing_regime": ""},
        {"candidate": "Swapped Cover", "election_year": "2020", "office": "Commission",
         "filing_date": "2020-10-25", "reporting_period": "October", "filing_type": "interim",
         "stated_beginning_balance": "9000.00", "stated_total_contributions": "2000.00",
         "stated_total_expenditures": "500.00", "stated_ending_balance": "10500.00",
         "source_filing": "raw/synthetic/swap_b.pdf", "notes": "", "filing_regime": ""},
    ]

    def test_no_chain_no_sum(self):
        r = run("weber_county", self.PAIR)
        self.assertLess(int(r["chain_len"]), int(r["n_live"]))
        self.assertNotIn(r["confidence"], ("A", "A-superseded"))
        self.assertNotEqual(r["raised_gross"], "7000.00")     # the forbidden silent sum

    def test_period_only_pair_gaps_with_chain_broken(self):
        r = run("weber_county", self.PAIR)
        # both covers are period-only (BB + C - E = EB on each), so no cumulative rule can
        # fire and the county prior may not overrule their own arithmetic
        self.assertEqual(r["raised_gross"], "")
        self.assertTrue(r["gap_reason"].startswith("chain-broken"))


class T13_Guard(unittest.TestCase):
    """The §0 landmine: the CITY reducer must not be able to touch a county, even if someone
    later runs `cycle_totals.py --all`."""

    def test_all_cities_returns_no_county(self):
        slugs = cycle_totals.all_cities()
        self.assertTrue(slugs)
        self.assertEqual([s for s in slugs if s.endswith("_county")], [])

    def test_write_city_refuses_a_county(self):
        with self.assertRaises(ValueError):
            cycle_totals.write_city("weber_county")

    def test_the_two_target_lists_are_disjoint(self):
        self.assertEqual(set(cycle_totals.all_cities()) & set(R.county_slugs()), set())

    def test_the_two_artifacts_have_different_names(self):
        # the structural half of the guard: the city loader reads cycle_totals.csv, so the
        # county artifact must never be able to answer to that name
        self.assertNotIn("cycle_totals_county.csv", str(cycle_totals.write_city.__doc__ or ""))
        self.assertTrue(all(os.path.basename(
            os.path.join(R.cf_dir(s), "cycle_totals_county.csv")) == "cycle_totals_county.csv"
            for s in R.county_slugs()))


class Primitives(unittest.TestCase):
    """The anti-fabrication primitives the whole layer rests on."""

    def test_a_blank_is_never_zero(self):
        for tok in ("", "  ", "-", "N/A", "n/a", "None", "--"):
            self.assertIsNone(R.money(tok), tok)
        self.assertEqual(R.money("0"), 0.0)
        self.assertEqual(R.money("$1,234.56"), 1234.56)
        self.assertEqual(R.money("(500.00)"), -500.0)

    def test_supersede_marker_is_structural_not_a_substring(self):
        # the bluffdale incident: a note that merely MENTIONS supersession is not a marker
        self.assertFalse(R.is_superseded(
            "the clerk explained that an amendment would have superseded this report"))
        self.assertTrue(R.is_superseded("superseded by amendment 2022-06-28"))
        self.assertTrue(R.is_superseded(
            "NOTE: this June amended report is SUPERSEDED by the 2022-11-01 report"))

    def test_county_prior_covers_all_eight_counties(self):
        self.assertEqual(set(R.COUNTY_PRIOR), set(R.county_slugs()))

    def test_only_annual_is_a_noncycle_stream(self):
        # `per-period` / `cumulative` / `period` are ARITHMETIC BASES in this column and must
        # never be filtered out — the city rule would drop all of utah, weber and wasatch
        for basis in ("per-period", "cumulative", "period", "election_cycle"):
            self.assertNotIn(basis, R.NONCYCLE_REGIMES)
        _, dropped = R.scope_filter([
            {"candidate": "X", "election_year": "2020", "filing_regime": "per-period"},
            {"candidate": "X", "election_year": "2020", "filing_regime": "cumulative"},
            {"candidate": "X", "election_year": "2020", "filing_regime": "period"},
            {"candidate": "X", "election_year": "2020", "filing_regime": "annual"},
            {"candidate": "X", "election_year": "", "filing_regime": ""},
        ])
        self.assertEqual([d[3] for d in dropped],
                         ["non-cycle-stream", "blank-election-year"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
