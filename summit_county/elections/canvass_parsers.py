"""canvass_parsers.py — the four Summit County canvass report-format parsers.

Format eras of the Summit County Clerk archive (2004-2026):
  * GEMS (Diebold/Premier GEMS, 2006-2016): "Statement of Votes Cast" SOVC
    precinct reports + two-column "Election Summary Report".
  * Electionware (ES&S, 2018-2021): per-precinct "Precinct Summary" pages +
    linear "Summary Results Report".
  * Table era (2021 crosstab city reports; 2022-2026 Precinct/County Table
    Reports): rotated precinct-x-candidate matrices + linear summaries.

Every parser is verification-first: parse failures raise (never skip
silently), and the build script reconciles each layer against an independent
in-document or cross-document certified total. See VERIFICATION.md.
"""
import re
import subprocess


def pdf_layout_pages(path):
    """pdftotext -layout, split into pages (form-feed)."""
    out = subprocess.run(["pdftotext", "-layout", path, "-"],
                         capture_output=True, text=True, check=True).stdout
    pages = out.split("\f")
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    return pages


NUM_RE = re.compile(r"^-?[\d,]+$")
PCT_RE = re.compile(r"^\d+(\.\d+)?%$")


def to_int(tok):
    return int(tok.replace(",", ""))


def is_num(tok):
    return bool(NUM_RE.match(tok))


# ---------------------------------------------------------------------------
# Electionware / table-era SUMMARY parser (layout text) — the reconciliation
# source and the per-contest candidate-order template.
# ---------------------------------------------------------------------------

FOOTERISH = re.compile(
    r"(Page \d+ of|Report generated with Electionware|Election Summary -|"
    r"Summary Results? -|Summary - \d|Results Summary -|County Summary -|"
    r"Table Report? -|Precinct Summary -|Municipal Report -|Custom Table Report -|"
    r"Precinct Table -|Bond Report -|District Report -|Precinct Results Report -|"
    r"Summary Report( 2021 General)? -)")

HEADERISH = re.compile(
    r"^(Summit County,? ?(Utah|UT)?|SUMMIT COUNTY(,? ?UT(AH)?)?|Summit|"
    r"General Election|GENERAL ELECTION|Municipal (General|Primary) Election|"
    r"MUNICIPAL (GENERAL|PRIMARY) ELECTION|Presidential Primary( Election)?|"
    r"Primary Election|PRIMARY ELECTION|SUMMIT COUNTY PRIMARY ELECTION|"
    r"(November|August|September|June|March) \d+, ?\d{4}|OFFICIAL RESULTS|"
    r"Official Results|UNOFFICIAL RESULTS|Summary Results( Report)?|Results Report|"
    r"Precinct Summary Results Report|Precinct Summary Report|Summary Report|"
    r"Election Summary\s*Report|Precinct Report|Precinct Table Report|"
    r"County (Summary Results|Table|Precinct Custom Table) Report|"
    r"\d{4} .*(Summary|Table|Report|Results).*|County GO Bond Summary Report|"
    r".*(Municipal|Bond|District|Summary) Report)\s*$", re.I)


def _headerish_line(ls):
    """True when every 2+-space-separated part of the line is page-header text
    (handles composite lines like 'November 4, 2025      County Summary')."""
    parts = re.split(r"\s{2,}", ls.strip())
    return all(HEADERISH.match(p) for p in parts if p)


def parse_ew_summary(path, per_section=False):
    """Summary Results Report (Electionware 2018-2021 / table era 2022-2026).

    Layout-text grammar per contest:
        <Contest Name (may wrap over 2 lines)>
        Vote For N
        TOTAL [VOTE %]
        NAME   votes  [pct]
        ...
        Total Votes Cast  n  [pct]
        Overvotes n / Undervotes n / [Contest Totals n]
    Returns list of contests (in order): dict(name, vote_for, candidates=[(name,votes)],
    tvc, over, under, contest_total, section).
    per_section: track the report-section line (e.g. 'Coalville City Summary Report')
    from the page header (line containing 'Report' in first 6 lines).
    """
    contests = []
    section = ""
    for page in pdf_layout_pages(path):
        lines = [l.rstrip() for l in page.split("\n")]
        if per_section:
            for l in lines[:6]:
                ls = l.strip()
                for part in re.split(r"\s{2,}", ls):
                    if part.endswith("Report") and "Summary Results Report" not in part:
                        section = part
        i = 0
        pending = []
        while i < len(lines):
            ls = lines[i].strip()
            if not ls:
                i += 1
                continue
            m = re.match(r"^Vote For (\d+)$", ls, re.I)
            if m is None:
                if (_headerish_line(ls) or FOOTERISH.search(ls) or ls == "STATISTICS"
                        or ls.startswith(("Registered Voters", "Ballots Cast",
                                          "Voter Turnout", "Election Day Precincts",
                                          "Precincts ", "Absentee/"))
                        or ls in ("TOTAL", "VOTE %") or is_num(ls) or PCT_RE.match(ls)
                        or re.match(r"^\d+ of \d+$", ls)):
                    if _headerish_line(ls) or ls == "STATISTICS":
                        pending = []
                    i += 1
                    continue
                # part of a (possibly wrapped) contest name; drop any page-header
                # parts sharing the visual line (composite lines), including a
                # report-title prefix fused onto the contest name.
                keep = [p for p in re.split(r"\s{2,}", ls) if p and not HEADERISH.match(p)]
                frag = " ".join(keep)
                frag = re.sub(r"^(Summary Results( Report)?|Results Report)\s+", "", frag)
                if frag:
                    pending.append(frag)
                i += 1
                continue
            name = " ".join(pending).strip()
            pending = []
            c = dict(name=name, vote_for=int(m.group(1)), candidates=[],
                     tvc=None, over=None, under=None, contest_total=None,
                     section=section)
            i += 1
            last_cand = None       # index into candidates for wrap-below joins
            prev_gap = False       # a blank/raw-gap line seen since last data row
            while i < len(lines):
                ls = lines[i].strip()
                if re.match(r"^Vote For \d+$", ls, re.I):
                    break
                if not ls:
                    prev_gap = True
                    i += 1
                    continue
                if _headerish_line(ls):
                    prev_gap = True
                    i += 1
                    continue
                if FOOTERISH.search(ls) or ls in ("TOTAL", "VOTE %"):
                    prev_gap = True
                    i += 1
                    continue
                # data row: NAME  <num>  [pct]   (split on 2+ spaces)
                parts = re.split(r"\s{2,}", ls)
                if len(parts) >= 2 and is_num(parts[-2] if PCT_RE.match(parts[-1]) else parts[-1]):
                    if PCT_RE.match(parts[-1]):
                        label = " ".join(parts[:-2]); val = to_int(parts[-2])
                    else:
                        label = " ".join(parts[:-1]); val = to_int(parts[-1])
                    label = label.strip()
                    if label == "Total Votes Cast":
                        c["tvc"] = val; last_cand = None
                    elif label == "Overvotes":
                        c["over"] = val; last_cand = None
                    elif label == "Undervotes":
                        c["under"] = val; last_cand = None
                    elif label in ("Contest Totals", "Contest Total"):
                        c["contest_total"] = val; last_cand = None
                    else:
                        c["candidates"].append((label, val))
                        last_cand = len(c["candidates"]) - 1
                    prev_gap = False
                    i += 1
                    continue
                if len(parts) == 1 and not is_num(ls) and not PCT_RE.match(ls):
                    # single-part non-numeric line: wrap-below continuation of
                    # the previous candidate when adjacent (no gap); otherwise
                    # the next contest's name (leave for the outer loop).
                    if not prev_gap and last_cand is not None:
                        nm, v = c["candidates"][last_cand]
                        c["candidates"][last_cand] = (nm + " " + ls, v)
                        i += 1
                        continue
                    break
                i += 1
            # write-in handling: when the report allocates write-ins to named
            # sub-rows ('Write-In: X', 'Not Assigned'), drop the 'Write-In Totals'
            # parent so candidate sums do not double-count.
            if any(n.startswith("Write-In:") for n, _ in c["candidates"]):
                c["candidates"] = [(n, v) for n, v in c["candidates"]
                                   if n != "Write-In Totals"]
            contests.append(c)
    return contests


