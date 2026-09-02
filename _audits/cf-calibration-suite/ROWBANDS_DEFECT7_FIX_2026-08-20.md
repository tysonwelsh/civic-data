# `rowbands.py` DEFECT 7 — reproduced, root-caused, fixed, regression-proved

**2026-08-20.** Closes the TODO [DEBT] entry "**`rowbands.py` DEFECT 7 — it can silently MISS a
grid's TOP rule, and no arithmetic gate can see that**" (filed 2026-08-20 off the utah_county
Phase B wave; record `_backups/2026-08-18-utah-cf/workdir/ROWBANDS_PROMOTION.md` §"DEFECT 7").

Writes made: `scripts/campaign_finance/rowbands.py`, this report, a run record appended to
`runs.md`, and backups + regression evidence under
`_backups/2026-08-20-rowbands-defect7/`. **No data file, no `vision/` cache, no
`build_finance.py`, no federation, no build** was touched. The frozen wave-kit copies
(`_backups/2026-08-14-tranche3/summit-b/rowbands.py`, `_backups/2026-08-18-utah-cf/workdir/`)
are byte-unchanged, so both closed waves stay reproducible against the tool they actually ran.

---

## 1. DEFECT 7 REPRODUCED — the filed numbers are exact

```
$ python3 scripts/campaign_finance/rowbands.py \
      utah_county/campaign_finance/raw/2026/2026_Taylor_Fox_Redacted.pdf 3
  h_rules_pct: [20.52, 24.68, 28.91, ... 81.29]   -> 15 rules
  v_rules_pct: [7.64]                             -> 1 rule
```

**15 horizontal rules for a 15-row grid** (16 required) and **1 of 5 vertical rules**, exactly
as filed. The grid's real top rule was located directly in the image at deskewed rows
**441-464 px**, centre **16.29 pct** — the filed extrapolation (20.52 − 4.22 = 16.30) is right
to 0.01 pct, and it matches the wave's own stored row-1 box `pct:77.50,16.30,13.30,4.22@p3`.

**Root cause, measured (this is NOT what the filed record assumed).** The rule is present and
dark; it is thrown away by the `fill` gate added in the 2026-08-18 promotion. The page is a
faded photocopy whose rules sit only ~20-40 grey levels below their own paper, so the absolute
threshold `a < 170` catches the rule on some pixel rows and misses it on others. Rows 455-458
fall under the cut, which **splits the single rule into two runs**:

| run (deskewed px) | median thickness | segments | `fill` | verdict under `min_fill=0.80` |
|---|---|---|---|---|
| 441-454 | 3 | 5 | **0.71** | rejected |
| 459-464 | 2 | 4 | **0.40** | rejected |
| (merged 441-464) | — | — | — | would pass |

Both halves fail `fill ≥ 0.80`, so the rule vanishes and the ladder is left perfectly regular
and one line short. That is the whole danger of the class: a shifted row index still sums.

**The vertical half has a different cause, which the filed record does not name.** The page is a
**curved** photocopy, so its column rules *shear*: the Amount column's right rule runs at
**87.9 pct** of page width beside row 1 and **91.1 pct** beside row 15 — a 3.2 pct (≈70 px)
drift. A global deskew is a rigid rotation and cannot straighten a shear, so no pixel column
accumulates ink and the whole-height projection finds only the leftmost (nearly straight) rule.
No threshold change recovers this; the scan has to be done per row band.

---

## 2. THE FIX

Five changes in `scripts/campaign_finance/rowbands.py`, each documented in the module.

1. **Background-normalised dark-run scan** (`bg_norm_mask`) — the terminating fix as filed.
   Subtract a Gaussian blur (σ = 0.08·dpi) from the page and threshold the difference,
   **UNIONed with the old absolute threshold**, so the new mask can only ADD dark pixels: a
   page the old mask read correctly cannot lose a rule to it. The adaptive-coverage ladder is
   run on **both** masks and the more regular grid wins (`_grid_score`, the same criterion the
   ladder already used); **ties go to the raw mask**, which is why 166 of the 180 regression
   pages still resolve on the raw mask.
   *Deviation from the filed fix, on evidence:* the filed recovery was normalisation
   **"restricted to the target column"**. Measured here, the column restriction is **not
   needed** — the full-width normalised scan recovers the rule (16.27 pct at cover 0.10). The
   `--col` path is untouched and still available.
