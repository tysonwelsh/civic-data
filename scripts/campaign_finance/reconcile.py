#!/usr/bin/env python3
"""reconcile.py — itemized-sum vs stated-total checks -> extraction_confidence.

The anti-fabrication core (SCHEMA.md §Reconciliation). For each filing side (contributions,
expenditures) we compare the sum of the itemized rows against the form's own printed total.
Match within $0.01 -> the side reconciles and its rows earn full confidence (high for
born-digital text, medium for OCR). Mismatch -> the whole side is flagged and its rows are
capped at `low`. A stated total we could not read leaves reconciles = "" (unknown).

Nothing here ever adjusts a figure. It only classifies.
"""
from __future__ import annotations

TOLERANCE = 0.01


def reconciles(itemized_sum, stated_total, tol=TOLERANCE):
    """Return (reconciles_bool_or_None, delta_or_None).

    None reconciliation when the stated total is unknown (can't judge). delta is
    itemized_sum - stated_total (signed) when both are known.
    """
    if stated_total is None:
        return None, None
    if itemized_sum is None:
        return False, None
    delta = round(itemized_sum - stated_total, 2)
    return (abs(delta) <= tol), delta


def side_confidence(is_text: bool, reconciles_bool) -> str:
    """Confidence for the rows on one side of a filing.

    born-digital + reconciles -> high ; OCR + reconciles -> medium ;
    anything that does not (or cannot) reconcile -> low.
    """
    if reconciles_bool is True:
        return "high" if is_text else "medium"
    return "low"


def filing_confidence(contrib_conf: str, expend_conf: str) -> str:
    """Filing-level confidence = the weaker of the two sides."""
    order = {"high": 3, "medium": 2, "low": 1, "": 0}
    return min([contrib_conf, expend_conf], key=lambda c: order.get(c, 0))