# ---------------------------------------------------------------------------
# Table-era PRECINCT parser (2021 crosstab + 2022-2026 Precinct/County Table
# Reports). Pages are rotated 90 deg: data rows are x-bands, columns are
# y-bands read in descending y. Candidate columns are verified against the
# election's Summary Report (wordset match) and the Totals row must equal the
# summary's candidate totals exactly.
# ---------------------------------------------------------------------------

def _norm_word(w):
    return re.sub(r"[^A-Z0-9#]", "", w.upper())


def _wordset(s):
    return frozenset(_norm_word(w) for w in s.split() if _norm_word(w))


def _lettersig(x):
    """Order-free signature tolerant of mid-word line breaks: the sorted
    character multiset of all normalized tokens."""
    if isinstance(x, str):
        toks = [_norm_word(w) for w in x.split()]
    else:
        toks = list(x)
    return "".join(sorted("".join(toks)))


def _cluster(vals, gap):
    """Cluster sorted (lo, hi, item) intervals by chaining with gap tolerance."""
    out = []
    for lo, hi, item in sorted(vals, key=lambda t: t[0]):
        if out and lo - out[-1][1] <= gap:
            out[-1] = (out[-1][0], max(out[-1][1], hi), out[-1][2] + [item])
        else:
            out.append((lo, hi, [item]))
    return out


PRECINCT_LABEL_RE = re.compile(r"^[0-9A-Za-z]+:[0-9A-Za-z]+$")

_TVC = ("CAST", "TOTAL", "VOTES")


def _cell_kind(wset):
    """Classify a header cell by its normalized wordset."""
    s = frozenset(wset)
    if s == frozenset({"TOTAL", "VOTES", "CAST"}):
        return "tvc"
    if s == frozenset({"OVERVOTES"}):
        return "over"
    if s == frozenset({"UNDERVOTES"}):
        return "under"
    if s in (frozenset({"CONTEST", "TOTAL"}), frozenset({"CONTEST", "TOTALS"})):
        return "ctotal"
    if s == frozenset({"WRITEIN", "TOTALS"}) or s == frozenset({"WRITEIN", "TOTAL"}):
        return "wtotal"
    return "cand"


