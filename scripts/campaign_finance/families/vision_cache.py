#!/usr/bin/env python3
"""vision_cache — form family for cities consumed ENTIRELY from vision caches.

These cities' filings are scans (or fillable templates whose text layer is garbage —
the taylorsville disease), so there is no text grammar to parse: every transcribed
filing is fed through the driver's `rows_override_fn` from its
`vision/<sha1(index_path)[:8]>.json` cache (see `scripts/campaign_finance/vision_lib.py`),
and a filing with NO cache flows through as an honest inventory-only row
(`vision_lib.empty_result`). This module exists to satisfy the family contract; its
`parse()` is only reached if a city's build forgets the override — it returns an empty,
clearly-noted result rather than pretending to read a scan.

§10-3-208 NOTE (2026-07-19 survey): herriman's city-local `_stdform_parse` (the born-
digital Utah §10-3-208 Schedule A/B/C text parser) was surveyed for promotion into
families/ and DECLINED — the statutory anchor phrases appear in 9 other cities' filings,
but the parser reconciled 0/15 sampled out-of-city filings both sides (per-city column
geometry differs). It stays herriman-only; see the verdict comment in
herriman_city_council/campaign_finance/build_finance.py.
"""
from __future__ import annotations


def parse(text, meta):  # noqa: ARG001 — contract signature
    return dict(contrib_rows=[], expend_rows=[], stated_contrib=None,
                stated_expend=None, stated_begin=None, stated_end=None,
                notes="vision_cache family: no text grammar (scan/template city); "
                      "filing not fed by a vision cache")
