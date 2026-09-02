#!/usr/bin/env python3
"""test_families.py — unit tests for the TRANCHE 3 Phase A county form families + the two new
driver capabilities (2026-08-02).

Run:  python3 scripts/campaign_finance/tests/test_families.py

Every fixture under `fixtures/` is a SMALL VERBATIM EXCERPT of a file the repo already retains
(the county's own `text/` sidecar, or `pdftotext -layout` of a retained born-digital PDF). The
assertions are the GROUND TRUTHS each county's own CLAUDE.md / AVAILABILITY.md states, so a
regression here means the library stopped reproducing a figure a human verified at the source:

  washco_split               Iverson 2014  $130 + $500 = $630 (summary states 630 for the 4/4
                             deadline);  Whitehead 2010  $375 + $25 = $400 expenditures
  utahcounty_schedab         Tanner Ainge 2018 Column A 4,585.77 / 7,845.74 (NOT the Column B
                             51,983.16 / 50,047.72);  Paxman 2026 Box B cash 168,872.24 with the
                             in-kind column reproducing the printed 7,670.68
  weber_polimorphic          New 1,000.19;  Beesley 1,120.00 / 867.92;  Tait 1,973.10 both sides
  cache_cfd                  Hurd Apr-3 397.76 / 613.88 (dash style);  Hurd Jun-16 316.72 /
                             508.83 (whitespace style) + per-FILING period_basis
  wasatch_disclosure_tableab Forsyth 2026-06 70.57 / 1,062.84 with Table B summing exactly;
                             Kahler "zero" -> 0.00;  Bonner 2024 general garbled -> NOTHING
  summit_form                Langston 20765 contributions 503.00 / expenditures 511.62 — AND an
                             explicit assertion that 511.62 is NOT produced as the contribution
                             total (the documented millcreek/ogden transposition failure)
"""
from __future__ import annotations

import os
import sys
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(HERE)
sys.path[:0] = [LIB, os.path.join(LIB, "families")]
FIX = os.path.join(HERE, "fixtures")

import common                                            # noqa: E402
import driver                                            # noqa: E402
import registry                                          # noqa: E402


def fx(name):
    with open(os.path.join(FIX, name), encoding="utf-8", errors="replace") as fh:
        return fh.read()


def meta(**kw):
    m = dict(candidate="X", office="", seat="", election_year="2026", filing_date="",
             reporting_period="", source_filing="raw/fixture", document_id="",
             extract_method="test/text", is_scanned=False)
    m.update(kw)
    return m


def csum(res, side="contrib_rows", cash_only=False):
    rows = res[side]
    if cash_only:
        rows = [r for r in rows if r.in_kind != "True"]
    return round(sum(float(r.amount) for r in rows if r.amount), 2)


# ===================================================================== shared primitives

class TestZeroGlyphAndMoney(unittest.TestCase):
    """GOTCHAS.md ZERO-GLYPH RULING (owner, 2026-08-02) + the never-repair rule."""

    def test_zero_glyphs_read_as_zero(self):
        for tok in ("Ø", "-0-", "- 0 -", "zero", "Zero", "ZERO"):
            v, kind = common.parse_money_cell(tok)
            self.assertEqual((v, kind), (0.0, "zero-glyph"), tok)

    def test_nil_marks_stay_blank(self):
        for tok in ("-", "--", "N/A", "n/a", "NA", "None", ""):
            v, kind = common.parse_money_cell(tok)
            self.assertIsNone(v, tok)
            self.assertIn(kind, ("nil", "empty"), tok)

    def test_malformed_decimals_are_never_repaired(self):
        # summit Ioannides 2024: cents comma; and a double-dot thousands read
        for tok in ("23,744,71", "23.744.71", "2,250.-", "0.-", "$ 15 1,4 11.5 4"):
            v, kind = common.parse_money_cell(tok)
            self.assertIsNone(v, tok)
            self.assertEqual(kind, "unparseable", tok)

    def test_malformed_token_yields_no_span(self):
        # the load-bearing lookaround: `23,744` must NOT be lifted out of `23,744,71`
        self.assertEqual(common.money_cell_spans("cum 23,744,71"), [])
        self.assertEqual([t[2] for t in common.money_cell_spans("cur 23,744.71 x")], [23744.71])


class TestPrivacyAddressSplit(unittest.TestCase):
    """PRIVACY.md: an itemized row carries donor_city/donor_state ONLY."""

    CASES = [
        ("168 S 50 W Hyde Park, UT 84318", ("Hyde Park", "UT")),
        ("3020 Sweetgum Cir, St George UT 84790", ("St George", "UT")),
        ("PO Box 128, Coalville, UT", ("Coalville", "UT")),
        ("Wellsville, UT", ("Wellsville", "UT")),
        ("460 S Greenfield Rd Ste 2, Mesa 85206", ("Mesa", "")),
        ("1005 Grove Drive, 84004", ("", "")),          # no city stated -> honest blank
        ("Hooper, UT", ("Hooper", "UT")),
    ]

    def test_city_state_only(self):
        for addr, want in self.CASES:
            self.assertEqual(common.split_city_state(addr), want, addr)

    def test_no_street_ever_returned(self):
        for addr, _want in self.CASES:
            city, state = common.split_city_state(addr)
            self.assertFalse(any(ch.isdigit() for ch in city + state), addr)


