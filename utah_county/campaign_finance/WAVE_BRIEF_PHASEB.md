# WAVE BRIEF — Utah County, Tranche 3 Phase B itemization

**Written 2026-08-18, after juab / wasatch / summit / weber closed.** This is the launch
kit for the LARGEST remaining Phase B corpus. Nothing here has been started.

> Read with: this module's `CLAUDE.md` (authoritative) · `AVAILABILITY.md` (§4/§4a gaps) ·
> `RECON.md` (channel map) · repo-root `GOTCHAS.md` · `_audits/cf-calibration-suite/` ·
> the closed waves' briefs in `_backups/2026-08-14-tranche3/summit-b/AGENT_BRIEF.md` and
> `_backups/2026-08-14-weber-cf/workdir/CHUNK_BRIEF.md`.

---

## 1. Scope — what is and is not already done

| | |
|---|---|
| Retained county-office filings | **263** (2008–2026, all 11 published cycles) |
| Stated-totals layer (cover figures) | **COMPLETE — 265 rows**, every cover vision-read 2026-08-01 |
| Format split | **245 scanned** · 17 real text layer · 1 spreadsheet |
| Itemized (donor/vendor rows) today | **2 filings** — Ainge 2018, Paxman 2026 (72 C + 81 E, 100% geometry) |
| **THE QUEUE** | **245 handwritten scans** |

The 17 machine-readable filings were swept by the registered `utahcounty_schedab` family on
2026-08-02; only 2 passed the reconciliation gate. **15 emitted nothing on purpose** — 6 have
no legible summary page (OCR floor), 8 parse to a sum that misses the stated total, 1 is the
compound-cell case (§4 below). Do not "fix" those by loosening a gate; several are genuine
filer-arithmetic or document-level gaps and are named in `filing_totals.notes`.

**Empty itemized on the other 261 means NOT TRANSCRIBED — never "no donors."**

---

## 2. ⚠ WHY UTAH IS NOT SUMMIT OR WEBER — read before writing any gate

### 2a. The regime is INVERTED relative to the last two waves

Summit and weber are **cumulative-regime** counties: the cover states a cycle-to-date figure,
and the trap was a *period* ledger sitting under a *cumulative* cover.

**Utah County is the opposite.** `filing_regime='per-period'` on every row. The module already
promotes the **per-period** column into `stated_total_*`, and keeps the cumulative in `notes`
as `ytd_contrib=` / `ytd_expend=`.

| variant | cycles | per-period cell (PROMOTED) | cumulative cell (NEVER SUMMED) |
|---|---|---|---|
| `legacy_colAB` (135) | 2008–2018, some 2020/2026 | **Column A — Total this Period** | Column B — Year-to-Date |
| `modern_boxAF` (130) | 2020+ | **Box B** (contrib) / **Box D** (expend) | Box C / Box E |
| `other` (2) | — | one blank form; one candidate spreadsheet | — |

**Consequence for the ratified basis rule:** the rule is unchanged — *reconcile each side
against the printed figure matching ITS OWN SCOPE* — but here the DEFAULT anchor is the
**per-period** cell (Column A / Box B / Box D), not the cumulative one. A ledger that
reconciles to Column B is the exception and must be flagged, not assumed. `is_incremental`
follows the anchor actually used. **Never difference two covers to synthesize a figure.**

A candidate-cycle total here is **Σ the per-period rows**, cross-checked against the LAST
report's `ytd_*` — never a sum of the cumulative column.

### 2b. The contribution anchor is CASH-ONLY on this family

Column A / Box B states the **cash** figure; in-kind is a separate printed line. The
`utahcounty_schedab` family reconciles cash rows only (`reconcile_cash_only`).