2. **Per-band column scan** (`_v_per_band`) — the vertical half. Row bands are scanned
   independently and their peaks matched by order; a column is kept only if it appears in
   ≥60% of the bands at the modal peak count. Reports `v_shear_pct` and
   `v_rules_per_band_pct`, because on a sheared page a single median x is wrong by half the
   shear at each end. **Taken only when the projection failed (<3 rules)** — so every page the
   projection already reads keeps its exact answer, weber's audited column bands included.
3. **Off-grid rules** (`split_off_grid`) — sibling 1. Rules whose x-extent is materially
   shorter than the page's modal rule, or which barely overlap it, are reported in
   `off_grid_pct` and excluded from the bands. Skipped under `--col`, where every rule is
   measured over the same narrow band and the width test carries no information.
4. **The tool audits its own output** (`grid_audit` + an ink probe). `interior_missing_pct`
   names rules missing at the measured pitch; the leading probe asks the image whether there
   is ink one pitch **above** the first rule — the DEFECT 7 signature, which leaves a
   perfectly regular ladder one line short. **Both are probed against the image, never
   asserted from arithmetic**: a gap the page does not show is reported separately as
   `unsupported_gaps_pct` (a section break, a form header, or an underline sheet that simply
   has no rule above row 1). Nothing is ever inserted into `h_rules` — the output is a flag
   for a crop proof.
5. **`--expect-rows N` assert + honest degradation.** `geometry_status` is one of `ok` /
   `gaps` / `row-count-mismatch` / `no-reliable-geometry`, with `notes` saying what to do, and
   the CLI **exits 2** on the last two. A caller that knows the row count now makes a short
   list FAIL loudly instead of trusting it.

**Public interface.** `render()`, `analyze()`, `rules()`, `bands()`, `data_bands()` all keep
their signatures; `analyze()` gained trailing keyword-only-in-practice args
(`normalize`, `norm_sigma`, `norm_t`) and new result keys. `rules()` now returns **grid rules
only** (off-grid rules excluded) — that is the sibling-1 fix and is intended.
**Callers checked:** `scripts/campaign_finance/fitgrid.py` (`RB.render`, `RB.rules(img, col=col)`
— re-run and verified below); `summit_county/campaign_finance/make_itemized_caches.py`
(pins `sys.path` to the **frozen** `_backups/2026-08-14-tranche3/summit-b` copy, so it does not
see this tool at all); `utah_county/campaign_finance/make_itemized_caches.py` (mentions rowbands
in prose only — no import). No other importer exists in the repo.

**Cost:** +7% wall clock on the reproducer (1.60 s → 1.71 s at 200 dpi); `best_angle` still
dominates.

---

## 3. PROOF ON THE REPRODUCER

```
$ python3 scripts/campaign_finance/rowbands.py .../2026_Taylor_Fox_Redacted.pdf 3
  mask_used     : bg-normalised          v_method: per-band       geometry_status: ok
  h_rules_pct   : [16.25, 20.52, 24.69, 28.89, 33.15, 37.40, 41.68, 45.95,
                   50.27, 54.59, 58.96, 63.35, 67.78, 72.26, 76.76, 81.28]   -> 16 rules
  v_rules_pct   : [7.67, 20.68, 49.89, 76.78, 89.40]                         ->  5 rules
  v_shear_pct   : [0.14, 0.45, 1.61, 2.79, 3.20]
  n_data_bands  : 15   (data_bands_trimmed: 0 leading, 0 trailing)
  grid_audit    : pitch 4.319, interior_missing [], leading probe supported=False
```

* **16 horizontal rules** for the 15-row grid ✓
* **top rule at 16.25 pct** — the filed expectation is ~16.30 and the wave's crop-proved
  stored box is `y=16.30`; agreement to **0.05 pct** (1.4 px at 200 dpi) ✓
* **5 vertical rules** ✓, with the shear that defeated the projection now reported
* the leading probe correctly says there is **no** further rule above 16.25 ✓

**Two-crop proof** (the B2 contract's gate), rendered from the tool's own output:

| band | box | renders |
|---|---|---|
| 1 | `pct:7.24,15.85,81.16,5.07@p3` | `1-8-26 │ Elections Division │ Applications Fee │ 901.50` |
| 15 | `pct:7.19,76.36,84.41,5.32@p3` | the last printed grid row (blank), all 5 column rules inside |

Row 1 is the real entry the wave recorded (901.50, Elections Division). The old output opened
this ledger at row 2.

---

## 4. REGRESSION PROOF

**The sample is pages the CLOSED waves actually measured.** Every `(filing, page)` carrying a
`pct:…@pN` box in a county's `contributions.csv` / `expenditures.csv` was enumerated (1,186
distinct pages across 6 counties), and **30 per county were drawn at seed 20260820**:

