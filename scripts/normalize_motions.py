#!/usr/bin/env python3
"""normalize_motions.py — cross-city vote-normalization layer (plan items 2.2 / 2.3 / 2.4).

Reads each city's canonical all_votes.csv files (NEVER modified) and writes, alongside them:

  <city>_city_council/<meeting_minutes|planning_commission>/motions_std.csv
      one row per motion, joinable to all_votes.csv on (source, motion_no)
      (sandy planning_commission additionally needs date — its `source` is a constant
      Legistar-staging string; the date column is emitted for every city anyway)

and the shared crosswalk tables (regenerated verbatim from the tables embedded below):

  crosswalks/motion_type_crosswalk.csv   (city, native_label, motion_type_std, land_use_type)
  crosswalks/body_crosswalk.csv          (city, native_code, canonical_name, description)
  crosswalks/vote_values.csv             (city, value, recorded_meaning, notes)

Deterministic, stdlib-only, idempotent.  Usage (strict argparse — an unknown arg
errors out; a bare invocation does NOT sweep, it requires an explicit city or --all):

  python3 scripts/normalize_motions.py <city> [city ...]   # one or more cities
  python3 scripts/normalize_motions.py --all               # every city + regenerate crosswalks/
  python3 scripts/normalize_motions.py --all --report      # + distribution tables
  python3 scripts/normalize_motions.py --help              # usage, exit 0

Contract (SCHEMA_SPEC.md "Normalization layer"):
  motion_type_std  : Land-Use | Ordinance | Resolution | Budget | Appointment |
                     Contract-Purchase | Grant-Funding | Interlocal | Ceremonial |
                     Procedural-Administrative | Public-Hearing | Legislative-Intent | Other
  land_use_type    : (only when motion_type_std = Land-Use) Rezone | Text-Amendment |
                     General-Plan-Amendment | Subdivision-Plat | Conditional-Use |
                     Site-Plan-Design-Review | Vacation | Annexation | Variance-Exception |
                     Development-Agreement | Other-Land-Use
  action_class     : recommendation | final-action | procedural
  outcome          : pass | fail | died | withdrawn | unknown
  vote_mode        : roll-call | voice | unanimous-declared | tally-only | unknown
  tally_aye/nay/other : integers or blank — parsed from the result string, or counted
                     from named member rows; never inferred.
                     ⚠ tally_other SEMANTICS (audited 2026-07-19, TODO "v_contested_all
                     follow-up (1)" — BY DESIGN, not a completeness gap): tally_* mirror
                     only what the source PRINTED (or, absent a printed tally, what a
                     consistent named roll counts). When a source prints a bare "A:N"
                     tally and notes an abstention/recusal only in prose / a labeled
                     roll / a table mark ("Abstentions: Cm Martinez", "Fitisemanu N/A",
                     an X in an Abstained column), tally_other stays BLANK (NULL) — the
                     VOTE ROW is the authority for abstentions/recusals. A blank is
                     never written as 0, so cities.db v_contested_all's
                     COALESCE(tally_other, named-count) correctly falls back to the
                     named rows; nothing undercounts. Ground-truthed at source across
                     9 cities (alta, draper, millcreek, murray, park_city, slc,
                     st_george, west_jordan, west_valley): no sampled source printed a
                     third tally number that this parser dropped (a printed third
                     number or a "N recused" phrase IS captured — TALLY_RX group 3 /
                     RECUSED_RX).
  classify_method  : rule:<id> | crosswalk | manual
  classify_confidence : high | medium | low

City-native values (motion_type, result, body, vote) are reproduced verbatim in
motion_type_native / result_raw and in the crosswalk tables; nothing canonical is touched.
"""
import argparse
import csv
import os
import re
import sys
from collections import Counter, OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# City list comes from the shared registry (scripts/cities.py).
from cities import SLUGS as CITIES
DATASETS = ['meeting_minutes', 'planning_commission']

# ---------------------------------------------------------------------------
# 2.3a  MOTION-TYPE CROSSWALK
# native motion_type -> (motion_type_std, land_use_type).  ('', '') = the native
# label is genuinely uninformative; the classifier decides from motion text.
# SHARED covers the clone extraction taxonomy used by most cities; CITY_SPECIFIC
# overrides/extends per city.  Coverage of every observed (city, native) pair is
# enforced at run time (unmapped label -> hard error).
# ---------------------------------------------------------------------------
SHARED_MT = {
    'Land-Use/Zoning':            ('Land-Use', ''),
    'Land-Use/Other':             ('Land-Use', 'Other-Land-Use'),  # PC extractor fallback (signs, misc code amendments)
    'Resolution':                 ('Resolution', ''),
    'Procedural/Administrative':  ('Procedural-Administrative', ''),
    'Contract/Purchase':          ('Contract-Purchase', ''),
    'Ordinance':                  ('Ordinance', ''),
    'Appointment':                ('Appointment', ''),
    'Budget Amendment':           ('Budget', ''),
    'Other':                      ('', ''),
    'Interlocal':                 ('Interlocal', ''),
    'Grant-Funding':              ('Grant-Funding', ''),
    'Ceremonial':                 ('Ceremonial', ''),
    'Public Hearing Action':      ('Public-Hearing', ''),
    'Minutes':                    ('Procedural-Administrative', ''),
    '':                           ('', ''),
}
CITY_MT = {
    'alta': {
        # the Alta extractor emits two labels not in SHARED_MT
        'Budget/Finance':                ('Budget', ''),
        'Consent/Minutes':               ('Procedural-Administrative', ''),
    },
    'draper': {
        # Draper's council extractor emits a bare 'Budget' label (SHARED_MT only has
        # 'Budget Amendment'); everything else falls through to SHARED_MT.
        'Budget':                        ('Budget', ''),
    },
    'holladay': {
        # Holladay's extractor uses two labels not in SHARED_MT.
        'Contract/Agreement':            ('Contract-Purchase', ''),
        'Procedural':                    ('Procedural-Administrative', ''),
    },
    'bluffdale': {
        # bare 'Budget' label (SHARED_MT only has 'Budget Amendment')
        'Budget':                        ('Budget', ''),
    },
    'magna': {
        'Budget/Finance':                ('Budget', ''),
    },
    'copperton': {
        'Budget/Fiscal':                 ('Budget', ''),
        'Recommendation':                ('', ''),   # bare PC recommendation label (unclassified)
    },
    'emigration_canyon': {
        'Land-Use/Recommendation':       ('Land-Use', ''),   # PC land-use recommendation to Council
    },
    'slc': {
        # council label variants
        'Ceremonial Resolution':         ('Ceremonial', ''),
        'Appointment/Advice & Consent':  ('Appointment', ''),
        'Grant/Funding':                 ('Grant-Funding', ''),
        'Interlocal/Agreement':          ('Interlocal', ''),
        'Legislative Intent':            ('Legislative-Intent', ''),
        'Contract/Property':             ('Contract-Purchase', ''),
        # planning-commission bespoke taxonomy
        'Planned Development':           ('Land-Use', 'Other-Land-Use'),
        'Conditional Use':               ('Land-Use', 'Conditional-Use'),
        'Zoning Map Amendment':          ('Land-Use', 'Rezone'),
        'Zoning Text Amendment':         ('Land-Use', 'Text-Amendment'),
        'Design Review':                 ('Land-Use', 'Site-Plan-Design-Review'),
        'Consent Agenda':                ('Procedural-Administrative', ''),
        'Master Plan Amendment':         ('Land-Use', 'General-Plan-Amendment'),
        'Street/Alley Closure':          ('Land-Use', 'Vacation'),
        'Subdivision/Plat':              ('Land-Use', 'Subdivision-Plat'),
        'Appointment/Election':          ('Appointment', ''),
        'Special Exception':             ('Land-Use', 'Variance-Exception'),
    },
    'millcreek': {
        # Planning Commission native land-use taxonomy (Council/CRA labels fall through to SHARED_MT)
        'Rezone':                        ('Land-Use', 'Rezone'),
        'Zone Text Amendment':           ('Land-Use', 'Text-Amendment'),
        'General Plan Amendment':        ('Land-Use', 'General-Plan-Amendment'),
        'Subdivision':                   ('Land-Use', 'Subdivision-Plat'),
        'Conditional Use':               ('Land-Use', 'Conditional-Use'),
        'Exception':                     ('Land-Use', 'Variance-Exception'),
        'Street Vacation':               ('Land-Use', 'Vacation'),
        'Planned Unit Development':      ('Land-Use', 'Other-Land-Use'),
        'Other Land-Use':                ('Land-Use', 'Other-Land-Use'),
    },
    'ogden': {
        'Subdivision/Plat':              ('Land-Use', 'Subdivision-Plat'),
        'Rezone':                        ('Land-Use', 'Rezone'),
        'Conditional Use Permit':        ('Land-Use', 'Conditional-Use'),
        'Site Plan':                     ('Land-Use', 'Site-Plan-Design-Review'),
        # combined native bucket: text amendment OR general-plan amendment — rules pick the sub
        'Zoning Text/General Plan Amendment': ('Land-Use', ''),
        'Street/Alley Vacation':         ('Land-Use', 'Vacation'),
        # first emitted by the 2026-07-19 PC 2020-2023 gap recovery (e.g. the
        # 2020-06-03 4753 Glasmann Way annexation items)
        'Annexation':                    ('Land-Use', 'Annexation'),
    },
    'orem': {
        'Plat/Subdivision':              ('Land-Use', 'Subdivision-Plat'),
        'Site Plan':                     ('Land-Use', 'Site-Plan-Design-Review'),
        'Code/Ordinance Amendment':      ('Land-Use', 'Text-Amendment'),
        'Rezone':                        ('Land-Use', 'Rezone'),
        'General Plan':                  ('Land-Use', 'General-Plan-Amendment'),
        'Conditional Use':               ('Land-Use', 'Conditional-Use'),
        'Annexation':                    ('Land-Use', 'Annexation'),
    },
    'provo': {
        'Project Plan':                  ('Land-Use', 'Site-Plan-Design-Review'),
        'Rezone':                        ('Land-Use', 'Rezone'),
        'Ordinance Text Amendment':      ('Land-Use', 'Text-Amendment'),
        'Subdivision/Plat':              ('Land-Use', 'Subdivision-Plat'),
        'General Plan Amendment':        ('Land-Use', 'General-Plan-Amendment'),
        'Conditional Use Permit':        ('Land-Use', 'Conditional-Use'),
        'Annexation':                    ('Land-Use', 'Annexation'),
        'Variance':                      ('Land-Use', 'Variance-Exception'),
        'Vacation':                      ('Land-Use', 'Vacation'),
    },
    'west_valley': {
        'Conditional Use':               ('Land-Use', 'Conditional-Use'),
        'General Plan & Rezone':         ('Land-Use', 'Rezone'),   # combined GPA+rezone app; rezone is the operative action
        'Zone Text Amendment':           ('Land-Use', 'Text-Amendment'),
        'Rezone':                        ('Land-Use', 'Rezone'),
        'Site Plan':                     ('Land-Use', 'Site-Plan-Design-Review'),
        'Subdivision Amendment':         ('Land-Use', 'Subdivision-Plat'),
        'Planned Unit Development':      ('Land-Use', 'Other-Land-Use'),
        'Subdivision':                   ('Land-Use', 'Subdivision-Plat'),
        'General Plan Amendment':        ('Land-Use', 'General-Plan-Amendment'),
        'Street Vacation':               ('Land-Use', 'Vacation'),
        'Code Exception':                ('Land-Use', 'Variance-Exception'),
    },
    'sandy': {
        'Planning Item':                 ('', ''),   # uninformative Legistar blob — classifier decides
        'Informational Report':          ('Procedural-Administrative', ''),
    },
}


