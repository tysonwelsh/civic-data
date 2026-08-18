# SLC campaign finance — GRAMA request package (researched 2026-08-14)

**Status: READY TO SEND — owner action required. Nothing here has been sent.**

What it takes, what it costs, what each request must contain, and three ready-to-paste
drafts. Every legal claim below is cited to a primary source and was verified on
2026-08-14. Evidence for the source-availability claims: `RECON_2026-08-02.md` and its
2026-08-14 addendum; `AVAILABILITY.md`.

---

## 1. Bottom line

**Effort:** ~30 minutes to send. GRAMA imposes no form requirement — a plain email
containing four identifiers plus a description satisfies the statute.

**Cost:** **$0 if the fee waiver is granted**, which is a strong ask here (§2 explains why).
Without a waiver, an estimated **$0–400 total** across all three requests — and the city
must give you an advance estimate before incurring anything, so there is no runaway risk.

**The leverage is unusually good.** This is not a "we hope they have it" request:

1. The records are a **registered, permanent-retention, PUBLICLY-classified records
   series** — Utah State Archives **Series 26415**, "Campaign finance statements," *Salt
   Lake City (Utah). City Recorder*, **1981–present**, classification **Public**,
   retention **Permanent** (disposition authority **GRS-282**; the municipal general item
   **GRS-1011** likewise says *"Retain permanently. Transfer records to the archives."*).
   The Archives holds **no copy** (`seriesHoldings: No`), so the city holds them. **"We no
   longer have it" is not an available answer** for a permanent series.
2. **The city is already under an affirmative statutory duty to publish these.** Utah Code
   **§10-3-208(10)(a)** requires the recorder to make each statement "available for public
   inspection and copying no later than one business day after the statement is filed," and
   **§10-3-208(10)(b)(i)** requires "posting an electronic copy or the contents of the
   statement on the municipality's website no later than seven business days" after filing.
   SLC's public portal has returned **HTTP 503 continuously since at least 2026-07-05** —
   re-verified 2026-08-14, with the 503 body **byte-identical** to the 2026-08-02 capture.
   The request is therefore asking the city to do what the law already obliges it to do.
3. Salt Lake City's **own ordinance** says the same: SLC Code **§2.46** (financial reporting
   §2.46.090; forms on file with the Recorder and **available for public inspection**
   §2.46.100). The city's own 2003-era notices printed it explicitly: *"All information
   supplied is determined to be public information and will be made available for public
   review at the Office of the City Recorder and on Salt Lake City Corporation's website."*
4. **The data demonstrably still exists.** The 503 page itself renders a live 38-row
   candidate/office/balance table from the database; the sibling candidate-login app answers
   401 (alive, authenticated) while the public read surface answers 503. For the 2005–2017
   era, the live HTTP 500 error discloses the application still sitting on the city's IIS
   host at `D:\IISRoot\dotnet.slcgov.com\managementservices\candidatereporting\`.

---

## 2. Where to send it

| | |
|---|---|
| **Office** | Salt Lake City Recorder's Office — "administers the City's Public Records Request Program" |
| **Online portal** | `https://saltlakecityut.justfoia.com/publicportal/home/newrequest` (JustFOIA / MCCi) — ⚠ **DOWN for "Scheduled Maintenance" as of 2026-08-14**, verified in a real browser. Re-check; if up, prefer it (it timestamps and tracks). |
| **Email (recommended now)** | `slcrecorder@slc.gov` |
| **Mail** | Salt Lake City Recorder, PO Box 145515, Salt Lake City, UT 84114-5515 |
| **In person** | City Hall, 451 S State St, Suite 415 · 9am–5pm M–F (appointment via their Bookings page) |
| **Phone** | (801) 535-7671 · fax (801) 535-7681 |

