# Provo — genuine written public comment: availability & verdict

**Question this file answers:** where (if anywhere) does Provo publish *genuine
public-submitted written/online comments* — the residents' OWN submitted text, like
SLC's weekly public-comment PDFs — and what was recoverable here?

**Reminder on the bar (see `extraction_standards.md`):** the target is text the public
actually wrote and submitted (web form / email / eComment portal / uploaded letter) and
that the city published. **Clerk paraphrases of in-person speakers in the minutes do NOT
count** — those are meeting-record notes and live in `minutes_speaker_log.csv`, never in
`all_comments_clean.csv`.

---

## Avenues checked (priority order)

### 1. OpenGov "Open City Hall" — portal `provout`  →  **PORTAL-GATED**
- Live portal: `https://communityfeedback.opengov.com/portals/provout`
  (aliases `OpenCityHall.provo.org`, `opentownhall.com/portals/provout`).
- The portal **is real and was actively used** — Google indexes dozens of live topic
  ("Issue") pages, e.g. `…/provout/Issue_11414` (PLRZ20210271 – Provo Bay Neighborhood),
  `Issue_10700` (2021 Neighborhood Program Survey), `Issue_6160` (General Plan Update),
  `Issue_4095` (West Side vision), `Issue_4337`, `Issue_10988`, `Issue_11602`, etc.
  Each topic gathers genuine *registered + unregistered statements* (written public
  comment). Example header recovered: Issue_11414 = **"27 statements: 22 registered
  statements and 5 unregistered statements."**
- **But the comment bodies are not retrievable from here:**
  - **Live fetch is bot-gated.** Every direct request (`curl`, desktop-UA, WebFetch,
    the `/api/...`, `.json`, `/forum_home`, `/topics`, `/statements`, `/respond`
    variants, and the alias hosts) returns **HTTP 404 "Community Feedback – Server
    Error"** — the host cloaks all portal slugs (even known-good ones like
    `saltlakecity`) to bots. It is a server-rendered Rails app gated behind
    Cloudflare; the real content needs an interactive, cookie-bearing browser session
    we don't have.
  - **Wayback only archived the topic *shells*, not the statements.** Via the
    non-rate-limited `archive.org/wayback/available` API: `forum_home`, `Issue_11414`,
    `Issue_10700` have snapshots, but the snapshot HTML contains only the topic intro +
    a "View Statements" link — **the actual statement text loads via JS and was never
    captured**. The `…/Issue_*/statements` sub-pages return **NONE** (no Wayback
    snapshot) for every issue checked. (`web.archive.org/web/…` and the CDX API are also
    heavily 429-rate-limited from this host; the `available` API is the reliable probe.)
- **Verdict: PORTAL-GATED.** The OpenGov written comments exist and were published on a
  live portal, but are not recoverable without an authenticated JS browser, and Wayback
  did not capture the statement bodies. This is the main coverage gap for *typed* online
  comment. Evidence: `raw/opengov_fetch_attempts.txt`, `raw/wb_issue_11414.html`
  (archived shell showing the statement *count* but not the text), `raw/wb_forum_home.html`.

### 2. Agenda-packet PDFs (`documentType=5`)  →  **IN-PACKETS (genuine comments FOUND)**
- `packet_url` in `../meeting_minutes/minutes_index.csv` (306 of 311 meetings) points to
  `agendas.provo.gov/Documents/DownloadFileBytes/…?documentType=5&meetingId=…`.
  **These download directly** (no auth needed) — large PDFs (8–120 MB, 44–800 pages).
- Provo packets **bundle genuine resident-submitted emails and letters**, forwarded to the
  Planning Commission / Council on (mostly) land-use & rezone items. They appear as verbatim
  email blocks (`From: <Resident> / Sent: <date> / To: <staff> / Subject: …` + the resident's
  own words). These are the public's OWN text — exactly the SLC-style target.