# ---------------------------------------------------------------------------
# 2.3a-bis  NON-CITY ENTITY MOTION-TYPE CROSSWALK (2026-07-29, TODO high (j))
# The county / MPO / state tier publishes NO motions_std.csv (there is no uniform
# flat-CSV shape across it, and two entities have no flat motion file at all), so
# its motion_std rows are computed at FEDERATION time by
# scripts/build_cities_db.py — which imports classify()/action_class()/
# parse_result()/vote_mode() from this module so the two tiers can never drift.
# This table is the crosswalk half of that: the native motion_type labels those
# entities emit.  It is consulted by crosswalk_lookup() BEFORE SHARED_MT and is
# NOT written into crosswalks/motion_type_crosswalk.csv (write_crosswalks()
# iterates CITIES only) — the city file layer is untouched by this addition.
#
# READ THE ('', '') ENTRIES AS A FINDING, NOT A GAP: most of this tier's native
# labels are NOT subject types at all —
#   * cache/utah/weber/mag_mpo publish an EMPTY motion_type on 100% of rows;
#   * salt_lake_county's labels are AGENDA-SECTION headings ("Discussion Items",
#     "Tax Letters", "Consent Item", "Letters from Other Offices");
#   * wfrc_mpo's are the motion VERB ("Approval", "Adoption", "Endorsement"),
#     which says what was done, never to what.
# ('', '') means "the native label carries no subject signal" — exactly the
# SHARED_MT convention — so classify() falls through to the text rules and
# honestly returns Other/low when the text carries no signal either.
ENTITY_MT = {
    'salt_lake_county': {
        # agenda-section headings (Legistar `EventItem` groupings) — no subject signal
        'Discussion Items':                  ('', ''),
        'Tax Letters':                       ('', ''),
        'Private Business Disclosures':      ('', ''),
        'Public Hearings and Notices':       ('', ''),
        'Consent Item':                      ('', ''),
        'Letters from Other Offices':        ('', ''),
        'other':                             ('', ''),
        # genuine type labels emitted by the minutes-side extractor
        'resolution':                        ('Resolution', ''),
        'budget':                            ('Budget', ''),
        'election-officers':                 ('Appointment', ''),
        'executive-session':                 ('Procedural-Administrative', ''),
        'minutes-approval':                  ('Procedural-Administrative', ''),
        'adjourn':                           ('Procedural-Administrative', ''),
        'consent-agenda':                    ('Procedural-Administrative', ''),
        'Proclamations, Declarations and Other Ceremonial or Commemorative Matters':
                                             ('Ceremonial', ''),
    },
    'summit_county': {
        'Financial/Contract':                ('Contract-Purchase', ''),
        # property-tax valuation appeals sat as the Board of Equalization — a
        # distinct statutory function, not one of the 13 motion_type_std buckets
        'Board of Equalization':             ('', ''),
    },
    'wfrc_mpo': {
        # the VERB, not the subject -> no signal; the text rules decide
        'Approval':                          ('', ''),
        'Acceptance':                        ('', ''),
        'Adoption':                          ('', ''),
        'Endorsement':                       ('', ''),
        'Certification':                     ('', ''),
        'Authorization':                     ('', ''),
        'Ratification':                      ('', ''),
        'Recommendation':                    ('', ''),
        'Motion':                            ('', ''),
        'Adjournment':                       ('Procedural-Administrative', ''),
        'Public Hearing':                    ('Public-Hearing', ''),
    },
    # NO ut_state ENTRY, DELIBERATELY (2026-07-29 owner ruling): the state tier is
    # NOT normalized through this municipal vocabulary. Its "motions" are BILL-STAGE
    # VOTES ('floor' / 'committee' is a stage, not a subject type) and the
    # motion_type_std enum (Land-Use | Ordinance | Resolution | Budget | Appointment
    # | …) does not describe them. ut_state's motion_std is intentionally EMPTY
    # pending TODO "STATE TIER — reevaluate how `ut_state` is integrated, ON ITS OWN TERMS (owner ruling 2026-07-29)", which will give the state tier first-class tables the way
    # wfrc_mpo got regional_project/project_vintage/project_history. Adding a
    # crosswalk entry here would pre-empt that decision.
}


def crosswalk_lookup(city, native):
    if city in CITY_MT and native in CITY_MT[city]:
        return CITY_MT[city][native]
    if city in ENTITY_MT and native in ENTITY_MT[city]:
        return ENTITY_MT[city][native]
    if native in SHARED_MT:
        return SHARED_MT[native]
    raise SystemExit('UNMAPPED motion_type: city=%r native=%r — extend the crosswalk' % (city, native))


# ---------------------------------------------------------------------------
# 2.3b  UNIFORM CLASSIFIER — one ordered rule set, identical for all 13 cities,
# applied to the motion text (which serves as title for item-blob extractions).
# Each rule: (id, motion_type_std, land_use_type, strength, regex).
# Precedence = list order.  strength 'high' may override the crosswalk's
# TOP-LEVEL category; 'medium' may only fill in a blank / refine a sub-type.
# ---------------------------------------------------------------------------
def _r(pat):
    return re.compile(pat, re.IGNORECASE)


