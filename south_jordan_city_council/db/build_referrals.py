#!/usr/bin/env python3
"""South Jordan cross-body referral build — thin stub (REFACTOR_PLAN 4.2).

Shared logic lives in scripts/referrals_lib.py (repo root). Idempotent; run AFTER
build_db.py:  python3 db/build_referrals.py
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, "scripts")))
from referrals_lib import main

# Utah planning FILE NUMBER (PL...) — the strongest possible cross-body key when BOTH sides cite it.
# In South Jordan the PC cites PL numbers richly but Council minutes are terse/ordinance-number-keyed
# and cite NONE, so this bridge is (correctly) empty; it is implemented + reported for honesty and
# so it fires automatically if a future council motion ever carries a PL number.
CASE_NO_RE = re.compile(r'\bPL[A-Z]{1,4}\d{5,}\b', re.I)
EXTRA_STOPWORDS = """
member made motioned moved motions second seconded approve approving adopt adopting boardmember
stated authorizing accepting designating consenting entering enter into
bevans bishop catmull darby farnsworth gedge harding harris hollist johnson marlor mcguire
morrissey peirce ramsey shelton starks wimmer zander""".split()    # SJ mover/second surnames — attribution boilerplate, not subject

if __name__ == "__main__":
    sys.exit(main(HERE, case_no_re=CASE_NO_RE, case_no_method_label="pl_number",
                  case_no_report_label="PL file numbers", extra_stopwords=EXTRA_STOPWORDS))
