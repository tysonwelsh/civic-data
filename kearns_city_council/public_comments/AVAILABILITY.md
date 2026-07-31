# Public comments — availability (City of Kearns)

**Verdict: SUBMIT-ONLY / NOT PUBLISHED.**  `all_comments_clean.csv` is **header-only** —
there is no genuine published written-comment corpus to populate it. This is an honest
empty result, not a gap to be filled.

## How Kearns takes public comment

Kearns accepts public comment two ways, both **ephemeral / submit-only**:

1. **In person or virtually at the meeting** — "Citizen Public Input," 3 minutes/person,
   via a required sign-up form and a virtual speaker queue. The clerk **paraphrases**
   speakers into the meeting minutes ("Numerous members of the public offered comments…",
   named residents summarized in the third person).
2. **Written comment emailed in advance to the City Recorder** — to **Diana Baun,
   `dbaun@msd.utah.gov`** (the recorder is Greater Salt Lake **MSD** staff), **before
   3:00 p.m. on the meeting day**; public-hearing comments to the recorder as well
   (`nsmedley@msd.utah.gov` seen on some hearing notices). These emailed comments are
   **considered by the council but not published** anywhere.

The city publishes **no** archive of emailed written comments: no dedicated comments page,
no eComment / Open City Hall / Speak-Up portal, no "correspondence received" folder, and
no correspondence section inside the agenda / "Meeting Supporting Documents" packets. The
only public record of a comment is the **clerk's paraphrase of in-meeting speakers in the
minutes** — a speaker log (meeting-record notes), **not** citizen-submitted written text,
so per the collection standard it does **not** populate `all_comments_clean.csv`.

## Avenues checked (2026-07-12)

1. **Dedicated published-comments page / archive** — **none.** The city site
   (`kearns.utah.gov`) is a **Cloudflare-protected custom CMS** that serves a JS challenge
   to all bots (browser UA included) → not directly scrapable; the canonical acquisition
   source for Kearns is **Utah PMN** (council body 5823, PC body 1561). Neither the meeting
   pages nor PMN expose a public-comment submission feed or comment export.
2. **eComment / Open City Hall / Speak-Up / Peak Democracy portal** — **none found.** Web
   search (2026-07-12) surfaced only the sign-up form + the email-to-recorder instruction;
   no online-comment submission or export system for Kearns.
3. **Inside the minutes** — in-meeting speakers are **paraphrased inline** (clerk speaker
   log), third-person, not the citizen's own submitted text. This is minutes material,
   never `all_comments_clean.csv`.
4. **Council "Meeting Supporting Documents" packets + MSD-run PC packets** — the recon
   inspected these for bundled written correspondence; they carry agenda + ordinance texts,
   **not** forwarded resident emails or comment cards. (Unlike West Jordan / Provo, Kearns
   does not fold resident correspondence into the packet.)

## If this changes

Should Kearns (or MSD) begin publishing an eComment archive or fold written correspondence
into the PMN packets, populate `all_comments_clean.csv` with the 14-column schema (shared
with South Jordan). Until then the header-only file is the honest, correct state.
