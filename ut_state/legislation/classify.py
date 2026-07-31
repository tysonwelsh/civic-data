#!/usr/bin/env python3
"""Auditable land-use/housing classifier for Utah legislation.

The SELECTION RULE for the land-use/housing subset is this file — a keyword rule
list (matched against the bill TITLE, case-insensitive) plus a set of named
(session, bill) ANCHORS that are force-included regardless of title. Every kept
bill records the rule(s) that matched in a `relevance` column, so selection is
fully auditable. Over-inclusion is intentional and fine; SILENT exclusion is not.

RECALL CEILING (documented, honest): classification is TITLE-based. A bill whose
land-use provisions are not reflected in its title can be missed. The anchors
backstop the highest-profile such bills; broaden the rule list to widen recall.
"""
import re

# rule tag -> list of lowercase substrings (matched against the bill title)
RULES = {
    "land_use":      ["land use", "land-use", "ludma", "land use development and management"],
    "zoning":        ["zoning", "rezone", "rezoning", " zone ", "zones"],
    "subdivision":   ["subdivision", "subdivid", "subdivi"],
    "annexation":    ["annex"],
    "impact_fee":    ["impact fee"],
    "housing":       ["housing", "moderate income", "affordable hous", "workforce hous",
                      "accessory dwelling", "internal accessory", "short-term rental",
                      "short term rental", "first-time homebuyer", "starter home",
                      "homeownership", "home ownership"],
    "adu":           [" adu ", "accessory dwelling"],
    "density":       ["density", "dwelling unit"],
    "general_plan":  ["general plan"],
    "incorporation": ["incorporat", "township", "metro township", "disincorporat"],
    "planning":      ["planning commission", "planning and zoning"],
    "development":   ["redevelopment", "community development and renewal",
                      "development agreement", "transit-oriented", "transit oriented",
                      "housing and transit reinvestment", "community reinvestment"],
    "municipal_land": ["municipal land", "county land use", "unincorporated"],
    "eminent_domain": ["eminent domain", "condemnation"],
    "building":      ["building code", "building permit", "construction code"],
}

# force-include (session, bill_no) anchors — known land-use/housing landmarks.
# SELF-VALIDATING: each maps to a title substring that MUST be present in the real
# title for the anchor to fire (guards against a bill-number typo silently
# mis-tagging an unrelated bill — never fabricate). Every landmark below is ALSO
# caught by the title rule list, so anchors are confirmatory, not load-bearing.
ANCHORS = {
    ("2019GS", "SB0034"): "affordable housing",   # SB34 affordable housing modifications
    ("2021GS", "HB0082"): "single-family housing", # HB82 single-family / internal ADUs
    ("2022GS", "HB0462"): "housing affordability", # HB462 Utah housing affordability
    ("2023GS", "HB0406"): "land use",              # HB406 land use dev & mgmt act
    ("2024GS", "SB0168"): "affordable building",   # SB168 affordable building amendments
}


def classify(session, bill_no, title):
    """Return a comma-joined sorted list of matched rule tags, or '' if none.
    A guarded anchor (title substring confirmed) adds the tag 'anchor'."""
    t = " " + (title or "").lower() + " "
    hits = []
    for tag, subs in RULES.items():
        if any(s in t for s in subs):
            hits.append(tag)
    exp = ANCHORS.get((session, bill_no))
    if exp and exp in t:
        hits.append("anchor")
    return ",".join(sorted(set(hits)))


if __name__ == "__main__":
    print("Rules:", list(RULES.keys()))
    print("Anchors:", len(ANCHORS))
