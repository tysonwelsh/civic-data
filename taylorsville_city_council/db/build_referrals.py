#!/usr/bin/env python3
"""Taylorsville cross-body referral build — thin stub (REFACTOR_PLAN 4.2).

Shared logic lives in scripts/referrals_lib.py (repo root). Idempotent; run AFTER
build_db.py:  python3 db/build_referrals.py
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, "scripts")))
from referrals_lib import main

# Utah planning CASE NUMBER (<SEQ><LETTER><YY>, e.g. 15Z19 / 2SI24) — the strongest possible
# cross-body key WHEN BOTH sides cite it. Here they do NOT: Taylorsville's Planning Commission
# cites case numbers richly, but the Council/RDA minutes are ordinance/resolution-number-keyed
# and cite ZERO case numbers (verified). So — like South Jordan's one-sided PL bridge, and
# UNLIKE Millcreek — this key never bridges PC->Council; it only groups PC motions within-body.
# The case-number probe therefore yields 0 shared cross-body numbers (reported, expected);
# cross-body links fall to address + subject + temporal.
CASE_NO_RE = re.compile(r'\b\d{1,3}(?:SI|GP|[ZSCGP])\d{2}\b', re.I)
EXTRA_STOPWORDS = """
member made motioned moved motions second seconded approve approving adopt adopting boardmember
stated authorizing accepting designating consenting entering enter into acclamation nominate
respects recommend recommendation granted preliminary
anna barbieri bob knudsen brad christopherson curt cochran dan armstrong ernest burgess
meredith harker don quigley david wright gordon willardson marc mcelreath lynette wendel
cindy wilkey russell young kent burggraaf barbara munoz murphy kristie overson
""".split()    # Taylorsville council/PC member + mayor + mover/second names — attribution boilerplate, not subject

if __name__ == "__main__":
    sys.exit(main(HERE, case_no_re=CASE_NO_RE, case_no_method_label="case_no",
                  case_no_report_label="case numbers", extra_stopwords=EXTRA_STOPWORDS))