def parse_table_precinct(path, summary_contests, precinct_re=PRECINCT_LABEL_RE):
    """Precinct Table Report parser (rotated pages; 2021 crosstab + 2022-2026).

    Region-based: each page may hold the tail of one table and the head of the
    next (STATISTICS + contest, or two contests). Columns are matched to the
    election's certified Summary Report candidates by UNORDERED letter-signature
    bijection (candidate order differs between the two report types). Contests
    wider than a page continue horizontally on later pages; per-candidate
    accumulation merges them.

    Gates (returned in checks): parsed sums == the table's own Totals row;
    shortfall vs the certified summary total allowed only for contests with
    Suppressed precinct rows (or write-in sub-lines absent from the table),
    reported per candidate.
    """
    import fitz
    doc = fitz.open(path)
    rows = []
    stats = {}
    checks = []
    tables = {}          # summary-contest name -> dict(sums, totals, summary)
    supp_seen = set()    # (contest, precinct) suppressed markers

    # candidate lookup across the whole summary: lettersig -> [(idx, name)]
    def cand_sigs(sc):
        d = {}
        for nm, _v in sc["candidates"]:
            sig = _lettersig(nm)
            if sig in d:
                raise ValueError(f"lettersig collision in {sc['name']}: {nm}")
            d[sig] = nm
        return d

    for pno, page in enumerate(doc):
        words = page.get_text("words")
        if not words:
            continue
        # ---- x-bands over all words
        bands = _cluster([(w[0], w[2], w) for w in words], gap=4.0)
        # ---- classify data bands
        def band_label(items):
            items = sorted(items, key=lambda w: -w[1])
            toks = []
            for w in items:
                if is_num(w[4]) or w[4] in ("-", "*"):
                    break
                toks.append(w[4])
            return toks, items[len(toks):]

        data_at = {}        # band index -> (label, values, suppressed)
        marker_at = {}      # band index -> "stats" | "votefor"
        for bi, (lo, hi, items) in enumerate(bands):
            toks, vals = band_label(items)
            label = " ".join(toks)
            supp = False
            if toks and toks[-1] == "Suppressed":
                label = " ".join(toks[:-1]); supp = True
            if label and (precinct_re.match(label) or label == "Totals"
                          or (toks and precinct_re.match(toks[0]))):
                data_at[bi] = (label, vals, supp)
                continue
            up = {_norm_word(w[4]) for w in items}
            if "STATISTICS" in up:
                marker_at[bi] = "stats"
            elif "VOTE" in up and "FOR" in up:
                marker_at[bi] = "votefor"

        # ---- regions: from each marker to the next marker
        marker_bis = sorted(marker_at)
        for mi, bi in enumerate(marker_bis):
            end_bi = marker_bis[mi + 1] if mi + 1 < len(marker_bis) else len(bands)
            # contest-name window: after the previous region's last band,
            # before this marker band (used for contest disambiguation)
            prev_end_x = 0.0
            if mi > 0:
                pbi = marker_bis[mi - 1]
                prev_last = max((b for b in range(pbi, bi) if b in data_at),
                                default=pbi)
                prev_end_x = bands[prev_last][1]
            name_words = [w for w in words
                          if prev_end_x < w[0] < bands[bi][0] - 0.5]
            name_cells = []
            for lo, hi, ws in _cluster([(w[1], w[3], w) for w in name_words],
                                       gap=2.5):
                toks = {_norm_word(w[4]) for w in ws if _norm_word(w[4])}
                if toks:
                    name_cells.append((lo, hi, toks))
            region_data = [(b, data_at[b]) for b in range(bi + 1, end_bi) if b in data_at]
            if not region_data:
                continue
            first_data_x = min(bands[b][0] for b, _ in region_data)
            marker_x1 = bands[bi][1]

            # header cells define the column anchors (value tokens left-align
            # at y0 and wide numbers drift toward the next column, so anchors
            # must come from the headers; empty columns are legitimate when
            # contests sit side by side and a precinct votes in only one).
            hdr = [w for w in words if marker_x1 < w[0] < first_data_x - 1]
            # drop "N of M Precincts Reporting" banner lines (2021 crosstab
            # reports) before cell clustering: x-lines whose tokens are only
            # numbers / OF / PRECINCTS / REPORTING
            keep_hdr = []
            for lo, hi, ws in _cluster([(w[0], w[2], w) for w in hdr], gap=2.0):
                toks = {_norm_word(w[4]) for w in ws if _norm_word(w[4])}
                if toks and toks <= ({"OF", "PRECINCTS", "REPORTING"} |
                                     {t for t in toks if t.isdigit()}) \
                        and {"PRECINCTS", "REPORTING"} & toks:
                    continue
                keep_hdr.extend(ws)
            hdr = keep_hdr
            cells = _cluster([(w[1], w[3], w) for w in hdr], gap=2.5)
            cellsets = []
            for lo, hi, ws in cells:
                wset = frozenset(_norm_word(w[4]) for w in ws if _norm_word(w[4]))
                if wset:
                    cellsets.append(((lo + hi) / 2.0, lo, hi, wset))
            cellsets.sort(key=lambda t: -t[0])          # reading order
            anchors = [c[0] for c in cellsets]

            def assign_row(vals):
                """Map one data row's value tokens to column indices.

                Tokens read in descending y0. When the row is fully populated,
                zip positionally (immune to wide-number drift); otherwise map
                each token to its nearest anchor, refusing collisions.
                """
                toks = sorted(vals, key=lambda w: -w[1])
                if len(toks) == len(anchors):
                    return {i: w[4] for i, w in enumerate(toks)}
                vv = {}
                for w in toks:
                    c0 = w[1]
                    k = min(range(len(anchors)), key=lambda i: abs(anchors[i] - c0))
                    if abs(anchors[k] - c0) > 16:
                        cmid = (w[1] + w[3]) / 2.0
                        k = min(range(len(anchors)),
                                key=lambda i: abs(anchors[i] - cmid))
                        if abs(anchors[k] - cmid) > 16:
                            raise ValueError(
                                f"{path} p{pno+1}: token {w[4]!r} off-grid")
                    if k in vv:
                        raise ValueError(
                            f"{path} p{pno+1}: column collision at {w[4]!r}")
                    vv[k] = w[4]
                return vv

            if marker_at[bi] == "stats":
                rv_col = bc_col = None
                for ci, (cy, lo, hi, wset) in enumerate(cellsets):
                    if wset == frozenset({"REGISTERED", "VOTERS", "TOTAL"}):
                        rv_col = ci
                    elif wset == frozenset({"BALLOTS", "CAST", "TOTAL"}):
                        bc_col = ci
                for _, (lab, vals, sp) in region_data:
                    if lab == "Totals" or sp:
                        continue
                    vv = assign_row(vals)
                    def geti(ci):
                        t = vv.get(ci)
                        return to_int(t) if t is not None and is_num(t) else None
                    stats[lab] = (geti(rv_col), geti(bc_col))
                continue

            # ---- contest region: cells in reading order are the columns
            cellcols = [(ci, wset) for ci, (cy, lo, hi, wset) in enumerate(cellsets)]
            # split into groups at under/ctotal boundaries
            kinds = [(_cell_kind(ws), ci, ws) for ci, ws in cellcols]
            groups, cur = [], []
            for k, (kind, ci, ws) in enumerate(kinds):
                cur.append((kind, ci, ws))
                closes = False
                if kind == "ctotal":
                    closes = True
                elif kind == "under":
                    nk = kinds[k + 1][0] if k + 1 < len(kinds) else None
                    closes = nk != "ctotal"
                if closes:
                    groups.append(cur); cur = []
            if cur:
                groups.append(cur)

            page_groups = []
            for g in groups:
                has_wsub = any(kind == "cand" and "WRITEIN" in ws
                               for kind, ci, ws in g)
                cand_cells = []
                for kind, ci, ws in g:
                    if kind == "cand":
                        cand_cells.append((ci, ws))
                    elif kind == "wtotal" and not has_wsub:
                        cand_cells.append((ci, ws))   # bare Write-In Totals = ballot line
                # the group's contest-name cell: the name cell overlapping the
                # group's column anchors in y
                g_anchors = [anchors[ci] for kind, ci, ws in g]
                g_lo, g_hi = min(g_anchors) - 21, max(g_anchors) + 21
                g_tokens = set()
                for lo, hi, toks in name_cells:
                    if lo < g_hi and hi > g_lo:
                        g_tokens |= toks
                # match to a summary contest: unordered lettersig bijection of
                # the candidate cells (required) + contest-name token overlap
                # (disambiguates identical candidate sets: YES/NO retentions,
                # FOR/AGAINST amendments)
                best = None
                for sc in summary_contests:
                    sigs = {}
                    dup = False
                    for nm, _v in sc["candidates"]:
                        s = _lettersig(nm)
                        if s in sigs:
                            dup = True
                        sigs[s] = nm
                    if dup:
                        continue
                    hit = []
                    ok = True
                    for ci, ws in cand_cells:
                        s = _lettersig(ws)
                        s2 = _lettersig(ws - {"WRITEIN"})
                        if s in sigs:
                            hit.append((ci, sigs[s]))
                        elif s2 in sigs:
                            hit.append((ci, sigs[s2]))
                        else:
                            ok = False
                            break
                    if not (ok and hit):
                        continue
                    ntoks = {_norm_word(w) for w in sc["name"].split()
                             if _norm_word(w)}
                    overlap = len(ntoks & g_tokens) / max(1, len(ntoks))
                    score = (len(hit), overlap)
                    if best is None or score > best[0]:
                        best = (score, sc, hit)
                if best is None:
                    raise ValueError(
                        f"{path} p{pno+1}: no summary contest matches header cells "
                        f"{[sorted(ws) for _, ws in cand_cells]}")
                _, sc, hit = best
                st = tables.setdefault(sc["name"], {"summary": sc, "sums": {},
                                                    "totals": {}})
                page_groups.append((sc, st, hit))

            for _, (lab, vals, sp) in region_data:
                vv = assign_row(vals)
                for sc, st, hit in page_groups:
                    for ci, cand in hit:
                        if sp:
                            key = (sc["name"], lab, cand)
                            if key not in supp_seen:
                                supp_seen.add(key)
                                rows.append(dict(contest=sc["name"],
                                                 vote_for=sc["vote_for"],
                                                 precinct=lab, candidate=cand,
                                                 votes=None, suppressed=True))
                            continue
                        tok = vv.get(ci)
                        if tok is None:
                            continue
                        if lab == "Totals":
                            if is_num(tok):
                                st["totals"][cand] = to_int(tok)
                        elif is_num(tok):
                            v = to_int(tok)
                            rows.append(dict(contest=sc["name"],
                                             vote_for=sc["vote_for"],
                                             precinct=lab, candidate=cand,
                                             votes=v))
                            st["sums"][cand] = st["sums"].get(cand, 0) + v

    # ---- final reconciliation. Two vintages of the Totals row exist in the
    # wild: 2025-style (Totals EXCLUDES Suppressed precincts -> got == trow)
    # and 2024-style (Totals INCLUDES them -> got <= trow). Certified truth is
    # always the Summary Report; shortfalls are allowed only for contests with
    # suppressed precinct rows and are reported as the honest suppression delta.
    supp_contests = {c for c, p, cd in supp_seen}
    for cname, st in tables.items():
        sc = st["summary"]
        seen_cands = set(st["sums"]) | {cd for c, p, cd in supp_seen if c == cname}
        for cand, votes in sc["candidates"]:
            got = st["sums"].get(cand, 0)
            trow = st["totals"].get(cand)
            has_supp = cname in supp_contests
            internal_ok = (trow is None) or (got == trow) or \
                          (has_supp and got <= trow)
            if cand not in seen_cands:
                certified_ok = False   # column absent from the precinct table
            else:
                certified_ok = (got == votes) or (has_supp and got <= votes)
            checks.append((cname, cand, votes, got, trow,
                           internal_ok and certified_ok))
    return rows, stats, checks


