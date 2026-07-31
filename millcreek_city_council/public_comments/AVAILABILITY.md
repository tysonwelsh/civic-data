# Millcreek public comments — availability audit

**Audit date:** 2026-07-06 · **Auditor pass:** comments-availability (GET-only, no fabrication)

> ## ✅ HARVEST COMPLETED + `?packet=true` CEILING CLOSED — 2026-07-19 (read this first)
> The queued Provo-style harvest was built AND the documented ceiling was then closed the same
> day. `all_comments_clean.csv` now holds **27 genuine verbatim written resident comments**
> (`source=agenda_packet`, SLC schema, 100 % `date_normalized`). By year: **2020 ×12, 2021 ×5,
> 2022 ×2, 2024 ×5, 2026 ×3**. By channel: **web-form 10, standalone letter 6, forwarded email
> 2, Minutes-view 9.**
>
> **Wave 1 (retained Minutes-view, no network) → 9.** `harvest_packets.py` (all 99 retained PC
> packets → `packets_scanned.csv`, 5 comment-bearing) + `extract_packet_comments.py` — the 2021
> & 2024 digital-billboard fights (Kathy Blake, Kelly Smith, Nancy Trouse, …) + a 2022 FCOZ
> slope-waiver (Randy Kerr).
>
> **Wave 2 (the `?packet=true` land-use packets, NETWORK) → +18.** `harvest_packet_true.py`
> fetched **all 100** PC `full_packet` `?packet=true` URLs (~4.8 GB; **99 ok, 1 not_pdf** =
> 2023-03-15 doc674 HTML error page), sha256'd each, `pdftotext`'d, and **DISCARDED the binaries
> per SCHEMA_SPEC §9** (provenance ledger `packet_true_fetch.csv`; millcreek `packets/` is an
> index-only / no-raw-duplication dataset). `extract_packet_true_comments.py` recovered three
> channels the Minutes-view docs omit: the city's **FormCenter "Public Comments" web-form
> submissions** (§2 — turns out they WERE archived, bundled into two 2020 packets), forwarded
> resident **emails**, and standalone **"Public Comments from Residents" letters** (e.g. the
> SD-25-007 Lexington Village letters — Caye Wycoff, Inge-Lise Goss, Marg Johns). **180 dropped**
> to audit: applicants/developers (Shopworks/CDCU, Woodbury Corp), the Millcreek Common events
> director, consultants, attorneys, the **Community Council's own recommendations**, forwarder
> wrappers, un-signed letters, and too-short/OCR-unreadable blocks. Author org/role is screened
> on the **signer/signature only** (never the body — residents routinely discuss "the developer"
> / "our HOA"); the positive gate is a first-person **resident dwelling self-identification**.
>
> **Residual (still-honest) ceiling.** Letters whose signer is unrecoverable in OCR (6 dropped
> `no_recoverable_signer`), any image-only appendix pages `pdftotext` cannot read, doc757
> (2023-12-20, no combined packet — a real city gap), and the pre-2018 agenda-only era. 27 is a
> near-complete floor now, not the trickle it was. Clerk in-minutes speaker paraphrase (§4)
> stays deliberately EXCLUDED (meeting-record notes, not written comments) — no
> `minutes_speaker_log.csv` was built.

**VERDICT (original 2026-07-06): `IN-PACKETS`** — Millcreek publishes **genuine verbatim
written public comments**, but only bundled **inside the combined Agenda + Packet PDFs** as
appendices to **Planning Commission land-use staff reports** (the same pattern as Provo).
There is **no standalone comments page, no eComment archive, and no separate correspondence
document category.**

**The original audit did NOT build `all_comments_clean.csv`** (now built 2026-07-19 — see
the box above). It deferred the harvest as a dedicated extraction pass, which this pass
executed against the retained packets.

---

## The bar (what counts)
`all_comments_clean.csv` may hold ONLY **genuine public-submitted written/online comments**
— text a resident actually wrote and submitted (letter / email / form) that the city
published. **Clerk third-person paraphrases of in-person speakers in the minutes do NOT
count** (they belong in a separate `minutes_speaker_log.csv`). This audit applies that bar.

---

## Avenues checked (item-by-item)

### 1. Dedicated comment / correspondence page or document category — NONE
- **AgendaCenter** (`https://www.millcreekut.gov/AgendaCenter`) categories: Board of
  Canvassers, City Council, Community Reinvestment Agency, Hearing Officer, Historic
  Preservation Commission, Legal Notice, Mayor, Millcreek Community Foundation, Planning
  Commission, Planning Director. **No "Public Comment / Correspondence / Communications
  Received" category.**
- No Open City Hall / Speak-Up / eComment archive surfaced on `millcreekut.gov`.

### 2. Submission mechanism — a FORM (submit-only, no public archive)
- **Public comment web form:** `https://www.millcreekut.gov/FormCenter/Contact-Us-5/Public-Comments-61`
  — collects name, city/state/zip, which meeting (Council / PC / HPC), meeting date,
  subject, comment text, optional address/phone and **document upload**. It is a
  **submission form only** — it does **not** display or archive past submissions, and the
  page says nothing about how comments are published.
- **In-person:** the agenda's standing "Public Comment Policy and Procedure" (boilerplate on
  every packet) states a speaker "may be asked to complete a **written comment form** and
  present it to the City Recorder"; ~2 minutes per speaker. Residents may also submit
  written requests for future agenda items.
- **Online during livestream:** minutes note each meeting "was recorded for the City's
  website and had an **option for online public comment**" (`/373/Meeting-Live-Stream`).
  This live online comment is **ephemeral — no archive located.**