RULES = [
    # --- unambiguous non-land-use first -----------------------------------
    ('legintent',   'Legislative-Intent', '', 'high', _r(r'\blegislative intent\b')),
    # pure hearing motions only — a compound "close the public hearing AND adopt/approve X"
    # is a substantive motion and falls through to the substantive rules below
    # ('continue' must take the hearing itself as object — "continue Z-1-2025 to the
    # May 28 Public Hearing" is a continuance of the land-use item, not a hearing motion)
    ('ph-openclose', 'Public-Hearing', '', 'high',
     _r(r'(\b(open(ed)?|close[ds]?|extend|set|schedule[ds]?|enter|exit|go (in|out) of|'
        r'move (in|out) of|went (in|out) of)\b[^.]{0,40}\bpublic (hearing|input|comment)\b|'
        r'\bcontinue[ds]?\s+(the\s+)?public (hearing|input|comment)\b|'
        r'\bpublic hearing\b[^.]{0,60}\bbe (held|closed|continued)\b|\baccept\w* public comment\b)'
        r'(?![^.]{0,120}\b(adopt|approv|amend(?!ment)|den(y|ie)|reject|authoriz)\w*\b)')),
    ('proc-minutes', 'Procedural-Administrative', '', 'high',
     _r(r'\bminutes\b\s*(of|from|for|as|dated)\b|\b(approve|adopt|accept|ratify)\b[^.]{0,60}\bminutes\b|\bminutes approved\b')),
    ('proc-adjourn', 'Procedural-Administrative', '', 'high', _r(r'\badjourn')),
    ('proc-agenda', 'Procedural-Administrative', '', 'high',
     _r(r'\bconsent (agenda|calendar|items?)\b|\b(approve|amend|adopt|accept|modify|reorder)\b[^.]{0,30}\bagenda\b')),
    ('proc-session', 'Procedural-Administrative', '', 'high',
     _r(r'\bclosed?\b[^.]{0,20}\b(session|meeting)\b|\bexecutive session\b|\brecess\b|\breconvene\b|\bmove into\b[^.]{0,30}\bsession\b')),
    ('proc-excuse', 'Procedural-Administrative', '', 'high',
     _r(r'\bexcuse\b|\bexcusal\b')),
    # --- land-use sub-taxonomy (all high) ----------------------------------
    # rezone before development-agreement: "rezoning X subject to a Development
    # Agreement" is primarily a rezone
    ('lu-rezone', 'Land-Use', 'Rezone', 'high',
     _r(r'\brezon\w+|\bzone change\b|\bzoning map\b|\bzone map\b|\breclassif\w+[^.]{0,60}\bzone|'
        r'\bchang(e[sd]?|ing) (of |in |the )+zon(e|ing)\b|\bzone district (change|amendment)\b|\bPLRZ\d')),
    ('lu-devagr', 'Land-Use', 'Development-Agreement', 'high',
     _r(r'\b(master )?development agreement\b|\bMDA\b|\bannexation agreement\b|'
        r'\bmaster development plan\b')),
    ('lu-annex', 'Land-Use', 'Annexation', 'high', _r(r'\bannex(ation|ing|ed)?\b|\bPLANX\d')),
    ('lu-textamend', 'Land-Use', 'Text-Amendment', 'high',
     _r(r'\b(zoning|zone|code|ordinance|land.?use) text amendment\b|\btext amendment\b|\bZTA\b|'
        r'\bamend\w*\b[^.]{0,50}\b(land use (code|ordinance|regulations)|zoning (code|ordinance|regulations)|development code|land management code)\b|'
        r'\b(development|zoning|land ?use|land management) code amendment\b|'
        r'\bland management code\b|'
        r'\b(enact\w*|establish\w*)[^.]{0,30}\bzoning regulations\b|\bPLOTA\d')),
    ('lu-gpa', 'Land-Use', 'General-Plan-Amendment', 'high',
     _r(r'\bgeneral plan (amendment|designation|map|land.?use)\b|\bamend\w*\b[^.]{0,60}\b(general|master) plan\b|'
        r'\bmaster plan amendment\b|\bfuture land.?use map\b|\bGPA\b|\bPLGPA\d')),
    ('lu-subdiv', 'Land-Use', 'Subdivision-Plat', 'high',
     _r(r'\bsubdivision\b|\bplat\b|\blot (line|split|consolidation|merger)\b|\bcondominium\b')),
    ('lu-cup', 'Land-Use', 'Conditional-Use', 'high',
     _r(r'\bconditional use\b|\bCUP\b|\bhome occupation\b|\bspecial use permit\b')),
    ('lu-variance', 'Land-Use', 'Variance-Exception', 'high',
     _r(r'\bvariance\b|\bspecial exception\b|\bcode exception\b|\bboard of adjustment\b|'
        r'\bsetback (waiver|exception|reduction)\b|\boverlay exception\b|\bstandards? waiver\b')),
    ('lu-accessory', 'Land-Use', 'Other-Land-Use', 'high',
     _r(r'\baccessory (structure|building|dwelling)\b')),
    ('lu-interp', 'Land-Use', 'Other-Land-Use', 'high',
     _r(r'\buse determination\b|\binterpretation of the term\b|\bchange of use\b')),
    ('lu-historic', 'Land-Use', 'Other-Land-Use', 'medium',
     _r(r'\bhistoric (district|resource|register|landmark|preservation)\b|\blocal register\b')),
    ('lu-vacate', 'Land-Use', 'Vacation', 'high',
     _r(r'\bvacat(e|ing|ion)\b[^.]{0,50}\b(street|alley(way)?|right.?of.?way|easement|road|avenue|lane|drive|court)\b|'
        r'\b(street|alley(way)?|easement|right.?of.?way|roadway) (vacation|closure)\b|\bpetition to vacate\b')),
    ('lu-site', 'Land-Use', 'Site-Plan-Design-Review', 'high',
     _r(r'\bsite plan\b|\bdesign review\b|\barchitectural review\b|'
        r'\bconcept\b[^.]{0,25}\b(located|plan|review|approval)\b|\bsign theme\b|\bcomprehensive sign\b|'
        r'\bsign permit\b|\bPLCP\d|\bPLPPA\d')),
    ('lu-pud', 'Land-Use', 'Other-Land-Use', 'high',
     _r(r'\bplanned (unit )?development\b|\bPUD\b')),
    # --- other categories ---------------------------------------------------
    ('interlocal', 'Interlocal', '', 'high', _r(r'\binterlocal\b|\bcooperation agreement\b')),
    ('appoint', 'Appointment', '', 'high',
     _r(r'\b(re)?appoint(ment|ments|ing|ed|s)?\b|\badvice and consent\b|\bratif\w+[^.]{0,30}\bappointment\b')),
    ('officer-elect', 'Appointment', '', 'high',
     _r(r'\b(elect\w*|nominat\w*)\b[^.]{0,50}\b(chair|vice.?chair|mayor pro.?tem)\b|'
        r'\b(approve|appoint\w*|designat\w*)\b[^.]{0,60}\bas\b[^.]{0,40}\b(vice.?chair\w*|chair\w*|mayor pro.?tem)\b')),
    ('budget', 'Budget', '', 'high',
     _r(r'\bbudget\b|\bcertified tax rate\b|\bproperty tax (rate|levy)\b|\btax levy\b')),
    ('grant', 'Grant-Funding', '', 'high',
     _r(r'\bgrant (application|agreement|award|funds?|funding|program|money)\b|'
        r'\b(accept\w*|receive|apply for)\b[^.]{0,40}\bgrant\b|\bCDBG\b|\bARPA\b')),
    # emergency proclamations/declarations are a substantive governance vehicle
    # (a resolution/ordinance extending a local state of emergency), NOT a
    # ceremonial recognition — they must be caught BEFORE the ceremonial rule so
    # its bare \bproclamation\b does not mislabel them (TODO "normalizer refinement
    # lead (alta)"). Placed after the proc-* rules so a genuine consent-agenda/
    # adjourn step referencing an emergency item stays Procedural. Ordinance
    # variant first (millcreek adopts these by ordinance); everything else = the
    # modal Resolution vehicle.  EMERG_PROC = "emergency" & "proclamation" co-occur.
    ('emergency-ord', 'Ordinance', '', 'high',
     _r(r'(?=[\s\S]*\bordinance\b)'
        r'(?=[\s\S]*(?:\bemergency\b[^.]{0,60}\bproclamation\b|\bproclamation\b[^.]{0,60}\bemergency\b))')),
    ('emergency-res', 'Resolution', '', 'high',
     _r(r'\bemergency\b[^.]{0,60}\bproclamation\b|\bproclamation\b[^.]{0,60}\bemergency\b')),
    ('ceremonial', 'Ceremonial', '', 'high',
     _r(r'\bproclamation\b|\bcommendation\b|\bceremonial\b|\bdeclaring\b[^.]{0,40}\b(day|week|month)\b')),
    ('contract', 'Contract-Purchase', '', 'high',
     _r(r'\b(award\w*|approv\w*|authoriz\w*|execut\w*|enter\w* into|accept\w*|amend\w*|ratif\w*|renew\w*)\b[^.]{0,60}\b(contract|purchase|procurement|bid|lease)\b|'
        r'\bchange order\b|\bpurchase (agreement|order|of)\b|\bprofessional services agreement\b|\bsurplus\b|\breal property (purchase|sale|acquisition|disposition)\b')),
    ('contract-weak', 'Contract-Purchase', '', 'medium', _r(r'\bcontract\b|\bagreement\b')),
    # --- weak/backstop signals ----------------------------------------------
    ('proc-report', 'Procedural-Administrative', '', 'medium',
     _r(r'\b(accept|receive)\b[^.]{0,45}\b(report|audit|ACFR|CAFR)\b')),
    ('proc-canvass', 'Procedural-Administrative', '', 'medium',
     _r(r'\bcertif\w+[^.]{0,40}\belection\b|\bcanvass\w*\b')),
    ('proc-schedule', 'Procedural-Administrative', '', 'medium',
     _r(r'\bmeeting schedule\b')),
    ('proc-remand', 'Procedural-Administrative', '', 'medium',
     _r(r'\b(send|refer|remand)\b[^.]{0,40}\bback to\b')),
    ('proc-reconsider', 'Procedural-Administrative', '', 'medium',
     _r(r'\b(motion\s+)?to\s+reconsider\b')),
    ('lu-generic', 'Land-Use', '', 'medium',
     _r(r'\bzoning\b|\bzone\b|\bland.?use\b|\bgeneral plan\b|\bpreliminary plan\b|\bfinal plan\b|\bsketch plan\b|\bconcept plan\b')),
    ('resolution-weak', 'Resolution', '', 'medium', _r(r'\bresolution\b')),
    ('ordinance-weak', 'Ordinance', '', 'medium', _r(r'\bordinance\b')),
    ('ph-weak', 'Public-Hearing', '', 'medium', _r(r'\bpublic hearing\b')),
]


