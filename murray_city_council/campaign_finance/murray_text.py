#!/usr/bin/env python3
"""murray_text.py — Murray's born-digital text-layer consumer for build_finance.py.

Murray is UNLIKE midvale: a large share of its filings are **born-digital** Utah Code
10-3-208 forms whose text layer carries REAL, parseable money (verified: Ben Peck 2025
Pre-Primary = $5,700.00 contributions / $4,002.81 expenditures). Leaving that money out
(the midvale "text-is-junk" default) would be an alta-style loss, so those filings were
transcribed from the authoritative born-digital text layer (pdftotext / openpyxl) into
`text_cache/<sha1(index_path)[:8]>.json` — the SAME WJ vision-cache schema the scanned
`vision/` caches use — and this module maps them to the driver's parse()-shaped result
with an honest `.../text` extract_method (so they read as born-digital, not vision).

Only 2021/2023/2025 in-scope born-digital filings have a text_cache entry; the
2017/2019 below-floor cycles are inventory-only (no text_cache), like the scans.
"""
from __future__ import annotations

import json
from pathlib import Path

import vision_lib  # shared repo lib (READ-ONLY; we consume, never edit)


def load_text_cache(text_dir, index_path):
    p = Path(text_dir) / f"{vision_lib.cache_key(index_path)}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def build_text_result(cache, meta, family_id):
    """Born-digital text_cache dict -> the parse()-shaped result the driver reconciles.
    Mirrors vision_lib.build_result's single-report path but stamps the rows with a
    `<family>/text` extract_method (born-digital), never `/vision`. Murray's text_cache
    filings are all single-report (no `reports[]` bundles)."""
    vm = f"{family_id}/text"
    crows, erows = vision_lib._rows_from(cache, meta, vm)
    return dict(
        contrib_rows=crows, expend_rows=erows,
        stated_contrib=vision_lib.vmoney(cache.get("total_contributions")),
        stated_expend=vision_lib.vmoney(cache.get("total_expenditures")),
        stated_begin=vision_lib.vmoney(cache.get("beginning_balance")),
        stated_end=vision_lib.vmoney(cache.get("ending_balance")),
        notes="born-digital text layer (pdftotext/openpyxl-transcribed)")