class TestGeometryChannel(unittest.TestCase):
    """SCHEMA.md §2a — the trailing, optional `geometry` column."""

    def test_canonical_headers_exclude_geometry(self):
        self.assertNotIn("geometry", common.CONTRIB_HEADER)
        self.assertNotIn("geometry", common.EXPEND_HEADER)
        self.assertEqual(common.CONTRIB_HEADER_GEO[-1], "geometry")
        self.assertEqual(common.EXPEND_HEADER_GEO[-1], "geometry")

    def test_row_to_dict_omits_blank_geometry(self):
        r = common.ContribRow(candidate="A")
        self.assertNotIn("geometry", common.row_to_dict(r))
        r.geometry = "p1:l2:c3-4"
        self.assertEqual(common.row_to_dict(r)["geometry"], "p1:l2:c3-4")

    def test_formatters(self):
        self.assertEqual(common.geom_text(2, 14, 46, 55), "p2:l14:c46-55")
        self.assertEqual(common.geom_cell("Sheet1", 4, 5), "Sheet1!F5")

    def test_page_index_survives_form_feeds(self):
        text = "a\nb\fc\nd"
        self.assertEqual(len(common.page_line_index(text)), len(text.splitlines()))
        self.assertEqual([p for p, _l in common.page_line_index(text)], [1, 1, 2, 2])


# ============================================================================ families

class TestSummitForm(unittest.TestCase):
    FAM = registry.get("summit_form")

    def setUp(self):
        self.res = self.FAM.parse(fx("summit_langston_20765.txt"),
                                  meta(candidate="Dawn Mathiesen Langston", election_year="2022",
                                       filing_date="2022-12-08"))

    def test_langston_cover_totals(self):
        self.assertAlmostEqual(self.res["stated_contrib"], 503.00, 2)
        self.assertAlmostEqual(self.res["stated_expend"], 511.62, 2)
        self.assertAlmostEqual(self.res["stated_end"], 11.17, 2)

    def test_the_transposition_failure_is_NOT_reproduced(self):
        """RECON.md §4: millcreek_form and ogden_form both return 511.62 as 'total
        contributions'. That WRONG answer must never be produced here."""
        self.assertNotAlmostEqual(self.res["stated_contrib"], 511.62, 2)
        self.assertNotAlmostEqual(self.res["stated_contrib"], 0.00, 2)   # nor the Last column

    def test_itemization_reconciles_after_dropping_the_template_row(self):
        self.assertEqual(csum(self.res, "contrib_rows"), 503.00)
        self.assertEqual(csum(self.res, "expend_rows"), 511.62)
        self.assertIn("printed template example row", self.res["notes"])
        names = {r.donor_raw for r in self.res["contrib_rows"]}
        self.assertNotIn("Jon and Jane Doe", names)

    def test_rows_carry_geometry_and_city_state_only(self):
        for r in self.res["contrib_rows"]:
            self.assertRegex(r.geometry, r"^p\d+:l\d+:c\d+-\d+$")
            self.assertFalse(any(ch.isdigit() for ch in r.donor_raw), r.donor_raw)

    def test_declares_cumulative_regime_per_filing(self):
        self.assertEqual(self.res["dedup_mode"], "cumulative")
        self.assertEqual(self.res["is_incremental"], "False")

    def test_ioannides_malformed_cumulative_falls_back_to_current(self):
        res = self.FAM.parse(fx("summit_ioannides_24231_cover.txt"),
                             meta(candidate="Aristides Ioannides", election_year="2024"))
        self.assertAlmostEqual(res["stated_contrib"], 23744.71, 2)   # Current column
        self.assertAlmostEqual(res["stated_expend"], 32744.71, 2)    # Cumulative column
        self.assertIn("cumulative cell unparseable", res["notes"])


