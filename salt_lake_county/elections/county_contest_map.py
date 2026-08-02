"""county_contest_map.py — classify a Salt Lake County SOVC contest title as a
SALT LAKE COUNTY-level contest (or not), across every naming era 2002-2026.

Shared by normalize_sovc_county.py (which uses it to scope the canonical long
file) and build_county_elections.py (the derived by-contest + races layers), so
the two can never drift.

    classify(contest) -> (office, district, kind)
        office   'Mayor' | 'Council' | 'Sheriff' | 'District Attorney' | 'Clerk' |
                 'Assessor' | 'Recorder' | 'Treasurer' | 'Auditor' | 'Surveyor' |
                 'Ballot Measure'      ('' = not a Salt Lake County contest)
        district 'At-Large A'|'At-Large B'|'At-Large C'|'1'..'9'|''   (Council)
        kind     'office' | 'measure' | ''

THE ERAS (every string below was read off a parsed workbook, 2026-08-01):
  2002  'County Sheriff' · 'SL County Council At-Large #A' · 'SLCO Council DISTRICT #1'
  2004  'Salt Lake County Mayor' · 'Write-In for SL County Mayor' ·
        'Salt Lake County Council At-Large B' · 'Salt Lake County Council District 2'
  2006  'COUNTY SHERIFF' · 'COUNTY CNCL AT-LARGE "C"' · 'COUNTY COUNCIL DIST #1'
  2008  'COUNTY MAYOR' · 'COUNTY COUNCIL #A' (at-large) · 'COUNTY COUNCIL #2' (district)
  2010  BARE office names — 'ASSESSOR' 'AUDITOR' 'CLERK' 'RECORDER' 'SHERIFF'
        'SURVEYOR' 'TREASURER' 'DISTRICT ATTORNEY' — the state offices always
        carry 'STATE' ('STATE AUDITOR'), and bare 'ATTORNEY GENERAL' is the STATE
        office, so the bare-name era is safely separable.
  2012-2016  'COUNTY MAYOR' · 'COUNTY COUNCIL AT LARGE C' · 'COUNTY COUNCIL DIST #4'
  2018-2020  bare offices again + 'COUNTY COUNCIL AT LARGE C' / "AT LARGE 'A'"
  2022-2026  'COUNTY SHERIFF' · 'COUNTY COUNCIL AT-LARGE B' ·
             'COUNTY COUNCIL DISTRICT 5 (REP) (REP)'
  measures   'County Proposition Number 1' · 'COUNTY PROP 1' · 'County Proposal #1' ·
             'SALT LAKE COUNTY PROPOSITION #1' · 'COUNTY PROPOSITION A' ·
             'SALT LAKE COUNTY JAIL BOND'

NEVER county (guarded explicitly, in this order):
  federal/state offices and measures · judicial retention (titled by the judge's
  NAME, with or without a 'JUDGE'/'JUSTICE' prefix) · school boards (Canyons,
  Granite, Jordan, Murray, Salt Lake City, State) · special districts · and every
  MUNICIPAL contest the even-year canvass carries (Cottonwood Heights 2004,
  Millcreek + the five metro townships 2016, city bonds/propositions/referenda).
"""
import re

PARTY_TAIL = re.compile(r"\s*[\(\[]\s*(REP|DEM|R|D|NP|NON|UNA|CON|LIB|IAP|GRN|G|L|P|C|U|S)"
                        r"\s*[\)\]]\s*", re.I)

# --- hard NON-county guards, checked first (order matters) --------------------
NOT_COUNTY = [
    r"\bSTATE\b",                       # STATE AUDITOR / TREASURER / SCHOOL BOARD / HOUSE …
    r"\bU\.?S\.?\b|UNITED STATES|PRESIDENT|GOVERNOR|LT GOVERNOR|ATTORNEY GENERAL",
    r"CONGRESSIONAL|\bSENATE\b|\bSENATOR\b|REPRESENTATIVE|\bHOUSE\b|\bST\.? (REP|SENATE)\b",
    r"STRAIGHT PARTY|CONSTITUTIONAL AMENDMENT|AMENDMENT|INITIATIVE|"
    r"NONBINDING|OPINION QUESTION",
    r"SCHOOL|BOARD OF EDUCATION|\bSSD\b|SERVICE DISTRICT|SERVICE AREA|WATER|"
    r"IMPROVEMENT|SEWER|FIRE|LIBRARY|MOSQUITO|CEMETERY",
    r"\bJUDGE\b|\bJUSTICE\b|JUDICIAL",
    # municipal contests carried by the even-year canvass
    r"COTTONWOOD HEIGHTS|MILLCREEK|KEARNS|MAGNA|COPPERTON|EMIGRATION|WHITE CITY|"
    r"BRIGHTON|DRAPER|BLUFFDALE|HOLLADAY|SANDY|MURRAY|RIVERTON|HERRIMAN|MIDVALE|"
    r"TAYLORSVILLE|WEST VALLEY|WEST JORDAN|SOUTH JORDAN|SOUTH SALT LAKE|ALTA|"
    r"SALT LAKE CITY|\bCITY\b|METRO TOWNSHIP|\bM ?T\b|TOWNSHIP",
]
NOT_COUNTY_RE = [re.compile(p) for p in NOT_COUNTY]