# Genuine ceremonial-recognition signal (proclamation of a day, commendation,
# etc.) — used to guard the "recommend→Ceremonial" extractor trap below.
CEREMONIAL_TEXT_RX = _r(r'\bproclamation\b|\bcommendation\b|\bceremonial\b|'
                        r'\bdeclaring\b[^.]{0,40}\b(day|week|month)\b')
# Recommendation grammar (the operative "recommend"/"forward a recommendation"
# verb) — mirrors TEXT_REC_RX (defined below for action_class) so a motion the
# per-city extractor mislabeled 'Ceremonial' off a "commend"/"recommend"
# substring is recognised as a recommendation, not a ceremony.
REC_GRAMMAR_RX = _r(r'\b(forward|send|give|make)\b[^.]{0,60}\brecommendation\b|'
                    r'\b(motion\s+)?to\s+recommend\b|\bmoved?\s+to\s+recommend\b|'
                    r'^\s*recommend\b')


def apply_rules(text):
    """Return (rule_id, std, sub, strength) of the first matching rule, else None."""
    for rid, std, sub, strength, rx in RULES:
        if rx.search(text):
            return rid, std, sub, strength
    return None


def classify(city, native, text):
    """Combine crosswalk candidate + uniform rules.
    Returns (motion_type_std, land_use_type, classify_method, classify_confidence)."""
    cw_std, cw_sub = crosswalk_lookup(city, native)
    hit = apply_rules(text)

    # GUARD (TODO "recommend→Ceremonial classifier trap"): several per-city
    # extractors emit native motion_type='Ceremonial' for a motion whose text is
    # actually a recommendation, because "recommend"/"recommendation" contains the
    # "commend" substring. That native label maps to Ceremonial via the crosswalk;
    # do not let it stand when the text is a recommendation and carries no genuine
    # ceremonial signal. Reclassify by the substantive rules (accept only a
    # high-confidence type; otherwise an honest Other). The classifier's own
    # ceremonial *rule* is NOT affected — \bcommendation\b never matches
    # "recommendation" (word boundary), verified corpus-wide.
    if cw_std == 'Ceremonial' and REC_GRAMMAR_RX.search(text) \
            and not CEREMONIAL_TEXT_RX.search(text):
        if hit:
            rid, rstd, rsub, strength = hit
            if strength == 'high':
                if rstd == 'Land-Use' and not rsub:
                    rsub = 'Other-Land-Use'
                return rstd, rsub, 'rule:' + rid, 'high'
        return 'Other', '', 'rule:rec-not-ceremonial', 'low'

    if not cw_std:                                   # uninformative native label
        if hit:
            rid, rstd, rsub, strength = hit
            if rstd == 'Land-Use' and not rsub:
                rsub = 'Other-Land-Use'
            return rstd, rsub, 'rule:' + rid, ('high' if strength == 'high' else 'medium')
        return 'Other', '', 'rule:no-signal', 'low'

    if hit:
        rid, rstd, rsub, strength = hit
        if rstd == cw_std:
            # agreement; rules may refine a blank land-use sub-type
            if cw_std == 'Land-Use':
                sub = cw_sub or rsub or 'Other-Land-Use'
                method = 'crosswalk' if cw_sub else ('rule:' + rid if rsub else 'crosswalk')
                return cw_std, sub, method, 'high'
            return cw_std, '', 'crosswalk', 'high'
        if strength == 'high':
            # rules win on top-level only with a high-confidence pattern
            if rstd == 'Land-Use' and not rsub:
                rsub = 'Other-Land-Use'
            return rstd, rsub, 'rule:' + rid, 'high'
        # disagreement on a weak pattern: keep the crosswalk value, medium confidence
        sub = (cw_sub or 'Other-Land-Use') if cw_std == 'Land-Use' else ''
        return cw_std, sub, 'crosswalk', 'medium'

    # crosswalk only, no rule signal
    sub = (cw_sub or 'Other-Land-Use') if cw_std == 'Land-Use' else ''
    conf = 'high' if (cw_std != 'Land-Use' or cw_sub) else 'medium'
    return cw_std, sub, 'crosswalk', conf


# ---------------------------------------------------------------------------
# 2.2  RESULT PARSER — one shared cascade + an exceptions table for true one-offs.
# Returns (outcome, aye, nay, other, mode_hint, parse_rule).  aye/nay/other are
# ints or None; everything comes from the string itself, never inferred.
# ---------------------------------------------------------------------------
TALLY_RX = re.compile(r'\b(\d{1,2})\s*[-:]\s*(\d{1,2})(?:\s*[-:]\s*(\d{1,2})\s*abs)?\b')
RECUSED_RX = re.compile(r'\((\d+) recused?\)', re.I)
FAIL_RX = re.compile(r'\bfail(ed|s)?\b|\bmotion failed\b', re.I)
PASS_RX = re.compile(r'\bpass(ed|es)?\b|\bcarrie[ds]\b|\bcarried\b', re.I)
ACTION_RX = re.compile(r'\bapproved?\b|\badopted\b|\bdenied\b|\bdenial\b|\bcontinued\b|'
                       r'\bpostponed\b|\brecommendation\b|\bremand\b', re.I)
UNANIMOUS_RX = re.compile(r'\bunanimous(ly)?\b|\ball (in favor|voted|voting)\b', re.I)
VOICE_RX = re.compile(r'\bvoice\b', re.I)

# True one-offs the cascade cannot read (exact result string -> mapping).
# outcome/aye/nay/other; None = leave blank.
EXCEPTIONS = {
    # nephi PC: opposition recorded as names inside the result string
    'Pass (Ann Peterson, Cory Thomson opposed)':      ('pass', None, 2, None, 'exc:named-opposed'),
    'Pass (Cory Thomson opposed)':                    ('pass', None, 1, None, 'exc:named-opposed'),
    'Positive recommendation (Alan Hancock opposed)': ('pass', None, 1, None, 'exc:named-opposed'),
    'Positive recommendation (Fran Petersen opposed)': ('pass', None, 1, None, 'exc:named-opposed'),
    # (note: slc '5:5 Approved (Final Action)' is NOT an exception — verified in the
    # minutes as a motion to DENY that tied and so FAILED, leaving the conditional
    # use approved; the generic tally-tie rule reads the motion outcome correctly)
    # ogden: extractor fallback when the narrative gave no parseable outcome
    # word (mostly OCR-spaced "ALL VOTING A YE") — honest unknown
    'Recorded':                                       ('unknown', None, None, None, 'exc:recorded'),
    # sandy: bare "Voice" — a voice vote whose outcome the minutes never state
    'Voice':                                          ('unknown', None, None, None, 'exc:voice-only'),
}