| | pages | wave-proven row boxes |
|---|---|---|
| utah | 30 | 395 |
| weber | 30 | 328 |
| summit | 30 | 318 |
| wasatch | 30 | 170 |
| juab | 30 | 147 |
| salt_lake | 30 | 584 |
| **total** | **180** | **1,942** |

Both tool versions were run over all 180 pages at 200 dpi (harness, inputs and both raw output
sets archived in `_backups/2026-08-20-rowbands-defect7/regression/`). Two measures were taken:
(a) exact equality of `h_rules` + `v_rules` + `data_bands`; (b) **containment** — does each
wave-proven row box's centre still fall inside a detected band, and how far is the band top
from the stored `y`.

| | before | after |
|---|---|---|
| crashes / render failures | 0 / 180 | **0 / 180** |
| pages byte-identical (h + v + data bands) | — | **138 / 180** |
| wave-proven boxes contained in a detected band | 1,048 / 1,942 | **1,072 / 1,942** |
| …of those, matched within 0.5 pct of the stored `y` | 871 | **892** |
| pages returning <3 rules | 18 | 17 — **and all 17 now say `no-reliable-geometry` (exit 2)** |

**No county lost containment**: juab 143→143, summit 213→213, weber 126→126, utah 260→261,
wasatch 130→139, salt_lake 176→190.

**Every one of the 42 changed pages was classified, and the 3 flagged as regression candidates
were opened at the page:**

| page | change | verdict |
|---|---|---|
| `salt_lake Jacobs_K_Assessor_June141.pdf` p6 | 37→39 rules; one stored row's band-top offset moved −1.45 → **+0.25** | **improvement** — the normalised mask found a missing rule at 39.05 pct; the row had been matched to a band a full row early (DEFECT 7 inside the sample) |
| `summit 4305_Doug-Clyde-General-Final.pdf` p2 | 19→25 rules; 8 rows changed band | **improvement** — rows matched >1 pct off drop **8 → 5**; this dense typed sheet was under-ruled before |
| `utah 2010_CountyRecorder-CampbellRodney` p3 | 22→18 rules; one stored row loses its match | **honest** — an underline form. Its two excluded top rules are the top-right "Page / Candidate / Date of Report" header box (x 72.9-95.2 against a grid of x 6.5-95.0). The lost "match" was that header box being read as a data band at offset −3.26; row 1 of an underline form has **no rule above it** and is legitimately unmatchable from rules alone |

The remaining 6 changed pages **gained** containment (0/8→8/8, 0/5→5/5, 0/23→9/23, …) and 33
changed with **identical** containment — the great majority of those being sibling 1 at scale
(see below).

**The 2026-08-18 / 2026-08-19 proven specimens were re-checked directly and are unchanged:**

