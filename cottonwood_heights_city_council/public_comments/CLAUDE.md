# public_comments/ — Cottonwood Heights (HONEST-EMPTY)

**Verdict: SUBMIT-ONLY / NOT PUBLISHED.** Cottonwood Heights publishes **no archive** of
written or eComment public comments, so `all_comments_clean.csv` is intentionally
**header-only** (schema-conformant, zero rows). This is a **legitimate honest zero**, not a gap
to be filled. The full avenue-by-avenue hunt is in **`AVAILABILITY.md`** (read it before
claiming any comment data exists).

```
all_comments_clean.csv   header-only (date,meeting,body,name,... ) — DELIBERATELY 0 rows
AVAILABILITY.md          the SUBMIT-ONLY verdict + every avenue checked (comments-auditor hunt)
raw/                     (empty / provenance notes only — nothing to retain)
```

## Why empty
Cottonwood Heights accepts public comment three ways — an **eComment** web form
(`/your-government/public-comment`, a Granicus/CivicPlus JS widget with a Submit control and **no
listing of prior submissions**), a **written comment emailed to the City Recorder**
(`recorder@ch.utah.gov`, by Tuesday noon), and **in person** at the meeting (3-minute limit).
The city exposes **no comments-archive page, no Open City Hall / Speak-Up / Peak Democracy
portal, and no "correspondence received" export**. The only public record of a comment is the
**clerk's paraphrase of in-person / hearing speakers written into the minutes** — which, per the
collection's extraction standard, is **meeting-record speaker notes, NOT public-submitted
written comments**, and therefore does **not** populate `all_comments_clean.csv`.

## Consequences for analysis
- **Do not** treat a hearing speaker named in the minutes as a "public comment" row — it is a
  minutes-layer note; quote it from the minutes, not as comment data.
- Cottonwood Heights is one of the honest-zero comment cities (compare `SCHEMA_SPEC.md`;
  substantive published comment archives exist only in **SLC** and **Park City**).
- `build_weeks.py` reports **0 comments** for every week — that is correct, not a stale/derived
  bug.

If the city ever launches a public comment portal or correspondence export, this becomes a real
acquisition target; until then the header-only CSV is the faithful record.