class TestWeberPolimorphic(unittest.TestCase):
    FAM = registry.get("weber_polimorphic")

    def _run(self, fixture, who):
        return self.FAM.parse(fx(fixture), meta(candidate=who, election_year="2026"))

    def test_new_1000_19(self):
        r = self._run("weber_new_polimorphic.txt", "Gary C New")
        self.assertAlmostEqual(r["stated_contrib"], 1000.19, 2)
        self.assertEqual(csum(r, "contrib_rows"), 1000.19)
        self.assertEqual(csum(r, "expend_rows"), 1000.19)
        self.assertEqual(len(r["contrib_rows"]), 3)

    def test_beesley_1120_and_867_92(self):
        r = self._run("weber_beesley_polimorphic.txt", "Jon D Beesley")
        self.assertAlmostEqual(r["stated_contrib"], 1120.00, 2)
        self.assertAlmostEqual(r["stated_expend"], 867.92, 2)
        self.assertEqual((len(r["contrib_rows"]), csum(r, "contrib_rows")), (7, 1120.00))
        self.assertEqual((len(r["expend_rows"]), csum(r, "expend_rows")), (2, 867.92))

    def test_tait_1973_10_both_sides(self):
        r = self._run("weber_tait_polimorphic.txt", "Michelle Tait")
        self.assertAlmostEqual(r["stated_contrib"], 1973.10, 2)
        self.assertAlmostEqual(r["stated_expend"], 1973.10, 2)
        self.assertEqual(csum(r, "contrib_rows"), 1973.10)
        self.assertEqual(csum(r, "expend_rows"), 1973.10)
        self.assertEqual((len(r["contrib_rows"]), len(r["expend_rows"])), (6, 6))

    def test_donor_geography_is_city_state_only(self):
        r = self._run("weber_new_polimorphic.txt", "Gary C New")
        self.assertEqual((r["contrib_rows"][0].donor_city, r["contrib_rows"][0].donor_state),
                         ("Hooper", "UT"))
        for row in r["contrib_rows"]:
            self.assertRegex(row.geometry, r"^p\d+:l\d+:c\d+-\d+$")

    def test_period_regime_declared_per_filing(self):
        r = self._run("weber_new_polimorphic.txt", "Gary C New")
        self.assertEqual((r["is_incremental"], r["dedup_mode"]), ("True", "incremental"))

    # --- the SINGLE-ENTRY fallback (2026-08-14, Tranche 3 Phase B) -----------------------
    # Polimorphic omits the `Itemized … Report (#n)` block header when a side has exactly one
    # entry, and the family used to return nothing for such a side (weber CLAUDE.md's
    # documented "FAMILY LIMITATION", the Allred 1,147.66 case). It is now parsed.
    def test_allred_single_entry_no_block_header(self):
        r = self._run("weber_allred_polimorphic_single.txt", "Chris Allred")
        self.assertAlmostEqual(r["stated_contrib"], 1147.66, 2)
        self.assertAlmostEqual(r["stated_expend"], 1147.66, 2)
        # ONE entry per side, each reconciling EXACTLY to the "on This Report" anchor
        self.assertEqual((len(r["contrib_rows"]), csum(r, "contrib_rows")), (1, 1147.66))
        self.assertEqual((len(r["expend_rows"]), csum(r, "expend_rows")), (1, 1147.66))
        c, e = r["contrib_rows"][0], r["expend_rows"][0]
        self.assertEqual((c.donor_raw, c.donor_city, c.date), ("Chris Allred", "Ogden",
                                                               "2026-01-02"))
        self.assertEqual((e.vendor_raw, e.purpose), ("Weber County Elections",
                                                     "Candidate filing fee"))
        self.assertRegex(c.geometry, r"^p\d+:l\d+:c\d+-\d+$")
        self.assertRegex(e.geometry, r"^p\d+:l\d+:c\d+-\d+$")
        self.assertIn("single-entry fallback", r["notes"])

    def test_arbon_answered_no_emits_nothing(self):
        """NEGATIVE CONTROL. Ryan Arbon 2026 answers **No** to both disclosure questions yet
        states 879.97 on both sides — an internal inconsistency in the source. The fallback
        must find no `Amount` line and emit NOTHING; a stated total is never turned into a
        fabricated row."""
        r = self._run("weber_arbon_polimorphic_noneyes.txt", "Ryan Arbon")
        self.assertAlmostEqual(r["stated_contrib"], 879.97, 2)
        self.assertAlmostEqual(r["stated_expend"], 879.97, 2)
        self.assertEqual((len(r["contrib_rows"]), len(r["expend_rows"])), (0, 0))

    def test_fallback_does_not_disturb_multi_entry_filings(self):
        """The fallback fires only when the header pass found nothing, so the three filings
        that DO carry block headers must be byte-for-byte what they always were."""
        for fixture, who, nc, ne in (("weber_new_polimorphic.txt", "Gary C New", 3, 3),
                                     ("weber_beesley_polimorphic.txt", "Jon D Beesley", 7, 2),
                                     ("weber_tait_polimorphic.txt", "Michelle Tait", 6, 6)):
            r = self._run(fixture, who)
            self.assertEqual((len(r["contrib_rows"]), len(r["expend_rows"])), (nc, ne),
                             fixture)
            self.assertNotIn("single-entry fallback", r["notes"], fixture)


class TestCacheCfd(unittest.TestCase):
    FAM = registry.get("cache_cfd")

    def test_dash_tokenized_filing_reconciles(self):
        r = self.FAM.parse(fx("cache_hurd_apr3.txt"),
                           meta(candidate="Mark Hurd", filing_date="2026-04-01"))
        self.assertAlmostEqual(r["stated_contrib"], 397.76, 2)
        self.assertAlmostEqual(r["stated_expend"], 613.88, 2)
        self.assertEqual((len(r["contrib_rows"]), csum(r, "contrib_rows")), (5, 397.76))
        self.assertEqual((len(r["expend_rows"]), csum(r, "expend_rows")), (7, 613.88))
        self.assertAlmostEqual(r["stated_begin"], 612.30, 2)
        self.assertAlmostEqual(r["stated_end"], 396.18, 2)

    def test_whitespace_filing_reconciles_and_is_period_scoped(self):
        r = self.FAM.parse(fx("cache_hurd_june16.txt"),
                           meta(candidate="Mark Hurd", filing_date="2026-06-14"))
        self.assertAlmostEqual(r["stated_contrib"], 316.72, 2)      # Box B, this period
        self.assertAlmostEqual(r["stated_contrib_ytd"], 491.73, 2)  # Box C, YTD — never summed
        self.assertEqual((len(r["contrib_rows"]), csum(r, "contrib_rows")), (3, 316.72))
        self.assertEqual((len(r["expend_rows"]), csum(r, "expend_rows")), (10, 508.83))
        self.assertIn("period_basis=period_and_ytd_differ", r["notes"])

    def test_per_filing_regime_differs_between_two_filings_of_one_candidate(self):
        a = self.FAM.parse(fx("cache_hurd_apr3.txt"), meta(candidate="Mark Hurd"))
        b = self.FAM.parse(fx("cache_hurd_june16.txt"), meta(candidate="Mark Hurd"))
        self.assertIn("period_basis=period_equals_ytd", a["notes"])
        self.assertIn("period_basis=period_and_ytd_differ", b["notes"])
        self.assertEqual(a["is_incremental"], "True")
        self.assertEqual(b["is_incremental"], "True")

    def test_street_address_never_leaves_the_parser(self):
        r = self.FAM.parse(fx("cache_hurd_apr3.txt"), meta(candidate="Mark Hurd"))
        for row in r["contrib_rows"]:
            self.assertFalse(any(ch.isdigit() for ch in row.donor_raw), row.donor_raw)
            self.assertNotIn("168 S 50 W", row.donor_raw + row.donor_city + row.donor_state)
        self.assertEqual({(x.donor_city, x.donor_state) for x in r["contrib_rows"]},
                         {("Hyde Park", "UT"), ("Wellsville", "UT")})


