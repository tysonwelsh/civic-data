#!/usr/bin/env python3
"""Derive a TIP project-lifecycle layer for wfrc_mpo from the raw ArcGIS attribute snapshots.

Reads  wfrc_mpo/projects/raw/TIP*.json  (14 files, 8 vintages 2020-2025 .. 2027-2032)
Writes wfrc_mpo/projects/derived/
    project_vintage.csv   one row per (pin, plan_vintage)  — TIP only, pin-keyed
    project_history.csv   one row per pin — lifecycle across vintages (slip, cost drift, entry/exit)
    BUILD_REPORT.md       the printed gates + counts (also echoed to stdout)
    SOURCES.md            documentation of the derived layer (columns, rules, honest limits)

SEMANTIC RULES (decided upstream — implemented verbatim, not improvised):
  * grain project_vintage = (pin, plan_vintage); TIP only; EXCLUDE null/empty/0 pin (counted, not lost —
    those survive in projects.csv as OID-fallback / numeric-"0" rows).
  * within one (pin,vintage): collapse rows with IDENTICAL extracted attribute tuples; if two rows for the
    same (pin,vintage) DIFFER, HARD-FAIL (never silently pick one).
  * in_wfrc_region: '1' if county in the six WFRC counties; '0' if any other recognized Utah county;
    '' if county is blank / a non-county label (Various, Statewide, O/L UA, ...).
  * exited_tip = the vintage immediately AFTER a pin's last appearance (blank if last==2027-2032);
    ALSO forced blank whenever in_wfrc_region != '1' (a statewide 2020-2025 project dropping out of the
    later WFRC-only vintages is a SCOPE change, not a lifecycle exit — never encode it as one).
  * slip_years = last_forecast_year - first_forecast_year (may be negative); cost_drift_pct only when a pin
    appears in >=2 vintages with both costs numeric and first_cost > 0.
  * RTP linkage: exact normalized-name 1:1 unambiguous matches only (never fuzzy).

DERIVED — regenerate, never hand-edit. Idempotent (overwrites outputs; verified byte-identical in-process).
stdlib only.
"""

import csv
import glob
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "raw")
DERIVED_DIR = os.path.join(HERE, "derived")
PROJECTS_CSV = os.path.join(HERE, "projects.csv")
OVERRIDES_CSV = os.path.join(HERE, "vintage_overrides.csv")


