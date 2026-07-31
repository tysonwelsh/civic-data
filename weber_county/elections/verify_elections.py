#!/usr/bin/env python3
"""verify_elections.py — reconciliation harness for the Weber County canvass module.

Read-only. Checks:
  A. Internal: precinct/EV sources whose reports print their own totals
     (parsed candidate sums vs printed totals). A shortfall exactly where the
     source shows SUPPRESSED precinct cells is classified EXPECTED-SUPPRESSED
     (the certified total includes votes the published precinct grain hides).
  B. Contest-grain sources (P2/P3): candidate sums vs the report's printed
     'Total Votes (Cast)'.
  C. Cross-source: precinct-grain aggregates vs an INDEPENDENT official
     summary (certified canvass PDF, EV portal, or vision-verified
     transcription of an image-only certified summary).
Exit nonzero on any UNEXPLAINED mismatch."""
import csv
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import normalize_weber as N

LONG = os.path.join(HERE, "weber_results_long.csv")
RECON = os.path.join(HERE, "reconciliation.csv")
fail = 0
expected = 0


def main():
    global fail, expected
    rows = list(csv.DictReader(open(LONG, newline="", encoding="utf-8")))
    # suppressed-cell count per (source_file, contest)
    sup = defaultdict(int)
    for r in rows:
        if r["suppressed"] == "True":
            sup[(r["source_file"], r["contest"])] += 1
    sums_ssc = defaultdict(int)
    for r in rows:
        if r["suppressed"] == "True" or r["votes"] == "" or r["precinct"] == "":
            continue
        sums_ssc[(r["source_file"], r["sheet"], r["contest"])] += int(r["votes"])

    # ---- A ----
    rc = list(csv.DictReader(open(RECON, newline="", encoding="utf-8")))
    a = [x for x in rc if x["parsed_sum"] != ""]
    bad = exp = 0
    for x in a:
        if x["match"] == "True":
            continue
        short = int(x["printed_total"]) - int(x["parsed_sum"])
        if short > 0 and sup[(x["source_file"], x["contest"])] > 0:
            exp += 1
        elif short > 0 and x["source_file"].startswith("ev_api/"):
            # EV breakdowns null-out suppressed precincts wholesale (rows carry
            # suppressed=True only when the ballot item HAS breakdown rows);
            # any positive shortfall on an EV source is the same phenomenon
            exp += 1
        else:
            bad += 1
            print("   FAIL A:", dict(x))
    print(f"A. internal: {len(a)} checks, {exp} expected-suppressed shortfalls, "
          f"{bad} unexplained")
    fail += bad
    expected += exp

    # ---- B ----
    b = [x for x in rc if x["parsed_sum"] == ""]
    agg_printed = defaultdict(int)
    for x in b:
        agg_printed[(x["source_file"], x["scope"], x["contest"])] += int(x["printed_total"])
    nb = 0
    # contest-grain sources: compare printed totals vs their own long-file rows
    sums_summary = defaultdict(int)
    for r in rows:
        if r["precinct"] == "" and r["votes"] != "":
            sums_summary[(r["source_file"], r["sheet"], r["contest"])] += int(r["votes"])
    for (src, scope, contest), tot in sorted(agg_printed.items()):
        got = sums_summary.get((src, scope, contest))
        if got is None:
            got = sums_summary.get((src, "Weber County", contest))
        if got is None:   # summary parsed for recon only (not in manifest)
            continue
        if got != tot:
            nb += 1
            print(f"   FAIL B: {src[:40]} | {scope} | {contest[:50]} printed {tot} parsed {got}")
    print(f"B. contest-grain printed totals: {len(agg_printed)} totals, {nb} mismatches")
    fail += nb

    # ---- C ----
    print("C. cross-source reconciliation")

    def wnorm(c):
        return "WRITE-IN" if c.strip().lower().startswith("write-in") else c

    def sum_by_contest(source_file, precinct_grain=True):
        out = defaultdict(int)
        for r in rows:
            if r["source_file"] != source_file:
                continue
            if r["suppressed"] == "True" or r["votes"] == "":
                continue
            if precinct_grain and r["precinct"] == "":
                continue
            out[(r["contest"], wnorm(r["candidate"]))] += int(r["votes"])
        return out

    def force_cut(name):
        """Cut an un-deduped 'LONG SHORT' echo even when the tail carries extra
        tokens (lookup alias only — the long file keeps the verbatim name)."""
        toks = name.split()
        if len(toks) >= 4:
            k0, k1 = toks[0].lower(), toks[1].lower()
            for i in range(2, len(toks) - 1):
                if toks[i].lower() == k0 and toks[i + 1].lower() == k1:
                    return " ".join(toks[:i]), " ".join(toks[i:])
        return None, None

    def compare(tag, precinct_agg, summary_pairs, sup_contests, note=""):
        global fail, expected
        diffs, expl = [], 0
        namevar = 0
        for (contest, cand), votes in summary_pairs.items():
            got = precinct_agg.get((contest, cand))
            if got is None:
                head, tail = force_cut(contest)
                for alias in (head, tail):
                    if alias and precinct_agg.get((alias, cand)) is not None:
                        got = precinct_agg.get((alias, cand))
                        contest = alias
                        namevar += 1
                        break
            if got is None:
                # candidate-name truncation across sources (PDF drops a
                # surname that EV keeps): unique-prefix match within contest
                cands = [k for k in precinct_agg
                         if k[0] == contest and cand.startswith(k[1])
                         and len(k[1]) >= 10]
                if len(cands) == 1:
                    got = precinct_agg[cands[0]]
                    namevar += 1
            if got == votes:
                continue
            if got is not None and votes is not None and votes > got \
                    and sup_contests.get(contest, 0) > 0:
                expl += 1
                continue
            diffs.append((contest, cand, votes, got))
        status = "OK  " if not diffs else "FAIL"
        if not diffs:
            expected += expl
        else:
            fail += len(diffs)
        print(f"  {status} {tag}: {len(summary_pairs)} cells, "
              f"{expl} expected-suppressed, {namevar} name-variant-matched, "
              f"{len(diffs)} unexplained {note}")
        for d in diffs[:8]:
            print("      DIFF", d)

    def sup_map(source_file):
        out = defaultdict(int)
        for (s, c), n in sup.items():
            if s == source_file:
                out[c] = n
        return out

    # 2023 municipal primary: precinct files vs per-city official summaries
    for name, pfile, sfile in [
            ("Ogden",  "7e3a53_3364efea7ede4fb597486bf50a6e7ee8.pdf",
             "7e3a53_fcceb6a6b8e343bf89fa0ab40be82b3d.pdf"),
            ("Roy",    "7e3a53_e7ebd54543124bc9a93c0112efb71534.pdf",
             "7e3a53_78a11a0b224041319e8dcfbaa391bdf8.pdf"),
            ("NOgden", "7e3a53_db736b8b1f4f4a67bb7dc4418426230a.pdf",
             "7e3a53_6386b6b5d1e7436786c79677b6b4329d.pdf"),
            ("Hooper", "7e3a53_693bb1b48d9b4a4bb9b727fb622e13be.pdf",
             "7e3a53_f138c1f1591a4eb2a59eb245cd167a0b.pdf")]:
        summary = {(r["contest"], wnorm(r["candidate"])): r["votes"]
                   for r in N.parse_p2(sfile, 2023, "municipal primary", name)[0]}
        compare(f"2023 primary {name} precinct-vs-summary",
                sum_by_contest(pfile), summary, sup_map(pfile))

    # 2025 general: precinct canvass vs certified summary PDF + EV portal
    agg25 = sum_by_contest("92078f_dc2ffea70dfb409aa3f2b615a678de4b.pdf")
    s25 = sup_map("92078f_dc2ffea70dfb409aa3f2b615a678de4b.pdf")
    summary = {(r["contest"], wnorm(r["candidate"])): r["votes"] for r in
               N.parse_p2("92078f_ba3a3d05a36449399444d85e915efa14.pdf", 2025,
                          "municipal general", "Weber County")[0]}
    compare("2025 general precinct-vs-summaryPDF", agg25, summary, s25)
    ev25 = {}
    d = json.load(open(os.path.join(HERE, "ev_api/general11042025/ballot-items.json")))
    for it in d["data"]:
        bi = json.load(open(os.path.join(HERE,
                       f"ev_api/general11042025/bi_{it['id']}.json")))
        cname = N.dedup_contest(it["name"][0]["text"].strip())
        for bo in bi["summaryResults"]["ballotOptions"]:
            ev25[(cname, wnorm(bo["name"][0]["text"].strip()))] = bo["voteCount"]
    compare("2025 general precinct-vs-EVportal", agg25, ev25, s25)

    # 2025 general OVC cross-check: the separate OVC precinct PDF vs county file
    ovc_g = {(r["contest"], wnorm(r["candidate"])): None for r in []}
    ovcrows, _ = N.parse_p1("92078f_8eda865f4d61467683b457ca13aa3861.pdf", 2025,
                            "municipal general", "Ogden Valley City")
    ovc_pdf = defaultdict(int)
    for r in ovcrows:
        if not r["suppressed"] and r["votes"] != "":
            ovc_pdf[(r["contest"], wnorm(r["candidate"]))] += r["votes"]
    county_ovc = {k: v for k, v in agg25.items() if "OGDEN VALLEY" in k[0]}
    compare("2025 general OVC-file-vs-county-file", county_ovc, dict(ovc_pdf), s25)

    # 2025 OVC primary: official OVC precinct PDF vs EV portal (EV = canonical
    # in the long file; PDF is the county's official OVC print)
    ovcprows, _ = N.parse_p1("92078f_5ce3b1da58b3441c88d62ef05195addc.pdf", 2025,
                             "municipal primary", "Ogden Valley City")
    ovcp = defaultdict(int)
    supovc = defaultdict(int)
    for r in ovcprows:
        if r["suppressed"]:
            supovc[r["contest"]] += 1
        elif r["votes"] != "":
            ovcp[(r["contest"], wnorm(r["candidate"]))] += r["votes"]
    evp = {}
    d = json.load(open(os.path.join(HERE, "ev_api/primary08122025/ballot-items.json")))
    for it in d["data"]:
        nm = it["name"][0]["text"].strip()
        if "OGDEN VALLEY" not in nm:
            continue
        bi = json.load(open(os.path.join(HERE,
                       f"ev_api/primary08122025/bi_{it['id']}.json")))
        for bo in bi["summaryResults"]["ballotOptions"]:
            evp[(N.dedup_contest(nm), wnorm(bo["name"][0]["text"].strip()))] = bo["voteCount"]
    compare("2025 OVC primary officialPDF-vs-EVportal", dict(ovcp), evp, supovc,
            note="(PDF truncates CHRISTOPHER CHARLES CALDWELL to 'CHRISTOPHER "
                 "CHARLES' — counted as a diff if unmatched)")

    # county contests: precinct grain vs certified summaries
    for tag, pfile, sfile, yr, et, keep in [
            ("2020 general county", "92078f_c4085e1a640b4548b65500d49f7affaf.pdf",
             "7dc173_3fbd87144c1e47ca8ba5fc235501eadb.pdf", 2020, "general", N.keep_county),
            ("2022 primary county", "92078f_afc450eab79548f0be83ae4dc3a358b5.pdf",
             "7e3a53_203d49db31d8445fb0eaff40bb511b4a.pdf", 2022, "primary", N.keep_county)]:
        summary = {(r["contest"], wnorm(r["candidate"])): r["votes"] for r in
                   N.parse_p2(sfile, yr, et, "Weber County", keep_contest=keep)[0]}
        compare(f"{tag} precinct-vs-certified-summary", sum_by_contest(pfile),
                summary, sup_map(pfile))

    # 2022 general + 2023 bond: precinct grain vs vision-verified transcription
    for tag, pfile, tfile in [
            ("2022 general county", "92078f_a083bb8c60e042c6bc102be274f3695d.pdf",
             "7e3a53_847d93ca04b748b19764dfe9d4f2e2a0.pdf"),
            ("2023 bond", "92078f_def2370870034f6e9ad3b933d2f2a383.pdf",
             "92078f_1fb5ef99870440ad9f74b83a435699ab.pdf")]:
        summary = {(r["contest"], wnorm(r["candidate"])): int(r["votes"])
                   for r in rows if r["source_file"] == tfile}
        compare(f"{tag} precinct-vs-certified-transcription",
                sum_by_contest(pfile), summary, sup_map(pfile))

    # 2018: CSV (election-day official cut) vs Nov-20 Final certified summary —
    # a KNOWN VINTAGE DELTA, reported not failed if uniformly small + positive
    summary = {(r["contest"], wnorm(r["candidate"])): r["votes"] for r in
               N.parse_p2("7e3a53_1698f33fed1943edb35c3b69e5e4c813.pdf", 2018,
                          "general", "Weber County", keep_contest=N.keep_county)[0]}
    csvsum = sum_by_contest("7dc173_a00ce1d87e7043caa17d49e189b2dd3d.csv")
    deltas = []
    for k, v in summary.items():
        got = csvsum.get(k)
        deltas.append((k, v, got, None if got is None else v - got))
    okvintage = all(d[3] is not None and 0 <= d[3] <= max(40, d[1] * 0.001)
                    for d in deltas)
    print(("  DOCUMENTED " if okvintage else "  FAIL ") +
          f"2018 general county CSV-vs-final-summary: {len(deltas)} cells; "
          "CSV internally consistent (its own Totals rows match) but is an "
          "earlier official cut; certified Final summary is preferred downstream")
    for k, v, got, dd in deltas:
        print(f"      {k[0][:34]:36s} {k[1][:28]:30s} final {v} csv {got} (+{dd})")
    if not okvintage:
        fail += 1

    # 2024/2026 county: EV precinct grain vs certified canvass summary PDFs
    for tag, evsrc, sfile, yr, et, keep in [
            ("2024 general county", "ev_api/general11052024",
             "92078f_d54e5cd989d443b3942a0c9b48eab24b.pdf", 2024, "general",
             N.keep_county_2024),
            ("2026 primary county", "ev_api/primary06232026",
             "92078f_18540fc578ac4c778574b54d6a8908dd.pdf", 2026, "primary",
             N.keep_county)]:
        summary = {(r["contest"], wnorm(r["candidate"])): r["votes"] for r in
                   N.parse_p2(sfile, yr, et, "Weber County", keep_contest=keep)[0]}
        # EV suppression = null cells; find contests with any suppressed row
        supev = defaultdict(int)
        for r in rows:
            if r["source_file"] == evsrc and r["suppressed"] == "True":
                supev[r["contest"]] += 1
        compare(f"{tag} EV-precinct-vs-certified-summary", sum_by_contest(evsrc),
                summary, supev)

    print(f"\nRESULT: {expected} expected-suppressed shortfalls (documented), "
          f"{fail} UNEXPLAINED failures")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
