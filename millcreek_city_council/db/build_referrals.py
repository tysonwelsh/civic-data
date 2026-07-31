#!/usr/bin/env python3
"""Millcreek cross-body referral build — thin stub (REFACTOR_PLAN 4.2).

Shared logic lives in scripts/referrals_lib.py (repo root). Idempotent; run AFTER
build_db.py:  python3 db/build_referrals.py
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, "scripts")))
from referrals_lib import main

# Utah planning CASE NUMBER (<PREFIX>-<YY>-<NNN>) — the strongest possible cross-body key when
# BOTH sides cite it. Millcreek's PC cites case numbers richly; Council minutes are mostly
# ordinance/resolution-number-keyed BUT a handful (~16 rows) DO cite the PC case number verbatim,
# so unlike South Jordan's one-sided PL bridge this key genuinely (thinly) bridges PC->Council.
CASE_NO_RE = re.compile(r'\b(?:CU|CUP|ZM|ZT|SD|SDA|GP|EX|SV|PUD|FC|LB|RC|SP)-\d{2}-\d{2,3}\b', re.I)
EXTRA_STOPWORDS = """
member made motioned moved motions second seconded approve approving adopt adopting boardmember
stated authorizing accepting designating consenting entering enter into acclamation nominate
respects recommend recommendation granted preliminary
allen anderson aryel bev booth burgess carlson catten cheri christian cianflone claerhout
david desirant diane dwayne dwight fred handy healey heather hulsberg ian jackson jacob jeff
jenny lamar larsen lofgren marchant mark mumford nicole per reid richardson russ scott shawn
sieber silvestrini silvia skye soule stephens steven thom tom uipi vance victoria wilson wright
""".split()    # Millcreek council/PC member + mover/second names — attribution boilerplate, not subject

if __name__ == "__main__":
    sys.exit(main(HERE, case_no_re=CASE_NO_RE, case_no_method_label="case_no",
                  case_no_report_label="case numbers", extra_stopwords=EXTRA_STOPWORDS))