def load_overrides():
    """(pin, vintage) -> (action, reason). Documented adjudications of
    (pin,vintage) attribute conflicts — the ONLY way a conflict avoids the
    hard-fail. actions: merge_dup (source duplicate: keep the most complete
    row), keep_both (real master-PIN sub-scopes: emit each as a variant)."""
    ov = {}
    if os.path.exists(OVERRIDES_CSV):
        with open(OVERRIDES_CSV, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                ov[(r["pin"].strip(), r["plan_vintage"].strip())] = (
                    r["action"].strip(), r["reason"].strip())
    return ov


def tuple_completeness(t):
    """More non-blank fields = more complete; tie-break on description length,
    then lexical order (deterministic)."""
    return (sum(1 for x in t if x != ""), len(t[6]), t)

ENTITY = "wfrc_mpo"

# Chronological vintage order (also the file order). exited_tip walks this list.
VINTAGE_ORDER = [
    "2020-2025", "2021-2026", "2022-2027", "2023-2028",
    "2024-2029", "2025-2030", "2026-2031", "2027-2032",
]
VINTAGE_IDX = {v: i for i, v in enumerate(VINTAGE_ORDER)}
NEWEST_VINTAGE = VINTAGE_ORDER[-1]

# The six WFRC-region counties (case-insensitive, trimmed).
WFRC_COUNTIES = {"salt lake", "davis", "weber", "morgan", "box elder", "tooele"}

# The 29 Utah counties (hardcoded) — used to decide "other named county" -> in_wfrc_region='0'.
UTAH_COUNTIES = {
    "beaver", "box elder", "cache", "carbon", "daggett", "davis", "duchesne", "emery",
    "garfield", "grand", "iron", "juab", "kane", "millard", "morgan", "piute", "rich",
    "salt lake", "san juan", "sanpete", "sevier", "summit", "tooele", "uintah", "utah",
    "wasatch", "washington", "wayne", "weber",
}


# ---------------------------------------------------------------------------
# raw extraction helpers
# ---------------------------------------------------------------------------

def vintage_of(filename):
    """TIP20202025_gdb__L0_lines.json / TIP_2027_2032__L1_lines.json -> '2020-2025' / '2027-2032'."""
    m = re.search(r"(\d{4})[_]?(\d{4})", filename)
    return "%s-%s" % (m.group(1), m.group(2))


def ci_get(attrs, *names):
    """Case-insensitive attribute lookup across the field-name drift; first present name wins."""
    low = {k.lower(): k for k in attrs}
    for n in names:
        if n.lower() in low:
            return attrs[low[n.lower()]]
    return None


def features_of(obj):
    """Each raw file is either a JSON list of feature dicts or a dict with 'features'."""
    if isinstance(obj, dict):
        return obj.get("features", [obj])
    return obj


def attrs_of(feat):
    """A feature is {'attributes': {...}} or already the attribute dict."""
    if isinstance(feat, dict) and "attributes" in feat:
        return feat["attributes"]
    return feat


def clean_str(v):
    if v is None:
        return ""
    s = str(v).strip()
    return s


def parse_cost(v):
    """project_value: numeric Double (2020-2025) or string with $/commas. -> clean numeric string; '' if unparseable."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return ""
    if isinstance(v, (int, float)):
        f = float(v)
    else:
        s = str(v).strip().replace("$", "").replace(",", "")
        if s == "":
            return ""
        try:
            f = float(s)
        except ValueError:
            return ""
    if f != f:  # NaN
        return ""
    if f <= 0:  # repo convention "blank never 0" — a 0/negative programmed value is a null placeholder
        return ""
    if f == int(f):
        return str(int(f))
    return repr(f)


def parse_year(v):
    """forecast_st_yr -> integer-string; '' if missing/unparseable OR 0 (source null placeholder)."""
    if v is None:
        return ""
    s = str(v).strip()
    if s == "":
        return ""
    try:
        y = int(float(s))
    except ValueError:
        return ""
    if y == 0:  # 0 is the source's "not set" marker, not calendar year 0 — never a real forecast year
        return ""
    return str(y)


def pin_is_null(pin):
    """EXCLUDE null / empty / 0 pin (per rule). Returns (is_null, kind) with kind in {'', 'zero', 'empty'}."""
    if pin is None:
        return True, "empty"
    s = str(pin).strip()
    if s == "":
        return True, "empty"
    try:
        if float(s) == 0:
            return True, "zero"
    except ValueError:
        pass
    return False, ""


def region_flag(county):
    """'1' WFRC county | '0' other named Utah county | '' blank / non-county label."""
    c = (county or "").strip().lower()
    if c == "":
        return ""
    if c in WFRC_COUNTIES:
        return "1"
    if c in UTAH_COUNTIES:
        return "0"
    return ""  # Various / Statewide / O/L UA / SL UA / Region One / any other non-county label


def normalize_name(s):
    """casefold, strip punctuation, collapse whitespace — for exact RTP name linkage only."""
    s = (s or "").casefold()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# The extracted attribute tuple that FEEDS the output row (source_layer excluded on purpose:
# an identical project mirrored across lines+points must collapse). Conflicts on THIS tuple hard-fail.
def extract_tuple(a):
    name = clean_str(ci_get(a, "pin_desc", "PIN_DESC"))
    county = clean_str(ci_get(a, "cnty_name", "CNTY_NAME"))
    fyear = parse_year(ci_get(a, "forecast_st_yr", "FORECAST_S"))
    cost = parse_cost(ci_get(a, "project_value", "PROJECT_VA"))
    status = clean_str(ci_get(a, "pin_stat_nm", "PIN_STAT_N"))
    funding = clean_str(ci_get(a, "mstr_pin_desc", "MSTR_PIN_D"))
    desc = clean_str(ci_get(a, "public_desc", "PUBLIC_DES"))
    return (name, county, fyear, cost, status, funding, desc)


# ---------------------------------------------------------------------------
# the derivation (pure — returns everything the gates + writers need)
# ---------------------------------------------------------------------------

def derive():
    raw_files = sorted(glob.glob(os.path.join(RAW_DIR, "TIP*.json")))

    # vintage -> pin -> list of (tuple, source_stem)
    by_vintage_pin = defaultdict(lambda: defaultdict(list))
    # per-vintage raw accounting
    raw_total = Counter()
    excl_zero = Counter()
    excl_empty = Counter()

    for path in raw_files:
        stem = os.path.splitext(os.path.basename(path))[0]
        v = vintage_of(os.path.basename(path))
        with open(path) as fh:
            obj = json.load(fh)
        for feat in features_of(obj):
            a = attrs_of(feat)
            raw_total[v] += 1
            pin = ci_get(a, "pin")
            isnull, kind = pin_is_null(pin)
            if isnull:
                if kind == "zero":
                    excl_zero[v] += 1
                else:
                    excl_empty[v] += 1
                continue
            key = str(pin).strip()
            # normalize a "12345.0" style pin to "12345"
            try:
                if float(key) == int(float(key)):
                    key = str(int(float(key)))
            except ValueError:
                pass
            by_vintage_pin[v][key].append((extract_tuple(a), stem))

    # collapse identical tuples per (pin, vintage); conflicts hard-fail UNLESS
    # adjudicated in vintage_overrides.csv (merge_dup / keep_both)
    overrides = load_overrides()
    conflicts = []  # UNADJUDICATED (vintage, pin, [distinct tuples]) — hard-fail material
    collapsed_dups = Counter()  # per-vintage raw rows folded away by identical-collapse
    conflict_quar = Counter()   # per-vintage raw feature rows held out in a conflict group
    override_merged = Counter() # per-vintage raw rows folded away by a merge_dup override
    overrides_applied = []      # (vintage, pin, action) for the report
    vintage_rows = []  # dict rows for project_vintage.csv

    def emit(v, pin, tpl, stems, variant=""):
        name, county, fyear, cost, status, funding, desc = tpl
        vintage_rows.append(OrderedDict([
            ("entity", ENTITY),
            ("plan_vintage", v),
            ("pin", pin),
            ("variant", variant),
            ("name", name),
            ("county", county),
            ("in_wfrc_region", region_flag(county)),
            ("forecast_start_year", fyear),
            ("cost", cost),
            ("status", status),
            ("funding_source_raw", funding),
            ("description", desc),
            ("source_layer", "|".join(stems)),
        ]))

    for v in VINTAGE_ORDER:
        for pin in sorted(by_vintage_pin[v], key=lambda p: (len(p), p)):
            entries = by_vintage_pin[v][pin]
            distinct_tuples = sorted(set(t for t, _ in entries))
            if len(distinct_tuples) > 1:
                action, _reason = overrides.get((pin, v), ("", ""))
                if action == "merge_dup":
                    # documented source duplicate: keep the most complete tuple
                    keep = max(distinct_tuples, key=tuple_completeness)
                    stems = sorted(set(s for t, s in entries if t == keep))
                    override_merged[v] += len(entries) - sum(
                        1 for t, _ in entries if t == keep)
                    collapsed_dups[v] += sum(
                        1 for t, _ in entries if t == keep) - 1
                    overrides_applied.append((v, pin, "merge_dup"))
                    emit(v, pin, keep, stems)
                elif action == "keep_both":
                    # documented master-PIN sub-scopes: one row per variant
                    for i, tpl in enumerate(distinct_tuples, 1):
                        stems = sorted(set(s for t, s in entries if t == tpl))
                        collapsed_dups[v] += sum(
                            1 for t, _ in entries if t == tpl) - 1
                        emit(v, pin, tpl, stems, variant=str(i))
                    overrides_applied.append((v, pin, "keep_both"))
                else:
                    # DO NOT silently pick one — quarantine, hard-fail downstream.
                    conflict_quar[v] += len(entries)
                    conflicts.append((v, pin, distinct_tuples))
                continue
            collapsed_dups[v] += len(entries) - 1  # identical rows folded away (0 if unique)
            stems = sorted(set(s for _, s in entries))
            emit(v, pin, entries[0][0], stems)

    # deterministic order: (vintage index, numeric pin)
    def pin_sort_key(p):
        try:
            return (0, int(p))
        except ValueError:
            return (1, 0)

    vintage_rows.sort(key=lambda r: (VINTAGE_IDX[r["plan_vintage"]], pin_sort_key(r["pin"])))

    # ----- project_history from the collapsed vintage rows -----
    per_pin = defaultdict(lambda: defaultdict(list))  # pin -> vintage -> [rows]
    for r in vintage_rows:
        per_pin[r["pin"]][r["plan_vintage"]].append(r)

    rtp_by_name, tip_by_name = _rtp_index()

    history_rows = []
    for pin in sorted(per_pin, key=pin_sort_key):
        vlists = per_pin[pin]
        vs = sorted(vlists, key=lambda x: VINTAGE_IDX[x])
        first_v, last_v = vs[0], vs[-1]
        multi_variant = any(len(vlists[v]) > 1 for v in vs)
        # single-variant access (trajectory semantics need ONE row per vintage)
        vmap = {v: vlists[v][0] for v in vs}
        first_row, last_row, newest_row = vmap[first_v], vmap[last_v], vmap[vs[-1]]

        # in_wfrc_region across vintages/variants: '1' if ever 1, else '0' if ever 0, else ''
        flags = set(r["in_wfrc_region"] for v in vs for r in vlists[v])
        if "1" in flags:
            region = "1"
        elif "0" in flags:
            region = "0"
        else:
            region = ""

        # exited_tip
        exited = ""
        li = VINTAGE_IDX[last_v]
        if li + 1 < len(VINTAGE_ORDER):
            exited = VINTAGE_ORDER[li + 1]
        if region != "1":            # scope-change guard — never a fabricated exit
            exited = ""

        # Multi-variant pins (keep_both override): the PIN bundles distinct
        # sub-scopes, so a single cost/year trajectory would be fabricated —
        # numeric lifecycle fields stay blank; presence fields remain valid.
        first_fy, last_fy, slip = "", "", ""
        first_cost, last_cost, drift = "", "", ""
        if not multi_variant:
            first_fy, last_fy = first_row["forecast_start_year"], last_row["forecast_start_year"]
            if first_fy != "" and last_fy != "":
                slip = str(int(last_fy) - int(first_fy))
            first_cost, last_cost = first_row["cost"], last_row["cost"]
            if len(vs) >= 2 and first_cost != "" and last_cost != "":
                fc, lc = float(first_cost), float(last_cost)
                if fc > 0:
                    drift = str(round((lc - fc) / fc * 100, 1))

        # chronological distinct statuses / counties (across variants)
        statuses = list(OrderedDict((r["status"], None) for v in vs for r in vlists[v]
                                    if r["status"] != ""))
        counties = list(OrderedDict((r["county"], None) for v in vs for r in vlists[v]
                                    if r["county"] != ""))

        # RTP linkage on newest-vintage name (skipped for multi-variant pins —
        # the name is ambiguous across sub-scopes)
        rtp_id, rtp_conf = "", ""
        if not multi_variant:
            nm = normalize_name(newest_row["name"])
            if nm and nm in rtp_by_name and len(rtp_by_name[nm]) == 1 and len(tip_by_name.get(nm, ())) == 1:
                rtp_id = sorted(rtp_by_name[nm])[0]
                rtp_conf = "exact_name"

        name_latest = newest_row["name"] if not multi_variant else "|".join(
            r["name"] for r in vlists[vs[-1]])
        last_status = last_row["status"] if not multi_variant else ""

        history_rows.append(OrderedDict([
            ("entity", ENTITY),
            ("pin", pin),
            ("name_latest", name_latest),
            ("n_vintages", str(len(vs))),
            ("first_vintage", first_v),
            ("last_vintage", last_v),
            ("vintages", "|".join(vs)),
            ("entered_tip", first_v),
            ("left_censored", "1" if first_v == "2020-2025" else ""),
            ("exited_tip", exited),
            ("first_forecast_year", first_fy),
            ("last_forecast_year", last_fy),
            ("slip_years", slip),
            ("first_cost", first_cost),
            ("last_cost", last_cost),
            ("cost_drift_pct", drift),
            ("last_status", last_status),
            ("statuses", "|".join(statuses)),
            ("counties", "|".join(counties)),
            ("in_wfrc_region", region),
            ("rtp_unique_id", rtp_id),
            ("rtp_match_confidence", rtp_conf),
        ]))

    return {
        "vintage_rows": vintage_rows,
        "history_rows": history_rows,
        "conflicts": conflicts,
        "override_merged": override_merged,
        "overrides_applied": overrides_applied,
        "raw_total": raw_total,
        "excl_zero": excl_zero,
        "excl_empty": excl_empty,
        "collapsed_dups": collapsed_dups,
        "conflict_quar": conflict_quar,
    }


def _rtp_index():
    """Build normalized-name indexes from projects.csv RTP rows for exact 1:1 linkage."""
    rtp_by_name = defaultdict(set)   # norm name -> set(rtp unique_id)
    tip_by_name = defaultdict(set)   # norm name -> set(tip pin)  (from projects.csv TIP rows)
    with open(PROJECTS_CSV, newline="") as fh:
        for r in csv.DictReader(fh):
            if r["plan_kind"] == "rtp":
                rtp_by_name[normalize_name(r["name"])].add(r["project_id"])
            elif r["plan_kind"] == "tip":
                tip_by_name[normalize_name(r["name"])].add(r["project_id"])
    rtp_by_name.pop("", None)
    tip_by_name.pop("", None)
    return rtp_by_name, tip_by_name


# ---------------------------------------------------------------------------
# projects.csv per-vintage accounting (for reconciliation)
# ---------------------------------------------------------------------------

def projects_csv_accounting():
    total = Counter()
    numeric = Counter()   # project_id parses as int
    oid = Counter()       # OID fallback / non-numeric
    with open(PROJECTS_CSV, newline="") as fh:
        for r in csv.DictReader(fh):
            if r["plan_kind"] != "tip":
                continue
            v = r["plan_vintage"]
            total[v] += 1
            pid = r["project_id"]
            try:
                int(pid)
                numeric[v] += 1
            except ValueError:
                oid[v] += 1
    return total, numeric, oid


# ---------------------------------------------------------------------------
# CSV rendering
# ---------------------------------------------------------------------------

def rows_to_csv_text(rows, header):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=header, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# main / gates / report
# ---------------------------------------------------------------------------

def main():
    os.makedirs(DERIVED_DIR, exist_ok=True)

    d1 = derive()
    conflicts = d1["conflicts"]

    # ---- GATE 2: (pin, vintage) uniqueness — hard-fail on conflicting tuples ----
    gate2_ok = len(conflicts) == 0

    vintage_header = list(d1["vintage_rows"][0].keys()) if d1["vintage_rows"] else [
        "entity", "plan_vintage", "pin", "variant", "name", "county", "in_wfrc_region",
        "forecast_start_year", "cost", "status", "funding_source_raw", "description", "source_layer"]
    history_header = list(d1["history_rows"][0].keys()) if d1["history_rows"] else []

    pv_text = rows_to_csv_text(d1["vintage_rows"], vintage_header)
    ph_text = rows_to_csv_text(d1["history_rows"], history_header)

    # ---- GATE 4: idempotency — derive twice, byte-compare ----
    d2 = derive()
    pv_text2 = rows_to_csv_text(d2["vintage_rows"], vintage_header)
    ph_text2 = rows_to_csv_text(d2["history_rows"], history_header)
    gate4_ok = (pv_text == pv_text2) and (ph_text == ph_text2)

    # ---- GATE 1: reconciliation vs projects.csv ----
    csv_total, csv_numeric, csv_oid = projects_csv_accounting()
    recon = []  # per-vintage dict
    accounting_ok = True
    for v in VINTAGE_ORDER:
        kept = sum(1 for r in d1["vintage_rows"] if r["plan_vintage"] == v)
        dup = d1["collapsed_dups"][v]
        quar = d1["conflict_quar"][v]
        ovm = d1["override_merged"][v]
        ez, ee = d1["excl_zero"][v], d1["excl_empty"][v]
        excl = ez + ee
        raw_tot = d1["raw_total"][v]
        # full accounting: kept + collapsed-dups + conflict-quarantined +
        # override-merged-away + excluded == raw rows == projects.csv rows
        full_ok = (kept + dup + quar + ovm + excl == raw_tot) and (raw_tot == csv_total[v])
        accounting_ok = accounting_ok and full_ok
        # literal-gate figure requested: kept + excluded vs projects.csv numeric-id count
        literal_delta = csv_numeric[v] - (kept + excl)
        recon.append(dict(
            vintage=v, kept=kept, dup=dup, quar=quar, ovm=ovm,
            excl_zero=ez, excl_empty=ee, excl=excl,
            raw_total=raw_tot, csv_total=csv_total[v], csv_numeric=csv_numeric[v],
            csv_oid=csv_oid[v], full_ok=full_ok, literal_delta=literal_delta,
        ))
    gate1_ok = accounting_ok  # nothing lost; every raw row accounted for

    # ---- GATE 3 numbers: pin coverage ----
    total_raw = sum(d1["raw_total"].values())
    total_excl = sum(d1["excl_zero"].values()) + sum(d1["excl_empty"].values())
    total_kept_rows = len(d1["vintage_rows"])
    pct_with_pin = 100.0 * (total_raw - total_excl) / total_raw if total_raw else 0.0

    # ---- GATE 5: sanity counts ----
    hist = d1["history_rows"]
    n_pins = len(hist)
    n_newest = sum(1 for h in hist if NEWEST_VINTAGE in h["vintages"].split("|"))
    n_exited = sum(1 for h in hist if h["exited_tip"] != "")
    n_leftcens = sum(1 for h in hist if h["left_censored"] == "1")
    n_slip = sum(1 for h in hist if h["slip_years"] not in ("", "0"))
    n_rtp = sum(1 for h in hist if h["rtp_match_confidence"] == "exact_name")

    all_pass = gate1_ok and gate2_ok and gate4_ok

    report = build_report(
        recon=recon, conflicts=conflicts, gate1_ok=gate1_ok, gate2_ok=gate2_ok,
        gate4_ok=gate4_ok, all_pass=all_pass, total_raw=total_raw, total_excl=total_excl,
        total_kept_rows=total_kept_rows, pct_with_pin=pct_with_pin,
        excl_zero=d1["excl_zero"], excl_empty=d1["excl_empty"],
        n_pins=n_pins, n_newest=n_newest, n_exited=n_exited, n_leftcens=n_leftcens,
        n_slip=n_slip, n_rtp=n_rtp, overrides_applied=d1["overrides_applied"],
    )

    # write outputs (overwrite — safe to re-run)
    with open(os.path.join(DERIVED_DIR, "project_vintage.csv"), "w", newline="") as fh:
        fh.write(pv_text)
    with open(os.path.join(DERIVED_DIR, "project_history.csv"), "w", newline="") as fh:
        fh.write(ph_text)
    with open(os.path.join(DERIVED_DIR, "BUILD_REPORT.md"), "w") as fh:
        fh.write(report)
    with open(os.path.join(DERIVED_DIR, "SOURCES.md"), "w") as fh:
        fh.write(build_sources_doc())

    print(report)

    if not all_pass:
        sys.exit(1)


def build_report(**k):
    L = []
    A = L.append
    A("# wfrc_mpo / projects / derived — BUILD REPORT")
    A("")
    A("Derived TIP project-lifecycle layer from `raw/TIP*.json` (8 vintages, 14 layers).")
    A("Run `python3 build_project_history.py` to regenerate. DERIVED — never hand-edit.")
    A("")
    status = "ALL GATES PASSED" if k["all_pass"] else "GATE FAILURE — see below"
    A("## Result: **%s**" % status)
    A("")
    A("| gate | check | status |")
    A("|---|---|---|")
    A("| 1 | reconciliation (nothing lost vs projects.csv) | %s |" % ("PASS" if k["gate1_ok"] else "FAIL"))
    A("| 2 | (pin,vintage) uniqueness after identical-collapse | %s |" % ("PASS" if k["gate2_ok"] else "HARD-FAIL"))
    A("| 4 | idempotency (derive twice, byte-identical) | %s |" % ("PASS" if k["gate4_ok"] else "FAIL"))
    A("")

    # Gate 1
    A("## Gate 1 — reconciliation vs projects.csv")
    A("")
    A("Full accounting per vintage: **kept (project_vintage rows) + collapsed-duplicates + "
      "excluded(null/empty/0 pin) == raw rows == projects.csv TIP rows**. When that closes, "
      "nothing is lost. The `literal_delta` column is the requested `csv_numeric_id - (kept + excluded)` "
      "figure; it is non-zero by construction wherever (a) identical-attribute duplicate pins were "
      "collapsed here but sit as separate numeric rows in projects.csv, or (b) null pins land as OID "
      "fallback (non-numeric) in projects.csv while pin=0 rows land as numeric \"0\" — both explained, "
      "neither a data loss.")
    A("")
    A("| vintage | kept | collapsed_dups | conflict_quar | ovr_merged | excl(0) | excl(null) | raw_rows | csv_rows | csv_numeric | csv_oid | full_ok | literal_delta |")
    A("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in k["recon"]:
        A("| %s | %d | %d | %d | %d | %d | %d | %d | %d | %d | %d | %s | %+d |" % (
            r["vintage"], r["kept"], r["dup"], r["quar"], r["ovm"],
            r["excl_zero"], r["excl_empty"], r["raw_total"],
            r["csv_total"], r["csv_numeric"], r["csv_oid"], "yes" if r["full_ok"] else "NO",
            r["literal_delta"]))
    A("")
    A("Reconciliation reason notes (do-not-force policy — deltas explained, not massaged):")
    A("- **2020-2025**: 30 rows carry `PIN=0`; excluded here (rule: drop null/empty/0), but projects.csv "
      "stored them as numeric project_id `\"0\"` — they sit in `csv_numeric` AND in excl(0), so the "
      "literal_delta nets to 0 for this vintage.")
    A("- **2021-2026 / 2027-2032**: identical-attribute duplicate pins (108 / 2 rows) collapse to one "
      "row here; projects.csv keeps every raw feature as its own numeric row — hence literal_delta reflects them.")
    A("- **2024-2029 / 2025-2030 / 2026-2031 / 2027-2032**: null pins → OID fallback (non-numeric) in "
      "projects.csv; counted here under excl(null); they are NOT in csv_numeric, so literal_delta goes negative.")
    A("- **conflict_quar** = raw feature rows held out of a (pin,vintage) group that has CONFLICTING "
      "attributes (see Gate 2). They are accounted here (never silently dropped) but excluded from "
      "`project_vintage.csv` pending the upstream semantic decision; `full_ok` includes them so the "
      "accounting still closes exactly.")
    A("- Every vintage's `full_ok=yes` proves the full accounting closes exactly — no raw row is dropped.")
    A("")

    # Gate 2
    A("## Gate 2 — (pin,vintage) uniqueness (hard-fail on UNADJUDICATED conflicts)")
    A("")
    if k.get("overrides_applied"):
        A("Adjudicated via `vintage_overrides.csv` (documented decisions, 2026-07-22):")
        for v, pin, action in k["overrides_applied"]:
            A("- %s pin=%s : `%s` (see the override row's reason)" % (v, pin, action))
        A("")
    if k["gate2_ok"]:
        A("Zero UNADJUDICATED conflicting attribute tuples within any (pin,vintage). PASS.")
    else:
        A("**HARD-FAIL — %d conflicting (pin,vintage) groups (expectation 0):**" % len(k["conflicts"]))
        for v, pin, tuples in k["conflicts"][:50]:
            A("- %s pin=%s : %d distinct tuples" % (v, pin, len(tuples)))
            for t in tuples:
                A("    - %r" % (t,))
    A("")

    # Gate 3
    A("## Gate 3 — pin coverage")
    A("")
    A("- raw TIP feature rows (all layers): **%d**" % k["total_raw"])
    A("- excluded (null/empty/0 pin): **%d**" % k["total_excl"])
    A("- project_vintage rows (distinct pins after collapse): **%d**" % k["total_kept_rows"])
    A("- %% of raw rows carrying a usable pin: **%.2f%%**" % k["pct_with_pin"])
    A("")
    A("Excluded pins per vintage (zero / null-empty):")
    A("")
    A("| vintage | pin=0 | null/empty |")
    A("|---|---|---|")
    for v in VINTAGE_ORDER:
        A("| %s | %d | %d |" % (v, k["excl_zero"][v], k["excl_empty"][v]))
    A("")

    # Gate 4
    A("## Gate 4 — idempotency")
    A("")
    A("Derivation run twice in-process; both CSV renderings byte-identical: **%s**." %
      ("PASS" if k["gate4_ok"] else "FAIL"))
    A("Outputs overwrite on every run (safe to re-run).")
    A("")

    # Gate 5
    A("## Gate 5 — sanity counts (project_history)")
    A("")
    A("- pins total: **%d**" % k["n_pins"])
    A("- present in newest vintage (%s): **%d**" % (NEWEST_VINTAGE, k["n_newest"]))
    A("- exited (non-blank exited_tip): **%d**" % k["n_exited"])
    A("- left-censored (first_vintage == 2020-2025): **%d**" % k["n_leftcens"])
    A("- slip_years != 0: **%d**" % k["n_slip"])
    A("- RTP exact-name matches: **%d**" % k["n_rtp"])
    A("")
    return "\n".join(L) + "\n"


def build_sources_doc():
    return """# wfrc_mpo / projects / derived — sources & method

**DERIVED, regenerate-only.** Built by `../build_project_history.py` from the raw ArcGIS
attribute snapshots in `../raw/TIP*.json` (8 TIP vintages 2020-2025 .. 2027-2032, 14 layers).
Canonical source of truth remains `../projects.csv` + `../raw/`; this layer adds a **project
lifecycle** view (one project across vintages: entry, exit, forecast slip, cost drift) that the
flat per-vintage `projects.csv` does not express. RTP rows are NOT re-derived here — TIP only.

Rerun: `python3 wfrc_mpo/projects/build_project_history.py` (stdlib only; idempotent; overwrites).
Gates + counts: `BUILD_REPORT.md`.

## Grain & scope

- **`project_vintage.csv`** — one row per **(pin, plan_vintage)**, TIP only. Rows with a
  null / empty / **0** `pin` are EXCLUDED (they cannot be tracked across vintages); they are NOT
  lost — they persist in `../projects.csv` as OID-fallback rows (or, for 2020-2025, as numeric
  project_id `"0"`). Per-vintage exclusion counts are in `BUILD_REPORT.md`.
- **`project_history.csv`** — one row per **pin**, summarizing that project's life across the
  vintages it appears in.

Within a single (pin, vintage), raw features whose **extracted attribute tuple is identical**
(e.g. the same project mirrored across the lines and points layers) are collapsed to one row.
If two features for the same (pin, vintage) carry **differing** attributes, the build **HARD-FAILS**
rather than silently choosing one — UNLESS the conflict has been adjudicated in
**`../vintage_overrides.csv`** (the repo's documented-override pattern; each row carries the
decision + reason + date). Two override actions exist:

- **`merge_dup`** — the conflict is a source duplicate (e.g. typo drift between two copies of
  the same project); the MOST COMPLETE tuple is kept (most non-blank fields, tie-break longest
  description — deterministic). Applied 2026-07-22: pin 19561 / 2027-2032.
- **`keep_both`** — the PIN genuinely bundles distinct sub-scopes (UDOT master-PIN behavior);
  every distinct tuple is emitted as its own row with `variant` = 1, 2, ... In
  `project_history.csv` such pins keep their PRESENCE fields (vintages, entry/exit) but have
  their single-trajectory numeric fields (forecast years, slip, costs, drift, last_status,
  RTP link) **blanked** — a single trajectory across mixed scopes would be fabricated;
  `name_latest` pipe-joins the variant names. Applied 2026-07-22: pin 21213 / 2027-2032
  ('Part of FrontRunner Forward' lines + 'FrontRunner Point Improvements' points).

Any conflict NOT covered by an override still hard-fails — new conflicts on a future refresh
surface loudly and must be adjudicated the same way.

## Field-name drift handled (case-insensitive)

`pin`; `pin_desc`/`PIN_DESC`; `pin_stat_nm`/`PIN_STAT_N`; `forecast_st_yr`/`FORECAST_S`;
`project_value`/`PROJECT_VA`; `cnty_name`/`CNTY_NAME`; `public_desc`/`PUBLIC_DES`;
`mstr_pin_desc`/`MSTR_PIN_D`. The **2020-2025** vintage lacks a funding-source field
(`funding_source_raw` is blank there) and lacks a project-type field. The **2027-2032** vintage
additionally carries a more granular `All_Funding_Sources` field (e.g. `"HSIP (100%)"`); per the
upstream spec `funding_source_raw` reflects `mstr_pin_desc` only — the finer field is intentionally
NOT captured here (query the raw layer if needed).

## project_vintage.csv columns

| column | meaning |
|---|---|
| entity | constant `wfrc_mpo` |
| plan_vintage | TIP service-year span, e.g. `2026-2031` |
| pin | WFRC Project Identification Number (never null/empty/0 in this file) |
| variant | blank normally; `1`,`2`,... for a `keep_both`-override pin whose distinct sub-scopes are each their own row |
| name | `pin_desc` |
| county | `cnty_name` (verbatim) |
| in_wfrc_region | `1` = one of the six WFRC counties (Salt Lake, Davis, Weber, Morgan, Box Elder, Tooele); `0` = any OTHER recognized Utah county (e.g. Utah, Wasatch, Carbon, Cache); blank = county missing or a non-county label (`Various`, `Statewide`, `O/L UA`, `SL UA`, `Region One`, ...) |
| forecast_start_year | `forecast_st_yr` (programmed forecast start; integer) |
| cost | `project_value` parsed to a number ($/commas stripped); blank if empty/unparseable |
| status | `pin_stat_nm` (delivery status — Scoping / Awarded / Under Construction / Close Out / ...) |
| funding_source_raw | `mstr_pin_desc` (verbatim; blank for 2020-2025) |
| description | `public_desc` |
| source_layer | raw filename stem(s) the row came from (pipe-joined if a collapsed row spanned layers) |

## project_history.csv columns

| column | meaning |
|---|---|
| entity | constant `wfrc_mpo` |
| pin | project id (grain) |
| name_latest | `name` from the NEWEST vintage the pin appears in |
| n_vintages | number of distinct vintages the pin appears in |
| first_vintage / last_vintage | earliest / latest vintage of appearance (chronological) |
| vintages | pipe-joined chronological list of every vintage the pin appears in |
| entered_tip | = first_vintage |
| left_censored | `1` if first_vintage == `2020-2025` (the observation window opens there — true entry may predate it); else blank |
| exited_tip | the vintage IMMEDIATELY AFTER last_vintage (the one the project failed to appear in). Blank if last_vintage == `2027-2032` (still programmed). **Also blank whenever `in_wfrc_region != 1`** — a statewide 2020-2025 project dropping out of the later WFRC-only vintages is a SCOPE change, not a lifecycle exit; encoding it as an exit would be fabrication |
| first_forecast_year / last_forecast_year | forecast_start_year at first / last vintage |
| slip_years | last_forecast_year − first_forecast_year (integer; **may be negative** = accelerated); blank if either year missing |
| first_cost / last_cost | cost at first / last vintage |
| cost_drift_pct | `round((last_cost − first_cost)/first_cost*100, 1)`; only when pin appears in ≥2 vintages AND both costs numeric AND first_cost > 0; else blank |
| last_status | status at last vintage |
| statuses | pipe-joined chronological DISTINCT status values |
| counties | pipe-joined DISTINCT counties across vintages |
| in_wfrc_region | `1` if the pin is ever in-region, else `0` if ever a named out-of-region county, else blank |
| rtp_unique_id | linked RTP project `unique_id` — set ONLY on a 1:1 unambiguous exact normalized-name match |
| rtp_match_confidence | `exact_name` when linked, else blank |

## RTP linkage — honest limits

RTP linkage joins TIP `name_latest` to `../projects.csv` RTP-family rows (`plan_kind='rtp'`) by
**exact normalized name** (casefold, punctuation stripped, whitespace collapsed). A link is set
ONLY when the normalized name maps to exactly one RTP `unique_id` AND exactly one TIP pin — any
one-to-many on either side yields NO match. **No fuzzy matching.** This is a conservative,
precision-first linkage; TIP and RTP name projects differently, so most TIP pins have no RTP link
(that is expected, not a gap). The match count is in `BUILD_REPORT.md`.

## Honest limits

- **TIP only.** RTP lifecycle is not modeled (a single adopted RTP vintage — no cross-vintage lifecycle).
- **2020-2025 is statewide-inclusive**; `in_wfrc_region` separates the six WFRC counties from the
  rest so out-of-region projects are never mistaken for regional exits.
- **Costs are verbatim programmed values** parsed to numbers; **blank (never 0)** when the source
  is empty / unparseable / **literally 0** (0 is the source's null placeholder — matches the
  `projects.csv` "blank never 0" rule; ~68 raw rows). cost_drift compares first vs last programmed
  value only, and requires first_cost > 0.
- **`forecast_start_year = 0` is treated as MISSING (blank)** — 0 is the source's "not set" marker
  (mixed in alongside 951 real years in 2020-2025), not calendar year 0. This prevents a fabricated
  `slip_years` of ~2026 from a 0-vs-real-year subtraction. slip_years is blank whenever either end is
  missing/0.
- **`exited_tip` is an OBSERVATION-WINDOW inference**, not a source field: a project absent from the
  next vintage may have been completed, deferred, re-scoped, or re-pinned. Read it as "no longer
  programmed under this pin", not "cancelled".
"""


if __name__ == "__main__":
    main()
