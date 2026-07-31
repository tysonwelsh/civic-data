#!/usr/bin/env python3
"""Pathology screen for extracted-text corpora (minutes/comments markdown).

Usage:
    python3 screen_corpus.py <dir> [<dir> ...]        # screen all .md/.txt under each dir
    python3 screen_corpus.py --json <dir>             # per-file JSONL to stdout instead of summary

Flags are SIGNALS, not verdicts. Known benign patterns (verified in the 2026-07 audit):
  - "ends_mid" on files ending in signature blocks, attendee lists, or page footers
  - "repeated_line" from per-page headers (cosmetic; vote extractors tolerate them)
  - ligature-loss regexes matching real prose ("...was led by...")
Every flagged file needs a human/agent look before being called a defect.
"""
import sys, os, re, json, hashlib, unicodedata, statistics
from collections import Counter

def load_dictionary():
    for p in ("/usr/share/dict/words", "/usr/dict/words"):
        if os.path.exists(p):
            return {w.strip().lower() for w in open(p, encoding="utf-8", errors="ignore")}
    return None

DICTIONARY = load_dictionary()

MOJIBAKE = re.compile(r"â€™|â€œ|â€\x9d|â€“|â€”|Ã©|Ã¨|Ã¡|Ã³|Â£|Â°|Ã¢")
LONG_TOKEN = re.compile(r"\b[A-Za-z]{26,}\b")
URL = re.compile(r"https?://\S+|www\.\S+|\S+\.(com|org|gov|net)\S*")
HYPHEN_BREAK = re.compile(r"[a-z]- [a-z]")
LIGATURES = "ﬁﬂﬀﬃﬄ"
SENTENCE_END = re.compile(r'[.!?:)"”’]$|\b(adjourned?|attest|recorder|secretary|clerk|approved)\b[.,]?\s*$', re.I)
PAGE_FOOTER = re.compile(r"^\s*(page\s+\d+|\d+\s*\|\s*p\s*a\s*g\s*e|-\s*\d+\s*-)\s*", re.I)
# A body that only announces that real content is missing/deferred, rather than being it.
PLACEHOLDER_BODY = re.compile(
    r"\b(deferred to the backfill|OCR\s*\+?\s*vote extraction deferred|existence confirmed"
    r"|image-only pdf|scanned\s*[—-]|no text layer|pending\s+(?:OCR|extraction)"
    r"|minutes not (?:yet )?(?:posted|available))\b", re.I)

def strip_header(text):
    """Drop the injected provenance header (# title / > Source / ---) to measure the real body."""
    m = re.match(r"^#[^\n]*\n(?:>[^\n]*\n|\n)*(?:---\n)?", text)
    return text[m.end():] if m else text

