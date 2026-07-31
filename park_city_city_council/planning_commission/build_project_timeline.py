#!/usr/bin/env python3
"""
build_project_timeline.py — cross-body PROJECT crosswalk for Park City.

Joins Planning Commission and City Council votes on the SAME development project so you can
trace a project end-to-end: PC recommendation/action -> Council vote. Output:
  planning_commission/project_timeline.csv  (long format, one row per project-event)

Method (heuristic, text-based — spot-check before quoting): for each land-use motion in either
body, extract the project name as the proper-noun run immediately before a land-use noun
(Subdivision / Plat / Condominium / MPD / Place / Lodge / Canyon / Estates / Annexation / ...),
normalize away Phase/Amended/Lot/ordinal qualifiers, and group events by that key. It is a fuzzy
join (motion text varies); treat it as a navigation aid, not a system of record.
"""
import csv, re, collections, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CC = os.path.join(ROOT, "meeting_minutes", "all_votes.csv")
PC = os.path.join(ROOT, "planning_commission", "all_votes.csv")
OUT = os.path.join(ROOT, "planning_commission", "project_timeline.csv")

# Terminate ONLY on truly generic land-use nouns (NOT Place/Canyon/Lodge/etc. — those are name parts).
GEN = re.compile(r"\b(Subdivisions?|Re-?Subdivisions?|Plat|Condominiums?|MPD|"
                 r"Master Planned Development|Annexations?|Steep Slope|Hillside|Townhomes?)\b", re.I)
ROMAN = re.compile(r"^[IVXLCM]{1,4}$")
STOP = {"plat","amendment","amended","master","planned","development","condominium","condominiums",
        "subdivision","affordable","accessory","conditional","use","permit","findings","fact","pod",
        "parcel","consideration","city","council","council’s","modifications","the","of","a","an",
        "for","at","on","and","phase","lot","first","second","third","fourth","fifth","sixth","west",
        "east","north","south","amend","re","its","approve","approval","continue","continued",
        "modification","modifications","deny","denial","forward","positive","negative","recommendation"}

def project_key(motion):
    """Project name = the Capitalized run sitting right before a generic land-use noun, taken from
    the last comma/dash-delimited segment (so a leading street address falls off)."""
    m = GEN.search(motion)
    if not m:
        return None
    window = motion[:m.start()].replace("’", "'")  # normalize curly apostrophe (King's vs King’s)
    seg = re.split(r"[,–—]|\s-\s|\bfor\b|\bon\b(?!e)", window)[-1]
    toks = re.findall(r"[0-9]{2,5}|[A-Z][A-Za-z'’.]+", seg)
    name = [t for t in toks if t.lower() not in STOP and not ROMAN.match(t) and not t.isdigit()]
    if not name or not any(len(t) >= 3 and t[0].isalpha() for t in name):
        return None
    return " ".join(name[-3:]).strip(" .,'’")

def motions(path, body_label):
    seen = {}
    for r in csv.DictReader(open(path)):
        k = (r["source"], r["motion_no"])
        if k not in seen:
            seen[k] = {"date": r["date"], "result": r["result"], "type": r["motion_type"],
                       "motion": " ".join(r["motion"].split()), "body": r["body"], "diss": set()}
        if r.get("vote") in ("Nay", "Abstain", "Recuse") and r.get("member"):
            seen[k]["diss"].add(r["member"].split()[-1])
    return list(seen.values())

def stage(ev):
    res = ev["result"].lower()
    if ev["body"] == "PlanningCommission":
        if "recommendation" in res: return "PC recommendation"
        if "continued" in res:      return "PC continued"
        return "PC final action"
    if ev["body"] in ("RDA", "HA"): return f"{ev['body']} vote"
    return "Council vote"

events = []
for ev in motions(PC, "PC") + motions(CC, "CC"):
    if ev["type"] not in ("Land-Use/Zoning", "Ordinance", "Other", "Contract/Purchase"):
        # land-use signal mostly lives in these; project_key gates the rest
        pass
    key = project_key(ev["motion"])
    if not key:
        continue
    events.append({"project": key, "date": ev["date"], "body": ev["body"], "stage": stage(ev),
                   "result": ev["result"], "dissenters": ",".join(sorted(ev["diss"])),
                   "motion": ev["motion"][:160], "source": ev.get("source", "")})

# keep projects that have >=2 events OR appear in both bodies (the useful ones)
byproj = collections.defaultdict(list)
for e in events:
    byproj[e["project"]].append(e)
keep = {p: evs for p, evs in byproj.items()
        if len(evs) >= 2 or len({e["body"] for e in evs}) > 1}

rows = []
for p, evs in keep.items():
    bodies = {e["body"] for e in evs}
    both = ("PlanningCommission" in bodies) and (bodies & {"Council", "RDA", "HA"})
    for e in sorted(evs, key=lambda x: x["date"]):
        e["project"] = p
        e["spans_both_bodies"] = "yes" if both else "no"
        rows.append(e)

cols = ["project", "spans_both_bodies", "date", "body", "stage", "result", "dissenters", "motion", "source"]
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for r in sorted(rows, key=lambda x: (x["project"], x["date"])):
        w.writerow(r)

nproj = len(keep)
nboth = len({r["project"] for r in rows if r["spans_both_bodies"] == "yes"})
print(f"projects tracked: {nproj} | spanning BOTH PC+Council: {nboth} | timeline rows: {len(rows)}")
print(f"-> {OUT}")