# a judicial-retention contest is titled by the judge's NAME (2010/2016 print no
# 'JUDGE' prefix): PERSON-shaped titles with no office word are never county.
OFFICE_WORDS = re.compile(
    r"COUNCIL|CNCL|MAYOR|SHERIFF|ASSESSOR|RECORDER|TREASURER|AUDITOR|SURVEYOR|"
    r"CLERK|DISTRICT ATTORNEY|PROPOSITION|PROPOSAL|\bPROP\b|BOND|REFERENDUM")

SIMPLE_OFFICES = [
    ("District Attorney", r"DISTRICT ATTORNEY"),
    ("Sheriff",           r"\bSHERIFF\b"),
    ("Assessor",          r"\bASSESSOR\b"),
    ("Recorder",          r"\bRECORDER\b"),
    ("Treasurer",         r"\bTREASURER\b"),
    ("Auditor",           r"\bAUDITOR\b"),
    ("Surveyor",          r"\bSURVEYOR\b"),
    ("Clerk",             r"\bCLERK\b"),
]


def _up(contest):
    s = " ".join(str(contest).upper().split())
    s = PARTY_TAIL.sub(" ", s)
    return " ".join(s.split()).strip()


def classify(contest):
    """(office, district, kind) — ('', '', '') when not a Salt Lake County contest."""
    up = _up(contest)
    if not up:
        return "", "", ""
    if not OFFICE_WORDS.search(up):
        return "", "", ""                     # judicial retention / other, never county
    for rx in NOT_COUNTY_RE:
        if rx.search(up):
            return "", "", ""

    # --- county ballot measures ------------------------------------------------
    if re.search(r"PROPOSITION|PROPOSAL|\bPROP\b|BOND|REFERENDUM", up):
        if re.search(r"COUNTY|\bSLCO\b|\bSL CO\b", up):
            return "Ballot Measure", "", "measure"
        return "", "", ""

    # --- county Mayor ----------------------------------------------------------
    if "MAYOR" in up:
        if re.search(r"COUNTY|\bSLCO\b|\bSL CO\b", up):
            return "Mayor", "", "office"
        return "", "", ""

    # --- county Council --------------------------------------------------------
    if re.search(r"\bCOUNCIL\b|\bCNCL\b", up):
        if not re.search(r"COUNTY|\bSLCO\b|\bSL CO\b", up):
            return "", "", ""
        m = re.search(r"AT[- ]?LARGE\s*[\"'#]?\s*([A-C])\b", up)
        if m:
            return "Council", "At-Large %s" % m.group(1), "office"
        if re.search(r"AT[- ]?LARGE", up):
            return "Council", "At-Large", "office"
        m = re.search(r"#\s*([A-C])\b", up)            # 2008 'COUNTY COUNCIL #A'
        if m:
            return "Council", "At-Large %s" % m.group(1), "office"
        m = re.search(r"DIST(?:RICT)?\.?\s*#?\s*(\d+)", up) or re.search(r"#\s*(\d+)", up)
        if not m:
            m = re.search(r"COUNCIL\s+(\d+)\b", up)     # 2024 'COUNTY COUNCIL 2'
        if m:
            return "Council", m.group(1), "office"
        return "Council", "", "office"

    # --- the eight elected county administrative offices -----------------------
    for office, pat in SIMPLE_OFFICES:
        if re.search(pat, up):
            return office, "", "office"
    return "", "", ""


def is_county(contest):
    return classify(contest)[0] != ""