### 3. Agenda-packet PDFs — **THE source of genuine written comments (IN-PACKETS)**
Packet URL pattern: `…/AgendaCenter/ViewFile/Agenda/_<MMDDYYYY>-<docId>?packet=true`
(the `?packet=true` variant is the full packet; the plain `ViewFile/Minutes/_…` doc is
minutes-only).

Samples pulled and `pdftotext -layout`'d:

| Packet (body, date) | URL | Pages / size | Genuine resident comments? |
|---|---|---|---|
| Council, 2025-07-14 | `…/Agenda/_07142025-938?packet=true` | 78 pp / 1.7 MB | No — agenda + staff reports + prior minutes only |
| Council, 2024-04-08 | `…/Agenda/_04082024-793?packet=true` | 204 pp / 9.6 MB | No — sign-code ordinance text + staff reports |
| **PC, 2026-05-20** | `…/Agenda/_05202026-1043?packet=true` | **269 pp / 35 MB** | **YES — verbatim resident letters appended to a land-use staff report** |
| PC, 2025-06-09 | `…/Agenda/_06092025-925?packet=true` | 170 pp / 11.7 MB | (larger PC packet; not fully classified this pass) |

**Proof (PC 2026-05-20, item SD-25-007, "4122 S Old Farm Way" subdivision):** the staff
report's **SUPPORTING DOCUMENTS** list explicitly includes **"Public Comments from
Residents,"** and the appended pages carry the residents' own words, e.g.:

> *"Dear Planning Commission, My husband and I have been residents in Lexington Village in
> Old Farm for over 10 years. We have been told that we can submit comments and concerns to
> the planning [commission]… My biggest concern is about the proposed height of the
> structures…"*

These are first-person, signed ("Sincerely"), verbatim written comments the city
published in the packet — they clear the bar. Staff reports also **note when there are
none** (e.g. another item: *"open house process, with no public comments received from
nearby residents"*), giving an honest per-item signal.

**Fidelity:** verbatim (full letter text), with the resident's name; addresses sometimes
present. Applicant/agency correspondence (e.g. an engineer's easement-vacation email chain,
SLC Public Utilities) also appears in packets and **must be excluded** — same
staff/vendor/applicant filtering Provo uses.

**Where they concentrate:** **Planning Commission land-use packets** (rezones,
subdivisions, text amendments) — the contentious items. The two **Council** packets sampled
carried none; Council public input is captured chiefly inline in the minutes (see §4).

### 4. The minutes themselves — inline SPEAKER LOG, not comments
Council/PC minutes transcribe public-hearing participation inline as **clerk third-person
paraphrase** (name + address + summarized position, e.g. recon's *"Dale Reeves, 2890 E,
expressed concern about pedestrian safety…"*; when none, *"There were no comments."*).
This is a **meeting-record speaker log — NOT the comments dataset.** If harvested it belongs
in `minutes_speaker_log.csv`, never `all_comments_clean.csv`. (Sampled council minutes
`ViewFile/Minutes/_05112026-1037`: two public hearings, both *"There were no comments."*)

### 5. Records / transparency / GRAMA — no comment archive
No open-data portal or "council correspondence" archive found beyond the AgendaCenter and
the FormCenter submission form above.

---

## Retrieval recipe / next step (Provo-style harvest — QUEUED, not done here)
1. Enumerate every **Council** and **Planning Commission** packet URL 2020–2026 via the
   CivicPlus `AgendaCenter/Search` / `PreviousVersions` paged endpoints (recon §1), forming
   `…/ViewFile/Agenda/_<MMDDYYYY>-<docId>?packet=true`.
2. GET each packet (browser UA), `pdftotext -layout`, and **page-walk classify**: keep only
   resident-authored comment blocks (staff-report "Public Comments from Residents"
   appendices + any `From:/Sent:/Subject:` resident email blocks). **Drop** staff / applicant
   / consultant / agency / Community-Council correspondence via a name blocklist + role regex
   (reuse Provo's `extract_packet_comments.py` logic).
3. Emit SLC schema
   (`date,contact_name,subject,topic,comment,district,source,has_attachment,source_file,page_numbers,period_start,period_end,date_normalized,quality_flag`),
   `source=agenda_packet`. Log **every** packet scanned to `packets_scanned.csv`
   (had_comments / n_comments) so coverage is provable; retain only comment-bearing PDFs in
   `raw/packets/`. Expect the yield to be **PC-land-use-heavy**, Council-light.
4. Separately, if desired, harvest the minutes speaker paraphrases into
   `minutes_speaker_log.csv` (clearly labeled non-comments).

Because a genuine published corpus exists, this city's `public_comments/` should NOT be
treated as an honest-empty; it is **IN-PACKETS pending harvest**.

```json
{"verdict":"IN-PACKETS","locations":["https://www.millcreekut.gov/AgendaCenter (Planning Commission land-use agenda packets, ?packet=true — 'Public Comments from Residents' staff-report appendices; verbatim, named)","https://www.millcreekut.gov/FormCenter/Contact-Us-5/Public-Comments-61 (submission form only, no public archive)"],"packets_carry_comments":true,"packet_fidelity":"verbatim resident letters, named, appended to PC land-use staff reports; Council packets sampled carried none","minutes_carry_comments":"inline clerk speaker-log paraphrase only (name+address+summary) — NOT genuine comments","submit_how":"web form (FormCenter/Public-Comments-61) or written comment form to City Recorder in-person; ephemeral online comment during livestream (not archived)","artifact_written":"AVAILABILITY.md (no all_comments_clean.csv built — full Provo-style packet harvest queued)","checked":["AgendaCenter categories","FormCenter public comment form","3 agenda packets (2 Council, 1 PC) + 1 PC packet partial","council minutes sample","web search + PMN"]}
```