class TestWasatchTableAB(unittest.TestCase):
    FAM = registry.get("wasatch_disclosure_tableab")

    def test_forsyth_reconciles_exactly(self):
        r = self.FAM.parse(fx("wasatch_forsyth_202606.txt"),
                           meta(candidate="Lauren Forsyth", filing_date="2026-06-01"))
        self.assertAlmostEqual(r["stated_contrib"], 70.57, 2)
        self.assertAlmostEqual(r["stated_expend"], 1062.84, 2)
        self.assertEqual((len(r["expend_rows"]), csum(r, "expend_rows")), (6, 1062.84))

    def test_zero_word_promotes_to_zero(self):
        r = self.FAM.parse(fx("wasatch_kahler_202603.txt"),
                           meta(candidate="Rachel Kahler", filing_date="2026-03-01"))
        self.assertEqual(r["stated_contrib"], 0.0)
        self.assertEqual(r["stated_expend"], 0.0)
        self.assertIn("ZERO-GLYPH RULING", r["notes"])

    def test_garbled_scan_yields_no_figure(self):
        """Bonner's 2024 general prints `$ f -7 DD.oo` / `r Vbi&/\"q`. Its real $700.00 /
        $3,612.69 live in the vision cache; this parser must produce NEITHER."""
        r = self.FAM.parse(fx("wasatch_bonner_202411_garbled.txt"),
                           meta(candidate="Colleen Bonner", election_year="2024"))
        self.assertIsNone(r["stated_contrib"])
        self.assertIsNone(r["stated_expend"])
        self.assertEqual(r["contrib_rows"], [])
        self.assertIn("garbled", r["notes"])

    def test_declares_period_regime_per_filing(self):
        r = self.FAM.parse(fx("wasatch_forsyth_202606.txt"), meta(candidate="Lauren Forsyth"))
        self.assertEqual((r["is_incremental"], r["dedup_mode"]), ("True", "incremental"))

    # ---- Phase B date-grammar extension (the `wasatch-field-shift` calibration specimen).
    # Each of these three filings had BOTH sides withheld in Phase A because its date token
    # landed in the NAME column while the amounts still summed exactly to the printed total.
    # The assertions are written the way the specimen states its answer: the date must be the
    # DATE, the name must be the NAME, and the sum must still close.

    def test_spaced_month_name_dates_do_not_shift_the_name_column(self):
        """Woodard 2026-03 writes `17 Jan 2026` / `5 Jan 2026` / `26 Feb 2026`."""
        r = self.FAM.parse(fx("wasatch_woodard_202603_datefmt.txt"),
                           meta(candidate="Jon Woodard", election_year="2026"))
        self.assertEqual((len(r["contrib_rows"]), csum(r, "contrib_rows")), (5, 1779.60))
        self.assertEqual((len(r["expend_rows"]), csum(r, "expend_rows")), (5, 1768.42))
        self.assertEqual({x.donor_raw for x in r["contrib_rows"]}, {"Jon Woodard"})
        self.assertEqual([x.date for x in r["contrib_rows"]][:2], ["2026-01-17", "2026-01-05"])
        self.assertEqual(r["expend_rows"][0].vendor_raw, "Wasatch County")

    def test_dotted_dates_do_not_shift_the_name_column(self):
        """Kellogg 2026-03 writes `1.2.26`, `2.14.26` and — via the text layer — `11 .7.25`."""
        r = self.FAM.parse(fx("wasatch_kellogg_202603_dotdate.txt"),
                           meta(candidate="Michelle Kellogg", election_year="2026"))
        self.assertEqual((len(r["contrib_rows"]), csum(r, "contrib_rows")), (1, 3576.08))
        self.assertEqual((len(r["expend_rows"]), csum(r, "expend_rows")), (7, 3576.08))
        self.assertTrue(r["contrib_rows"][0].donor_raw.startswith("Self-Funded"))
        self.assertEqual(r["contrib_rows"][0].date, "2026-01-02")
        self.assertEqual(r["expend_rows"][0].date, "2025-11-07")      # the `11 .7.25` cell
        self.assertEqual(r["expend_rows"][0].vendor_raw, "Wix.com")

    def test_separatorless_dates_do_not_shift_the_name_column(self):
        """Vance 2026-06 writes `5May26` / `15Apr26` / `13May26` — no separators at all."""
        r = self.FAM.parse(fx("wasatch_vance_202606_compactdate.txt"),
                           meta(candidate="William B. Vance", election_year="2026"))
        self.assertEqual((len(r["contrib_rows"]), csum(r, "contrib_rows")), (1, 1200.00))
        self.assertEqual((len(r["expend_rows"]), csum(r, "expend_rows")), (6, 823.79))
        self.assertEqual(r["contrib_rows"][0].donor_raw,
                         "Wasatch County Republican Party")
        self.assertEqual(r["contrib_rows"][0].date, "2026-05-05")
        self.assertEqual([x.vendor_raw for x in r["expend_rows"]][:2],
                         ["SquareSpace", "Big Daddy Signs"])

    def test_a_month_word_is_never_eaten_as_a_date_when_the_date_cell_is_empty(self):
        """The negative control on the extension: enumerated month names only, and a date must
        be followed by digits. A vendor row whose date cell is blank keeps its whole name."""
        text = ('                 CAMPAIGN FINANCIAL DISCLOSURE\n'
                ' 2. Itemized total of all campaign expenditures*\n'
                '       (from Table "B" on page 2)                        $75.00\n'
                '              ITEMIZED EXPENDITURE REPORT - TABLE "B"\n'
                ' Date of   Person or Organization      Amount   Expenditure Purpose\n'
                '           May Company                 $50.00   Flyers\n'
                '           April Showers Printing      $25.00   Signs\n'
                '                             TOTAL:    $75.00\n')
        r = self.FAM.parse(text, meta(candidate="Test Filer", election_year="2026"))
        self.assertEqual([x.vendor_raw for x in r["expend_rows"]],
                         ["May Company", "April Showers Printing"])
        self.assertEqual([x.date for x in r["expend_rows"]], ["", ""])


