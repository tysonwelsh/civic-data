# VERIFICATION — Town of Copperton

Independent QA of the Copperton repo, performed **2026-07-12** at build closeout. Method:
`scripts/validate_city.py`, the audit corpus screener, structured-data invariants, ground-truth
against source PDFs, derived-layer reconciliation, and **live external cross-checks** (the
2017–2018 gap; Mayor Clayton). No canonical CSVs, minutes, or extractors were modified.

**Bottom line: PASS on every built dataset, 0 FAIL.** The single most important check — whether
the reported **2017-02 → 2018-06 council gap** is a genuine retention purge or a missed harvest —
resolved to **GENUINE (purge)**, with 40+ file-IDs confirmed 404 against three HTTP-200 controls.

`scripts/validate_city.py copperton_city_council` → **23 PASS / 2 WARN / 0 FAIL** (the 2 WARNs are
the honest submit-only comments zero and the tiny-city thin-PC volume, both expected).

## Dataset verdicts

| Dataset | Verdict | Basis |
|---|---|---|
| Council minutes (106) | **PASS** | index == disk (106 == 106); corpus screener clean (dict 0.776, split ~0, weird ~0); OCR years screen clean; provenance headers present |
| Council votes (431 mot / 458 rows) | **PASS** | roll calls verbatim-match source; invariants clean (0 dup-voter, 0 rolls>5, 0 tally mismatch); `validate_votes.py` RESULT: PASS |
| PC minutes (18) | **PASS** | index == disk (18 == 18); screener clean; thin-by-design VERIFIED (see §PC) |
| PC votes (57 mot) | **PASS** | mover-only tally; 3 named Breinholt abstentions match source; `validate_votes.py` PASS |
| db (`db/civic.db`) | **PASS** | 44 named CSV rows == 44 db votes; 488 motions == 431+57; meeting 111 == 94+17; federated into `cities.db` identically |
| Elections (6 races) | **PASS** | 2017/2021/2023 seats match county SOVC; 2 documented gaps (2019, 2025) |
| Public comments | **PASS (honest-empty)** | submit-only; town site 404s for any comment page (probed live) |
| Geo | **PASS** | one UGRC town polygon; at-large (no districts) — correct for Copperton |
| weeks/ (105 bundles) | **PASS** | weekly vote sum == flat total; mtime newer than canonical CSVs |

## §Gap — the 2017-02 → 2018-06 council gap is GENUINE (the key check)

**Claim under test:** `meeting_minutes/minutes_unrecovered.csv` logs **29 meetings (2017-02-15 →
2018-06-20)** as unrecoverable — "PMN files HTTP 404 (retention purge); not on the GoDaddy site
(coverage starts 2023)." A sibling build (Kearns) had a FALSE "audio-only" gap where minutes were
actually on PMN, so this was independently re-verified against live PMN.

**Method (2026-07-12, `curl -k` + browser UA):**
1. Paginated the PMN body-5831 notices list (`utah.gov/pmn/list/notices.html?id=5831`, cumulative;
   page 48 reaches the oldest rows). The list **confirms 28 notice rows for 2017 and 17 for 2018**
   — so the meetings genuinely happened.
2. Parsed each 2017-2018 meeting's *agenda* notice for its attachment file-IDs. Every one lists a
   minutes/agenda PDF file-ID (e.g. 2017-02-15 → `315659.pdf`; 2018-06-20 → `413287.pdf`).
3. **Downloaded 40+ of those 2017-2018 attachment PDF file-IDs — ALL returned HTTP 404** (a
   315-byte HTML error page). The meeting **audio** (`.mp3`/`.wav`) for the same dates also 404s.
4. **Positive controls:** the three earliest files the repo *did* recover — `459667.pdf`
   (2018-07-18), `459671.pdf` (2018-08-15), `522659.pdf` (2019-01-16) — all returned **HTTP 200**
   with real multi-KB PDFs. So the fetch method works; the 404s are real, not a UA/TLS artifact.

**Conclusion: GENUINE retention purge.** PMN removed every attachment older than ~mid-2018 (the
earliest survivor is file 459667 = 2018-07-18); the GoDaddy town site only reaches 2023. The
meetings existed but their minutes documents are unrecoverable — correctly logged, never stubbed.
This is the OPPOSITE of the Kearns false-gap: there, minutes were live on PMN; here, they 404.

*Minor provenance nit (not a defect):* `minutes_unrecovered.csv`'s `candidates` column names guessed
filenames (`pmn:02-15-17.pdf`) rather than the actual purged file-IDs found here (315659, 413287,
…). The verdict is unaffected — every candidate 404s — but enriching that column with the real
notice/file-IDs is a nice-to-have follow-up (logged in TODO).

## §Spot-checks (source quoted)

**1. 2020-03-18 — township-era per-member roll call (3-2 split), source PMN 612045.** The minutes
name the roll verbatim:
> "…moved to approve the UFA agreement. Roll was called showing the vote to be: Council Member
> Severson voted 'Aye,' Council Member Stitzer voted 'Aye,' Council Member Bailey voted 'Aye,'
> Council Member Pazell voted 'Nay,' and **Mayor Clayton voted 'Nay.'**"