**BUT** the 2026-08-17/18 waves established that **in-kind treatment is PER-FILER, not a form
property** (summit: McKenna separate vs Adair/Gochnour inline; weber: Bolos closes only WITH
in-kind, and Gochnour's Form A excludes it). **Test BOTH conventions per filing and record
which one closes.** Do not inherit the family default without testing it.

### 2c. Everything is redacted UPSTREAM, and inconsistently

Nearly every file is `*_Redacted.pdf` — **the clerk blacked out donor addresses before
publication.** Do not read a redaction bar as a failed transcription; it is the document.
Note also that `rowbands.py` treats redaction bars as printed rules (see §3).

The county's redaction is inconsistent and this is recorded, not corrected: Andrea Allen 2024
and Anthony Canto 2024 each appear TWICE (once redacted, once in the clear) and Brian Bird's
2024 filing is unredacted. **Repo privacy contract still applies to what we WRITE:** donor
**city/state only, never street addresses**, regardless of what the county published.

### 2d. Known document traps (verified, do not rediscover the hard way)

- **BOUND-IN SECOND REPORT:** `2020_SakievichTom6.23.20_Redacted.pdf` **page 6 carries a 2018
  Schedule B**. One index row may bind TWO reports. Flagged during the summit wave as
  "verify before the utah wave" — verify it FIRST and sweep for siblings.
- **THE CHECKLIST DECOY** (calibration specimen `utah-checklist-decoy`): ~20 filings bind the
  Elections Division *Campaign Financial Disclosure Checklist*, which names every summary-page
  label and carries **zero dollar figures**. Page position is NOT a classifier — locate the
  summary page by CONTENT. The control case is real: `2022_Cox_Hyrum_4.1.2022` p5 IS a genuine
  summary page at the same page ordinal.
- **SUMMARY PAGE POSITION VARIES:** `legacy_colAB` usually p2; `modern_boxAF` usually the LAST
  page. Never assume an ordinal.
- **MALFORMED DECIMALS** (`utah-malformed-decimal`): `23,744,71` / `23.744.71` →
  **unparseable-BLANK, never repaired**. Only the handwritten decimal-comma repair is
  whitelisted, and only on handwriting — weber found a TYPED malformed decimal (`$1,327,00`)
  that the whitelist deliberately does not cover.
- **COMPOUND `+Inkind` CELL:** Paxman's Box B prints `168872.24 +Inkind 7670.68` in ONE cell.
  `money()` refuses to reduce two numbers to one, so `stated_total_contributions` is BLANK and
  **stays blank**; itemized rows publish alongside it with `reconciles_contrib` blank
  (unknown — there is no published figure to test). Do not invent a gate where none exists.
- **MULTI-REPORT PDFs:** 2 filings are genuine bundles (Buhman 2014 original+amendment,
  Westmoreland 2024) emitted as separate rows, never merged.
- **FILER NAME ≠ CHANNEL LABEL:** the Strapi record files **Paul V. Child's** 2020 Recorder
  filing under **Taylor Dayton**. Join on `source_filing`, never on `candidate`. Page-face
  name wins; the channel label is preserved in `notes`.
- **DO NOT INFER A COMMISSION SEAT** the filing does not print, and **do not adjudicate a
  filer's own inconsistency** (Graves types Seat A on 3/31/22 and writes "B" on 4/11/22).

---

## 3. ⛔ PREREQUISITES — do these BEFORE bulk transcription is authorized

### 3a. A FRESH CALIBRATION PRE-FLIGHT IS MANDATORY

`_audits/cf-calibration-suite/runs.md` has pre-flights for SLCo, summit, weber, juab and
wasatch — **none for utah**. More decisively, **the configuration has CHANGED since the last
pre-flight** (2026-08-14), which triggers the standing rule on its own:

- `scripts/campaign_finance/make_snippet.py` — **FIXED 2026-08-18** (page size now returned as
  poppler renders it, `/Rotate` applied; fixes the pct/px/span paths together; oversized-
  mediabox blank-crop defect fixed with a dpi clamp).
- `weber_county/.../build_finance.py` — in-kind monetary-only fallback added (module-local).

Run the **13-specimen suite** and record the result in `runs.md` before authorizing bulk work.
Three specimens are utah's own: `utah-checklist-decoy`, `utah-malformed-decimal`,
`utah-colAB-regime`. Grow the suite with the four candidates the weber/summit waves produced
(swapped-cover pair · rows running right-to-left · "0 in every This-Report cell" ·
wrong-column pointer that still sums correctly — the geometry negative control).

### 3b. FIX `rowbands.py` FIRST — it is filed [DEBT]

LEADS proposes promoting `rowbands.py` / `fitgrid.py` to `scripts/campaign_finance/` **for this
wave**. Do not promote it broken. Known defects, all found on real pages:

- On **typed** sheets it registers TEXT BASELINES as printed rules — the real grid is every
  other one — and returns header / shaded-spacer bands as rows.
- **Redaction bars throw spurious rules** (and this corpus is redaction-heavy — see §2c).
- The black "PLEASE NOTE" box is detected as a rule.
- At ~0.4° skew it can fail to return the row grid **at all**.
- Its percentages are measured on a **DESKEWED** copy while crops come from the **RAW** render
  — a full row of drift on skewed scans.
- The recovery that worked on weber: scan for dark runs **restricted to the Amount column's own
  band on the other axis**.

Also carry weber's hard-won lessons: leading trims are per **page** (2/3/4-band, sometimes at
the *high*-pct end); printed-line ordinal ≠ row ordinal (filers skip ruled lines); a `cell`
bounded on a detected rule can still **clip** a right-aligned figure — it must run to the
printed border, provable only by render.