def parse_result(s):
    s = (s or '').strip()
    if s in EXCEPTIONS:
        out, a, n, o, rule = EXCEPTIONS[s]
        mode = 'voice' if VOICE_RX.search(s) else ''
        return out, a, n, o, mode, rule

    m = TALLY_RX.search(s)
    aye = nay = other = None
    if m:
        aye, nay = int(m.group(1)), int(m.group(2))
        if m.group(3):
            other = int(m.group(3))
    rm = RECUSED_RX.search(s)
    if rm:
        other = (other or 0) + int(rm.group(1))

    mode = ''
    if VOICE_RX.search(s):
        mode = 'voice'
    elif UNANIMOUS_RX.search(s) and not m:
        mode = 'unanimous-declared'
    elif m:
        mode = 'tally-only'

    if not s:
        return 'unknown', aye, nay, other, mode, 'empty'
    if re.search(r'no second', s, re.I):
        return 'died', aye, nay, other, mode, 'died-no-second'
    if re.search(r'\bwithdrawn?\b', s, re.I):
        return 'withdrawn', aye, nay, other, mode, 'withdrawn'
    if FAIL_RX.search(s):
        return 'fail', aye, nay, other, mode, 'fail-word'
    if PASS_RX.search(s):
        return 'pass', aye, nay, other, mode, 'pass-word'
    if m:
        if aye > nay:
            return 'pass', aye, nay, other, mode, 'tally-majority'
        if aye < nay:
            return 'fail', aye, nay, other, mode, 'tally-minority'
        if re.search(r'tie.?break', s, re.I):
            return 'pass', aye, nay, other, mode, 'tie-break'
        return 'fail', aye, nay, other, mode, 'tally-tie'
    if ACTION_RX.search(s):
        # disposition happened (approved/denied/continued/recommendation made)
        # with no tally -> the motion carried
        return 'pass', aye, nay, other, mode, 'action-word'
    if UNANIMOUS_RX.search(s):
        return 'pass', aye, nay, other, mode, 'unanimous-word'
    return 'unknown', aye, nay, other, mode, 'unparsed'


# ---------------------------------------------------------------------------
# 2.3c  ACTION_CLASS
# ---------------------------------------------------------------------------
RESULT_REC_RX = re.compile(r'\brecommendation\b', re.I)
RESULT_FINAL_RX = re.compile(r'\(final action', re.I)
RESULT_CONT_RX = re.compile(r'\bcontinued\b|\bpostponed\b|\btabled\b', re.I)
TEXT_REC_RX = re.compile(r'\b(forward|send|give|make)\b[^.]{0,60}\brecommendation\b|'
                         r'\b(motion\s+)?to\s+recommend\b|\bmoved?\s+to\s+recommend\b|'
                         r'^\s*recommend\b', re.I)
TEXT_CONT_RX = re.compile(r'^\s*(motion\s+)?(to\s+)?(tabled?|continued?|postponed?)\b|'
                          r'\b(tabled?|continued?|postponed?)\b[^.]{0,50}\b(item|request|application|appeal|until|to the next|to a (date|later))|'
                          r'\b(moved?|continued?|tabled?|postponed?)\b[^.]{0,50}\bdate (un)?certain\b|'
                          r'\bdefer (action|the|consideration)\b', re.I)
# advisory land-use sub-types: a planning commission acting on these is by Utah
# code advisory to the council (used only when phrasing gives no signal)
PC_ADVISORY_SUBS = {'Rezone', 'Text-Amendment', 'General-Plan-Amendment', 'Annexation'}
SLC_ACTION_CLASS = {'procedural': 'procedural', 'recommendation': 'recommendation',
                    'final_action': 'final-action'}


def action_class(city, dataset, native_ac, result, text, std, sub):
    if native_ac:                       # SLC PC has its own verified taxonomy — map verbatim
        return SLC_ACTION_CLASS[native_ac]
    if RESULT_REC_RX.search(result):
        return 'recommendation'
    if TEXT_CONT_RX.search(text) or RESULT_CONT_RX.search(result):
        return 'procedural'             # tabling/continuance beats a clone "(Final Action)" tag
    if std in ('Procedural-Administrative', 'Public-Hearing'):
        return 'procedural'
    if RESULT_FINAL_RX.search(result):
        return 'final-action'
    if TEXT_REC_RX.search(text):
        return 'recommendation'
    if dataset == 'planning_commission' and std == 'Land-Use' and sub in PC_ADVISORY_SUBS:
        return 'recommendation'         # statutory default when phrasing is silent
    return 'final-action'


# ---------------------------------------------------------------------------
# vote_mode: named member rows beat every string hint
# ---------------------------------------------------------------------------
def vote_mode(names_recorded, mode_hint, has_tally):
    if names_recorded:
        return 'roll-call'
    if mode_hint:
        return mode_hint
    if has_tally:
        return 'tally-only'
    return 'unknown'


# vote values counted as "other" in the member-row tally (recorded non-aye/nay
# VOTES; Absent/Excused are non-votes and are never counted into tallies)
OTHER_VOTE_VALUES = {'Abstain', 'Recuse'}
NAY_VOTE_VALUES = {'Nay', 'Nay (Mayor tie-break)'}
AYE_VOTE_VALUES = {'Aye', 'Aye (Mayor tie-break)'}


# ---------------------------------------------------------------------------
# main per-file processing
# ---------------------------------------------------------------------------
OUT_COLS = ['source', 'motion_no', 'date', 'body', 'motion_type_native', 'motion_type_std',
            'land_use_type', 'action_class', 'outcome', 'tally_aye', 'tally_nay',
            'tally_other', 'vote_mode', 'result_raw', 'classify_method', 'classify_confidence']


def process(city, dataset, stats):
    path = os.path.join(ROOT, city + '_city_council', dataset, 'all_votes.csv')
    if not os.path.exists(path):
        return None
    motions = OrderedDict()             # (source, date, motion_no) -> dict
    with open(path, newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            key = (r['source'], r['date'], r['motion_no'])
            m = motions.get(key)
            if m is None:
                m = motions[key] = {'row': r, 'votes': Counter(), 'names': False}
            if r.get('member'):
                m['names'] = True
                m['votes'][r['vote']] += 1

    out_rows = []
    for (source, date, motion_no), m in motions.items():
        r = m['row']
        result = r['result']
        text = r['motion'] or ''
        outcome, aye, nay, other, mode_hint, prule = parse_result(result)
        # fallback: extractor fallback strings ('Recorded') sometimes sit on a
        # motion whose captured text itself states it died for lack of a second
        if outcome == 'unknown' and re.search(r'motion died|died for lack of a second|'
                                              r'for lack of a second', text, re.I):
            outcome, prule = 'died', prule + '+text-died'

        counted_aye = sum(m['votes'].get(v, 0) for v in AYE_VOTE_VALUES)
        counted_nay = sum(m['votes'].get(v, 0) for v in NAY_VOTE_VALUES)
        counted_other = sum(m['votes'].get(v, 0) for v in OTHER_VOTE_VALUES)

        # tallies: prefer the string's own numbers; else count named member rows.
        # Guard: some cities name only dissenters/absents (provo, sandy 2020,
        # west_jordan PC, occasional logan) — a counted tally inconsistent with
        # the stated outcome would be a partial roster, so leave it blank.
        if aye is None and m['names']:
            consistent = (outcome == 'pass' and counted_aye > counted_nay) or \
                         (outcome == 'fail' and counted_nay >= counted_aye) or \
                         outcome == 'unknown'
            if consistent:
                aye, nay = counted_aye, counted_nay
                other = counted_other if counted_other else None
                prule += '+counted-members'
        # outcome: if the string yields nothing but a full named roll call exists,
        # take the recorded majority (deterministic reading of the roll call)
        if outcome == 'unknown' and m['names'] and (counted_aye or counted_nay):
            outcome = 'pass' if counted_aye > counted_nay else ('fail' if counted_nay > counted_aye else 'unknown')
            if outcome != 'unknown':
                prule += '+members-majority'

        # cross-check parsed tally vs counted member rows
        tm = TALLY_RX.search(result or '')
        if tm and m['names']:
            stats['xcheck_total'][city] += 1
            if int(tm.group(1)) == counted_aye and int(tm.group(2)) == counted_nay:
                stats['xcheck_agree'][city] += 1
            else:
                stats['xcheck_diff'][(city, dataset)].append(
                    (date, motion_no, result, counted_aye, counted_nay))

        std, sub, method, conf = classify(city, r['motion_type'], text)
        ac = action_class(city, dataset, r.get('action_class', ''), result or '', text, std, sub)

        stats['outcome'][(city, dataset)][outcome] += 1
        stats['dist'][city][std] += 1
        stats['parse_rule'][prule] += 1

        out_rows.append({
            'source': source, 'motion_no': motion_no, 'date': date, 'body': r['body'],
            'motion_type_native': r['motion_type'], 'motion_type_std': std,
            'land_use_type': sub, 'action_class': ac, 'outcome': outcome,
            'tally_aye': '' if aye is None else aye,
            'tally_nay': '' if nay is None else nay,
            'tally_other': '' if other is None else other,
            'vote_mode': vote_mode(m['names'], mode_hint, aye is not None),
            'result_raw': result, 'classify_method': method, 'classify_confidence': conf,
        })

    out_path = os.path.join(ROOT, city + '_city_council', dataset, 'motions_std.csv')
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLS)
        w.writeheader()
        w.writerows(out_rows)
    return len(out_rows)