class TestUtahCountySchedAB(unittest.TestCase):
    FAM = registry.get("utahcounty_schedab")

    def test_legacy_column_A_is_the_anchor_not_column_B(self):
        r = self.FAM.parse(fx("utahco_tainge_2018_legacy.txt"),
                           meta(candidate="Tanner Ainge", election_year="2018"))
        self.assertAlmostEqual(r["stated_contrib"], 4585.77, 2)      # Column A, this period
        self.assertAlmostEqual(r["stated_expend"], 7845.74, 2)
        self.assertAlmostEqual(r["stated_contrib_ytd"], 51983.16, 2)  # Column B — NEVER the anchor
        self.assertAlmostEqual(r["stated_expend_ytd"], 50047.72, 2)
        self.assertNotAlmostEqual(r["stated_contrib"], 51983.16, 2)
        self.assertEqual(csum(r, "contrib_rows"), 4585.77)

    def test_box_ladder_and_compound_inkind_cell(self):
        r = self.FAM.parse(fx("utahco_paxman_2026_boxaf.txt"),
                           meta(candidate="Isaac Paxman", election_year="2026"))
        self.assertAlmostEqual(r["stated_contrib"], 168872.24, 2)     # Box B cash component
        self.assertAlmostEqual(r["stated_expend"], 151411.54, 2)      # Box D
        self.assertIn("COMPOUND cell", r["notes"])
        self.assertEqual(csum(r, "contrib_rows", cash_only=True), 168872.24)
        ik = round(sum(float(x.amount) for x in r["contrib_rows"] if x.in_kind == "True"), 2)
        self.assertEqual(ik, 7670.68)                                 # printed IN-KIND total
        self.assertEqual({x.donor_raw for x in r["contrib_rows"] if x.in_kind == "True"},
                         {"Spencer Stokes", "Doug Ford", "All In For Utah PAC"})
        self.assertIn("in-kind split VERIFIED", r["notes"])

    def test_multipage_schedules_are_all_read(self):
        r = self.FAM.parse(fx("utahco_paxman_2026_boxaf.txt"), meta(candidate="Isaac Paxman"))
        self.assertGreater(len(r["contrib_rows"]), 40)
        pages = {x.geometry.split(":")[0] for x in r["contrib_rows"]}
        self.assertGreater(len(pages), 1)


