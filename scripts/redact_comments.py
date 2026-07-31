#!/usr/bin/env python3
"""Redact email addresses and phone numbers from the CONSTRUCTED comment layers.

Policy (PRIVACY.md, decided 2026-07-31): the public-comment CSVs/JSON and their
derived copies are this project's aggregation, not a verbatim government document,
so contact details are redacted in the published form. Names and street addresses
are retained. Verbatim layers (minutes markdown, campaign_finance/text/) are NEVER
touched by this script.

Idempotent. MUST be re-run after any comment-layer rebuild (all_comments_clean.csv
regeneration or weeks/ rebuild) — see GOTCHAS.md.

Usage:
  python3 scripts/redact_comments.py --dry-run   # counts + samples, no writes
  python3 scripts/redact_comments.py             # apply in place
"""
import argparse
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The constructed comment layers only — never minutes or campaign_finance/text.
TARGET_GLOBS = [
    "*/public_comments/all_comments_clean.csv",
    "*/public_comments/comments_clean.json",
    "*/weeks/*/comments.csv",
]

EMAIL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._%+\-]*@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
# US phone forms: (801) 555-1234 / 801-555-1234 / 801.555.1234 / 801 555 1234.
# Anchored to avoid dollar amounts, vote tallies, and case/ordinance numbers:
# no leading $ or digit/hyphen, no trailing digit.
PHONE_RE = re.compile(
    r"(?<![\d$#\-.])(?:\(\d{3}\)\s?|\d{3}[-. ])\d{3}[-.]\d{4}(?!\d)"
)

def redact(text):
    n_e = len(EMAIL_RE.findall(text))
    n_p = len(PHONE_RE.findall(text))
    if n_e:
        text = EMAIL_RE.sub("[redacted-email]", text)
    if n_p:
        text = PHONE_RE.sub("[redacted-phone]", text)
    return text, n_e, n_p

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--samples", type=int, default=0,
                    help="print up to N matched strings per kind (dry-run aid)")
    args = ap.parse_args()

    total_e = total_p = files_touched = 0
    samples_e, samples_p = [], []
    for pat in TARGET_GLOBS:
        for path in sorted(glob.glob(os.path.join(ROOT, pat))):
            with open(path, encoding="utf-8") as f:
                text = f.read()
            if args.samples:
                samples_e += EMAIL_RE.findall(text)[: args.samples]
                samples_p += PHONE_RE.findall(text)[: args.samples]
            new, n_e, n_p = redact(text)
            if n_e or n_p:
                files_touched += 1
                total_e += n_e
                total_p += n_p
                rel = os.path.relpath(path, ROOT)
                print(f"  {rel}: {n_e} emails, {n_p} phones")
                if not args.dry_run:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new)
    mode = "DRY RUN — no writes" if args.dry_run else "APPLIED"
    print(f"{mode}: {total_e} emails + {total_p} phones across {files_touched} files")
    if args.samples:
        print("email samples:", samples_e[: args.samples * 3])
        print("phone samples:", samples_p[: args.samples * 3])
    return 0

if __name__ == "__main__":
    sys.exit(main())