# ---------------------------------------------------------------------------
# 2.4  BODY + VOTE-VALUE CROSSWALKS (embedded authoritative tables)
# ---------------------------------------------------------------------------
BODY_CROSSWALK = [
    # (city, native_code, canonical_name, description)
    ('*', 'Council', 'City Council', 'the elected legislative body'),
    ('*', 'PlanningCommission', 'Planning Commission', 'appointed land-use body; recommends on legislative items, decides administrative ones'),
    ('*', 'RDA', 'Redevelopment Agency', 'council sitting as the redevelopment agency board (in-meeting recess in most cities; separate meetings in ogden/west_valley/west_jordan)'),
    ('slc', 'CRA', 'Community Reinvestment Agency', 'council sitting as the CRA board (Utah 17C reinvestment agency)'),
    ('nephi', 'CRA', 'Community Reinvestment Agency', 'council/agency sitting as the Nephi City Community Reinvestment Agency (Utah 17C); modeled as a body= value inside meeting_minutes (slc/holladay/millcreek pattern), not a separate dataset. PMN body 5737 harvested in full 2026-07-19 (10 notices 2016-2023, pmn_backfill/cra.json): within the 2020 floor it recovers nothing new — the one audited motion (2021-07-27 interlocal, AgendaCenter minutes) already carries body=CRA in meeting_minutes/all_votes.csv, and the 2023-12-19 CRA meeting is agenda-only (minutes 404 on every channel -> meeting_minutes/minutes_unrecovered.csv). Pre-floor CRA history (2016-2019) enumerated but not promoted; its only live attachment is a 2019 schedule doc.'),
    ('magna', 'CRA', 'Community Reinvestment Agency', 'council sitting as the Magna Community Reinvestment Agency board (Utah 17C; "Board Member" roles) — audited in-recess/one-off CRA docs PLUS standalone CRA meeting minutes (PMN body 6925) recovered and promoted 2026-07-16 (provenance=pmn_minutes); 32 motions tagged in meeting_minutes/all_votes.csv'),
    ('millcreek', 'CRA', 'Community Reinvestment Agency', 'council sitting as the Millcreek Community Reinvestment Agency board (Utah 17C; project-area plans/budgets, participation agreements, inter-fund loans); 246 motions tagged in meeting_minutes/all_votes.csv'),
    ('kearns', 'CRA', 'Community Reinvestment Agency', 'council sitting as the Kearns Community Reinvestment Agency board (Utah 17C, established 2025; "Board Member" roles, Chair Bush votes) — standalone CRA minutes docs on PMN body 9273, recovered via pmn_backfill and promoted 2026-07-16 (provenance=pmn_minutes); 9 motions tagged body=CRA in meeting_minutes/all_votes.csv'),
    ('alta', 'BudgetCommittee', 'Budget Committee', 'SEPARATE body whose meetings are minuted in the SAME council-minutes PDF (opened by "CALL THE BUDGET COMMITTEE MEETING TO ORDER"): the Mayor + 2 councilmembers + the staff TREASURER — NOT the Town Council (the other 2 councilmembers do not sit or vote on it). 7 motions tagged in meeting_minutes/all_votes.csv (2022-04-13 .. 2023-06-07); before the 2026-07-29 body walk these were recorded as Council votes, which put Treasurer Craig Heimark (staff until certified to the Council for the 2026 term) in the 2022 council roll.'),
    ('slc', 'LBA', 'Local Building Authority', 'council sitting as the LBA board (facility financing)'),
    ('holladay', 'LBA', 'Local Building Authority', 'council recesses & reconvenes as the Local Building Authority (facility financing); 12 vote rows tagged in meeting_minutes/all_votes.csv (RDA, 60 rows, is covered by the * wildcard)'),
    ('bluffdale', 'LBA', 'Local Building Authority', 'council recesses in-session as the Local Building Authority (the mayor votes as Chair here, max 6); 84 vote rows tagged in meeting_minutes/all_votes.csv (RDA, 300 rows, via the * wildcard)'),
    ('lehi', 'MBA', 'Local Building Authority', 'lehi\'s building authority meets separately; repo coded it MBA — lehi docs name it the Local Building Authority'),
    ('ogden', 'MBA', 'Municipal Building Authority', 'separate MBA meetings (facility financing); 2022 sets never acquired (documented)'),
    ('orem', 'MBA', 'Municipal Building Authority', 'in-meeting recess segments'),
    ('west_jordan', 'MBA', 'Municipal Building Authority', 'separate MBA meetings'),
    ('west_valley', 'MBA', 'Municipal Building Authority', 'separately-meeting finance/lease body'),
    ('south_jordan', 'MBA', 'Municipal Building Authority', 'MBA board convenes inside council meetings (in-meeting recess); 1 vote row tagged in meeting_minutes/all_votes.csv'),
    ('midvale', 'MBA', 'Municipal Building Authority', 'standalone board meeting docs ("Board Member"/"Chair" roles; the tie-break-only Mayor presides as Chair, non-voting); 1 PMN-recovered doc promoted 2026-07-16 (provenance=pmn_minutes; 5 motions, 2024-05-07 FY2025 MBA budget) in meeting_minutes/all_votes.csv'),
    ('midvale', 'RDA', 'Redevelopment Agency', 'council sitting as the RDA board — audited in-session captures inside council minutes docs PLUS standalone RDA board docs ("Board Member"/"Chair" roles) PMN-recovered and promoted 2026-07-16 (provenance=pmn_minutes); 84 motions tagged in meeting_minutes/all_votes.csv'),
    ('park_city', 'HA', 'Housing Authority', 'council sitting as the housing authority board (in-meeting recess)'),
    ('orem', 'SSLD', 'Special Service Lighting District', 'council sitting as the street-lighting district board'),
    ('st_george', 'ArtsCommission', 'St. George Arts Commission', 'SEPARATE body with different members (not councilmembers) — minutes published in the same stream'),
    ('st_george', 'Canvass', 'Board of Canvassers', 'the council convened to certify an election (same people as Council)'),
    # sandy db bodies (Legistar body table in db/sandy.db; only 138/140 produce vote rows)
    ('sandy', 'City Council', 'City Council', 'Legistar body 138; = body "Council" in all_votes.csv'),
    ('sandy', 'Planning Commission', 'Planning Commission', 'Legistar body 140; = body "PlanningCommission" in all_votes.csv'),
    ('sandy', 'Board of Adjustment', 'Board of Adjustment', 'Legistar body 139 (no vote rows in the standard CSVs)'),
    ('sandy', 'Community Development', 'Community Development', 'Legistar body 173 (department; no vote rows)'),
    ('sandy', 'CDBG Committee', 'CDBG Committee', 'Legistar body 186 (no vote rows)'),
    ('sandy', 'Historic Preservation Committee', 'Historic Preservation Committee', 'Legistar body 187 (no vote rows)'),
    ('sandy', 'Public Utilities Advisory Board', 'Public Utilities Advisory Board', 'Legistar body 192 (no vote rows)'),
    ('sandy', 'Arts Guild', 'Arts Guild', 'Legistar body 194 (no vote rows)'),
    ('sandy', 'Civic Center Architectural Review Committee', 'Civic Center Architectural Review Committee', 'Legistar body 195 (no vote rows)'),
    ('sandy', 'Community Development Director', 'Community Development Director', 'Legistar body 197 (no vote rows)'),
    ('sandy', 'RDA', 'Redevelopment Agency', 'RDA board convenes inside council meetings; 1 vote row tagged'),
    ('taylorsville', 'RDA', 'Redevelopment Agency', 'council sitting as the Taylorsville Redevelopment Agency board (in-meeting recess); 8 motions tagged body=RDA in meeting_minutes/all_votes.csv'),
    # explicit rows for the 3 cities previously covered only by the '*' RDA wildcard
    # (REFACTOR_PLAN 4.6) — documents each city's actual convening mode
    ('logan', 'RDA', 'Redevelopment Agency', 'same-night in-council recess with its own roll calls; split into separate redevelopment-agency-meeting files (31 meetings)'),
    ('provo', 'RDA', 'Redevelopment Agency', 'council sitting as the RDA board via in-meeting convene/reconvene segments (39 meetings tagged by the body column)'),
    ('vineyard', 'RDA', 'Redevelopment Agency', 'council sitting as the RDA board (in-meeting segments, often inside joint work-session documents; 9 meetings)'),
    ('herriman', 'CDRA', 'Community Development and Renewal Agency', 'council sitting as the Community Development and Renewal Agency of Herriman City board (Utah 17C reinvestment agency; the mayor sits as CDRA Chair) — separate CDA/CDRA minutes docs + PMN-recovered standalone minutes (provenance=pmn_minutes, promoted 2026-07-16); 64 motions tagged in meeting_minutes/all_votes.csv'),
    ('cottonwood_heights', 'CDRA', 'Community Development and Renewal Agency', 'council sitting as the Cottonwood Heights Community Development and Renewal Agency board (Utah 17C reinvestment agency) via in-meeting recess segments; 128 vote rows tagged in meeting_minutes/all_votes.csv'),
    ('herriman', 'HCSEA', 'Herriman City Safety Enforcement Area', 'special safety-enforcement service area board (Board Member/Trustee/Director roles); standalone minutes docs incl. PMN-recovered (provenance=pmn_minutes, promoted 2026-07-16); 39 motions tagged in meeting_minutes/all_votes.csv'),
    ('herriman', 'HCFSA', 'Herriman City Fire Service Area', 'fire-service special-service area board (Board Member/Trustee/Director roles); standalone minutes docs incl. PMN-recovered (provenance=pmn_minutes, promoted 2026-07-16); 31 motions tagged in meeting_minutes/all_votes.csv'),
]