class TestWashcoSplit(unittest.TestCase):
    FAM = registry.get("washco_split")

    @staticmethod
    def _parts(*names):
        return [dict(ix={}, text=fx(n), sidecar=n, is_scanned=False) for n in names]

    def test_iverson_2014_xls_630(self):
        r = self.FAM.parse_group(
            self._parts("washco_iverson_2014_summary.xlstxt",
                        "washco_iverson_2014_contributions.xlstxt"),
            meta(candidate="Victor Iverson", election_year="2014", filing_date="2014-04-04",
                 deadline="2014-04-04"))
        self.assertAlmostEqual(r["stated_contrib"], 630.00, 2)
        self.assertEqual(len(r["contrib_rows"]), 2)
        self.assertEqual(csum(r, "contrib_rows"), 630.00)
        self.assertEqual([(x.donor_raw, x.amount) for x in r["contrib_rows"]],
                         [("Derek Brown", "130.00"), ("Spencer Stokes", "500.00")])

    def test_iverson_geometry_is_a_real_cell_reference(self):
        r = self.FAM.parse_group(
            self._parts("washco_iverson_2014_summary.xlstxt",
                        "washco_iverson_2014_contributions.xlstxt"),
            meta(candidate="Victor Iverson", election_year="2014", deadline="2014-04-04"))
        for x in r["contrib_rows"]:
            self.assertRegex(x.geometry, r"^Sheet\d+![A-Z]+\d+$")

    def test_whitehead_2010_pdf_400(self):
        r = self.FAM.parse_group(
            self._parts("washco_whitehead_2010_summary.txt",
                        "washco_whitehead_2010_expenditures.txt"),
            meta(candidate="David Whitehead", election_year="2010", filing_date="2010-06-15",
                 deadline="2010-04-09"))
        self.assertAlmostEqual(r["stated_expend"], 400.00, 2)
        self.assertEqual(len(r["expend_rows"]), 2)
        self.assertEqual(csum(r, "expend_rows"), 400.00)
        self.assertEqual([(x.vendor_raw, x.amount) for x in r["expend_rows"]],
                         [("Washington County", "375.00"),
                          ("Washington County Republican Party", "25.00")])

    def test_wrapped_name_is_joined_dates_are_not_truncated(self):
        r = self.FAM.parse_group(
            self._parts("washco_whitehead_2010_summary.txt",
                        "washco_whitehead_2010_expenditures.txt"),
            meta(candidate="David Whitehead", election_year="2010", deadline="2010-04-09"))
        self.assertEqual([x.date for x in r["expend_rows"]], ["2010-03-15", "2010-04-05"])

    def test_column_positional_read_keeps_street_out_and_geography_in(self):
        r = self.FAM.parse(fx("washco_pulsipher_2010_contributions.txt"),
                           meta(candidate="Cory Pulsipher", election_year="2010",
                                filing_date="2010-06-15"))
        self.assertGreater(len(r["contrib_rows"]), 15)
        first = r["contrib_rows"][0]
        self.assertEqual(first.donor_raw, "Cory Pulsipher")
        self.assertEqual((first.donor_city, first.donor_state), ("St George", "UT"))
        for x in r["contrib_rows"]:
            self.assertNotIn("Sweetgum", x.donor_raw + x.donor_city)

    # ---------------------------------------------------------------- 2026-08-23 parser wave

    @staticmethod
    def _boxes(text):
        """A laid-out fixture -> the `bbox` word-box structure `bbox_lib.read_pdf_boxes` returns.

        Character cell -> points at a nominal 6.0pt advance and 26.0pt line pitch, which
        preserves every column RELATIONSHIP the real coordinates have. Used so the
        true-coordinate reader can be tested without shipping a binary PDF fixture.
        """
        lines = []
        for r, ln in enumerate(text.splitlines()):
            words = []
            for m in re.finditer(r"\S+", ln):
                words.append((m.start() * 6.0, m.end() * 6.0, m.group(0)))
            if words:
                lines.append({"y0": 74.0 + r * 26.0, "y1": 84.0 + r * 26.0, "words": words})
        return [{"width": 612.0, "height": 792.0, "lines": lines}]

    def test_name_above_address_layout_never_ships_the_street_as_the_donor(self):
        """The 2012 workbooks print the NAME ABOVE and the ADDRESS on the figures' own row.
        Read as the 2014 layout, the ADDRESS becomes `donor_raw` — a wrong value and a privacy
        breach at once."""
        r = self.FAM.parse(fx("washco_gardner_2012_nameabove.xlstxt"),
                           meta(candidate="Alan Gardner", election_year="2012"))
        got = [(x.donor_raw, x.amount, x.donor_type, x.donor_city) for x in r["contrib_rows"]]
        self.assertEqual([g[0] for g in got], ["Bob Holt", "AG LLC", "Jim Flohr"])
        self.assertEqual([g[1] for g in got], ["100.00", "600.00", "200.00"])
        for x in r["contrib_rows"]:
            self.assertNotRegex(x.donor_raw, r"\d")          # no street number ever
            self.assertNotIn("Joshua", x.donor_raw)

    def test_loan_column_ships_as_a_loan_not_as_a_dropped_row(self):
        r = self.FAM.parse(fx("washco_gardner_2012_nameabove.xlstxt"),
                           meta(candidate="Alan Gardner", election_year="2012"))
        loans = [x for x in r["contrib_rows"] if x.donor_type == "loan"]
        self.assertEqual([(x.donor_raw, x.amount) for x in loans], [("AG LLC", "600.00")])
        self.assertEqual(r["coverage"]["contributions"],
                         {"logical": 3, "emitted": 3})

    def test_in_kind_column_figure_is_a_contribution(self):
        """Kevin Brooks 2010: J Ryan Lee's three entries right-align under `In Kind` while cash
        amounts right-align under `Amount`, and the county's own summary row ($744.05) counts
        them as contributions."""
        text = (
            "All Contributions for          Kevin Brooks                                  Sheriff\n"
            "\n"
            "Name                                    Received           Amount            In Kind       Loan\n"
            "Address\n"
            "J Ryan Lee                                     3/18/2010                         $400.00\n"
            "2182 S 2440 E Cir, St George, UT\n"
            "Ryan Lee                                       5/19/2010        $300.00\n"
            "2182 S 2440 E Cir, St George, UT\n")
        part = dict(ix={}, text=text, sidecar="", is_scanned=False, bbox=self._boxes(text))
        r = self.FAM.parse_group([part], meta(candidate="Kevin Brooks", election_year="2010"))
        got = [(x.donor_raw, x.amount, x.in_kind) for x in r["contrib_rows"]]
        self.assertEqual(got, [("J Ryan Lee", "400.00", "True"),
                               ("Ryan Lee", "300.00", "False")])
        self.assertEqual(csum(r, "contrib_rows"), 700.00)

    def test_malformed_money_is_refused_and_the_side_reads_short(self):
        """`$5,00.00` is the county's own export typo (Cory Pulsipher 2010). It is never
        repaired, so the row is refused AND the coverage counters say the side is short — which
        is what makes the module withhold it rather than publish a short sum."""
        text = (
            "All Contributions for         Cory Pulsipher                              County Sheriff\n"
            "\n"
            "Name                                    Received           Amount         In Kind     Loan\n"
            "Address\n"
            "Cory Pulsipher                                 10/1/2009        $200.00       NO           NO\n"
            "Accu Form Plastics                             10/5/2009       $5,00.00       NO           NO\n"
            "Utah Bail Bond                                 2/17/2010        $100.00       NO           NO\n")
        part = dict(ix={}, text=text, sidecar="", is_scanned=False, bbox=self._boxes(text))
        r = self.FAM.parse_group([part], meta(candidate="Cory Pulsipher", election_year="2010"))
        self.assertEqual([x.amount for x in r["contrib_rows"]], ["200.00", "100.00"])
        cov = r["coverage"]["contributions"]
        self.assertEqual((cov["logical"], cov["emitted"]), (3, 2))
        self.assertIn("never repaired", r["notes"])

    def test_rows_are_stamped_with_the_part_file_they_were_read_from(self):
        """SCHEMA.md 2a caveat 1, fixed at emission: `(source_filing, line_no)` must point at
        the LEDGER file, not at the group's Summary."""
        parts = [dict(ix={"path": "raw/x/summary.xls"},
                      text=fx("washco_iverson_2014_summary.xlstxt"), sidecar="",
                      is_scanned=False),
                 dict(ix={"path": "raw/x/contributions.xls"},
                      text=fx("washco_iverson_2014_contributions.xlstxt"), sidecar="",
                      is_scanned=False)]
        r = self.FAM.parse_group(parts, meta(candidate="Victor Iverson", election_year="2014",
                                             deadline="2014-04-04",
                                             source_filing="raw/x/summary.xls"))
        self.assertEqual({x.source_filing for x in r["contrib_rows"]},
                         {"raw/x/contributions.xls"})

    def test_bbox_reader_keeps_one_column_model_across_pages(self):
        """The `-layout` grid drifts between pages of one document (Tersigni p1 cols 40-47 ->
        p2 cols 19-26) while the PDF's own coordinates do not. Page 2 must parse."""
        page1 = (
            "All Expenditures for Rob Tersigni                           Sheriff\n"
            "\n"
            "Recipient                      Received Amount     In Kind   Description\n"
            "\n"
            "Staples                                   $9.54             Mailing\n")
        pages = self._boxes(page1)
        # a SECOND page, laid out differently in characters but at the SAME true x as page 1
        p2 = {"width": 612.0, "height": 792.0, "lines": [
            {"y0": 88.0, "y1": 98.0, "words": [(56.0, 104.0, "Office"), (106.0, 140.0, "Max"),
                                               (252.0, 282.0, "$153.98"),
                                               (360.0, 400.0, "Mailing")]}]}
        pages.append(p2)
        part = dict(ix={}, text=page1, sidecar="", is_scanned=False, bbox=pages)
        r = self.FAM.parse_group([part], meta(candidate="Rob Tersigni", election_year="2010"))
        self.assertEqual([(x.vendor_raw, x.amount, x.geometry.split("@")[-1])
                          for x in r["expend_rows"]],
                         [("Staples", "9.54", "p1"), ("Office Max", "153.98", "p2")])

    def test_bbox_rows_carry_pct_geometry(self):
        text = ("All Expenditures for Rob Tersigni                           Sheriff\n"
                "\n"
                "Recipient                      Received Amount     In Kind   Description\n"
                "\n"
                "Staples                                   $9.54             Mailing\n")
        part = dict(ix={}, text=text, sidecar="", is_scanned=False, bbox=self._boxes(text))
        r = self.FAM.parse_group([part], meta(candidate="Rob Tersigni", election_year="2010"))
        for x in r["expend_rows"]:
            self.assertRegex(x.geometry, r"^pct:[\d.]+,[\d.]+,[\d.]+,[\d.]+@p\d+$")

    def test_summary_sheet_declares_the_incremental_regime(self):
        r = self.FAM.parse_group(
            self._parts("washco_iverson_2014_summary.xlstxt",
                        "washco_iverson_2014_contributions.xlstxt"),
            meta(candidate="Victor Iverson", election_year="2014", deadline="2014-04-04"))
        self.assertEqual((r["is_incremental"], r["dedup_mode"]), ("True", "incremental"))
        self.assertIn("never sum the summary rows", r["notes"])


