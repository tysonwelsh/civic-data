#!/usr/bin/env python3
"""link_text_sidecars.py — populate the §9 text-layer columns on packets/index.csv.

Draper's primary-document layer is CLASSIFY-IN-PLACE: the raw PDFs/HTML and their
extracted text sidecars (packets/text/) already exist on disk from the
expand-city-sources build. This script does NOT fetch anything — it links each
CLASSIFIED row (doc_class != "") to its existing sidecar and records provenance.

For each classified row (deterministic, rerunnable):
  stored == 'yes' (raw on disk at `path`):
    sha256    = sha256 of the stored raw binary
    sidecar text/<stem>.txt exists & non-empty:
        fetch_status = 'ok'
        text_path    = 'text/<stem>.txt'   (dataset-relative)
        text_chars   = character length of the sidecar
    else (image-only PDF / empty HTML strip — no usable text layer):
        fetch_status = 'needs_ocr'   (honest OCR floor; text_path/text_chars blank)
  stored == 'no' (index-only: oversize-dropped or dead-link — no raw, no text):
        fetch_status = ''   (blank: not fetched this wave — see AVAILABILITY.md)
        sha256       = from a raw/*/_fetch_log.jsonl entry matching source_url, if any
                       (oversize rows were HEAD-only, so usually blank)
Unclassified rows (doc_class == '') keep all four columns blank.

DISCARD-ROW SAFETY (SCHEMA_SPEC section 9 discard-binary exception, 2026-07-19):
  A stored == 'no' row that ALREADY carries a populated text_path is a section-9
  discard row: the binary was fetched, hashed, text-extracted, then DISCARDED
  (text-only corpus; re-fetchable via source_url). Its section-9 columns are
  maintained DIRECTLY in index.csv (the binary is gone, so nothing on disk can
  re-derive them). Such rows are PRESERVED VERBATIM here -- the script never
  resets or recomputes their doc_class/fetch_status/sha256/text_path/text_chars
  (nor extraction_method), including the vision-transcribed (claude_vision)
  needs_ocr->ok rows. Before this guard they fell through the stored != 'yes'
  branch and were blanked on every rerun.

Run:  python3 link_text_sidecars.py            # populate + rewrite index.csv
      python3 link_text_sidecars.py --dry-run  # report the split, write nothing
"""
import csv, os, sys, json, hashlib, glob

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.csv")
TEXT = os.path.join(HERE, "text")
RAW = os.path.join(HERE, "raw")

EXT_COLS = ("doc_class", "fetch_status", "sha256", "text_path", "text_chars")


def stem(path):
    return os.path.splitext(os.path.basename(path))[0]


def sha256_file(abspath):
    h = hashlib.sha256()
    with open(abspath, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_url_sha():
    """url -> sha256 from every raw/*/_fetch_log.jsonl (for index-only rows)."""
    m = {}
    for logp in glob.glob(os.path.join(RAW, "*", "_fetch_log.jsonl")):
        with open(logp) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                sha = d.get("sha256")
                if sha:
                    for k in ("url", "final_url"):
                        if d.get(k):
                            m[d[k]] = sha
    return m


def main():
    dry = "--dry-run" in sys.argv

    with open(INDEX, newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = list(reader)
    for col in EXT_COLS:
        if col not in fields:
            fields.append(col)

    url_sha = None
    counts = {"ok": 0, "needs_ocr": 0, "index_only": 0, "discard_preserved": 0}
    per_class = {}

    for r in rows:
        for col in EXT_COLS:
            r.setdefault(col, "")
        # SCHEMA_SPEC section 9 discard-binary rows: stored='no' but a text sidecar
        # already exists (binary was fetched/hashed/extracted then discarded). Their
        # §9 columns are maintained in-file with no on-disk binary to re-derive from,
        # so PRESERVE the row verbatim (never reset/recompute). Guard runs BEFORE the
        # reset below. See module docstring "DISCARD-ROW SAFETY".
        if r.get("stored") == "no" and (r.get("text_path") or "").strip():
            counts["discard_preserved"] += 1
            dc0 = r.get("doc_class", "")
            if dc0:
                per_class.setdefault(dc0, {"ok": 0, "needs_ocr": 0, "index_only": 0})
            continue
        # reset the derived columns so reruns are idempotent
        r["fetch_status"] = ""
        r["sha256"] = ""
        r["text_path"] = ""
        r["text_chars"] = ""
        dc = r.get("doc_class", "")
        if not dc:
            continue
        per_class.setdefault(dc, {"ok": 0, "needs_ocr": 0, "index_only": 0})
        path = (r.get("path") or "").strip()
        if r.get("stored") == "yes" and path:
            abspath = os.path.join(HERE, path)
            if os.path.exists(abspath):
                r["sha256"] = sha256_file(abspath)
            sidecar = os.path.join(TEXT, stem(path) + ".txt")
            if os.path.exists(sidecar):
                txt = open(sidecar, encoding="utf-8", errors="replace").read()
                if txt.strip():
                    r["fetch_status"] = "ok"
                    r["text_path"] = "text/" + stem(path) + ".txt"
                    r["text_chars"] = str(len(txt))
                    counts["ok"] += 1
                    per_class[dc]["ok"] += 1
                    continue
            # raw present but no usable sidecar → image-only / needs OCR
            r["fetch_status"] = "needs_ocr"
            counts["needs_ocr"] += 1
            per_class[dc]["needs_ocr"] += 1
        else:
            # index-only (oversize-dropped or dead link): not fetched this wave
            if url_sha is None:
                url_sha = load_url_sha()
            sha = url_sha.get((r.get("source_url") or "").strip())
            if sha:
                r["sha256"] = sha
            counts["index_only"] += 1
            per_class[dc]["index_only"] += 1

    print("classified rows linked:")
    print(f"  ok (text sidecar): {counts['ok']}")
    print(f"  needs_ocr (raw on disk, no text): {counts['needs_ocr']}")
    print(f"  index-only (no raw this wave): {counts['index_only']}")
    print(f"  discard-rows preserved verbatim (section 9): {counts['discard_preserved']}")
    print("per class (ok / needs_ocr / index-only):")
    for k in sorted(per_class):
        c = per_class[k]
        print(f"  {k}: {c['ok']} / {c['needs_ocr']} / {c['index_only']}")
    if dry:
        print("(dry run — index.csv not written)")
        return

    tmp = INDEX + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, INDEX)
    print(f"wrote {INDEX} ({len(rows)} rows, {len(fields)} cols)")


if __name__ == "__main__":
    main()