# ---------------------------------------------------------------------------
# Electionware per-precinct PRECINCT SUMMARY parser (2018-2021):
# one or more pages per precinct; layout-text grammar per page:
#   <header block> / <precinct name> / [Statistics ...] / contest sections
# Contest sections mirror the summary grammar. Wrapped candidate names put the
# vote on the FIRST line and the continuation BELOW it with no blank line
# between; contest names are separated from data by blank lines.
# ---------------------------------------------------------------------------

def parse_ew_precinct(path):
    """Returns (rows, stats): rows = dicts (precinct, contest, vote_for,
    candidate, votes); stats = {precinct: (registered, ballots_cast)}."""
    rows = []
    stats = {}
    precinct = None
    open_contest = None      # dict(name, vote_for) carried across pages

    for pno, page in enumerate(pdf_layout_pages(path)):
        lines = [l.rstrip() for l in page.split("\n")]
        # drop leading header block: skip lines until (and including) the run of
        # page-header lines; the first non-headerish, non-blank line is the
        # precinct name.
        i = 0
        seen_hdr = 0
        page_precinct = None
        while i < len(lines):
            ls = lines[i].strip()
            if not ls:
                i += 1
                continue
            if _headerish_line(ls) and page_precinct is None:
                seen_hdr += 1
                i += 1
                continue
            if page_precinct is None:
                page_precinct = ls
                i += 1
                continue
            break
        if page_precinct is None:
            continue
        if page_precinct != precinct:
            precinct = page_precinct
            open_contest = None

        pending = []          # candidate-name-above wrap OR contest name parts
        last_data = None      # last emitted candidate row index (for wrap-below)
        prev_blank = True
        in_stats = False
        while i < len(lines):
            raw = lines[i]
            ls = raw.strip()
            if not ls:
                prev_blank = True
                last_data_this_line = None
                i += 1
                continue
            if FOOTERISH.search(ls):
                i += 1
                continue
            if ls in ("STATISTICS", "Statistics") or ls.startswith(("STATISTICS ", "Statistics ")):
                in_stats = True
                open_contest = None
                prev_blank = False
                i += 1
                continue
            if ls == "TOTAL" or ls == "VOTE %":
                prev_blank = False
                i += 1
                continue
            m = re.match(r"^Vote For (\d+)$", ls, re.I)
            if m:
                name = " ".join(pending).strip()
                if name:
                    open_contest = dict(name=name, vote_for=int(m.group(1)))
                elif open_contest is None:
                    raise ValueError(f"{path} p{pno+1}: Vote For with no contest name")
                else:
                    open_contest = dict(name=open_contest["name"],
                                        vote_for=int(m.group(1)))
                pending = []
                in_stats = False
                last_data = None
                prev_blank = False
                i += 1
                continue
            parts = re.split(r"\s{2,}", ls)
            # stats rows — leave stats mode as soon as a line stops looking
            # like a statistics row (the next contest name follows).
            if in_stats:
                statish = (parts[0].startswith(("Registered Voters", "Ballots Cast",
                                                "Voter Turnout", "Election Day",
                                                "Precincts", "Absentee/"))
                           or all(is_num(p) or PCT_RE.match(p) or
                                  re.match(r"^\d+ of \d+$", p) for p in parts))
                if not statish:
                    in_stats = False   # fall through and reprocess below
                else:
                    if len(parts) >= 2:
                        nums = [p for p in parts[1:] if is_num(p)]
                        if nums:
                            lab, val = parts[0], to_int(nums[0])
                            if lab == "Registered Voters - Total":
                                stats.setdefault(precinct, [None, None])[0] = val
                            elif lab == "Ballots Cast - Total":
                                stats.setdefault(precinct, [None, None])[1] = val
                    prev_blank = False
                    i += 1
                    continue
            # data row: NAME ... value [pct]
            tail_num = None
            if len(parts) >= 2:
                if PCT_RE.match(parts[-1]) and len(parts) >= 3 and is_num(parts[-2]):
                    tail_num = to_int(parts[-2]); label = " ".join(parts[:-2])
                elif is_num(parts[-1]):
                    tail_num = to_int(parts[-1]); label = " ".join(parts[:-1])
            if tail_num is not None:
                if open_contest is None:
                    # e.g. stray statistics after page break; ignore turnout rows
                    prev_blank = False
                    i += 1
                    continue
                label = label.strip()
                if pending:      # name-above wrap (rare in this format)
                    label = (" ".join(pending) + " " + label).strip()
                    pending = []
                if label in ("Total Votes Cast", "Overvotes", "Undervotes",
                             "Contest Total", "Contest Totals"):
                    last_data = None
                else:
                    rows.append(dict(precinct=precinct,
                                     contest=open_contest["name"],
                                     vote_for=open_contest["vote_for"],
                                     candidate=label, votes=tail_num))
                    last_data = len(rows) - 1
                prev_blank = False
                i += 1
                continue
            # non-numeric line: wrap-below of previous candidate, or (after a
            # blank) the next contest's name
            if not prev_blank and last_data is not None:
                rows[last_data]["candidate"] += " " + ls
            else:
                pending.append(ls)
                last_data = None
            prev_blank = False
            i += 1

    # write-in sub-line handling (mirror of the summary parser)
    by_c = {}
    for r in rows:
        by_c.setdefault((r["precinct"], r["contest"]), []).append(r)
    drop = set()
    for key, rs in by_c.items():
        if any(r["candidate"].startswith("Write-In:") or
               r["candidate"].startswith("Write-in:") for r in rs):
            for r in rs:
                if r["candidate"] in ("Write-In Totals", "Write-in Totals"):
                    drop.add(id(r))
    rows = [r for r in rows if id(r) not in drop]
    stats = {k: tuple(v) for k, v in stats.items()}
    return rows, stats