`all_votes.csv` m2: Bailey=Aye, Severson=Aye, Stitzer=Aye, Pazell=Nay, **Clayton=Nay** → `3-2 Pass`.
**Exact match.** The next motion (m3) resolution roll (Severson Aye, Stitzer Nay, Bailey Aye,
Pazell Nay, Clayton Aye) also matches exactly. Confirms the **Mayor/Chair votes and is counted in
the 5** even in the township era.

**2. 2025-07-16 — town-era OCR minutes (a mayor-votes 5-0 tally), source GoDaddy (RICOH scan).**
> "Council Member Stitzer moved to approve the June 18, 2025 Council Meeting Minutes as published.
> Council Member McCalmon seconded the motion; **vote was 5-0, unanimous in favor.**"

Extracted as `5-0 Pass`, tally-only (`member` blank) — correct narrative-tally handling. Proper
names survive OCR intact (Sean Clayton, Tessa Stitzer, McCalmon, Bailey) → **faithful OCR
transcription**, not a hallucination. Confirms the town-era **Mayor Clayton presides and is
counted in the 5**.

**3. 2018-07-18 — named 5-0 roll (earliest surviving council doc), PMN 459667.** `all_votes.csv`
m2/m3: Pazell, Bailey, Severson, Patrick, Clayton = all Aye → `5-0 Pass`. Five named Ayes = the
full township roster, consistent with a voting chair.

**4. 2023-11-15 — 0-4 Fail (contested), PMN.** Source: "Roll was called showing the vote to be:
Council Member Olsen voting 'Nay', Council Member Bailey voting 'Nay', Council Member Stitzer
voting 'Nay', and **Mayor Clayton voting 'Nay'**." Extracted as four Nay rows, `0-4 Fail` — matches
(the 5th seat absent). This is the SLVLESA tax-rate-increase rejection.

**5. 2020-09-16 — named 5-0 (Stitzer now seated).** Roster transition captured: Pazell, Bailey,
Severson, Clayton, Stitzer all Aye — matches.

**6. PC 2023-01-10 (ground-truth), PMN body 1560.** Source: "Motion: To nominate Commissioner
Breinholt as Chair for 2023 … Vote: Commissioners voted unanimous in favor." Extracted as
`Pass (unanimous)`, mover-only, no seconder field — correct PC-format handling.

## §PC — thin-by-design VERIFIED (not a harvest miss)

The repo holds **18 PC minutes docs** (2019-03-12 → 2025-07-02) while PMN body 1560 lists ~100
meeting notices with PDF attachments. To rule out a Kearns-style under-harvest, **23 of the
non-indexed PC candidate dates were downloaded and classified (2026-07-12)** spanning 2019–2026:
**22 are ~150-word CANCELLATION agendas** (title "Public Meeting Agenda"; body literally e.g.
"WE WILL CANCEL THE JULY 13, 2021 MEETING"), 1 returned empty, and the multi-attachment dates
carried large staff-report/plan packets — **0 were standalone minutes.** Copperton's PC schedules
monthly but cancels the overwhelming majority; the 18 captured docs correspond to the meetings
actually held. Thin is the source reality, correctly represented. (A full enumeration of all ~100
notices is a deferred completeness nicety — logged in TODO — but no missed minutes were found.)

## §External cross-check — Mayor Sean Clayton (2025)

The town's own council page (`copperton.utah.gov/meet-copperton-council`, fetched `curl -k` +
browser UA) lists **"Sean Clayton — Mayor"**, "Stitzer — Deputy Mayor", plus Bailey, McCalmon, and
Pratt — an outside (publisher-side) source confirming Clayton is the sitting Mayor and the roster
in `meeting_minutes/roster.csv`. Consistent with the recon (Clayton ran unopposed for Mayor,
Nov 2025) and with his 2023 township Seat-B win in `election_results/copperton_races.csv`.

## §Reconciliation

- **db == CSVs:** vote 44 == 44 named rows (Council 41 + PC 3); motion 488 == 431 + 57; meeting
  111 == 94 council vote-dates + 17 PC; person 17; referral 2 (both medium). 0 dropped rows.
- **cities.db federation:** copperton motion 488 / vote 44 / meeting 111 / person 17 /
  election_race 6 — identical to the per-city db.
- **weeks:** summed weekly vote rows == flat council total; index lists 105 bundles; mtime newer
  than the canonical CSVs (not stale).
- **Invariants (both bodies):** 0 motions with a duplicate voter, 0 rolls exceeding 5 voters, 0
  full-roll tally mismatches.

## Audit blind spots (honesty)

- PC completeness was **sampled (23/~100 non-indexed dates), not exhaustively enumerated** — all
  sampled were cancellations/packets, but a full sweep is deferred.
- The `minutes_unrecovered.csv` `candidates` column was not rewritten with the real purged
  file-IDs (verdict unaffected).
- Ground-truth focused on council contested/OCR/roll-call strata + one PC doc; the many tally-only
  unanimous council motions were checked by invariant, not individually re-read.
