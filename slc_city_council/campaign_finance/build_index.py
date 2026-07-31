#!/usr/bin/env python3
"""build_index.py — turn the retained SLC campaign-finance JSON (raw/*.json) into:
  - text/<id>.txt   : a human-readable sidecar for EVERY filing (Source-6 requirement)
  - index.csv       : one row per (election, candidate) filing, with the join to
                      election_results/ by candidate + year + district.

Reads ONLY what harvest.py saved. Does NOT build structured contribution/expenditure
tables (separate planned layer) — the per-contribution arrays inside the raw JSON are
retained as documents but summarized here only as counts/stated totals.

Idempotent: regenerates text/ + index.csv from raw/ each run.
"""
import csv, json, os, re, glob
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
TEXT = os.path.join(HERE, "text")
IDX = os.path.join(HERE, "index.csv")
ELECTIONS_CSV = os.path.join(HERE, "..", "election_results", "slc_results_by_candidate.csv")
RETRIEVED = date.today().isoformat()
PORTAL = "https://dotnet.slcgov.com/Attorneys/CampaignFinance_Public/#/Candidates/Contribution"
API = "https://dotnet.slcgov.com/Attorneys/CampaignFinance_Public/api/CampaignFinanceAPI/"

# SCHEMA_SPEC §9 campaign_finance contract header first, city extras after.
# reporting_period is not populated (portal filings are whole-election summaries) —
# DictWriter restval emits it blank, per contract.
INDEX_COLS = ["date", "candidate", "office", "election_year", "filing_type", "reporting_period",
              "title", "source_url", "retrieved_date", "format", "extraction_method", "path",
              "district", "candidate_id", "election_id", "status",
              "stated_total_contributions", "stated_total_expenditures", "ending_balance",
              "n_contributions", "n_expenditures",
              "matched_election_candidate", "join_confidence"]