# ---------------------------------------------------------------------------
# GEMS SOVC parser (2006-2016 Statement of Votes Cast, pdftotext -layout).
# Per page: header block + contest title, a column-header band (candidate
# names at fixed char positions, possibly wrapped over 2 lines), then
# precinct groups: an unvalued precinct-header line followed by method rows
# 'Method  reg counted totalvotes  (count pct)*n'. The unindented 'Total'
# group is the jurisdiction-wide certified total (captured separately,
# never emitted as a precinct). Contests wider than a page repeat the
# precinct rows with the remaining candidate columns (horizontal
# continuation) — rows merge by (contest, precinct, method, candidate).
# ---------------------------------------------------------------------------

GEMS_METHODS = {"POLLING", "ABSENTEE", "EARLY", "PROVISIONAL", "TOTAL",
                "PAPER AT CANVASS", "PAPER AT CANVAS", "PAPER AT POLLS",
                "MAIL-IN", "BY-MAIL", "MAIL IN", "BY MAIL", "EARLY VOTING",
                "ELECTION DAY"}
GEMS_HDR_RE = re.compile(
    r"Statement of Votes Cast|SOVC For |Date:|Time:|Page:\d|"
    r"^\s*\d{4} .*Election\s*$|Summit County, Utah|General Election|"
    r"Primary Election|November \d|June \d|February \d|Jurisdiction Wide|"
    r"^\s*OFFICIAL RESULTS\s*$|^\s*Official Results|COUNTY WIDE|"
    r"^\s*\d+ Municipal General Election|This report contains|"
    r"Paper ballots were counted")


