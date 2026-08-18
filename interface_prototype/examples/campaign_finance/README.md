# What campaign finance looks like before it becomes data

Two real 2021 filings from neighboring Salt Lake County cities. Same law, same deadline,
two completely different documents — which is the whole problem in one comparison.

## 1 — Murray, Joe Silverzweig, City Council District 2

**141 donors.** The candidate filled out the summary page by hand in ballpoint. Then, on
the official Schedule A — the form's own itemized-contributions table — he wrote one line:

> *"See Attachment."*

The actual donors are on a page he built in Excel and printed out. Every donor in this
filing lives on a document the city never designed and no system expects.

## 2 — Sandy, Monica Zoltanski, Mayor

**224 donors, 24 pages.** This is the form used correctly: typed, every contribution on the
official Schedule A, with a subtotal printed at the foot of each page.

It is still a scan. And the filer's own arithmetic slipped — the year-to-date column reads
`$3,325.05` against a period total of `$33,254.05`, a transposition that stands in the
public record to this day.

*(A mayoral filing rather than a council one — kept because it's the cleanest example of a
correctly completed form in the collection.)*

## The point

Both are public records. Neither is machine-readable. Standard text extraction returns
nothing usable for the dollar figures, and no parser can be written that handles both — one
is handwriting plus a homemade spreadsheet, the other is 24 scanned pages of a form.

Getting from documents like these to a searchable table of who gave what to whom meant
reading them by sight, page by page, and checking every transcribed page against the
subtotal printed on it.

## A note on sharing

These duplicate files the repository deliberately keeps local: campaign finance filings
print donor street addresses on the face of the form, and the project's policy
(`PRIVACY.md`) is that unredacted source PDFs stay off the published repo — only the
structured data, which keeps donor city and state and never street addresses, is shared.
They're gitignored here for that reason. Showing them on your own screen is fine; posting
the files is a different decision.