### 3c. Verify the Sakievich bound-in report (§2d) before the queue is derived

---

## 4. THE CONTRACT (B2, unchanged — do not renegotiate it mid-wave)

- **ARITHMETIC CLOSURE OUTRANKS GLYPH READING** (GOTCHAS; the Rhodes reversal). If the schedule
  sums to the filer's stated figure, that reading wins over what a character looks like.
- **`pct:` geometry on EVERY row**, measured — a declared frame only where measurement is
  impossible, and say why. Weber closed at 100% geometry; that is the bar.
- Full-page first read at ~200 dpi; **tight-cell-crop escalation at 600–2000 dpi for disputed
  cells only**, never a full-page dpi raise.
- **Zero-glyph ruling** (slashed zero = 0.00, verbatim mark retained); a bare `-` is a NIL MARK
  → blank, never 0; `N/A` → blank.
- Whitelisted decimal-comma repair ONLY, and only on handwriting.
- **Field-shift screen** on every side; withhold rather than guess.
- **Per-filing checkpoints**; transcribe-once-per-sha256.
- **"No schedule page exists" vs "page exists but is blank" vs "withheld" are THREE DIFFERENT
  FACTS** and are never conflated.
- Filer arithmetic that does not close is **retained verbatim** with `reconciles_*=False` and
  the cause traced on the page — that is a fact about the document, not a defect.
- Period-basis sides need the declared exception in `validate_finance.py` check 6: every row
  `is_incremental=True` **and** the literal marker `ITEMIZED <side> PERIOD-SCOPED
  (is_incremental=True)` in `filing_totals.notes`. **Use that mechanism; never weaken the check.**

**Screen for the correlated-error trap** before calling a delta filer arithmetic: weber's
strongest proof was that filings 1082 and 1246 carry the *same* +$40.00 on the same filer's two
filings. And an **OCR render-back is a screen for TYPED sheets only** — on handwriting it
scored 18 correct weber rows as failures. Never read it as a negative.

---

## 5. PROHIBITIONS (wave agents)

- **NEVER run `scripts/build_cities_db.py`.** The coordinator runs ONE federation at wave close.
- **NEVER edit** root `TODO.md` / `LEADS.md` / `HANDOFF.md` / `GOTCHAS.md` / `CLAUDE.md`.
  Leads go in the final report; the coordinator files them.
- **Never commit to git.**
- **Never weaken a shared validator or gate** to make something pass. Report the blocker.
- **Never fabricate.** Withheld-with-a-stated-reason is a CORRECT outcome.
- All writes through the sole-writer path; the rebuild must be **idempotent** (run twice, prove
  byte-identical); the **cover tranche (`stated_*`) must not change** — it is already verified.

---

## 6. SIZING AND PACING

| | |
|---|---|
| Queue | **245 filings** — ~2.5× summit (116) or weber (93) |
| Measured cost | vision scans ~15–20k tokens/filing; closed legs ran ~460–590k each |
| Estimate | **~5M tokens** — the largest single wave attempted |
| Fan-out cap | **≤3 concurrent chunk sub-agents**, declared in the final report |

**This will not finish in one session.** Plan for checkpoint-and-resume from the start: the
2026-08-14 wave survived three kills (session limit, laptop network watchdog, deliberate pause)
without data loss because every filing was checkpointed on disk. Split the queue by cycle
(2008/2010/2012/2014/2016/2018/2020/2021/2022/2024/2026) so a resumed leg has a clean boundary.

**Consider running the 2008–2018 `legacy_colAB` era and the 2020+ `modern_boxAF` era as separate
legs** — they have different summary-page positions, different cell vocabularies, and different
redaction behaviour.

---

## 7. DELIVERABLES AT CLOSE

- Verified itemized layer written only through the sole-writer path
- A dated close-out in `AVAILABILITY.md`, in the form of the juab/wasatch/summit/weber close-outs
- Pre-flight result recorded in `_audits/cf-calibration-suite/runs.md`
- `python3 scripts/validate_entity.py utah_county` at or better than the recorded baseline
- Exact replacement text for utah_county's `cf-*` caveat in `scripts/build_cities_db.py`
- A final report carrying: queue derivation · kept/redone counts if resuming · rows by side ·
  reconciliation breakdown (exact / period-exact / delta-verbatim / empty-schedule /
  no-schedule-page / withheld) · fan-out used · leads + calibration specimens · anything
  unfinished and precisely where it stands