def _gems_header_cells(hdr_lines):
    """Reconstruct column cells from the 1-3 header lines by char position.
    Returns list of (start, end, text) beyond the stats columns."""
    # segments per line: (start, end, text) split on 2+ spaces
    segs = []
    for li, line in enumerate(hdr_lines):
        for m in re.finditer(r"\S(?:.*?\S)?(?=\s{2}|\s*$)", line):
            # split manually: find runs separated by 2+ spaces
            pass
    # simpler: per line, find token runs
    segs = []
    for li, line in enumerate(hdr_lines):
        for m in re.finditer(r"[^\s].*?(?=\s{2,}|$)", line):
            txt = m.group(0).strip()
            if txt:
                segs.append([m.start(), m.start() + len(txt), txt, li])
    # merge segments across lines when their char ranges overlap
    segs.sort(key=lambda s: (s[0], s[3]))
    cells = []
    for s in segs:
        merged = False
        for c in cells:
            if s[0] < c[1] + 1 and s[1] > c[0] - 1:
                c[0] = min(c[0], s[0]); c[1] = max(c[1], s[1])
                c[2] = (c[2] + " " + s[2]) if s[3] > c[3] else (s[2] + " " + c[2])
                c[3] = s[3]
                merged = True
                break
        if not merged:
            cells.append([s[0], s[1], s[2], s[3]])
    cells.sort(key=lambda c: c[0])
    return [(c[0], c[1], c[2]) for c in cells]