| specimen | result |
|---|---|
| weber `2026_ugd_92078f_741f163c.pdf` p2 (`weber-wrong-column-pointer`) | **byte-identical** — 27 rules, 25 data bands, column bands **4.72 / 12.87 / 43.17 / 85.24 / 95.90** at the strict 0.60 threshold; `fitgrid` still returns pitch **3.1013** |
| utah Graves 2014 p3 (`utah-underline-band-offset`) | **byte-identical** — 17 rules, **16** data bands, and the underline form still correctly returns **no** vertical rules |
| utah `2022_Balderree_Heidi_4.2.22` p3 `--col 74,90` (the promotion's two-crop specimen) | **byte-identical** — 15 data bands, band 1 `y=23.32 h=3.68`, band 15 `y=74.32 h=3.89` |
| utah `2018_TAinge.pdf` p3 (the defect-3 typed-sheet control) | **unchanged** — 16 data bands |

---

## 5. THE TWO SIBLINGS

### Sibling 1 — subtotal underline proposed as a data band (Voeks p2, Forbush p2)

**The filed description names the wrong printed element, and the source governs.** On
`2026_Christopher_Forbush_Redacted.pdf` p2 the subtotal underline (a short right-hand segment
under "Subtotal for this page $___") is **not detected at all**. The two false data bands came
from the **footer box** — the "Name of Candidate" / "Date of Report / Page" block — whose rules
are half-width:

```
16 grid rules      x 5.65 -> 94.20   (span ~88.5)
rule y=88.64       x 5.62 -> 49.15   <- footer box
rule y=92.68       x 5.71 -> 49.12   <- footer box
```

| page | before | after |
|---|---|---|
| `2026_Christopher_Forbush_Redacted.pdf` p2 | 18 rules → **17 data bands** | 16 grid rules → **15 data bands**, 2 rules in `off_grid_pct` |
| `2026_Brian_Voeks_Redacted.pdf` p2 | 18 rules → **16 data bands** | 16 grid rules → **15 data bands**, 2 rules in `off_grid_pct` |

Two-crop proof on Forbush p2: band 1 renders `3/2/2026 │ Christopher Forbush │ Saratoga
Springs, 84045 │ $189.92` (the page's only entry, equal to its printed subtotal), band 15 the
last blank printed row. 15 is right; 17 was not. Both stored wave records sit at band 1
(`y=15.93` / `15.98`) and are unaffected.

Across the 180-page regression sample this excluded **57 rules on 31 pages** (utah 14 pages,
salt_lake 13, summit 3, wasatch 1) — every one inspected was a footer or header box — and it is
the reason a dozen utah Schedule A/B pages move from 16-17 data bands to the correct **15**,
with containment unchanged on every one.

### Sibling 2 — zero rules returned on schedule pages

The regression sample contained **18** such pages (14 with literally zero rules). After the fix:

* **3 recovered a real grid** — `wasatch 2020_JuneAArmer.pdf` p3 (1→9 rules, 0→6 data bands,
  containment 0/23→**9/23**), `salt_lake pcorroon_jan3106.pdf` p4 (2→6), `weber
  2022_combined_…78d55edd.pdf` p35 (0→2).
* **15 still find nothing — and now SAY SO.** They return
  `geometry_status: "no-reliable-geometry"` with a note naming the fallback order (`--col`, then
  a declared frame) and the CLI **exits 2**. Before, they returned an empty list silently.
  Sampled at the page: `utah 2022_Gray_Jeff_4.4.2022_Redacted.pdf` p2 is a **typed list with no
  printed grid at all** (only two header underlines) — there is no geometry to find, and
  `--text-lines` returns its 21 text bands as the documented drafting aid. That is the honest
  answer, not a failure.

---

## 6. HONEST-DEGRADATION PATH

| state | when | what the caller gets |
|---|---|---|
| `ok` | ≥3 grid rules, bands found, no ink-supported gap | the measurement |
| `gaps` | an ink-supported rule is missing inside the ladder, or ink sits one pitch above row 1 | the measurement **plus** `interior_missing_pct` / `leading_rule_probe` and a note to crop-prove first. Interpolated positions are flagged as interpolated and are never added to `h_rules` |
| `row-count-mismatch` | `--expect-rows N` given and `n_data_bands != N` | the numbers **plus** `ASSERT FAILED: N rows expected, M data bands detected`; **exit 2** |
| `no-reliable-geometry` | <3 grid rules or no bands — including a legitimately unruled grid | no usable band list, a note naming the fallback order; **exit 2** |

Measured on the 180-page sample: `ok` 130, `gaps` 30, `no-reliable-geometry` 20; the leading
probe fires on 10 pages. The probe's ink test is what keeps it from crying wolf — before it was
added, arithmetic alone put 61 pages in `gaps`, including underline forms whose "missing" rules
the page simply does not print.

---

## 7. WHAT THE FILED [DEBT] GOT WRONG

The filed record is evidence, not fact. Checked at the source:

1. **The 15-vs-16 and 1-of-5 numbers are exactly right**, and so is the 16.30 pct position of
   the missing rule (measured 16.29 in the image, 16.25 by the fixed tool).
2. **The stated cause is not the one that was operating.** The filed fix is normalisation
   *restricted to the target column*; the column restriction turns out to be unnecessary
   (full-width normalisation recovers the rule), and the actual mechanism is the **`fill` gate
   rejecting a rule that a marginal threshold split in two** — a side effect of the
   2026-08-18 defect-3 fix, not a faintness problem per se.
3. **The vertical failure has a separate cause the record does not mention.** It is **shear**
   from page curvature, not threshold; no normalisation of any kind recovers it, and the fix is
   a per-band scan.
4. **Sibling 1 names the wrong printed element** — it is the half-width **footer box**, not the
   subtotal underline, that was being read as data bands. The subtotal underline is not
   detected on either cited page.
5. **"Zero rules on four filings' schedule pages" is not one defect.** On the measured sample
   most such pages are genuinely unruled typed sheets where the correct answer is *no geometry*;
   only a minority were recoverable. The fix for the rest is honest reporting, not detection.

Nothing in the record was found to be fabricated or reversed; items 2-4 are refinements of
cause, and each is recorded in the module so the next reader does not re-derive them.
