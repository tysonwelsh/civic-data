#!/usr/bin/env python3
"""The five marquee research questions, end to end, against gov.db (read-only).

Doubles as a documentation regression test: each query is the one the docs
advertise, and the script exits 1 if any returns nothing. Run from anywhere:

  python3 examples/marquee_queries.py
"""
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "gov.db")
if not os.path.exists(DB):
    sys.exit("gov.db not found — download the release asset or run "
             "`python3 scripts/build_cities_db.py` first (see README Quickstart).")

db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
failures = 0


def show(title, sql, params=(), limit=8):
    global failures
    print(f"\n{'='*76}\n{title}\n{'-'*76}")
    print(sql.strip())
    rows = db.execute(sql, params).fetchall()
    if not rows:
        print("!! NO ROWS — documented query returned nothing (doc regression)")
        failures += 1
        return
    for r in rows[:limit]:
        print("  " + " | ".join(str(c) for c in r))
    if len(rows) > limit:
        print(f"  … {len(rows) - limit} more rows")


# 1. Thematic full-text sweep (counts are matching DOCUMENTS, not occurrences)
show("1. Which entities' minutes discuss accessory dwelling units the most?", """
SELECT city, COUNT(*) AS docs
FROM fts_minutes WHERE fts_minutes MATCH '"accessory dwelling unit"'
GROUP BY city ORDER BY docs DESC
""")

# 2. Contested-vote rates, caveat-aware
show("2. Council-side contested rates (caveats flag non-comparable cities)", """
WITH c AS (SELECT city, COUNT(*) n FROM v_contested_all
           WHERE body != 'PlanningCommission' GROUP BY city),
     t AS (SELECT m.city, COUNT(*) n FROM motion m
           JOIN body b ON b.body_id = m.body_id
           WHERE b.name != 'PlanningCommission' AND m.gov_level='city'
           GROUP BY m.city)
SELECT t.city, t.n AS motions, COALESCE(c.n,0) AS contested,
       ROUND(100.0*COALESCE(c.n,0)/t.n, 1) AS pct,
       (SELECT GROUP_CONCAT(code,',') FROM caveat cv
         WHERE (cv.city=t.city OR cv.city='*')
           AND cv.dataset IN ('meeting_minutes','*')
           AND code IN ('tally-only','tally-only-partial','dissent-only','vote-ceiling'))
FROM t LEFT JOIN c ON c.city = t.city ORDER BY pct DESC
""")

# 3. PC-said-deny -> Council-approved (the technical-vs-political divergence)
show("3. Where did the elected body override the appointed body?", """
SELECT city, confidence, pc_date, pc_recommendation,
       council_date, council_outcome, substr(council_item, 1, 50)
FROM v_pc_divergence WHERE diverged = 1 ORDER BY city, council_date DESC
""")

# 4. Who voted against enacted land-use law
show("4. Nay votes on adopted land-use ordinances (unique-linked only)", """
SELECT o.city, o.ordinance_no, substr(o.title,1,45), p.full_name, v.vote_value
FROM ordinance o
JOIN motion m ON m.motion_id = o.motion_id
JOIN vote v   ON v.motion_id = m.motion_id
JOIN person p ON p.person_id = v.person_id
WHERE o.land_use != '' AND v.vote_value = 'Nay'
ORDER BY o.adoption_date DESC
""")

# 5. Money vs land-use votes (note the donor_type scope — see gov_db_SCHEMA.md)
show("5. Business-donor money vs land-use Ayes (cf_cycle holds real totals)", """
SELECT cc.city, cc.candidate, ROUND(SUM(cc.amount_num)) AS business_amt,
       (SELECT COUNT(*) FROM vote v
         JOIN motion_std ms ON ms.motion_id = v.motion_id
        WHERE v.person_id = cp.person_id
          AND ms.motion_type_std = 'Land-Use' AND v.vote_value='Aye') AS landuse_ayes
FROM cf_contribution cc
JOIN cf_candidate_person cp
  ON cp.city = cc.city AND cp.candidate = cc.candidate AND cp.person_id IS NOT NULL
WHERE cc.donor_type = 'business'
GROUP BY cc.city, cc.candidate HAVING business_amt > 0
ORDER BY business_amt DESC
""")

built = db.execute("SELECT value FROM build_info WHERE key='built_at'").fetchone()[0]
print(f"\ngov.db built_at: {built}")
if failures:
    print(f"{failures} marquee quer{'y' if failures==1 else 'ies'} returned NOTHING — "
          "documentation regression, investigate.")
    sys.exit(1)
print("All 5 marquee queries returned results.")
