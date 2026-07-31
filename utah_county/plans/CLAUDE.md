# utah_county/plans — how to use this module

The **governing General Plan** for **unincorporated Utah County** (FIPS 49049; a
3-member Board of Commissioners county), as a **searchable plain-text corpus** for
growth / housing / development questions. Self-contained: the 2006 raw PDF, extracted
text for both plan versions, and a manifest. Nothing here feeds gov.db/cities.db — it
is a document layer. Utah County Community Development plans/permits only the
**unincorporated** areas; incorporated cities (lehi, orem, provo, vineyard, …) run
their own plans.

## Layout

- `raw/utah_county_general_plan.pdf` — the 2006 General Plan PDF (Laserfiche WebLink),
  3.2 MB, stored (<50 MB).
- `text/<stem>.txt` — extracted plain text of **both** plan versions. **This is the
  searchable layer — read/grep these.**
  - `utah_county_general_plan_codified.txt` — the CURRENT plan (Ord. 2020-1110, amended
    through 2025), from municipalcodeonline; ~430k chars.
  - `utah_county_general_plan.txt` — the 2006 PDF snapshot; ~74k chars.
- `index.csv` — the manifest. Columns:
  `doc_type,title,adopted_date,jurisdiction,path,text_path,format,source_url,doc_class,
  fetch_status,sha256,text_chars,notes` (SLCo plans schema + SCHEMA_SPEC §9
  primary-document columns from day one). `path` is blank for the web-book codified plan.
- `SOURCES.md` — provenance, publishers, MIH note, size policy, and honest gaps.

## Which document for which question

- **Current growth / land-use / housing vision (in force):** the codified plan
  (`utah_county_general_plan_codified.txt`). Chapters: 1 Preface; 2 Goals/Objectives/
  Policies (16 objectives); **4 Moderate Income Housing Element**; 6 Transportation &
  Traffic Circulation; 8 Environmental; 9 Resource/Water/Agriculture; 10 Land Use Element.
- **Moderate-income / affordable housing obligations & strategies:** grep either plan
  text for "Moderate Income". MIH is **Chapter 4** of the current plan (Chapter 2 in the
  2006 PDF) — there is **no standalone MIH plan document**.
- **Historical / as-of-2006 plan record:** `utah_county_general_plan.txt` /
  `raw/utah_county_general_plan.pdf`.

## doc_type / doc_class vocabulary

`doc_type`: `general_plan`. `doc_class` (SCHEMA_SPEC §9): `general_plan`.
(Open set — extend, e.g. `plan_amendment` / `general_plan_element`, if area plans or
standalone elements are later added.)

## Cardinal rules (inherited from repo root)

- **Never fabricate.** There is no separate MIH plan PDF and no located sub-area plans —
  recorded as **honest gaps** in `SOURCES.md`, not invented rows. `index.csv` lists only
  documents actually retrieved with a live `source_url`.
- **Text is derived; the PDF / codified web book + `source_url` are canonical.** The
  current plan lives only as a Municode web book — regenerate its text by re-fetching
  `book/print?type=plan` and re-running the section splitter (see `SOURCES.md`).

## Scope note

The current codified General Plan (Ord. 2020-1110, amended through Ord. 2025-1064) is the
authoritative in-force plan; the 2006 PDF is retained as the historical adopted-record
snapshot. Both contain the MIH element. Area/community/small-area plans, if the county
publishes any, are a logged follow-up (SOURCES.md) — not yet ingested.