def parse_gems_sovc(path):
    """GEMS SOVC parser.

    Per page: char-sliced at 'Reg.' starts (side-by-side tables; a leading
    candidate-only slice is the horizontal continuation of the previous
    contest). Within a slice, the CANDIDATE COUNT comes from the maximum
    number of %-tokens in any data row (every candidate slot prints a pct
    whenever the row has votes; '-' only in zero-vote rows), values parse in
    token order (counts right-align; pcts float), and candidate NAMES are
    header words assigned positionally to the count-column grid — immune to
    single-space header merges. Flat mode (2006: one row per precinct, no
    method sub-rows) is per-row; its trailing 'Total' row is the certified
    jurisdiction total.

    Returns (rows, totals, turnout).
    """
    rows = []
    seen = set()
    totals = {}
    turnout = {}
    precinct = None
    for pno, page in enumerate(pdf_layout_pages(path)):
        lines = page.split("\n")
        hdr_i = None
        for i, l in enumerate(lines):
            if re.search(r"\bReg\.?\s", l) and ("Times" in l or "Cards" in l
                                                or "Total Votes" in l):
                hdr_i = i
                break
        if hdr_i is None:
            continue
        reg_starts = [m.start() for m in re.finditer(r"Reg\.? Voters|Reg\.\s",
                                                     lines[hdr_i])]
        hdr_lines = [lines[hdr_i]]
        for j in (hdr_i + 1, hdr_i + 2):
            if j < len(lines) and lines[j].strip() and \
               not re.match(r"\s*(Jurisdiction|\d)", lines[j]) and \
               not any(lines[j].strip().upper().startswith(mm)
                       for mm in GEMS_METHODS):
                hdr_lines.append(lines[j])
            else:
                break
        cells = _gems_header_cells(hdr_lines)
        first_cell = min(st for st, en, txt in cells)
        label_end = min(first_cell, reg_starts[0] if reg_starts else 10 ** 6) - 1
        slices = []
        if reg_starts and first_cell < reg_starts[0] - 2:
            slices.append((first_cell - 1, reg_starts[0] - 1))
        elif not reg_starts:
            slices.append((first_cell - 1, 10 ** 6))
        for si, s in enumerate(reg_starts):
            end = reg_starts[si + 1] - 1 if si + 1 < len(reg_starts) else 10 ** 6
            slices.append((s, end))

        title_segs = []
        for li, l in enumerate(lines[:hdr_i]):
            if not l.strip() or GEMS_HDR_RE.search(l):
                continue
            for m in re.finditer(r"[^\s].*?(?=\s{2,}|$)", l):
                if m.group(0).strip():
                    title_segs.append((li, m.start(), m.group(0).strip()))

        body = lines[hdr_i + len(hdr_lines):]

        def slice_toks(line, lo, hi):
            out = []
            for m in re.finditer(r"\S+", line):
                mid = (m.start() + m.end()) / 2.0
                if lo <= mid < hi:
                    out.append((m.start(), m.end(), m.group(0)))
            return out

        # ---- table specs per slice
        table_specs = []
        for (lo, hi) in slices:
            title = " ".join(t for li, p, t in sorted(title_segs)
                             if lo <= p < hi).strip()
            hdr_txt = " ".join(txt for st, en, txt in cells
                               if lo <= (st + en) // 2 < hi)
            is_turnout = ("TURN OUT" in title.upper() or
                          "Cards Cast" in hdr_txt or "Turnout" in hdr_txt)
            # scan rows: ncand = max %-token count; count-col ends from tokens
            # immediately preceding a %-token; nstat from full-width rows
            ncand = 0
            countcol_ends = []
            nstat_seen = set()
            for raw in body:
                if not raw.strip() or GEMS_HDR_RE.search(raw):
                    continue
                if not raw[label_end:].strip():
                    continue
                toks = slice_toks(raw, max(lo, label_end), hi)
                toks = [(st, en, t) for st, en, t in toks
                        if re.match(r"^(-|[\d,]+|\d+(\.\d+)?%)$", t)]
                if not toks:
                    continue
                npct = sum(1 for _, _, t in toks if t.endswith("%"))
                if npct > ncand:
                    ncand = npct
                for k in range(1, len(toks)):
                    if toks[k][2].endswith("%") and not toks[k - 1][2].endswith("%"):
                        countcol_ends.append(toks[k - 1][1])
                if npct and not is_turnout:
                    nstat_seen.add(len(toks) - 2 * npct)
            if is_turnout:
                table_specs.append((lo, hi, title, [], True, 0))
                continue
            if ncand == 0:
                table_specs.append((lo, hi, title, [], False, 0))
                continue
            nstat_c = {n for n in nstat_seen if n in (0, 2, 3)}
            if len(nstat_c) != 1:
                raise ValueError(f"{path} p{pno+1}: inconsistent stats columns "
                                 f"{nstat_seen} in {title!r}")
            nstat = nstat_c.pop()
            # cluster count-column ends
            ccols = []
            for en in sorted(countcol_ends):
                if ccols and en - ccols[-1] <= 3:
                    ccols[-1] = max(ccols[-1], en)
                else:
                    ccols.append(en)
            if len(ccols) != ncand:
                raise ValueError(f"{path} p{pno+1}: {len(ccols)} count columns "
                                 f"vs {ncand} pct slots in {title!r}")
            # ---- candidate NAMES, two strategies:
            # (1) segment order: 2+-space segments of the header lines within
            #     the slice, stats segments dropped, single-space merges
            #     pre-split at '(ABC)' party markers and before 'Write-In' —
            #     used when the segment count equals ncand (robust to the
            #     per-page horizontal drift of GEMS headers);
            # (2) positional midpoints between count-column ends (fallback,
            #     needed for mid-name line wraps like 'HUNTER,'/'DUNCAN').
            STATS_SEG = re.compile(
                r"^(Reg\.?( Voters)?|Voters|Times( Counted)?|Counted|"
                r"Total Votes|Cards Cast|%( Turnout)?|Turnout)$")
            segs = []
            for li2, hl in enumerate(hdr_lines):
                for m in re.finditer(r"[^\s].*?(?=\s{2,}|$)", hl):
                    txt = m.group(0).strip()
                    mid = (m.start() + m.start() + len(txt)) / 2.0
                    if txt and lo <= mid < hi:
                        segs.append((li2, m.start(), txt))
            line1 = [t for li2, p, t in segs if li2 == 0 and not STATS_SEG.match(t)]
            extra = [t for li2, p, t in segs if li2 > 0 and not STATS_SEG.match(t)]
            split1 = []
            for t in line1:
                if re.search(r"\([A-Z]{2,4}\)", t):
                    parts = re.split(r"(?<=\))\s+", t)
                else:
                    parts = [t]
                for p2 in parts:
                    p2 = p2.strip()
                    if not p2:
                        continue
                    m2 = re.match(r"^(.*\S)\s+(Write-[Ii]n Votes?)$", p2)
                    if m2:
                        split1.extend([m2.group(1), m2.group(2)])
                    else:
                        split1.append(p2)
            cand_names = None
            if len(split1) == ncand and not extra:
                cand_names = split1
            else:
                # positional fallback
                bounds = [ccols[0] - 26 if nstat else lo]
                for k in range(len(ccols) - 1):
                    bounds.append((ccols[k] + ccols[k + 1]) / 2.0)
                bounds.append(hi)
                names = [[] for _ in range(ncand)]
                STATW = {"REG", "VOTERS", "TIMES", "COUNTED", "TOTAL", "VOTES",
                         "CARDS", "CAST", "%", "TURNOUT"}
                for li2, hl in enumerate(hdr_lines):
                    for m in re.finditer(r"\S+", hl):
                        mid = (m.start() + m.end()) / 2.0
                        if not (lo <= mid < hi):
                            continue
                        for ci in range(ncand):
                            if bounds[ci] <= mid < bounds[ci + 1]:
                                names[ci].append((li2, m.start(), m.group(0)))
                                break
                cand_names = []
                for ci in range(ncand):
                    toks2 = sorted(names[ci])
                    while toks2 and toks2[0][2].upper().rstrip(".") in STATW:
                        toks2 = toks2[1:]
                    nm = " ".join(t for _, _, t in toks2)
                    nm = " ".join(nm.split())
                    if not nm:
                        raise ValueError(f"{path} p{pno+1}: empty candidate "
                                         f"name col {ci} in {title!r}")
                    cand_names.append(nm)
            final = []
            for nm in cand_names:
                if nm in final:
                    n = 2
                    while f"{nm} (column {n})" in final:
                        n += 1
                    nm = f"{nm} (column {n})"
                final.append(nm)
            table_specs.append((lo, hi, title, final, False, nstat))

        # ---- walk rows
        saw_flat = False
        for raw in body:
            ls = raw.strip()
            if not ls or GEMS_HDR_RE.search(raw):
                continue
            label = raw[:label_end].strip()
            has_vals = bool(raw[label_end:].strip())
            if not has_vals:
                if label:
                    precinct = label
                continue
            if not label:
                raise ValueError(f"{path} p{pno+1}: values with no label: {ls!r}")
            is_method = label.upper() in GEMS_METHODS
            if is_method and label != "Total" and precinct is None:
                raise ValueError(f"{path} p{pno+1}: method row before precinct")
            if not is_method:
                saw_flat = True
            for lo, hi, contest, cand_names, is_turnout, nstat in table_specs:
                toks = [(st, en, t) for st, en, t in
                        slice_toks(raw, max(lo, label_end), hi)
                        if re.match(r"^(-|[\d,]+|\d+(\.\d+)?%)$", t)]
                if not toks:
                    continue
                vals = [t for _, _, t in toks]
                if is_turnout:
                    if len(vals) != 3:
                        raise ValueError(f"{path} p{pno+1}: turnout row {ls!r}")
                    tgt = None
                    if is_method and label.upper() == "TOTAL" and precinct != "Total":
                        tgt = precinct
                    elif not is_method and label != "Total":
                        tgt = label
                    if tgt is not None and (vals[0] != "-" or vals[1] != "-"):
                        turnout[tgt] = (
                            to_int(vals[0]) if vals[0] != "-" else None,
                            to_int(vals[1]) if vals[1] != "-" else None)
                    continue
                if not cand_names:
                    continue
                ncand = len(cand_names)
                # token-order walk: nstat leading stats, then per candidate a
                # count (+ pct token when the count is non-dash and pct printed)
                idx = 0
                svals = []
                while len(svals) < nstat and idx < len(vals):
                    if vals[idx].endswith("%"):
                        raise ValueError(f"{path} p{pno+1}: pct in stats slot: {ls!r}")
                    svals.append(vals[idx]); idx += 1
                cvals = []
                while idx < len(vals):
                    c = vals[idx]; idx += 1
                    if c.endswith("%"):
                        raise ValueError(f"{path} p{pno+1}: unexpected pct: {ls!r}")
                    # pct slot: %-form, or '-' (zero-vote rows print '0  -')
                    if idx < len(vals) and (vals[idx].endswith("%") or
                                            vals[idx] == "-"):
                        idx += 1
                    cvals.append(c)
                if len(cvals) != ncand:
                    raise ValueError(
                        f"{path} p{pno+1}: {contest!r} {label!r}: {len(cvals)} "
                        f"candidate values, expected {ncand}: {ls!r}")
                reg = svals[0] if nstat >= 2 else "-"
                counted = svals[1] if nstat == 3 else "-"
                row_precinct = precinct if is_method else label
                row_method = label if is_method else "Total"
                is_total_row = (not is_method and label == "Total") or \
                               (is_method and precinct == "Total") or \
                               (is_method and label == "Total" and saw_flat)
                for ci in range(ncand):
                    cnt = cvals[ci]
                    if cnt == "-":
                        continue
                    v = to_int(cnt)
                    if is_total_row:
                        if (not is_method) or label.upper() == "TOTAL":
                            key = (contest, cand_names[ci])
                            if key in totals and totals[key] != v:
                                raise ValueError(f"{path}: conflicting totals {key}")
                            totals[key] = v
                        continue
                    if is_method and label.upper() == "TOTAL":
                        continue
                    key = (contest, row_precinct, row_method, cand_names[ci])
                    if key in seen:
                        raise ValueError(f"{path} p{pno+1}: duplicate row {key}")
                    seen.add(key)
                    rows.append(dict(
                        contest=contest, precinct=row_precinct,
                        vote_method=row_method,
                        candidate=cand_names[ci], votes=v,
                        registered=(to_int(reg) if reg != "-" else None),
                        times_counted=(to_int(counted) if counted != "-" else None)))
    return rows, totals, turnout


# ---------------------------------------------------------------------------
# GEMS Election Summary Report parser (2006-2014, two-column layout).
# Per column, grammar:
#   CONTEST NAME (may wrap)
#   Total / Number of Precincts n / Precincts Reporting n pct /
#   [Times Counted a/b pct] / Total Votes n /
#   NAME [PARTY] votes pct  ...  / Write-in Votes n pct
# ---------------------------------------------------------------------------

GEMS_SUM_HDR = re.compile(
    r"Election Summary Report|Summary For Jurisdiction|OFFICIAL RESULTS|"
    r"Official Results|COUNTY WIDE|Canvass Report|canvass report|"
    r"Official Canvass|Date:|Time:|Page:|Summit County, Utah|"
    r"^\s*\d{4} .*Election\s*$|General Election|Primary Election|"
    r"November \d|June \d|February \d|Registered Voters .* Cards Cast|"
    r"Num\. Report Precinct")


def _gutter(lines):
    """Find the two-column gutter char position (min occupancy in 45..110)."""
    best, best_occ = None, 10 ** 9
    for g in range(45, 110):
        occ = 0
        for l in lines:
            if len(l) > g + 1 and (l[g] != " " or l[g + 1] != " "):
                occ += 1
        if occ < best_occ:
            best, best_occ = g, occ
    return best if best_occ == 0 else None


def parse_gems_summary(path):
    """Returns list of contests: dict(name, candidates=[(name, votes)],
    total_votes, n_precincts). Candidate rows keep the party token attached
    to the name verbatim ('GRANATO, SAM F. DEM' -> 'GRANATO, SAM F. (DEM)'
    is NOT applied — text kept as printed minus alignment)."""
    contests = []
    for page in pdf_layout_pages(path):
        lines = [l.rstrip() for l in page.split("\n")]
        body = [l for l in lines if l.strip() and not GEMS_SUM_HDR.search(l)]
        g = _gutter([l for l in body])
        columns = []
        if g is None:
            columns = [body]
        else:
            left = [l[:g].rstrip() for l in body]
            right = [l[g:].rstrip() for l in body]
            columns = [[l for l in left if l.strip()],
                       [l for l in right if l.strip()]]
        for col in columns:
            i = 0
            pending = []
            cur = None
            while i < len(col):
                ls = col[i].strip()
                i += 1
                if not ls:
                    continue
                mth = re.match(r"^(.*?)\s\s+Total$", ls)
                if ls == "Total" or mth:
                    # start of a contest block; pending (+ any name prefix on
                    # the same line as the 'Total' header) = contest name
                    if mth and mth.group(1).strip():
                        pending.append(mth.group(1).strip())
                    if pending:
                        cur = dict(name=" ".join(pending).strip(),
                                   candidates=[], total_votes=None,
                                   n_precincts=None)
                        contests.append(cur)
                        pending = []
                    continue
                m = re.match(r"^Number of Precincts\s+(\d+)$", ls)
                if m:
                    if cur:
                        cur["n_precincts"] = to_int(m.group(1))
                    continue
                if re.match(r"^Precincts Reporting", ls) or \
                   re.match(r"^Times Counted", ls):
                    continue
                m = re.match(r"^Total Votes\s+([\d,]+)$", ls)
                if m:
                    if cur:
                        cur["total_votes"] = to_int(m.group(1))
                    continue
                # candidate row: NAME [PARTY] votes [pct]
                m = re.match(r"^(.*?)\s\s+([\d,]+)(\s+\d+(\.\d+)?\s*%)?$", ls)
                if m and cur is not None:
                    nm = " ".join(m.group(1).split())
                    cur["candidates"].append((nm, to_int(m.group(2))))
                    continue
                # otherwise: (part of) the next contest name
                pending.append(ls)
        # page done
    return contests