VOTE_VALUES = [
    # (city, value, recorded_meaning, notes)
    ('*', 'Aye', 'vote in favor', ''),
    ('*', 'Nay', 'vote against', ''),
    ('lehi', 'Absent', 'not present at the vote', ''),
    ('lehi', 'Abstain', 'present, declined to vote', 'rare (6 rows)'),
    ('lehi', 'Recuse', 'recused for conflict', '1 row'),
    ('logan', 'Absent', 'not present at the vote', ''),
    ('logan', 'Abstain', 'present, declined to vote', ''),
    ('logan', '', '(no member rows)', 'many logan council votes are narrative "Carried unanimously (no names)" — no member rows exist'),
    ('millcreek', 'Absent', 'not present at the vote', 'Council (7 rows); mayor VOTES here so full council tally tops out at 5 (4 districts + mayor)'),
    ('millcreek', 'Abstain', 'present, declined to vote', 'Council + Planning Commission'),
    ('millcreek', 'Recuse', 'recused for conflict', '4 rows (Planning Commission)'),
    ('nephi', 'Absent', 'not present at the vote', ''),
    ('nephi', 'Abstain', 'present, declined to vote', ''),
    ('nephi', 'Recuse', 'recused for conflict', ''),
    ('nephi', '', '(no member rows)', 'nephi minutes are mostly tally-only; named rows exist for only ~260 votes'),
    ('ogden', 'Absent', 'not present at the vote', ''),
    ('ogden', 'Abstain', 'present, declined to vote', ''),
    ('ogden', 'Recuse', 'recused for conflict', ''),
    ('orem', '', 'Aye/Nay only ceiling', 'orem minutes record only Aye/Nay (+8 Abstain rows); absences appear as missing names, never as Absent rows'),
    ('orem', 'Abstain', 'present, declined to vote', '8 rows'),
    ('park_city', 'Absent', 'not present at the vote', ''),
    ('park_city', 'Abstain', 'present, declined to vote', ''),
    ('park_city', 'Recuse', 'recused for conflict', ''),
    ('park_city', 'Nay (Mayor tie-break)', 'mayor cast tie-breaking Nay', '2 rows; in db/parkcity.db these carry vote.note="Mayor tie-break" on vote_value=Nay'),
    ('provo', 'Absent', 'not present at the vote', ''),
    ('provo', 'Abstain', 'present, declined to vote', ''),
    ('sandy', 'Absent', 'not present at the vote', ''),
    ('sandy', 'Abstain', 'present, declined to vote', ''),
    ('sandy', 'Recuse', 'recused for conflict', ''),
    ('sandy', 'Excused', 'absence excused in the minutes', 'sandy-only value (Legistar); treat as Absent for comparisons'),
    ('sandy', 'Nonvoting', 'nonvoting seat', 'db-only value (Legistar EventItemVote); never appears in all_votes.csv'),
    ('slc', 'Absent', 'not present at the vote', ''),
    ('slc', 'Abstain', 'present, declined to vote', ''),
    ('slc', 'Recuse', 'recused for conflict', ''),
    ('south_jordan', 'Absent', 'not present at the vote', ''),
    ('south_jordan', 'Abstain', 'present, declined to vote', '5 rows (Planning Commission)'),
    ('st_george', 'Absent', 'not present at the vote', ''),
    ('st_george', 'Abstain', 'present, declined to vote', ''),
    ('st_george', 'Recuse', 'recused for conflict', ''),
    ('vineyard', 'Absent', 'not present at the vote', ''),
    ('vineyard', 'Recuse', 'recused for conflict', 'vineyard records no Abstain'),
    ('west_jordan', 'Absent', 'not present at the vote', ''),
    ('west_jordan', 'Abstain', 'present, declined to vote', ''),
    ('west_jordan', 'Recuse', 'recused for conflict', ''),
    ('west_valley', 'Absent', 'not present at the vote', ''),
    ('west_valley', 'Abstain', 'present, declined to vote', ''),
    ('west_valley', 'Recuse', 'recused for conflict', ''),
    ('taylorsville', 'Absent', 'not present at the vote', 'Council + Planning Commission; mayor does NOT vote so a full council roll call tops out at 5 (5 councilmembers, presiding Chair one of them)'),
    ('taylorsville', 'Abstain', 'present, declined to vote', '35 rows (Planning Commission)'),
    ('taylorsville', 'Recuse', 'recused for conflict', '3 rows (Planning Commission)'),
    ('murray', 'Absent', 'not present at the vote', 'Council + Planning Commission; mayor does NOT vote (executive) so a full council roll call tops out at 5 (5 districts D1-D5, no at-large)'),
    ('murray', 'Abstain', 'present, declined to vote', 'Council + Planning Commission'),
    ('murray', 'Excused', 'absence excused in the minutes', 'Murray records Excused distinctly from Absent (39 council rows); treat as Absent for comparisons'),
    ('herriman', 'Absent', 'not present at the vote', 'Council + Planning Commission + CDRA/HCSEA/HCFSA; the MAYOR VOTES here (Millcreek model, NOT non-voting) so a full council roll tops out at 5 (4 districts D1-D4 + mayor)'),
    ('herriman', 'Excused', 'absence excused in the minutes', '14 rows (Planning Commission)'),
    ('herriman', 'Abstain', 'present, declined to vote', 'Planning Commission (surfaced in the recovered named rolls)'),
    ('herriman', 'Recuse', 'recused for conflict', '1 row (Planning Commission 2023-01-04 m4: Commissioner Fenn conflict-of-interest recusal, PMN-recovered minutes promoted 2026-07-16)'),
    ('draper', 'Absent', 'not present at the vote', 'Council + Planning Commission; 5 AT-LARGE council seats + separately-elected Mayor who is NON-voting except a rare tie-break (1 row, Mayor Troy K. Walker 2024-10-15, recorded as a plain Aye) - max ordinary council roll = 5'),
    ('draper', 'Abstain', 'present, declined to vote', '76 rows (Planning Commission)'),
    ('draper', 'Recuse', 'recused for conflict', 'Council (1) + Planning Commission (167; the PC grid column "Not Participating" maps to Recuse)'),
    ('riverton', 'Absent', 'not present at the vote', 'Council; 5 districts + separately-elected NON-voting Mayor (Park City model) so max ordinary council roll = 5'),
    ('riverton', 'Recuse', 'recused for conflict', 'Council (9) + Planning Commission'),
    ('riverton', 'Abstain', 'present, declined to vote', 'Council (1) + Planning Commission (9)'),
    ('riverton', 'Aye (Mayor tie-break)', 'mayor cast tie-breaking Aye', '1 row (2025-12-16, Mayor Staggs broke a 2-2 tie); documented tie-break extension like park_city\'s Nay variant'),
    ('alta', 'Abstain', 'present, declined to vote', '1 row (Council). Town form: the MAYOR VOTES (max council tally = 5: 4 at-large councilmembers + voting Mayor Bourke)'),
    ('midvale', 'Absent', 'not present at the vote', 'Council + RDA + Planning Commission; 5 districts + a six-member-form Mayor who votes ONLY on ties (max ordinary council roll = 5). Council also convenes in-session as the RDA (body=RDA).'),
    ('midvale', 'Recuse', 'recused for conflict', 'Council (1 row)'),
    ('midvale', 'Abstain', 'present, declined to vote', 'Planning Commission (1 row)'),
    ('cottonwood_heights', 'Absent', 'not present at the vote', 'Council + CDRA + Planning Commission; the MAYOR VOTES (max council roll = 5: 4 districts + a separately-elected voting Mayor). Council convenes in-session as the CDRA (body=CDRA).'),
    ('cottonwood_heights', 'Abstain', 'present, declined to vote', 'Council (16) + Planning Commission (10)'),
    ('holladay', 'Recuse', 'recused for conflict', 'Council (1) + Planning Commission (2). The MAYOR VOTES here (Council-Manager form) so a full council roll = 6 (5 districts + mayor); printed "Yes/No" tokens are normalized to Aye/Nay per SCHEMA_SPEC §4.'),
    ('holladay', 'Abstain', 'present, declined to vote', 'Planning Commission (2 rows)'),
    ('south_salt_lake', 'Absent', 'not present at the vote', 'Council (7 members: 5 districts + 2 at-large) + RDA + Planning Commission; the executive Mayor does NOT vote (max council roll = 7). Council also convenes as a separate RDA (body=RDA).'),
    ('south_salt_lake', 'Abstain', 'present, declined to vote', 'Planning Commission (6 rows)'),
    ('bluffdale', 'Absent', 'not present at the vote', 'Council + RDA + LBA + Planning Commission; 5 AT-LARGE council seats + a Mayor who is NON-voting in Council (max member tally = 5) except 2 tie-breaks, but VOTES as Chair in the in-session RDA/LBA (max 6).'),
    ('bluffdale', 'Abstain', 'present, declined to vote', 'Council (5) + Planning Commission (10)'),
    ('white_city', 'Abstain', 'present, declined to vote', 'Council (12 rows) + Planning Commission (1 row - Millen 2021-05-25). Metro township (2017-2024) -> CITY 2024; the presiding Chair/Mayor VOTES in both eras (max tally 5). PC minutes recovered from PMN body 5879 (provenance=pmn_minutes, promoted 2026-07-16); the MSD narrative-tally form names only mover/seconder/abstainers, so unanimous PC rolls are tally-only placeholders.'),
    ('kearns', 'Abstain', 'present, declined to vote', 'Council (1) + Planning Commission (4). Metro township (2017-2024) -> CITY 2024; city-era Mayor VOTES (max 5). Votes are narrative-tally (unanimous rolls are unnamed tally-only placeholders; only abstainers named). Township-era council 2017-2023 published no written minutes (audio-only; logged in minutes_unrecovered.csv) - text minutes begin 2024.'),
    ('magna', 'Absent', 'not present at the vote', 'Council + CRA + Planning Commission; 5 districts. Metro township (2017-2024) -> CITY 2024: the township-era elected Chair (titled "Mayor") VOTES, but the 2026+ directly-elected executive Mayor (Sudbury) does NOT vote (max council roll = 5 both eras). Council also convenes as the CRA (body=CRA) — in-recess captures plus standalone CRA meeting docs (PMN body 6925) promoted 2026-07-16.'),
    ('magna', 'Abstain', 'present, declined to vote', 'Council (6) + Planning Commission (6)'),
    ('copperton', 'Abstain', 'present, declined to vote', 'Council (7) + Planning Commission (3). Metro township (2017-2024) -> TOWN 2024; the Mayor/Chair VOTES in both eras (max tally 5). Narrative-tally votes (unanimous rolls unnamed/tally-only); 2017-mid2018 council minutes purged from PMN (404, logged).'),
    ('emigration_canyon', 'Abstain', 'present, declined to vote', 'Council (2) + Planning Commission (2). Metro township (2017-2024) -> CITY 2024; the peer-selected Mayor (Smolka township -> Brems city) PRESIDES AND VOTES (Millcreek pattern, max tally 5). Narrative-tally votes. 2017 PMN file store purged (404); coverage begins 2018-10.'),
    ('emigration_canyon', 'Recuse', 'recused for conflict', 'Council (1): 2021-04-27 m3, Mayor David Brems recused (conflict of interest) on the $12,000 Fuel Mitigation Program funding motion (4-1 tally). The peer-selected Mayor PRESIDES AND VOTES (Millcreek pattern); a recusal removes him from the roll. See the emigration_canyon,Abstain row for entity context.'),
]