# ================================================================= driver capabilities

class TestDriverPerFilingRegime(unittest.TestCase):
    """DELIVERABLE 1(a): a family may declare the regime PER FILING, composing with the existing
    string / callable `dedup_mode` without changing any current city's outcome."""

    @staticmethod
    def _ft(cand, year, date, src, notes="", period="p"):
        return common.FilingTotals(candidate=cand, election_year=year, filing_date=date,
                                   reporting_period=period, source_filing=src, notes=notes)

    def test_string_mode_unchanged_when_no_per_filing_verdicts(self):
        pairs = [(self._ft("A", "2026", "2026-03-01", "f1"), {}),
                 (self._ft("A", "2026", "2026-06-01", "f2"), {})]
        driver._mark_supersessions(pairs, "cumulative", lambda ix: False)
        self.assertIn("superseded", pairs[0][0].notes)
        self.assertEqual(pairs[1][0].notes, "")

    def test_per_filing_verdict_wins_over_the_run_level_mode(self):
        pairs = [(self._ft("A", "2026", "2026-03-01", "f1", period="March"), {}),
                 (self._ft("A", "2026", "2026-06-01", "f2", period="June"), {})]
        # run-level says cumulative, but the FAMILY read `incremental` off both filings
        driver._mark_supersessions(pairs, "cumulative", lambda ix: False,
                                   {"f1": "incremental", "f2": "incremental"})
        self.assertEqual(pairs[0][0].notes, "")     # incremental: distinct periods, no supersession
        self.assertEqual(pairs[1][0].notes, "")

    def test_callable_mode_partition_is_preserved(self):
        pairs = [(self._ft("A", "2026", "2026-03-01", "f1", period="March"), {}),
                 (self._ft("A", "2026", "2026-06-01", "f2", period="June"), {}),
                 (self._ft("B", "2026", "2026-03-01", "g1", period="March"), {}),
                 (self._ft("B", "2026", "2026-06-01", "g2", period="June"), {})]
        driver._mark_supersessions(
            pairs, lambda cand, year, members: "cumulative" if cand == "A" else "incremental",
            lambda ix: False)
        self.assertIn("superseded", pairs[0][0].notes)
        self.assertEqual(pairs[2][0].notes, "")

    def test_filings_with_no_regime_at_all_are_left_unmarked(self):
        pairs = [(self._ft("A", "2026", "2026-03-01", "f1", period="March"), {}),
                 (self._ft("A", "2026", "2026-06-01", "f2", period="June"), {})]
        driver._mark_supersessions(pairs, None, lambda ix: False, {"f1": "cumulative"})
        self.assertEqual(pairs[0][0].notes, "")     # a group of one in its partition
        self.assertEqual(pairs[1][0].notes, "")     # no regime -> untouched, never guessed