---

## 8. LAUNCH PROMPT

Paste this to start the wave. It assumes the prerequisites in §3 are done, or instructs the
agent to do them first.

```
You are the WAVE COORDINATOR for the utah_county campaign-finance itemization wave
(Tranche 3 Phase B, contract "B2") in /Users/tysonwelsh/civic-data. This is the LARGEST
remaining Phase B corpus — 245 handwritten scanned filings — and nothing has been started.

READ FIRST, IN THIS ORDER:
1. /Users/tysonwelsh/civic-data/CLAUDE.md (cardinal rules)
2. /Users/tysonwelsh/civic-data/GOTCHAS.md ("ARITHMETIC CLOSURE OUTRANKS GLYPH READING")
3. /Users/tysonwelsh/civic-data/utah_county/campaign_finance/WAVE_BRIEF_PHASEB.md
   — THIS IS YOUR CHARTER. Follow it section by section.
4. That module's CLAUDE.md (authoritative) + AVAILABILITY.md §4/§4a + RECON.md
5. /Users/tysonwelsh/civic-data/_audits/cf-calibration-suite/ (manifest + runs.md)
6. The closed waves' kits, as models of method:
   _backups/2026-08-14-tranche3/summit-b/AGENT_BRIEF.md and
   _backups/2026-08-14-weber-cf/workdir/CHUNK_BRIEF.md

DO THE PREREQUISITES FIRST (brief §3), in this order, and STOP if any fails:
  (a) Fix rowbands.py's filed [DEBT] defects, then promote rowbands.py/fitgrid.py to
      scripts/campaign_finance/ as LEADS proposes. Prove the fix on real pages.
  (b) Run the 13-specimen calibration pre-flight and RECORD it in runs.md. This is
      MANDATORY: no utah pre-flight exists, and the configuration changed on 2026-08-18
      (make_snippet.py rotation + oversized-mediabox fixes). Bulk transcription is not
      authorized until it passes.
  (c) Verify the bound-in second report (2020_SakievichTom6.23.20_Redacted.pdf p6 carries a
      2018 Schedule B) and sweep for siblings, THEN derive the true queue.

THEN transcribe, under the brief's §4 contract. Respect §2 above all — utah's regime is
PER-PERIOD and INVERTED relative to summit/weber: the promoted anchor is Column A / Box B /
Box D, the cumulative Column B / Box C / Box E is NEVER summed as an increment, and in-kind
is PER-FILER (test both conventions, record which closes). Honour every §2d document trap.

FAN-OUT: at most 3 concurrent Opus chunk sub-agents. Declare the actual fan-out used.

PACING: this will NOT finish in one session (~5M tokens estimated). Checkpoint every filing
to disk as you go and split legs on cycle boundaries so a resume has a clean edge. If you
must stop, leave the state checkpointed and say exactly where you stopped.

PROHIBITIONS (brief §5): never run scripts/build_cities_db.py; never edit root TODO.md /
LEADS.md / HANDOFF.md / GOTCHAS.md / CLAUDE.md; never commit; never weaken a shared gate to
make something pass; never fabricate — withheld-with-a-reason is a correct outcome. All
writes through the sole-writer path; rebuild idempotent (prove byte-identical); the cover
tranche (stated_*) must not change.

DELIVERABLES: brief §7.
```

---

## 9. OPEN ITEMS THAT TOUCH THIS WAVE

- **[DEBT] `rowbands.py`** — §3b. Blocking-by-judgment, not by gate.
- **Repo-wide geometry re-proof** — geometry validated with the pre-2026-08-18 `make_snippet.py`
  on ROTATED pages is unproved (closed SLCo B2 + summit work). Separate from this wave, but the
  fixed tool is the reason it is now possible.
- **Cross-county cover-chain sweep** (Last-Report vs prior Cumulative across all 8 counties'
  1,911 cover rows) — catches the swapped-cover class no arithmetic gate sees. Utah's covers
  are already transcribed, so it can run BEFORE this wave and cheaply.
- **SCHEMA.md §4** should record the declared period-basis exception added to
  `validate_finance.py` check 6.
- **County `cycle_totals` remains DEFERRED BY DESIGN** — `cf_cycle` stays city-only. Do not
  derive a utah rollup as part of this wave.
