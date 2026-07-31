# Public comments — availability (South Salt Lake City)

**Verdict: SUBMIT-ONLY / NOT PUBLISHED (honest empty).** As-of 2026-07-12.

South Salt Lake City takes public comment three ways — (1) **in person** at the Council
meeting, (2) live over **Zoom**, and (3) via the city **"connect line" `801-464-6757` /
`connect@sslc.gov`**. The city publishes **no** archive of written/emailed comments: there
is **no dedicated comments page, no eComment / Open City Hall / Speak-Up portal, and no
"correspondence received" export**. The only public record of a comment is the **clerk's
paraphrase of in-person / Zoom speakers written into the recorded meeting minutes** (a
`Public Comments/Questions` item plus the `OTHERS PRESENT` attendee list on the PMN
minutes). Per the collection standard, those clerk paraphrases are **meeting-record
speaker notes, NOT public-submitted written comments**, so they do **not** populate
`all_comments_clean.csv`.

`all_comments_clean.csv` is therefore **HEADER-ONLY** (the SLC/South-Jordan sibling
14-column schema, zero data rows). This is an honest empty result, not a gap to be filled
or fabricated.

## Avenues checked (comments-auditor hunt order)

1. **Dedicated published-comments page / archive** — **none.** `https://sslc.gov/` and the
   City Council page `https://sslc.gov/160/City-Council` (browser-UA fetch, HTTP 200,
   2026-07-12) carry meeting times, Zoom/YouTube links, agendas and member contacts, but
   **no** public-comment submission form, comment archive, or "correspondence received"
   link. The only comment-intake artifact surfaced is the connect-line phone number
   `801-464-6757`. No SLC-style weekly comment PDFs, no St. George-style
   `public_comments.php`.

2. **eComment / Open City Hall / Speak-Up / Peak Democracy portal** — **none found.** The
   CivicPlus/CivicEngage AgendaCenter (`https://sslc.gov/AgendaCenter`, HTTP 200) exposes
   only agenda/packet documents; it has no online-comment submission or export feed.

3. **Utah Public Notice (PMN) — recorded minutes + packets.** The recorded minutes on PMN
   body **1295 (Council)** / **1297 (Planning Commission)** carry a `Public
   Comments/Questions` agenda item with the clerk's in-meeting speaker paraphrase — the
   `OTHERS PRESENT` list and hearing-speaker notes — which is meeting-record content, not
   a written-comment corpus. The PMN council body landing page
   (`https://www.utah.gov/pmn/sitemap/publicbody/1295.html`, HTTP 200, 2026-07-12) shows
   **no** correspondence/public-comment archive section.

4. **Correspondence embedded in agenda packets** — **incidental only, not an archive.**
   Written correspondence occasionally appears *inside* a PMN/AgendaCenter agenda packet
   (e.g. a resident email attached as an exhibit to a specific item), as flagged in
   `../recon.md`. That is item-specific packet material, not a systematic published
   comment channel, and is out of scope for `all_comments_clean.csv`. If a future
   `packets/` expansion dataset is built (mirroring South Jordan's), a packet-text sweep
   for emailed correspondence would be the place to harvest any such stray items — logged
   here as a deferred lead, not a present dataset.

## If this ever changes

Should the city stand up an eComment/Open City Hall portal or begin publishing a
"correspondence received" archive, build `all_comments_clean.csv` to the 14-column schema
(`date,contact_name,subject,topic,comment,district,source,has_attachment,source_file,page_numbers,period_start,period_end,date_normalized,quality_flag`)
and delete this verdict. Until then, the header-only CSV + this file are the honest record.