class TestDriverGrouping(unittest.TestCase):
    """DELIVERABLE 1(b): a family may parse a FILE-SET as one filing."""

    def test_no_group_fn_is_one_row_per_filing(self):
        rows = [{"path": "a"}, {"path": "b"}, {"path": "c"}]
        units, skipped = driver._group_index(rows, lambda ix: True, None)
        self.assertEqual([len(u) for u in units], [1, 1, 1])
        self.assertEqual(skipped, 0)

    def test_group_fn_merges_a_file_set_in_first_appearance_order(self):
        rows = [{"path": "s1", "k": "F1"}, {"path": "s2", "k": "F2"},
                {"path": "c1", "k": "F1"}, {"path": "e1", "k": "F1"}]
        units, _s = driver._group_index(rows, lambda ix: True, lambda ix: ix["k"])
        self.assertEqual([[r["path"] for r in u] for u in units],
                         [["s1", "c1", "e1"], ["s2"]])

    def test_falsy_key_leaves_the_row_standalone(self):
        rows = [{"path": "a", "k": ""}, {"path": "b", "k": ""}]
        units, _s = driver._group_index(rows, lambda ix: True, lambda ix: ix["k"])
        self.assertEqual([len(u) for u in units], [1, 1])

    def test_out_of_scope_rows_are_counted_not_grouped(self):
        rows = [{"path": "a", "k": "F"}, {"path": "b", "k": "F"}]
        units, skipped = driver._group_index(rows, lambda ix: ix["path"] != "b",
                                             lambda ix: ix["k"])
        self.assertEqual(([len(u) for u in units], skipped), ([1], 1))


class TestRegistry(unittest.TestCase):
    NEW = ("washco_split", "utahcounty_schedab", "weber_polimorphic", "cache_cfd",
           "wasatch_disclosure_tableab", "summit_form")

    def test_all_six_families_are_registered_and_importable(self):
        for fam in self.NEW:
            self.assertIn(fam, registry.known())
            mod = registry.get(fam)
            self.assertTrue(callable(getattr(mod, "parse", None)), fam)
            self.assertTrue((mod.__doc__ or "").strip(), f"{fam} has no module docstring")

    def test_every_new_family_cites_its_evidence(self):
        for fam in self.NEW:
            doc = registry.get(fam).__doc__ or ""
            self.assertIn("EVIDENCE", doc, fam)
            self.assertIn("CLAUDE.md", doc, fam)


if __name__ == "__main__":
    unittest.main(verbosity=2)
