#!/usr/bin/env python3
"""Ogden cross-body referral build — thin stub enabling the SHARED referral guard.

Shared logic lives in scripts/referrals_lib.py (repo root). Idempotent; run AFTER
build_db.py:  python3 db/build_referrals.py

The two-layer false-positive guard below was PORTED into scripts/referrals_lib.py as opt-in
parameters on 2026-07-20 (TODO "port the ogden referral guard" follow-up). Ogden now ENABLES
it by passing member_names / template_stopwords / content_veto=True / name_anchor_min=2 to
main() — no monkeypatching, no shared-lib fork. The defaults are a faithful no-op, so no other
city's referrals change; ogden is the ONLY city enabling the guard until per-city evidence
review clears others. The design rationale below is retained verbatim (it now documents the
PARAMETERS, not a local override).

OGDEN GUARD (2026-07-19, TODO "Ogden build_referrals surname-token weakness")
==================================================================================
Ogden's recorded motions carry no file/case number, so every cross-body link falls to
the subject matcher. Two things make Ogden uniquely prone to the surname-token false
positive the TODO names:

  * build_db grants an application_id even to terse PROCEDURAL agency motions
    ("MOVED THE MEETING ADJOURN AT 8:47 P.M. MOTION WAS SECONDED BY BOARD MEMBER HYER").
    Their only rare tokens are the mover/seconder SURNAMES (Hyer / Myers / Graf /
    Choberka / Lundell ...).
  * Ogden's adoption motions are boilerplate-heavy ("ON A MOTION BY COUNCIL MEMBER X AND
    SECONDED BY COUNCIL MEMBER Y, ORDINANCE 20NN-N WAS ADOPTED [ENTITLED: 'An ordinance of
    Ogden City ...']"). Words like ADOPTED / ENTITLED / MEMBER / SECONDED / WAS / OGDEN /
    MASTER are NOT in the shared STOP list, so two UNRELATED matters overlap on this
    template plus whatever member names they happen to share.

Result: false PC/RDA/MBA<->Council "subject" referrals whose entire overlap is
{boilerplate template words} + {member surnames} and ZERO genuine subject content. They
reach the linker by BOTH scoring paths — the asymmetric name-anchored CONTAINMENT path
(terse ADJOURN motions) AND the symmetric Jaccard path (two substantial adoption motions).
The 4 hand-suppressed 2026-07-02 examples are exactly this class; in the live corpus they
now surface as e.g. 141<-157 (Council Ord 2024-12 code amendments vs RDA Ogden Bend Master
Plan — matched on {adopted,entitled,hyer,member,myers,ogden,seconded,was}) and 243<-239/241
(Council Ord 2026-7 clean-energy vs RDA ADJOURN — matched on the lone surname {lundell}).

THE GUARD (two layers, now in the SHARED lib, gated on by ogden's params here). Neither
layer changes global tokenization (so every genuine link's subject_score is byte-identical to
before), and neither disturbs the app_key-keyed override mechanism.

  1. CONTENT-VETO on IDF.score + IDF.contain (lib param content_veto=True) — a subject link must rest on at least one
     shared token that is GENUINE CONTENT: not a motion/plan/CRA boilerplate template word
     (ADOPTED, ENTITLED, MEMBER, SECONDED, WAS, MOVED, OGDEN, MASTER, AREA, COMMUNITY,
     REINVESTMENT ...) and not a council/PC/RDA/MBA MEMBER NAME. If the two motions'
     overlap is nothing but template + names, score() and contain() return 0.0 and no link
     forms — on either scoring path. Genuine links always share a distinguishing project
     token (AIRPORT, ADAMS, UNION, STATION, MODERATE, INCOME ...), so this is a pure veto:
     when real content is shared the original weighted scores are used unchanged.
     (MEMORY: surnames collide — prefer full-name resolution; a shared surname is never,
     by itself, evidence that two matters are the same project.)

  2. Multi-token name-anchor guard (lib param name_anchor_min=2) — the name-anchored
     (asymmetric containment) path must additionally share >=2 DISTINCTIVE (rare) NON-NAME
     tokens, not a lone rare token. This catches the lone-token co-location case that survives
     the content veto: a shared STREET name across two DIFFERENT parcels (Council 1450 Gibson
     Ave rezone-deny vs RDA 1781 Gibson Ave purchase share only the street word "gibson" —
     same street, different parcels, not the same matter). Implemented in the lib by counting
     only rare NON-NAME shared tokens in IDF.distinctive_shared (its sole caller is the
     name_anchored test) and requiring name_anchor_min of them.

AMBIGUOUS member surnames that double as Ogden PLACE names are DELIBERATELY excluded from
the name set — WASHINGTON (member Alicia Washington vs Washington Boulevard) and WHITE
(member Marcia White) — so a genuine street-based link is never blinded by them.

Scope note: this guard removes the surname/boilerplate-template FP CLASS. A SEPARATE, wider
weakness (two DIFFERENT named CRAs sharing the generic "Community Reinvestment Project Area"
template, distinguished only by their project noun) is only partly covered and is logged as
follow-up, not chased here.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, "scripts")))
from referrals_lib import main

# --- Ogden council + Planning Commission + RDA/MBA member NAMES (db `person` table + PC
#     roster). First AND last names, because minutes cite both "COUNCIL MEMBER <first>
#     <last>" and bare surnames. WASHINGTON / WHITE intentionally OMITTED (place-name
#     collision — treated as content, never as an attribution token). Passed to the shared
#     guard's member_names: used by BOTH the content veto and the name-anchor floor.
_MEMBER_NAMES = frozenset("""
richard hyer rick safsten dave graf cathy blaisdell bart blair bryan schade
southwick jenny sandau angela choberka marcia ken richey luis lopez flor
ben nadolski mandy shale shaun myers neil garner doug stephens jeremy shinoda
jordan aaberg jessica stoker wesley boykin william ross michelle williams
andrey akhmedov kevin lundell janith wright angel castillo james humphreys
robert herman alicia caldwell
""".split())

# --- Motion / plan / CRA boilerplate that leaks through STOP and is NOT genuine subject
#     content. Only clearly-generic, non-identifying words (a real project is always
#     identified by a token OUTSIDE this set: airport, adams, union, moderate, income ...).
#     Passed to the shared guard's template_stopwords (vetoed alongside member_names).
_TEMPLATE = frozenset("""
adopted adopting adoption entitled member members second seconded moved moving move
motioned was were will shall hereby thereof whereas pursuant provisions provision
section closed adjourn adjourned trustee trustees boardmember posted ordered nominate
roll call following same sign signed authorized authorizing authorize execute executed
executing director ogden master area community reinvestment
""".split())

if __name__ == "__main__":
    # content_veto=True + name_anchor_min=2 turn on the two guard layers; every other city
    # leaves them at their no-op defaults. See scripts/referrals_lib.py main() docstring.
    sys.exit(main(HERE, member_names=_MEMBER_NAMES, template_stopwords=_TEMPLATE,
                  content_veto=True, name_anchor_min=2))