- **FULL HARVEST (all 138 Regular-Meeting packets, 2020–2026):** every regular `packet_url` was
  downloaded + `pdftotext`-scanned (`harvest_packets.py`; audit in `packets_scanned.csv`).
  **26 packets carried ≥1 genuine comment → 81 genuine written comments** after excluding
  staff/vendor/applicant senders and de-duping. Named residents e.g. Erin Preston (Treeside
  Charter), Robert & Heidi Lawrence, the foothills-protection cohort (Hunter Gibson, Susan &
  Craig Christensen, Kaye Nelson, John Bennion…), the LaFontaine/Riverbottoms neighbors, Kathleen
  Damron, Dean Griffin, Sandra Brady, Christian vom Lehn, the Bogdin family, RaDene Hatfield…
  35 non-public blocks dropped → `all_comments_dropped.csv`. See `extract_packet_comments.py`.
- **By year:** 2020 = 60, 2021 = 19, 2022 = 2, 2023–2026 = 0. Genuine attached comments cluster
  hard on the contentious **2020–2021 land-use fights** (Critical Hillside/Foothills Overlay,
  Christensen Oil M1 text amendment, Heron's Landing, LaFontaine, Osprey Town Homes, East Bay).
  From 2023 on, packets carry only the boilerplate "written comments … addressed in the Staff
  Report" footer with **no attached resident emails** — that typed input now flows through the
  (gated) OpenGov portal instead.
- **Disk:** only the **26 comment-bearing PDFs** are retained (`raw/packets/<date>_packet.pdf`,
  ~1.3 GB) as provenance; the 112 comment-free packets were scanned and discarded (logged in
  `packets_scanned.csv`, `had_comments=false`) rather than hoarding several GB.
- **Verdict: IN-PACKETS, fully harvested.** `source = agenda_packet`, `has_attachment = True`.

### 3. provo.gov pages publishing council correspondence  →  **SUBMIT-ONLY**
- `provo.gov/546/Public-Comments` and the Council pages describe **how to submit** (email
  `council@provo.org`, email your district rep, comment 2 min in person at the 5:30 pm
  Tuesday meeting, or "weigh in" via Open City Hall). They are intake/instruction pages —
  **no archive of received written comments is published** on provo.gov.
- **Verdict: SUBMIT-ONLY** (no published correspondence archive).

### (not a source) In-meeting minutes transcription  →  reclassified, NOT counted
- The Provo minutes paraphrase in-person speakers in the third person with video
  timestamps. **737 such paraphrases** were previously (wrongly) in
  `all_comments_clean.csv`; they have been **moved to `minutes_speaker_log.csv`** with a
  header note marking them MEETING-RECORD NOTES, not public-submitted written comments.

---

## Bottom line

| Avenue | URL | Verdict |
|---|---|---|
| OpenGov Open City Hall (`provout`) | communityfeedback.opengov.com/portals/provout | **PORTAL-GATED** — comments exist & were published, but live portal cloaks bots and Wayback archived only topic shells (not the statement bodies) |
| Agenda-packet PDFs (documentType=5) | agendas.provo.gov/…?documentType=5 | **IN-PACKETS (fully harvested)** — genuine resident emails/letters bundled on contentious items; **all 138 regular packets scanned → 81 found** (26 comment-bearing packets) |
| provo.gov council-comment pages | provo.gov/546/Public-Comments | **SUBMIT-ONLY** — intake instructions, no published archive |
| Minutes speaker paraphrases | (the minutes) | **NOT a written-comment source** — reclassified to `minutes_speaker_log.csv` |

**Net:** Provo's genuine written public comment is split between a **gated OpenGov portal**
(richest for 2022+ typed online comment, but unrecoverable here) and **agenda-packet
attachments** (recoverable, concentrated on 2020–2021 land-use fights). The packet avenue is
now **fully harvested**: `all_comments_clean.csv` holds **81 genuine written comments** from
all 138 Regular-Meeting packets (`source=agenda_packet`, `has_attachment=True`, 100%
`date_normalized`), with `packets_scanned.csv` documenting that every packet was checked. The
**only remaining ceiling** is an interactive, authenticated browser session against the
OpenGov "Open City Hall" portal — everything obtainable from the packets has been obtained.
