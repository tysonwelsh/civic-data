#!/usr/bin/env python3
"""Generate registry/HIERARCHY.md — the human-readable entity hierarchy.

DERIVED from registry/entities.csv + registry/relationships.csv (the canonical
truth); regenerate after any registry change, never hand-edit the output.
Added 2026-07-20 (Phase 6). Read-only over the registry; writes only HIERARCHY.md.
"""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "registry")
OUT = os.path.join(REG, "HIERARCHY.md")


def rows(name):
    with open(os.path.join(REG, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    ents = {e["slug"]: e for e in rows("entities.csv")}
    rels = rows("relationships.csv")
    within = {}      # child -> [(parent, confidence, note)]
    members = {}     # mpo -> [member]
    for r in rels:
        if r["relation"] == "within":
            within.setdefault(r["entity_a"], []).append(
                (r["entity_b"], r["confidence"], r["note"]))
        elif r["relation"] == "member_of":
            members.setdefault(r["entity_b"], []).append(r["entity_a"])

    def built(e):
        if e["db_rel_path"]:
            return "built (db)"
        if os.path.isdir(os.path.join(ROOT, e["dir"] or "")):
            return "built (modules, db-less)"
        return "registered only"

    def label(slug):
        e = ents[slug]
        return "**%s** (`%s`, fed %s, %s)" % (e["name"], slug, e["fed_index"], built(e))

    lines = [
        "# Entity hierarchy (GENERATED — `python3 scripts/build_hierarchy.py`)",
        "",
        "Derived from `entities.csv` + `relationships.csv`; regenerate, never edit.",
        "Geography lives in the relationship edges, not the folder tree (SCHEMA_SPEC §0).",
        "",
    ]
    # A state-level entity that sits `within` another state-level entity is an
    # AGENCY/DISTRICT leaf (udot, uta), not a root — only true roots template
    # the full regional/county/city tree beneath them.
    state_slugs = {s for s, e in ents.items() if e["level"] == "state"}
    agency = {s for s in state_slugs
              if any(p in state_slugs for p, _, _ in within.get(s, []))}
    for st in sorted(state_slugs - agency):
        lines.append("- %s" % label(st))
        for ag in sorted(a for a in agency
                         if any(p == st for p, _, _ in within.get(a, []))):
            note = next((n for p, _, n in within[ag] if p == st and n), "")
            lines.append("  - %s%s" % (label(ag),
                                       (" — " + note) if note else ""))
        regionals = sorted(s for s, e in ents.items() if e["level"] == "regional")
        for rg in regionals:
            n = len(members.get(rg, []))
            lines.append("  - %s — %d member entities" % (label(rg), n))
        counties = sorted((s for s, e in ents.items() if e["level"] == "county"),
                          key=lambda s: int(ents[s]["fed_index"]))
        for co in counties:
            lines.append("  - %s" % label(co))
            kids = sorted(c for c, ps in within.items()
                          if ents.get(c, {}).get("level") == "city"
                          and any(p == co for p, _, _ in ps))
            for c in kids:
                marks = []
                for p, conf, note in within[c]:
                    if p == co and ("secondary" in (note or "").lower()
                                    or "straddle" in (note or "").lower()
                                    or conf != "high"):
                        marks.append("straddle/secondary (%s)" % conf)
                    elif p == co and note:
                        marks.append(note.split(";")[0])
                suffix = (" — " + "; ".join(marks)) if marks else ""
                lines.append("    - %s%s" % (label(c), suffix))
    lines.append("")
    n_city = sum(1 for e in ents.values() if e["level"] == "city")
    n_cnty = sum(1 for e in ents.values() if e["level"] == "county")
    n_reg = sum(1 for e in ents.values() if e["level"] == "regional")
    n_st = sum(1 for e in ents.values() if e["level"] == "state")
    lines.append("Totals: %d cities/towns · %d counties · %d regional · %d state = %d entities."
                 % (n_city, n_cnty, n_reg, n_st, len(ents)))
    lines.append("")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("Wrote %s (%d entities)" % (OUT, len(ents)))


if __name__ == "__main__":
    main()
