# ut_state — legislation module recon (channel verdicts)

State of Utah, the repo's first **state-tier** entity (fed_index 301, `gov_level='state'`,
dir `ut_state/`). This file covers the **legislation** module only (Legislature bills +
roll-call votes, land-use/housing subset). Sibling modules (advisory_opinions, statutes,
projections) are built separately. Recon performed **2026-07-20**; all URLs probed live.

## Scope

Utah **General Sessions 2015GS → 2026GS** (12 sessions), **land-use / housing subset**
selected by an auditable classifier (`legislation/classify.py`) run over bill TITLES plus
5 guarded named anchors. Over-inclusion is intentional (each kept bill carries the matched
`relevance` rule); silent exclusion is not. Specials were NOT swept in this pass (see gaps).

## Channel verdicts

### 1. le.utah.gov developer API (glen.le.utah.gov) — OWNER-GATED, NOT USED
- Base `https://glen.le.utah.gov`; endpoints are path-style with the token as the LAST path
  segment, e.g. `glen.le.utah.gov/bills/2022GS/billlist/<TOKEN>`,
  `.../bills/2018GS/HB0001/<TOKEN>`, `.../legislators/<TOKEN>`.
- Bills back to **2016**; legislators, committees, calendars, Utah Code/Constitution/Rules.
- **NO vote data in the API** (confirmed against the endpoint catalog on developer.htm).
- **Token gating: the "Get my developer token" button → `/tracking/trackingCreateNewDeveloperToken.jsp`
  → 302 → `tracking.jsp?tab=dev`, which is the "My Legislature Login" page (email + password
  account required).** The token is therefore **account-gated / owner-gated** — NOT freely
  issued on the page. Per build directive, no account was created. Documented as an
  acquisition lead only. Even with a token the API would not add votes.

### 2. le.utah.gov PUBLIC website — THE WORKING CHANNEL (no account) ✔
Three reachable-per-bill page types, all requiring only a browser `User-Agent`
(a BIG-IP WAF returns a 247-byte "Request Rejected" to header-less clients — send a normal
UA). Pages are **cp1252-encoded** (decode accordingly). URLs:
- **Bill list per session** — `le.utah.gov/billlist.jsp?session=<SESSION>` (e.g. `2022GS`).
  One `<LI>` per bill: static-page URL, `H.B. N`, `<B>title</B>`, `<I>(sponsor)</I>`.
  Complete enumeration (694–931 bills/session). This is the enumeration backbone.
  (`billlist.jsp` works for **all 12** sessions 2015–2026; `passedbills.asp` ignores its
  `sess` GET param and always renders the current session, so it was not used.)
- **Bill static page** — `le.utah.gov/~<YEAR>/bills/static/<BILL>.html` (e.g.
  `~2022/bills/static/HB0462.html`). Gives status ("Governor Signed"), **Effective Date**,
  **Session Law Chapter**, and the **Bill Status action table** — each row = date, "chamber/
  action", actor, and a vote LINK whose text is either a `Y N A` tally (RECORDED roll call)
  or "Voice vote" (no names). (Bill-text `.htm` links are JS-injected and absent from the
  served HTML, so `text_url`/`enrolled_url` are CONSTRUCTED deterministically at
  `~<YR>/bills/{h,s}bill{int,enr}/<BILL>.htm`.)
  **SHELL-PAGE TRAP (2025GS + 2026GS):** these two sessions' static pages are broken —
  JS-injected skeletons whose served HTML carries the real content only as JavaScript, while
  the only vote LINKS present sit inside HTML **comments** as stale **2024 placeholder** rows
  (a single 2024 committee/floor vote otherwise gets wrongly attached to dozens of bills).
  `harvest_bills.py` STRIPS HTML comments first, so 2025/2026 static pages correctly yield
  ZERO roll calls (never fabricate); their real votes are recovered separately (below).
  2015–2024 pages are fine.
