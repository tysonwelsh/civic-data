#!/usr/bin/env python3
"""
South Jordan Planning Commission refresh — thin mirror of the repo-root
`../fetch_new.py`, scoped to the `planning_commission` dataset.

Council + PC both live on the same CivicPlus ArchiveCenter portal (council list
/484, PC list /486), so the real logic is the shared root driver; this mirror
just forces `--dataset planning_commission` for convenience:

    python3 planning_commission/fetch_new.py            # probe PC only
    python3 planning_commission/fetch_new.py --fetch    # fetch PC only

Equivalent to `python3 fetch_new.py --dataset planning_commission [...]`.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import fetch_new as driver  # noqa: E402
import refresh_lib as rl  # noqa: E402

if __name__ == "__main__":
    if "--dataset" not in sys.argv:
        sys.argv += ["--dataset", "planning_commission"]
    rl.run_cli(ROOT, driver.DATASETS,
               "South Jordan PC refresh (CivicPlus ArchiveCenter)")
