# Data license — CC-BY-4.0, with carve-outs

This repository contains three legally distinct kinds of material. The `LICENSE` file (MIT)
covers the **code**; this file covers the **data**.

## 1. The derived and normalized layers — CC-BY-4.0

Everything this project *created* is licensed under
[Creative Commons Attribution 4.0 International (CC-BY-4.0)](https://creativecommons.org/licenses/by/4.0/):
the schemas and entity model (`SCHEMA_SPEC.md`), the extracted and structured vote/motion
records, the normalization layer (`motions_std`, crosswalks, `motion_type_std` /
`land_use_type` / `action_class` / `disposition` classifications), the reconstructed
confidence-scored referral chains, the rolling roster layer, the campaign-finance
structured layer, the caveat/coverage apparatus, the weekly bundles, the minutes markdown
conversions, and the federated database built from them.

**Attribution:** cite as described in `CITATION.cff` / the README's "License & citation"
section. A link to `https://github.com/tysonwelsh/civic-data` satisfies attribution for
casual reuse.

## 2. The underlying public records — not ours to license

Meeting minutes, roll-call votes, adopted ordinances, election canvasses, campaign-finance
disclosures, advisory opinions, statutes, and other government records reproduced or
transcribed here are **Utah public records** (Utah GRAMA, Utah Code 63G-2). They are not
subject to our copyright, and nothing in this repository restricts your use of the
underlying records themselves. Per-record provenance (source URL, retrieval date, method)
is carried in each dataset's `sources.csv` / `index.csv` and the `document` catalog.

## 3. Third-party works — their own terms

Some cataloged documents are third-party authored works reproduced for research
convenience: consultant-authored general plans and housing plans, and redistributed GIS
layers. **These retain their owners' terms.** GIS catalogs carry a per-layer `license`
column (see each entity's `gis/index.csv`); plan documents remain the property of their
authors/commissioning governments. If you redistribute those files, check their terms
independently — CC-BY-4.0 applies only to the layers described in §1.

## Warranty

The data is provided **as is**, with measured coverage and documented ceilings (see the
`caveat` table in the federated database, `coverage.json`, and `METHODS.md`). Honest gaps
are data: absences are documented, never filled. No warranty of completeness or fitness
for any purpose; see `PRIVACY.md` for correction/takedown contact.