- **Floor roll call** — `le.utah.gov/DynaBill/svotes.jsp?sessionid=<S>&voteid=<N>&house=<H>`.
  Sections **`Yeas - N` / `Nays - N` / `Absent or not voting - N`** with every legislator
  named `Last, F.` — **full named roll calls, no account.** ✔ Reachable DIRECTLY by voteid
  even when the bill's static page is a shell, and each page self-identifies its bill — so the
  2025/2026 shell sessions are recovered by crawling the voteid space (`voteid` is scoped PER
  HOUSE — crawl both; tally header reads `N/V` in the House but `Abs` in the Senate).
- **Committee vote** — `le.utah.gov/mtgvotes.jsp?voteid=<N>`. Committee proper name
  (`<b><center>House Natural Resources, Agriculture, and Environment Committee</b>`),
  meeting date, `Yeas/Nays/Absent` counts, names listed in count order. **Named.** ✔

**Verdict:** the public website systematically yields **named floor AND committee roll
calls per bill without any account** — richer than the (vote-less) API. This is the harvest
channel. Voice votes are honest tally-only (recorded in `rollcalls.csv` with `recorded=0`,
no name rows).

**Recording ceilings found on this channel:**
- **Party and district are NOT on the vote pages** (names + chamber + vote value only) —
  honest gap in `votes.csv` (`party`/`district` blank). Mappable later from the public
  legislator roster pages or the gated API (closing-pass enhancement).
- **Voice votes** carry no names by nature (a source ceiling, not an extraction gap).
- Classification is **title-based** — a bill with land-use provisions but a generic title
  can be missed (the 5 anchors backstop the top landmarks). Documented recall ceiling.

### 3. LegiScan — GATED ALTERNATIVE, NOT USED
`api.legiscan.com` (`getRollCall` gives full per-member detail) and bulk datasets at
`legiscan.com/UT/datasets` need a **free account/API key**. Owner-gated per directive;
documented as the fallback channel should the le.utah.gov roster (party/district) mapping or
a specials sweep be wanted. Not registered.

## Coverage floors actually found
- **Bill enumeration:** all 12 General Sessions 2015GS–2026GS enumerate cleanly
  (694–931 bills each; 9,478 bills total across sessions).
- **Land-use/housing subset:** 264 bills (16–29 per session) by the classifier.
- **Votes 2015–2024:** floor + committee named roll calls harvested directly from the
  (working) static pages — spot-verified HB0462 2022 (House 56-18-1 floor + 12-2-0
  committee, both fully named). All **759** recorded 2015-2024 roll calls reconcile name-count == tally (the file carries 1,137 rollcall rows; 378 are unrecorded voice votes). [count corrected 2026-07-26 — the text said 847]
- **Votes 2025 + 2026 (shell sessions):** FLOOR votes recovered by direct voteid crawl
  (`harvest_shell_recovery.py`); **COMMITTEE (mtgvotes) votes for 2025+2026 are a residual
  gap** — that voteid sequence is global, not session-scoped, so it can't be swept per
  session without the (broken) static-page linkage. Left for the closing pass.
- **Party / district:** not present on any vote page — honest blank in `votes.csv`.
- **Specials:** NOT harvested this pass — land-use-relevant specials are rare; flagged for
  the closing pass (enumerate `<YEAR>S<N>` sessions, classify, append).

## Finalized build totals (2026-07-20 — all modules complete)

The legislation harvest above (759 recorded 2015-2024 roll calls) plus the 2025/2026 shell-session
FLOOR recovery totals, as built into `db/ut_state.db`: **264 bills** (from 9,478 enumerated),
**1,208 roll calls** (`rollcalls.csv` 1,137 + `rollcalls_recovered.csv` 71), **27,887 named votes**
(`votes.csv` 23,988 + `votes_recovered.csv` 3,899). Cosmetic artifact: `bills.csv.n_rollcalls`
reads 0 for the shell-session bills (populated from the stripped static pages, not the recovery
files) — trust the db / `*_recovered.csv` for 2025/2026. The **sibling modules are now COMPLETE**
and documented in the entity `CLAUDE.md` + their own SOURCES.md: `advisory_opinions/` (309-row
index, 307 fetched, gaps #102/#206, image-only #142/#145, 117 repo-entity matches),
`statutes/` (218 sections; the 2025 LUDMA recodification 10-9a→10-20 / 17-27a→17-79 headline
finding), `projections/` (140 rows, Gardner state grain, baseline-only).
