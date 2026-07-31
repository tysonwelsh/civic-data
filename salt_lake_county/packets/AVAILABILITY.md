# packets/ — availability, coverage, and the §9 doc_class layer

**As-of 2026-07-16** (doc_class backfill). Source: Legistar Web API `v1/slco`,
via `../db/harvest_packets.py`. Honest gaps/empties are data — recorded, never filled.

## Coverage ledger (index.csv — 454 rows)

| packet_kind | rows | stored | text | notes |
|---|---|---|---|---|
| agenda | 310 | 310 | 310 | County Council 259, Redevelopment Agency 35, Municipal Building Authority 16 (2020–2026) |
| staff_report | 49 | 49 | 48 | matter attachments named "Staff Report"; 1 (matter 4700) is RTF-as-.pdf → no text |
| matter_attachment | 95 | 0 | 0 | INDEX-ONLY: live `source_url` + `matter_id`; binaries not stored |

Disk: `raw/` 359 PDFs, `text/` 358 sidecars. Attachments were fetched only for the
**land-use matters** behind the development pipeline (the harvest filtered matter motion
text on rezone/zoning/planned-development/subdivision/annex/general-plan/conditional-use);
staff-report attachments were downloaded + text-extracted, the rest catalogued index-only.

## §9 doc_class layer

Classified by `classify_attachments.py` (deterministic; joins `matter_id` → county db
motion text for the land-use signal). Only `staff_report` occurs on the on-disk corpus.

| doc_class | rows | fetch_status | rationale |
|---|---|---|---|
| staff_report | 44 | ok 43, no_extractor 1 | LAND-USE staff reports, 40 County Council matters 2020–2025 |
| member_memo | 0 | — | honest empty — county has no council-member proposal memos |
| plan_amendment | 0 | — | honest empty in packets/ — GP exhibits are index-only + live in `plans/` |
| development_agreement | 0 | — | honest empty in stored corpus — sole MDA amendment (matter 6980) is index-only |

**5 staff_report rows deliberately left BLANK** (general-government, not land-use):
matters 9529 / 9868 / 10048 (Clark Planetarium **Annex** building-remodel budget adjustments —
the harvest's `%annex%` filter false-matched the building name), 11430 (budget adjustment
funding a GP water-element contractor — a funding action), 6062 (West GP Steering Committee
appointment). All 5 ground-truthed against their stored text.

## Quality gates (2026-07-16, ground-truthed against on-disk text/raws)

- **Precision** — staff_report **44/44 = 100%** (whole class; n<50 so whole class per the
  gate). Every classified row's stored text confirmed a land-use action (rezone / Title
  9·17·18·19 zoning code / annexation / GP adoption-amendment / subdivision / code revision).
- **Recall** — 100-row random sample of the 410 unclassified rows: **0 on-disk mis-blanked
  land-use staff reports**. All "misses" (6 in the sample; 13 in the full corpus) are
  INDEX-ONLY content-doc-family rows left blank per the documented boundary decisions below —
  documented, not silent. Estimated miss on the classifiable (on-disk) universe: 0%.
- **Determinism** — reruns of `classify_attachments.py` reproduce the index byte-for-byte.

## Boundary decisions (county doc families differ from the Sandy city pilot)

1. **General-government staff reports stay blank.** doc_class=staff_report is LAND-USE only;
   budget adjustments and committee appointments (even when the harvest's land-use filter
   pulled them in) are honestly unclassified.
2. **plan_amendment is empty in packets/ by architecture.** The county maintains a dedicated
   `plans/` module holding the authoritative GP text (West GP, Wasatch Canyons GP, Sandy Hills
   GP, township GPs, MIH). The GP exhibits appearing among packets index-only rows are large
   (13–52 MB) pointers to those same documents; a newly-adopted full GP is `general_plan`
   (a distinct §9 class), not a plan `amendment`. They are NOT re-classified here.
3. **development_agreement is empty in the stored corpus.** Exactly one DA instrument rides
   the corpus — matter 6980 "Amendment No 2_Final" (Olympia Hills MDA Amendment No. 2) — and
   it is an index-only row with no on-disk text. A "Master Development **Plan**" (matter 4931)
   is a plan, not an agreement, and is excluded.
4. **Index-only, not fetched.** The 95 matter_attachment rows carry live `source_url`s; the
   13 content-family rows among them (9 plan-amendment, 3 staff-report, 1 dev-agreement) are
   future fetch-and-classify candidates (Sandy's fetch→extract→discard pattern), recorded
   here rather than force-classified without text.

## Validator inapplicability (reported, not restructured)

`python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py salt_lake_county/packets/`
FAILs by design. The county packets dataset predates the SCHEMA_SPEC §9 packets contract and
uses its own header + `format='pdf'` convention. Two FAIL categories:
- header does not start with the §9 packets contract prefix (`date,title,body,meeting_type,…`);
- `format 'pdf'` is not in the city format vocab (`text|scanned|html|json|xml|video|caption|na`).

Both are **pre-existing county conventions** — identical in the 2026-07-16 pre-change backup;
the doc_class backfill introduced **zero** new failures (it only appended 4 trailing columns).
Per the primary-docs rollout rule, county datasets keep their own conventions and the header
was NOT restructured. Backup: `_backups/2026-07-16-primary-docs-rollout/salt_lake_county/packets/`.

## Acceptance candidate

**Matter 9505** — a Title 19 rezone (A-1 → R-2-6.5) staff report
(`text/staffreport_m9505_staff_report.txt`, doc_class=staff_report, fetch_status=ok,
text_chars=1278, sha256 `5e1a11da51fd…`) joins the enacting **County Council** action of
**2023-10-03**, outcome **Pass** on a **contested 8 Aye / 1 Nay** roll call (Sheldon Stewart
dissenting). The staff report explains the land-use recommendation behind that vote.