def write_crosswalks(observed_mt):
    cw_dir = os.path.join(ROOT, 'crosswalks')
    os.makedirs(cw_dir, exist_ok=True)
    # motion_type crosswalk: expand to every observed (city, native) pair
    with open(os.path.join(cw_dir, 'motion_type_crosswalk.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['city', 'native_label', 'motion_type_std', 'land_use_type'])
        for city in CITIES:
            for native in sorted(observed_mt.get(city, [])):
                std, sub = crosswalk_lookup(city, native)
                w.writerow([city, native, std, sub])
    with open(os.path.join(cw_dir, 'body_crosswalk.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['city', 'native_code', 'canonical_name', 'description'])
        w.writerows(BODY_CROSSWALK)
    with open(os.path.join(cw_dir, 'vote_values.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['city', 'value', 'recorded_meaning', 'notes'])
        w.writerows(VOTE_VALUES)


def build_parser():
    p = argparse.ArgumentParser(
        prog='normalize_motions.py',
        description='Regenerate the cross-city motions_std.csv normalization layer '
                    '(and, on a full sweep, the crosswalks/ tables).',
        epilog='Examples:\n'
               '  normalize_motions.py nephi            # just one city\n'
               '  normalize_motions.py nephi orem       # several cities\n'
               '  normalize_motions.py --all            # every city + regenerate crosswalks/\n'
               '  normalize_motions.py --all --report   # + distribution/cross-check tables',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('cities', nargs='*', metavar='city',
                   help='one or more city slugs to normalize; omit and pass --all to '
                        'sweep every city in the registry')
    p.add_argument('--all', action='store_true',
                   help='normalize every city in the registry and regenerate crosswalks/ '
                        '(required for a full sweep — a bare invocation will NOT sweep)')
    p.add_argument('--report', action='store_true',
                   help='also print the distribution / tally cross-check tables')
    return p


def main(argv):
    parser = build_parser()
    ns = parser.parse_args(argv)          # strict: --help exits 0, unknown args exit 2
    report = ns.report
    if ns.all and ns.cities:
        parser.error('give either city slugs or --all, not both')
    if not ns.all and not ns.cities:
        parser.error('no city given. Pass one or more city slugs, or --all to sweep '
                     'every city in the registry.')
    cities = list(CITIES) if ns.all else ns.cities
    for c in cities:
        if c not in CITIES:
            parser.error('unknown city %r (choose from %s)' % (c, ', '.join(CITIES)))

    stats = {'outcome': defaultdict(Counter), 'dist': defaultdict(Counter),
             'xcheck_total': Counter(), 'xcheck_agree': Counter(),
             'xcheck_diff': defaultdict(list), 'parse_rule': Counter()}
    observed_mt = defaultdict(set)
    for city in cities:
        for ds in DATASETS:
            path = os.path.join(ROOT, city + '_city_council', ds, 'all_votes.csv')
            if not os.path.exists(path):
                continue
            with open(path, newline='', encoding='utf-8') as f:
                for r in csv.DictReader(f):
                    observed_mt[city].add(r['motion_type'])

    for city in cities:
        for ds in DATASETS:
            n = process(city, ds, stats)
            if n is not None:
                oc = stats['outcome'][(city, ds)]
                known = sum(v for k, v in oc.items() if k != 'unknown')
                total = sum(oc.values())
                print('%-12s %-19s %5d motions  outcome-coverage %5.1f%%' %
                      (city, ds, n, 100.0 * known / total if total else 0))

    if set(cities) == set(CITIES):
        write_crosswalks(observed_mt)
        print('crosswalks/ regenerated (motion_type, body, vote_values)')

    print('\nTally cross-check vs counted member rows (motions with both):')
    for city in cities:
        t, a = stats['xcheck_total'][city], stats['xcheck_agree'][city]
        if t:
            print('  %-12s %5d/%5d agree (%.1f%%)' % (city, a, t, 100.0 * a / t))

    if report:
        cats = ['Land-Use', 'Ordinance', 'Resolution', 'Budget', 'Appointment',
                'Contract-Purchase', 'Grant-Funding', 'Interlocal', 'Ceremonial',
                'Procedural-Administrative', 'Public-Hearing', 'Legislative-Intent', 'Other']
        print('\nmotion_type_std share per city (%% of motions, both datasets):')
        print('%-26s' % 'category' + ''.join('%8s' % c[:7] for c in cities))
        for cat in cats:
            row = '%-26s' % cat
            for city in cities:
                tot = sum(stats['dist'][city].values())
                row += '%8.1f' % (100.0 * stats['dist'][city][cat] / tot if tot else 0)
            print(row)
        print('\ntop parse rules:', stats['parse_rule'].most_common(15))
        ndiff = sum(len(v) for v in stats['xcheck_diff'].values())
        print('\ntally-vs-members disagreements: %d (known source quirks expected)' % ndiff)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