def load(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def norm_name(s):
    if not s:
        return ""
    s = s.upper()
    s = re.sub(r"\(NP\s*\)|\(NP\)", "", s)           # strip nonpartisan marker
    s = re.sub(r'["“”]', "", s)             # quotes around nicknames
    s = re.sub(r"[.,]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def name_tokens(s):
    return set(t for t in norm_name(s).split() if len(t) > 1)


def load_election_index():
    """(year, office) -> list of (name, district, is_winner) from the by-candidate CSV."""
    idx = []
    if not os.path.exists(ELECTIONS_CSV):
        return idx
    for r in csv.DictReader(open(ELECTIONS_CSV)):
        idx.append(r)
    return idx


def join_candidate(name, year, office, district, elec_rows):
    """Return (matched_name, confidence) joining a filing candidate to election_results."""
    ft = name_tokens(name)
    if not ft:
        return "", "none"
    cands = [r for r in elec_rows if str(r.get("year")) == str(year)]
    best, best_score, best_conf = "", 0, "none"
    for r in cands:
        rn = r.get("candidate", "")
        rt = name_tokens(rn)
        if not rt:
            continue
        inter = ft & rt
        score = len(inter)
        # last-name + first-name match is the anchor
        exact = (ft == rt)
        dist_ok = (not district) or (str(r.get("district", "")).strip() == str(district).strip()) \
            or office == "Mayor"
        if exact and dist_ok:
            return rn, "exact"
        if score >= 2 and score > best_score:
            best, best_score = rn, score
            best_conf = "high" if (score >= 2 and dist_ok) else "medium"
    return best, best_conf


def g(d, *keys, default=""):
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, ""):
            return d[k]
    return default


def as_list(x, *wrap_keys):
    if isinstance(x, list):
        return x
    if isinstance(x, dict):
        for k in wrap_keys + ("data", "value", "Items", "items"):
            if isinstance(x.get(k), list):
                return x[k]
    return []


def main():
    os.makedirs(TEXT, exist_ok=True)
    elec_rows = load_election_index()

    # map election_id -> year from elections.json
    eid_year = {}
    elections = as_list(load(os.path.join(RAW, "elections.json")) or [], "Elections")
    for e in elections:
        eid = g(e, "ElectionId", "Id", "id")
        yr = g(e, "ElectionYear", "Year")
        if eid != "":
            eid_year[str(eid)] = yr

    rows = []
    # one filing per candidate summary file
    for sfile in sorted(glob.glob(os.path.join(RAW, "summary_e*_c*.json"))):
        m = re.search(r"summary_e(\w+)_c(\w+)\.json$", os.path.basename(sfile))
        if not m:
            continue
        eid, cid = m.group(1), m.group(2)
        summary = load(sfile) or {}
        fin = load(os.path.join(RAW, f"financial_e{eid}_c{cid}.json")) or {}
        contribs = as_list(load(os.path.join(RAW, f"contributions_e{eid}_c{cid}.json")) or [], "Contributions")
        expends = as_list(load(os.path.join(RAW, f"expenditures_e{eid}_c{cid}.json")) or [], "Expenditures")

        # candidate object may live inside summary or financial payloads
        cand = {}
        for src in (summary, fin):
            if isinstance(src, dict):
                if isinstance(src.get("Candidate"), dict):
                    cand = src["Candidate"]; break
                if src.get("FullName") or src.get("LastName"):
                    cand = src; break
        name = g(cand, "FullName") or f"{g(cand,'FirstName')} {g(cand,'LastName')}".strip()
        office_type = g(cand, "OfficeType", "Office")
        district = g(cand, "District")
        district = "" if str(district) in ("0", "") else str(district)
        office = "Mayor" if "MAYOR" in str(office_type).upper() else \
                 ("Council" if "COUNCIL" in str(office_type).upper() or district else str(office_type))
        year = eid_year.get(str(eid)) or g(summary, "ElectionYear") or g(fin, "ElectionYear")
        status = g(cand, "Status")
        tot_c = g(cand, "TotalContributions", default=g(fin, "TotalContributions"))
        tot_e = g(cand, "TotalExpenditures", default=g(fin, "TotalExpenditures"))
        end_bal = g(cand, "EndingBalance", default=g(fin, "EndingBalance"))

        matched, conf = join_candidate(name, year, office, district, elec_rows)

        # text sidecar
        tid = f"e{eid}_c{cid}"
        tpath = os.path.join(TEXT, f"{tid}.txt")
        lines = [
            f"Salt Lake City Campaign Finance Disclosure",
            f"Candidate: {name}",
            f"Office: {office}" + (f"  District: {district}" if district else ""),
            f"Election year: {year}   ElectionId: {eid}   CandidateId: {cid}",
            f"Status: {status}",
            f"Total contributions (stated): {tot_c}",
            f"Total expenditures (stated): {tot_e}",
            f"Ending balance (stated): {end_bal}",
            f"Itemized contribution records: {len(contribs)}",
            f"Itemized expenditure records: {len(expends)}",
            f"Source: {PORTAL}",
            f"API: {API}GetElectionSummaryByCandidate?pElectionId={eid}&pCandidateId={cid}",
            f"Retrieved: {RETRIEVED}",
        ]
        with open(tpath, "w", encoding="utf-8") as f:
            f.write("\n".join(str(x) for x in lines) + "\n")

        rows.append({
            "date": (str(year) + "-01-01") if year else "",
            "title": f"{name} — {year} SLC campaign finance disclosure ({office}"
                     + (f" Dist {district}" if district else "") + ")",
            "source_url": f"{API}GetElectionSummaryByCandidate?pElectionId={eid}&pCandidateId={cid}",
            "retrieved_date": RETRIEVED,
            "format": "json",
            "extraction_method": "SLC Campaign Finance WebAPI (JSON); text sidecar rendered",
            "candidate": name,
            "office": office,
            "district": district,
            "election_year": year,
            "filing_type": "summary",
            "path": f"raw/summary_{tid}.json",
            "candidate_id": cid,
            "election_id": eid,
            "status": status,
            "stated_total_contributions": tot_c,
            "stated_total_expenditures": tot_e,
            "ending_balance": end_bal,
            "n_contributions": len(contribs),
            "n_expenditures": len(expends),
            "matched_election_candidate": matched,
            "join_confidence": conf,
        })

    rows.sort(key=lambda r: (str(r["election_year"]), str(r["office"]), str(r["district"]), r["candidate"]))
    with open(IDX, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=INDEX_COLS)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    matched = sum(1 for r in rows if r["join_confidence"] in ("exact", "high"))
    print(f"index.csv: {len(rows)} filings; {matched} joined to election_results "
          f"({100*matched//len(rows) if rows else 0}%)")
    from collections import Counter
    print("by year:", dict(Counter(str(r['election_year']) for r in rows)))


if __name__ == "__main__":
    main()