**People** (from the Recorder's live staff-contacts page, 2026-08-14):

- **Keith Reynolds — City Recorder** · (801) 535-6236 · `keith.reynolds@slc.gov` — the
  records officer; address the request here.
- **Thais Stewart — Deputy City Recorder** · (801) 535-6225 · `thais.stewart@slc.gov`
  *(this is the number `AVAILABILITY.md` had recorded without a name).*
- **Matthew Brown — Deputy City Recorder** · (801) 535-6045 · `matthew.brown1@slc.gov`
- **DeeDee Robinson — Elections Management Coordinator** · (801) 535-6228 ·
  `elections@slc.gov` — **the person who actually knows the campaign-finance system.**
  Worth a courtesy cc.
- **Steven Thain — Records Archive Clerk** · (801) 535-6239 — relevant to the paper era.

> ⚠ Do **not** use `requestwaiver@slc.gov`. Despite the name, the Recorder's page uses it for
> **service of subpoenas and complaints on the City Attorney**, not fee waivers.

There is an old **GRAMA request form** (`slcdocs.com/recorder/GRAMArequest.pdf`, "Version 4,
August 2011"). It is **optional** — GRAMA requires no particular form — and it is stale.
Use it only if the city insists; its fields are covered by the drafts below.

---

## 3. What each request MUST contain

**Utah Code §63G-2-204(1)** — a written request must state the requester's:

1. **name**
2. **mailing address**
3. **email address** (if you have one and will accept communications by email)
4. **daytime telephone number**
5. **a description of the record requested that identifies the record with reasonable
   specificity**

That is the entire legal requirement. Everything else below is tactical — it exists to
prevent the three ways this request can be deflected.

**Add these five things by choice:**

| Add | Why |
|---|---|
| **Series 26415 + GRS-282** citation | Names the exact registered series. Forecloses "we don't have such a record" and "it was destroyed." |
| **"as maintained" framing + native format** | See §5 — the single biggest legal risk is a §63G-2-201(7) refusal. |
| **Fee waiver request under §63G-2-203(4)** | Must be *requested*; it is not automatic. |
| **Explicit fee cap authorization** | Prevents the request stalling on a fee question. Say: waive, but if denied, notify before exceeding $50. |
| **Expedited-response request under §63G-2-204** | 5 business days instead of 10, if you show the benefit runs to the public rather than to you. Defensible here. |

---

## 4. Cost

**Statutory framework** — Utah Code §63G-2-203:

- **§63G-2-203(1)(a)** — the entity "may charge a reasonable fee to cover the governmental
  entity's actual cost of providing a record." *Actual cost, not a price list.*
- **§63G-2-203(2)(b)** — the hourly staff-time charge "may not exceed the salary of the
  lowest paid employee who…has the necessary skill and training."
- **§63G-2-203(5)(b)(iii)** — **no charge for the first quarter hour of staff time.**
  ⚠ **Exception:** this free quarter hour is forfeited if you filed a separate request with
  the same entity **within the preceding 10 days** and you are not a Utah media
  representative. *This drives the sequencing recommendation in §6.*
- No charge for **reviewing** a record to determine whether it is disclosable, or for
  **inspecting** it.
- **§63G-2-203(8)(a)** — the entity may require **prepayment** of estimated fees.
  In practice this means you will get a number before any work starts.
- **§63G-2-203(4)** — **fee waiver.**
- **§63G-2-203(6)(a)** — a denied fee waiver is **appealable** the same way a denied record is.

**SLC's local fee instrument** is the Consolidated Fee Schedule, SLC Code **Chapter 3.02**
(`3.02.010`). Its record-related lines could not be rendered on 2026-08-14 (the code library
returns 403 to scripted fetches and lazy-loads in a browser) — **so the per-page/per-hour
local rates below are inferred from the statutory cap, not read off SLC's schedule.**
Ask for the schedule with the estimate.

**Estimates — these are reasoned projections, NOT quotes from the city:**

| Request | Driver | Estimate | Basis |
|---|---|---|---|
| **A — 2005–2017 legacy app** | IT time to locate/export a retired app's DB or copy the report files off the IIS host | **$0–400** | 2–8 staff hours at an assumed $30–55/hr salary cap; wide because restoring a retired application is unpredictable |
| **B — 2019–present portal DB** | DB query/export from a live, running system | **$0–200** | 1–4 hours; their own SPA already bundles `angular2-csv`, so an export path exists in their tooling |
| **C — paper-era residue** | Clerk pulls a small number of files | **$0–25** | Likely inside the free first quarter hour |
| **Copies** | — | **$0** | Request electronic delivery; no paper, no per-page charge |
| **All three, waiver granted** | — | **$0** | §63G-2-203(4) |

**The fee-waiver argument is strong and should be made explicitly.** §63G-2-203(4) permits a
waiver where "releasing the record primarily benefits the public rather than a person." Here:

- The records are **already legally required to be free and public** on the city's own
  website (§10-3-208(10)(b)(i)); the only reason a request is necessary is that the city's
  publication channel has been down for months. Charging for restored access to records the
  city is obliged to publish is hard to defend.
- The requester is not seeking them for private advantage — the output is a **public,
  openly-licensed civic dataset** (see `DATA-LICENSE.md`, `PRIVACY.md`).
- Salt Lake City is the **only** major Utah municipality missing from an otherwise complete
  31-city structured campaign-finance layer; restoring it completes a public research resource.

---

## 5. The one real legal risk, and how the drafts neutralize it

**Utah Code §63G-2-201(7)(a)** — a governmental entity is **"not required to create a
record"** (i)&nbsp;or to **"compile, format, manipulate, package, summarize, or tailor
information"** (ii). This is the standard basis for refusing "send us a CSV export."

**§63G-2-201(8)(a)** lets the entity do it anyway if it chooses, and **§63G-2-201(8)(c)**
lets it charge for doing so.

**Mitigation, built into the drafts:**

1. **Ask primarily for the records as they are already maintained** — the database backup,
   the table exports the system already produces, the report files already sitting on the
   IIS host. Copying an existing file is production, not creation.
2. **Say you will accept any format** — native, backup, CSV, JSON, XML, PDF, or supervised
   on-site inspection. Removing format preferences removes the "tailoring" objection.
3. **Point out an export already exists in their tooling** — the public SPA bundles
   `angular2-csv`, i.e. the CSV export is a feature of the application the city already
   owns, not something being invented for this request.
4. **Offer inspection as a fallback** — inspection cannot be charged for, and a refusal to
   permit inspection of a Public-classified series is a much weaker position for the city.

---

## 6. Sequencing, timeline, and appeals

**Recommended: send A and B together as ONE request, and C separately at least 11 days
later** (or also bundled, if you would rather have one clock than save ~$15).

- Rationale: multiple requests inside a 10-day window forfeit the free first quarter hour on
  the later ones (§63G-2-203(5)(b)(iii) exception). Bundling A+B keeps them on one clock and
  one waiver decision. C is small and independent.
- Counter-consideration: a single large request is more likely to draw an "extraordinary
  circumstances" extension under §63G-2-204. If speed matters more than tidiness, send B
  alone first — it is the highest-value and most tractable ask.

**Timeline:**

| Step | Deadline | Authority |
|---|---|---|
| City response | **10 business days** from receipt | §63G-2-204 |
| …if expedited request granted | **5 business days** | §63G-2-204 |
| **Silence = denial** | on expiry | **§63G-2-204(9)** — "failure to provide the requested records or issue a denial within the specified time period…is considered the equivalent of a determination denying access" |
| Appeal to **chief administrative officer** | within **30 days** | §63G-2-401(1) |
| CAO decision | 10 business days (5 expedited) | — |
| Appeal to **Government Records Office director** | within **30 days** of the CAO decision | — |
| Director's decision | 7 business days after hearing | — |
| Judicial review, district court | within **30 days** | — |

> **Note the 2024–25 change:** the appeal path is now CAO → **Government Records Office
> director** → district court. Older repo notes and most city web pages still say "State
> Records Committee." Use the current Utah State Archives appeal forms
> (`GRAMA-appeal_to_CAO_2025.pdf`, `GRAMA-Director_appeal_2025.pdf`).
> A **denied fee waiver is separately appealable** on the same track (§63G-2-203(6)).

**Keep the submission timestamp.** The clock runs from receipt, and §63G-2-204(9) makes
silence a denial — which is what starts the 30-day appeal window. Email gives you that proof;
the portal, when it is up, gives you a tracking number.

---

## 7. Ready-to-send drafts

> Fill the four bracketed identifiers. Do **not** send from an address you don't monitor —
> the city will send the fee estimate there and may close the request if you don't answer.

### Request A+B — the two electronic eras (primary ask)

> **Subject:** GRAMA request — campaign finance disclosure records, 2005–present (Series 26415)
>
> Salt Lake City Recorder's Office
> Attn: Keith Reynolds, City Recorder
> PO Box 145515, Salt Lake City, UT 84114-5515
> cc: DeeDee Robinson, Elections Management Coordinator
>
> Dear Mr. Reynolds,
>
> Under the Government Records Access and Management Act, Utah Code §63G-2-101 et seq., I
> request access to the following records.
>
> **Requester information (§63G-2-204(1)):**
> Name: **[FULL NAME]**
> Mailing address: **[STREET, CITY, STATE, ZIP]**
> Email: **[EMAIL]** — I am willing to receive communications by email regarding this request.
> Daytime telephone: **[PHONE]**
>
> **Records requested.** All campaign finance disclosure records filed with the City Recorder
> by candidates for Salt Lake City municipal office (Mayor and City Council, all districts),
> and by their personal campaign committees, for **every election cycle from 2005 through the
> present**, including all itemized contributions and expenditures, summary and interim
> statements, amendments, and the associated candidate, committee, election-cycle, and
> reporting-period records. These are the records described by Utah State Archives **Series
> 26415** ("Campaign finance statements," Salt Lake City (Utah). City Recorder, 1981–,
> classification **Public**, retention **Permanent**, disposition authority **GRS-282**), and
> required by **SLC Code §2.46** and **Utah Code §10-3-208**.
>
> To the extent it assists in locating them, these records are held in two systems:
>
> 1. **2005–2017 (approx.)** — the "Salt Lake City Corporation Candidate Finance Reporting
>    System" formerly served at `dotnet.slcgov.com/ManagementServices/CandidateReporting/`,
>    whose search interface enumerated election years 2003, 2005, 2007, 2009, 2011, 2013,
>    2015, 2017 and 2019. That application currently returns HTTP 500; its error response
>    identifies the application directory as
>    `D:\IISRoot\dotnet.slcgov.com\managementservices\candidatereporting\`.
> 2. **2019–present** — the Campaign Finance Reporting System served at
>    `dotnet.slcgov.com/Attorneys/CampaignFinance_Public/`, backed by the
>    `CampaignFinanceAPI` web service. Its public interface has returned HTTP 503 on every
>    data request continuously since at least 2026-07-05, verified again on 2026-08-14. The
>    underlying database is plainly intact: the maintenance page itself renders a live
>    38-row table of candidates, offices and account balances.
>
> **Form of production.** I request these records **in the form in which they are already
> maintained** — for example a database export or backup, the report files as stored on the
> server, or any existing extract. I am **not** asking the City to create a new record or to
> compile, format, manipulate, package, summarize, or tailor information within the meaning
> of §63G-2-201(7). **I will accept any format the City finds least burdensome**, including
> native database format, CSV, JSON, XML, or PDF; I note that the City's own public
> application already bundles the `angular2-csv` export component, so a CSV export exists
> within the City's existing tooling. Electronic delivery is preferred; no paper copies are
> needed. **If production in any form is declined, I request to inspect the records** under
> §63G-2-201, at the Recorder's office at a time convenient to your staff.
>
> **Fee waiver (§63G-2-203(4)).** I request a full waiver of fees on the ground that release
> primarily benefits the public rather than me. These are Public-classified records that
> **Utah Code §10-3-208(10)(a)–(b) already requires the Recorder to make available for public
> inspection within one business day of filing and to post on the municipality's website
> within seven business days of filing.** This request is necessary only because that
> publication channel has been unavailable for an extended period. The records will be used
> for a non-commercial public research project that publishes Utah municipal civic data as a
> free, openly-licensed public resource; Salt Lake City is the only major Utah municipality
> currently absent from it. **If the waiver is denied, please notify me of the estimated fee
> before performing any billable work, and do not incur charges exceeding $50 without my
> written authorization.** Please also provide the fee schedule relied upon.
>
> **Expedited response (§63G-2-204).** I request a response within five business days. The
> benefit of expedited release runs to the public rather than to me: these records are
> currently unavailable to every member of the public through the channel the City is
> statutorily obliged to maintain.
>
> If any portion is withheld, please cite the specific statutory exemption for each withheld
> item, release all reasonably segregable public portions, and provide the notice of appeal
> rights required by §63G-2-205. If any responsive record has been destroyed or transferred,
> please identify the record, the date and authority for the disposition, and its current
> custodian — noting that Series 26415 carries a **permanent** retention.
>
> Thank you for your assistance.
>
> **[NAME]** · **[DATE]**

### Request C — paper-era residue (send separately, ≥11 days later)

> **Subject:** GRAMA request — 2003–2007 paper campaign finance filings (Series 26415)
>
> *[Same requester block and fee-waiver paragraph as above.]*
>
> **Records requested.** All campaign finance disclosure statements filed with the City
> Recorder by candidates for Salt Lake City municipal office for the **2003, 2005 and 2007**
> election cycles, held in paper or imaged form — Utah State Archives **Series 26415**.
>
> I specifically request the **2003 disclosure statement of candidate Dale Lambert**, who is
> listed on the Recorder's own published index ("February 15th 2003 Candidate Financial
> Disclosures," formerly at `slcgov.com/recorder/fin_disc/feb_fin_disc.htm") but whose
> statement is the only one on that index of which no public copy survives.
>
> I also request any §2.46.080 public notices of a candidate's decision to make or decline a
> declaration to limit contributions and expenditures for those cycles, to the extent not
> already published.
>
> Electronic scans are preferred; I will accept inspection at your office.

---

## 8. Before ingesting anything the city sends

- **Privacy.** Series 26415's own description says the records include *"the names and
  addresses of contributors."* The 2003 PDFs already held carry **no** addresses, so this
  would be new. `PRIVACY.md` governs; decide the handling rule **before** ingest, not after.
- **Provenance.** Anything received enters through the same `raw/` + `_fetch_log.jsonl`
  discipline as every other channel, with `channel: "grama:slc-recorder-<date>"`.
- **Never overwrite.** The 2003 tranche is city-faithful and reconciled. GRAMA-supplied data
  for 2003 would be a *second* source for the same cycle — reconcile and record the
  divergence; do not silently replace.
- **Provenance vocabulary.** The city tier's `provenance` column would need a new value for
  GRAMA-supplied records; it currently has no such value.

---

## 9. Open items

- **JustFOIA portal was down 2026-08-14.** Re-check before sending; prefer it if it is up.
- **SLC's local record-fee lines (Code 3.02.010) were not readable** — request the fee
  schedule alongside the estimate.
- **Who SLC's chief administrative officer is for GRAMA appeals** was not confirmed. A
  §63G-2-205 denial notice must state the appeal path; take it from there rather than guessing.
- **A separate, non-CF GRAMA target exists** on the same host: the retired `CityElections`
  Laserfiche subtree holding per-candidate Declaration-of-Candidacy packets (see `LEADS.md`,
  2026-08-14). Different records, different request — do not mix it into these.
