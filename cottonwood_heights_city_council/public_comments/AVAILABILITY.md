# Public comments — availability (Cottonwood Heights City)

**Verdict: SUBMIT-ONLY / NOT PUBLISHED.**

Cottonwood Heights accepts public comment three ways — (1) an **electronic "eComment"
form** on the city site, (2) a **written comment emailed in advance to the City Recorder**
(`recorder@ch.utah.gov` / `cityrecorder@ch.utah.gov`, by **Tuesday noon** on the meeting
date), and (3) **in person** at the meeting (3-minute limit; state name + resident status +
address/district). The city publishes **no archive of the submitted written / eComment
comments**: no dedicated comments-archive page, no Open City Hall / Speak-Up / Peak
Democracy portal, and no "correspondence received" export. The **only** public record of a
comment is the **clerk's paraphrase of in-person / hearing speakers written into the meeting
minutes** — a speaker log, which per the collection's extraction standard is
**meeting-record notes, NOT public-submitted written comments**, and therefore does **not**
populate `all_comments_clean.csv`.

**`all_comments_clean.csv` is intentionally HEADER-ONLY** (schema-conformant, zero rows). No
genuine published written-comment corpus exists. This is an **honest empty result**, not a
gap to be filled (compare the 6 honest-zero comment cities in `SCHEMA_SPEC.md`; substantive
published comment archives exist only in SLC + Park City).

## Avenues checked (comments-auditor hunt order)

1. **Dedicated public-comment page** — `https://www.cottonwoodheights.utah.gov/your-government/public-comment`
   (fetched live 2026-07-12, HTTP 200 with the full browser header set — the CMS 403s a bare
   UA). It is an **"eComment" SUBMISSION form** (Granicus/CivicPlus widget, JS-rendered;
   "eComment" + a Submit control, no listing of prior submissions). **No archive of past
   comments, no export feed, no "correspondence" document.**

2. **Agendas & Minutes landing** —
   `https://www.cottonwoodheights.utah.gov/your-government/elected-officials/council-meeting-agendas-and-minutes`
   (fetched live 2026-07-12, HTTP 200). Three document columns per meeting date —
   **Agenda | Packet | Minutes** — with an eComment link, but **no "public comment" /
   "correspondence" document type** and no comment archive.

3. **Other portals** — web/page scan for Open City Hall / Speak-Up / Peak Democracy /
   "correspondence received": **none found.** The city runs only the eComment submit form.

4. **Inside the minutes** — the council minutes **do** carry a **"Public Comment"** section
   and transcribe in-person / public-hearing speakers **inline as clerk paraphrase**
   (third-person, `(Resident)`-tagged — e.g. the 2024-01-16 trail-maintenance hearing names
   and summarizes multiple resident speakers). Confirmed present across the 2020–2026 minutes
   corpus (grep `Public Comment`). Per the extraction standard these are **speaker-log notes,
   not written comments**, so they belong in a labeled minutes speaker-log (if built during
   the votes/minutes phase), **never** in `all_comments_clean.csv`.

5. **Agenda packets** — CH bundles emailed/eComment submissions to the Recorder, which *may*
   be attached to agenda **Packets**. Packets are **not downloaded in this repo** (only
   minutes were acquired). A packet-level "correspondence received" grep remains the single
   open lead before this verdict could ever flip; on all evidence to date (no published
   archive anywhere on the site), the honest call is **submit-only**.

## If this changes

If the city later publishes a comment archive / correspondence export, or packets are
acquired and contain bundled emailed comments, extract to the 14-column schema
(`date,contact_name,subject,topic,comment,district,source,has_attachment,source_file,page_numbers,period_start,period_end,date_normalized,quality_flag`)
and populate `all_comments_clean.csv`. Until then it stays header-only.
