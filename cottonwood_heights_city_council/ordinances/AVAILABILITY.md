# Cottonwood Heights — adopted ordinances: availability & gaps

**As-of:** 2026-07-13. **Window:** 2020-01-07 → 2026 (data floor 2020; city incorporated
2005). Source type 3 of `/expand-city-sources`.

## What was checked

| Source | Result |
|---|---|
| **MunicipalCodeOnline** codifier (`cottonwoodheights.municipalcodeonline.com`) | Public book UI is an AngularJS SPA; its ordinance-list endpoint (`bookadmin/ordinance`) is **auth-gated** (returns Sign In); the consolidated code text is browse-only. **But its backing public S3 bucket allows anonymous `ListBucket`** → every tracked adopted-ordinance PDF is enumerable. Used. |
| **MunicipalCodeOnline public S3** (`s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/cottonwoodheights/ordinances/documents/`) | 39 keys listed & downloaded (1 is a same-file re-upload duplicate of Ord 454). Reaches the most recent ordinances (through **Ord 454**, Dec 2025). Filenames carry an UPLOAD timestamp, not the adoption date. |
| **Utah Public Notice (PMN)**, CH entity 111, **City Council body 2147** | No dedicated PMN "ordinances" body for CH; signed ordinance PDFs ride as **attachments on council meeting notices**. Full history via the cumulative `notices.html?id=2147&page=300` GET → 2,531 attachment rows parsed; **83 ordinance-document attachments** selected, 82 downloaded, dense **2020–2024 (Ord 336–422)**. |
| CivicEngage Document Center / city `/city-ordinances` page | No standalone ordinance-listing page (`404`s); the city routes ordinance access through the MunicipalCodeOnline codifier + GRAMA. |
| GRAMA (`recorder@ch.utah.gov`) | The city's stated path for older/other ordinances and resolutions. **Not pursued** (out of scope for an automated polite-GET build); noted as the fallback. |

## Coverage (final build 2026-07-13)

- **128 adopted ordinances indexed**, window **2020-01-07 → 2026-05-19** (Ord 336 → 467 +
  one `Ordinance 2024-58`).
- **Documents on disk:** 121 PDFs in `raw/` (39 S3 + 82 PMN). **92 index rows are
  doc-backed** (pmn 57 · s3 35); **36 are `within_source`** (motion-only, no PDF yet).
- **S3 ordinance PDFs** span Ord 331–454 (reaches the 2025 tail); **PMN ordinance PDFs**
  span Ord 331–422 (the 2020–2024 core is near-complete via PMN). Their union documents
  most of Ord 336–445 plus 454.
- **Linkage:** high 86 (number+date both cited in the enacting motion — all verified) ·
  within_source 36 · none 5 · low 1.

## Known gaps (honest; see `unrecovered.csv`)

1. **The most recent ordinances (roughly Ord 455–467, 2026) have NO published PDF** in
   either source yet — the codifier S3 tail ends at Ord 454 (Dec 2025) and PMN attachment
   posting of ordinance PDFs tapered after 2024. These ordinances are still **enumerated
   from the vote layer** (`match_confidence=within_source`) but carry no document.
2. **Many 2020–2023 ordinances have no independent PDF** in either source (the codifier
   only uploaded a subset as "proposed action documents"); these are likewise
   `within_source` rows — the number/date/subject are taken from the enacting motion.
3. **Sequential-number gaps 392, 455, 456, 457** — no motion citation anywhere in the vote
   layer and no published PDF in either source. The numbers may be unused/reserved or were
   adopted at meetings absent from the minutes layer (e.g. a 2020-10-06 and 2022-12-06/13
   meeting that Ord 344/345/389/390/391 corroborate but the vote layer lacks). Logged.
4. **Ord 464 is NOT in the index — by design.** The motion to APPROVE Ordinance 464
   (Community Clean Energy Program) **failed 4-to-2** on 2026-05-19; it was not adopted.
   Logged in `unrecovered.csv` so the absence is explicit.
5. **PMN file `419895.pdf` (Ord 304, 2018) 404'd** — pre-floor and irrelevant to the 2020
   window; logged.
6. The **codified consolidated code text** (current Titles) is NOT mirrored — it is
   browse-only at the codifier and is not an "adopted ordinance" artifact. Use
   MunicipalCodeOnline / Municode Library manually for current code text.

## Not a gap (by design)

- `within_source` rows are a **complete, honest enumeration** of adopted ordinances whose
  only public record in this pipeline is the council motion — not a retrieval miss. CH
  motions name the ordinance number, so the enumeration is reliable; it is simply not
  corroborated by a separate PDF.
- Budget, surplus-property, and bank-account ordinances (incl. the `Ordinance 2024-NN`
  administrative series) are real adopted ordinances and are included where cited in a
  passed motion.