def screen_file(path):
    raw = open(path, encoding="utf-8", errors="surrogateescape").read()
    body = strip_header(raw).strip()
    n = max(len(body), 1)
    flags = {}

    flags["cid"] = raw.count("(cid:")
    flags["replacement_char"] = raw.count("�")
    pua = sum(1 for c in body if 0xE000 <= ord(c) <= 0xF8FF)
    flags["pua_chars"] = pua
    flags["pua_ratio"] = round(pua / n, 4)          # Sandy-style broken font cmap: ratio > 0.01 is a garbled file
    flags["mojibake"] = len(MOJIBAKE.findall(raw))
    flags["ligature_chars"] = sum(body.count(c) for c in LIGATURES)
    long_toks = [t for t in LONG_TOKEN.findall(URL.sub(" ", body))]
    flags["long_tokens"] = len(long_toks)
    flags["long_token_sample"] = long_toks[:3]
    flags["hyphen_breaks"] = len(HYPHEN_BREAK.findall(body))
    flags["body_bytes"] = len(body.encode("utf-8"))
    flags["stub"] = flags["body_bytes"] < 200        # Vineyard-style header-only file presented as minutes
    flags["short"] = flags["body_bytes"] < 500
    # placeholder: a body that is only a deferral/pending marker, NOT minutes text. Sits
    # above the stub threshold (cache's 160 "[SCANNED — … DEFERRED]" bodies scored 0/307 on
    # stub) yet contributes no extractable content, while document.has_text and fts_minutes
    # both count it as built. 2026-07-25 non-city-tier audit.
    flags["placeholder"] = bool(PLACEHOLDER_BODY.search(body)) and len(body) < 1200
    # no_content: too few real word tokens to be a minutes document, whatever the byte size.
    flags["no_content"] = len(re.findall(r"[A-Za-z]{3,}", body)) < 40

    # --- Failure-mode-AGNOSTIC detectors: catch garbling we have never seen before. ---
    # dict_ratio: fraction of ordinary-looking words that are real English words.
    # Any corruption that mangles words (bad cmap, OCR splits, mojibake, interleaving,
    # encodings not yet imagined) craters this without us having to name the pathology.
    toks = re.findall(r"[A-Za-z]{4,}", URL.sub(" ", body))
    if DICTIONARY and len(toks) >= 50:
        hits = sum(1 for t in toks if t.lower() in DICTIONARY)
        flags["dict_ratio"] = round(hits / len(toks), 3)
    else:
        flags["dict_ratio"] = None
    # split_word_rate: adjacent token pairs that form a dictionary word joined but not
    # apart ("bou levard", "adm inistrative") — generic detector for any split-word
    # corruption (bad OCR layers, kerning-space extraction), per 1000 tokens.
    if DICTIONARY:
        all_toks = re.findall(r"[A-Za-z]+", body)
        splits = 0
        for a, b in zip(all_toks, all_toks[1:]):
            if len(a) >= 2 and len(b) >= 2 and len(a) + len(b) >= 6:
                joined = (a + b).lower()
                if joined in DICTIONARY and not (a.lower() in DICTIONARY and b.lower() in DICTIONARY):
                    splits += 1
        flags["split_word_rate"] = round(1000 * splits / max(len(all_toks), 1), 2)
    else:
        flags["split_word_rate"] = None
    # weird_char_ratio: chars outside ASCII + common typographic punctuation/accents.
    common_extra = set("’‘“”–—…•·°éèáíóúñüçÉ§¶®©™½¼¾")
    weird = sum(1 for c in body if (ord(c) > 126 and c not in common_extra
                                    and not unicodedata.category(c).startswith("Z"))
                or (ord(c) < 32 and c not in "\n\t\r"))
    flags["weird_char_ratio"] = round(weird / n, 4)

    lines = [l.strip() for l in body.splitlines() if l.strip()]
    lc = Counter(l for l in lines if len(l) > 15 and not PAGE_FOOTER.match(l))
    top = lc.most_common(1)
    flags["repeated_line"] = top[0][1] if top and top[0][1] >= 6 else 0

    last = ""
    for l in reversed(lines):
        if not PAGE_FOOTER.match(l):
            last = l
            break
    flags["ends_mid"] = bool(last) and not SENTENCE_END.search(last)
    flags["last_line"] = last[-80:]

    flags["body_hash"] = hashlib.md5(
        unicodedata.normalize("NFKC", re.sub(r"\s+", " ", body)).encode()).hexdigest() if body else ""
    return flags

