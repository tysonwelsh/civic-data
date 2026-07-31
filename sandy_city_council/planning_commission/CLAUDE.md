# Sandy City — Planning Commission subtree

Parallel dataset for Sandy's **Planning Commission** (Legistar body 140), sibling of
`meeting_minutes/`. Sandy is a **Legistar** city, so — unlike the prose-portal cities whose PC votes
are regex-parsed from minutes — Sandy's PC votes are the **exact structured Legistar roll-call records**
(`EventItemVote`), the same source the `db/` is built from.

## Files
- `all_votes.csv` — long format, one row per member-vote, `body="PlanningCommission"` / `title="Planning
  Commission"` every row. **Built from `db/staging/` (Legistar) by `build_from_legistar.py`**, filtered to
  EventBodyId 140. EXACT structured votes (not prose-parsed). 157 PC meetings 2020-01 → 2026-06; 554
  motions carrying a recorded roll call; 4,431 member-vote rows; 14 commissioners. Motions without a
  recorded per-member roll call (consent, voice) are not emitted as member rows (the `db/` still holds them).
- `roster.csv` — commissioners observed in the roll-call votes (commissioner, first_seen, last_seen, n_votes).
- `build_from_legistar.py` — regenerates the two CSVs from `db/staging/`. Pure Python, deterministic, no API.

**No PC minutes are on disk** (corrected 2026-07-02: an earlier version of this doc claimed a
`minutes/` dir, `minutes_index.csv`, and `minutes_unrecovered.csv` here — those were never
created). This subtree is exactly four files: `all_votes.csv`, `roster.csv`,
`build_from_legistar.py`, and this doc. PC minutes PDFs remain retrievable from Legistar InSite
(`View.ashx?M=M&ID=&GUID=`, GUIDs harvested from `Calendar.aspx`) if ever needed — but the votes
here do not depend on them (they come from the structured Legistar harvest, below).

## Why this differs from the other 12 cities
The other cities resolve votes by parsing minutes prose; Sandy gets them from the Legistar structured
harvest (exact, MatterId-keyed), so no minutes corpus is needed (or kept) in this subtree. The
cross-body PC↔Council referral layer lives in `db/` and, since 2026-07-02 (plan item 2.6), is built
by the same generalized template as the prose cities — the standard
`(primary_application_id, primary_body, related_application_id, related_body)` schema, 116 links.
In `db/sandy.db` every one of this file's 554 motions maps 1:1 to its Legistar EventItem
(`app_match_method='matter_id'`, exact); the full harvest is preserved in `legistar_*` extension
tables. See `db/SCHEMA.md`.

## Cardinal rule
Votes trace to Legistar `EventItemVote` records. Nothing is synthesized: motions with no
recorded per-member roll call simply have no member rows.
