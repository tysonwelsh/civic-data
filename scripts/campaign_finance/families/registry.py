#!/usr/bin/env python3
"""registry.py — form-family dispatch for the structured campaign-finance layer.

Each city's build_finance.py selects its parser by family id rather than importing a module
directly, so the framework generalizes to N families behind one shared driver contract. Every
family module exposes `parse(text: str, meta: dict) -> dict` returning at least:
  contrib_rows, expend_rows, stated_contrib, stated_expend, stated_begin, stated_end, notes
(and MAY add family-specific keys, e.g. EasyVote's stated_*_ytd / is_amendment).

Add a new family: drop `families/<name>.py` with a `parse()` and register it below.
"""
from __future__ import annotations

import importlib

# family id -> module name under scripts/campaign_finance/families/
_FAMILIES = {
    "provo_form": "provo_form",          # F1 — Provo self-hosted per-cycle pivot form
    "lehi_formab": "lehi_formab",        # F5 — Lehi Municipal Campaign Financial Disclosure + Form A/B
    "easyvote_schedab": "easyvote_schedab",  # F2 — EasyVote Report of Contributions & Expenditures
    "utah_standard_form": "utah_standard_form",  # self-hosted Utah municipal C&E form (Orem;
                                                 # reused by Logan/Nephi/Vineyard)
    "parkcity_form": "parkcity_form",            # Park City self-hosted Form A/B Campaign Financial Report
    "stgeorge_formab": "stgeorge_formab",        # St. George scanned "Campaign Finance Report" Form A/B
                                                 # (multi-candidate compilation; segmented per candidate)
    "ogden_form": "ogden_form",                  # Ogden self-hosted "Combined Report of Contributions &
                                                 # Expenditures" whole-cycle packet (Attachment A/B)
    "westvalley_form": "westvalley_form",        # West Valley City self-hosted "Campaign Finance
                                                 # Statement" Form A/B (bare-decimal amounts, cover-
                                                 # total anchor, inline in-kind/loan markers)
    "southjordan_form": "southjordan_form",      # South Jordan self-hosted "Campaign Financial
                                                 # Disclosure Report" (Section 1.12.050): EasyVote-
                                                 # like Column A/B summary + Schedule A/B itemization
    "taylorsville_form": "taylorsville_form",    # Taylorsville self-hosted "Report of Contributions
                                                 # & Expenditures" fillable PDF — TEMPLATE text layer
                                                 # w/ HANDWRITTEN figures (most filings need vision);
                                                 # two regimes (annual + election_cycle)
    "millcreek_form": "millcreek_form",          # F9 — Millcreek self-hosted "FINANCIAL CAMPAIGN
                                                 # REPORT" Form A/B (3-column LAST/THIS/CUMULATIVE
                                                 # cover box; 2021 = cumulative whole-cycle bundle,
                                                 # else per-period; interior subtotal lines dropped)
    "vision_cache": "vision_cache",              # F10 — vision-cache-consumed cities (2026-07-17
                                                 # wave: midvale reference + 13 clones): scans /
                                                 # garbled templates, ALL data from
                                                 # vision/<sha1(path)[:8]>.json via rows_override_fn
                                                 # (vision_lib.py); parse() is an honest empty stub
}


def get(family_id: str):
    """Return the family module for `family_id` (raises KeyError if unknown)."""
    if family_id not in _FAMILIES:
        raise KeyError(f"unknown campaign-finance form family {family_id!r}; "
                       f"known: {sorted(_FAMILIES)}")
    return importlib.import_module(_FAMILIES[family_id])


def known():
    return sorted(_FAMILIES)
