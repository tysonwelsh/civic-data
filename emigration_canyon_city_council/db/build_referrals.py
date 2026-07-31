#!/usr/bin/env python3
"""Cross-body referral build — thin stub over scripts/referrals_lib.py."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, "scripts")))
from referrals_lib import main
if __name__ == "__main__":
    sys.exit(main(HERE))