def main():
    as_json = "--json" in sys.argv
    dirs = [a for a in sys.argv[1:] if a != "--json"]
    files = []
    for d in dirs:
        for root, _, names in os.walk(d):
            files += [os.path.join(root, f) for f in names if f.endswith((".md", ".txt"))]
    files.sort()

    results, hashes = {}, {}
    for p in files:
        try:
            f = screen_file(p)
        except Exception as e:
            f = {"error": str(e)}
        results[p] = f
        if f.get("body_hash"):
            hashes.setdefault(f["body_hash"], []).append(p)

    dupes = {h: ps for h, ps in hashes.items() if len(ps) > 1}
    for ps in dupes.values():
        for p in ps:
            results[p]["duplicate_of"] = [q for q in ps if q != p]

    if as_json:
        for p, f in results.items():
            print(json.dumps({"file": p, **f}, ensure_ascii=False))
        return

    total = len(files)
    print(f"screened {total} files under {', '.join(dirs)}\n")
    def rate(key, pred):
        hits = [p for p, f in results.items() if pred(f)]
        print(f"{key:22s} {len(hits):4d}/{total}")
        for p in hits[:8]:
            print(f"    {p}")
        if len(hits) > 8:
            print(f"    ... +{len(hits)-8} more")
        return hits
    rate("cid_artifacts", lambda f: f.get("cid", 0) > 0)
    rate("replacement_chars", lambda f: f.get("replacement_char", 0) > 0)
    rate("PUA_garbled(>1%)", lambda f: f.get("pua_ratio", 0) > 0.01)
    rate("mojibake", lambda f: f.get("mojibake", 0) > 0)
    rate("long_tokens(3+)", lambda f: f.get("long_tokens", 0) >= 3)
    rate("stub(<200B)", lambda f: f.get("stub"))
    rate("short(<500B)", lambda f: f.get("short") and not f.get("stub"))
    rate("PLACEHOLDER(deferred/scanned marker)", lambda f: f.get("placeholder"))
    rate("no_content(<40 words)", lambda f: f.get("no_content") and not f.get("stub"))
    rate("duplicate_bodies", lambda f: bool(f.get("duplicate_of")))
    rate("hyphen_breaks(3+)", lambda f: f.get("hyphen_breaks", 0) >= 3)
    rate("repeated_line(6+)", lambda f: f.get("repeated_line", 0) >= 6)
    rate("ends_mid(advisory)", lambda f: f.get("ends_mid"))
    rate("read_errors", lambda f: "error" in f)

    # Corpus-relative anomaly report: judge each file against THIS corpus's own baseline,
    # so the screen works on cities/formats we haven't met yet.
    drs = [f["dict_ratio"] for f in results.values() if f.get("dict_ratio") is not None]
    if drs:
        med = statistics.median(drs)
        print(f"\ndict_ratio: median {med:.3f}  min {min(drs):.3f}")
        rate("dict_ratio_outlier", lambda f: f.get("dict_ratio") is not None
             and f["dict_ratio"] < min(med - 0.15, 0.70))
    elif DICTIONARY is None:
        print("\n(no system dictionary found — dict_ratio skipped)")
    srs = [f["split_word_rate"] for f in results.values() if f.get("split_word_rate") is not None]
    if srs:
        med_s = statistics.median(srs)
        print(f"split_word_rate/1k: median {med_s:.2f}  max {max(srs):.2f}")
        rate("split_word_outlier", lambda f: f.get("split_word_rate") is not None
             and f["split_word_rate"] > max(5 * med_s, 3.0))
    wrs = [f.get("weird_char_ratio", 0) for f in results.values()]
    if wrs:
        med_w = statistics.median(wrs)
        print(f"weird_char_ratio: median {med_w:.4f}  max {max(wrs):.4f}")
        rate("weird_char_outlier", lambda f: f.get("weird_char_ratio", 0) > max(10 * med_w, 0.005))

    # Per-year stratification: a single bad year hides inside corpus-wide medians.
    def year_of(p):
        m = re.search(r"/(20\d\d)/", p) or re.search(r"\b(20\d\d)-\d\d-\d\d", os.path.basename(p))
        return m.group(1) if m else "?"
    years = sorted({year_of(p) for p in results})
    if len(years) > 1:
        print(f"\n{'year':6s} {'files':>5s} {'med_dict':>8s} {'med_split':>9s} {'med_weird':>9s}")
        for y in years:
            fs = [f for p, f in results.items() if year_of(p) == y]
            def m(key):
                vals = [f[key] for f in fs if f.get(key) is not None]
                return f"{statistics.median(vals):.3f}" if vals else "-"
            print(f"{y:6s} {len(fs):5d} {m('dict_ratio'):>8s} {m('split_word_rate'):>9s} {m('weird_char_ratio'):>9s}")
        print("(investigate any year whose medians break from its neighbors)")

if __name__ == "__main__":
    main()
