# Nephi City (Juab County, Utah) — Election Winner Verification

**Verification date:** 2026-06-26
**Method:** Each repo-claimed winner independently cross-checked against an external source (Deseret News, Mid-Utah Radio, Ballotpedia, Juab County). Repo data was NOT trusted; winners confirmed from outside sources.

| year | office | repo winner(s) | external winner(s) | source URL | MATCH/MISMATCH |
|------|--------|----------------|--------------------|------------|----------------|
| 2019 | Council (3 seats) | Justin D. Seely; Larry O. Ostler; Nathan H. Memmott | Seely (501), Ostler (500), Memmott (495) — top 3 of 4 | https://www.deseret.com/utah/2019/11/6/20951150/utah-2019-election-results-general-municipal/ | MATCH |
| 2021 | Mayor | Justin D. Seely | Justin D. Seely (965) def. Glade R. Nielson (673) | https://midutahradio.com/news/local-news/unofficial-2021-municipal-election-results/ | MATCH |
| 2021 | Council (2 seats) | Skip F. Worwood; Jeramie L. Callaway | Skip F. Worwood (1,162) & Jeramie L. Callaway (834) — top 2 (Parady 708 third) | https://midutahradio.com/news/local-news/unofficial-2021-municipal-election-results/ | MATCH |
| 2023 | Council (3 seats) | Travis L. Worwood; Shari Cowan; J.D. Parady | Travis L. Worwood (887), Shari Cowan (802), J.D. Parady (756) — top 3 of 6 | https://midutahradio.com/news/local-news/unofficial-2023-special-election-results/ | MATCH |
| 2025 | Mayor | Justin D. Seely (unopposed) | Justin D. Seely (1,283) — sole candidate | https://midutahradio.com/news/local-news/unofficial-2025-municipal-general-election-results-2/ | MATCH |
| 2025 | Council (2 seats) | Tate T. Douglas; Jeramie L. Callaway | Tate T. Douglas (855) & Jeramie L. Callaway (665) — top 2 (Skip Worwood 629 third) | https://midutahradio.com/news/local-news/unofficial-2025-municipal-general-election-results-2/ | MATCH |

**Result: 6 of 6 races MATCH. No mismatches.**

## Notes

- **2019 & 2021 figures (UNOFFICIAL):** Juab County's online results portal only covers 2023 onward, so the repo flags 2019/2021 as unofficial (news-archive sourced). Winners independently confirmed: 2019 from Deseret News' statewide municipal tally (exact vote-total match: 501/500/495/139); 2021 from Mid-Utah Radio (exact match). Both confirmed correct.
- **Two distinct Worwoods — NOT conflated:** *Skip F. Worwood* won a council seat in **2021** (and ran again in 2025, finishing 3rd / lost). *Travis L. Worwood* won a council seat in **2023**. These are two different people; the repo keeps them separate and so do the external sources.
- **2021 council seat count:** Mid-Utah Radio lists Worwood/Callaway/Parady in descending order; the race was vote-for-**2**, so the winners are Worwood and Callaway only (Parady third = not elected). Matches repo.
- **2023 labeled "special election" by Mid-Utah Radio URL** while repo labels it "municipal general." The office, candidates, and winners are identical; the label difference does not affect winner verification.
- **Minor vote-total drift (winners unaffected):** External 2025 totals are unofficial (last updated 2025-11-20) and run a few votes below the repo's final-canvass figures (e.g., Mayor 1,283 vs 1,298; Douglas 855 vs 860). Ordering and winners are identical. 2023 unofficial Worwood 887 vs repo 895 — same pattern. These reflect unofficial-vs-final counts, not a winner discrepancy.
- **2025 municipal primary** (vote-for-2, 5 candidates) is an advancement contest, not a final winner race; top 4 advanced. Not counted among the 6 decisive races above.
- **2023 municipal primary (Sept 5 2023) — added 2026-07-20.** An advancement contest, not counted among the 6 decisive races. Confirmed from the **OFFICIAL Juab County Clerk canvass PDF** (`https://juabcounty.gov/wp-content/uploads/2023/09/Official-Results-Prim-23.pdf`; header "OFFICIAL RESULTS — Municipal Primary Election — September 5, 2023"): Nephi City Council, Vote For 3, 9 candidates — Worwood 733, Parady 672, Cowan 652, Ostler 583, Bradley 484, Miller 449 (top-6 **advanced**); Andersen 281, Ford 200, Goates 160 (eliminated). The six advancers are exactly the six 2023-general candidates, so the primary→general chain reconciles. This contest was earlier mis-recorded as "not held" (the state Enhanced Voting portal carries only an empty `primary09052023_Demo` slug); the official county PDF is authoritative.
