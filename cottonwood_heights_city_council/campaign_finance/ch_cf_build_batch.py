#!/usr/bin/env python3
"""Build the polite_fetch --batch list (url,name) for the Cottonwood Heights
campaign_finance acquisition, from the saved disclosure-listing HTML pages.

- State files (municipal.utah.gov) use Windows backslash paths -> rewrite to
  https + forward-slash + %-encode.
- City files (CivicEngage showpublisheddocument) are opaque doc ids -> named by
  the (candidate, label) mapping discovered from the elections-page table.

Discovery/acquisition helper only; not part of any derived layer.
Usage: python3 ch_cf_build_batch.py > batch_state.csv   (state)
       python3 ch_cf_build_batch.py city > batch_city.csv (2025 city)
"""
import re, sys, html, urllib.parse

PROBE = "/tmp/chcf_probe"


def slug(s):
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def state_rows():
    # map: year -> saved html file
    years = {"2017": "chf_2017.html", "2019": "chf_2019.html",
             "2021": "chf_2021.html", "2023": "chf_2023.html"}
    out = []
    for year, fn in years.items():
        data = open(f"{PROBE}/{fn}", encoding="utf-8", errors="replace").read()
        for m in re.finditer(r'href="(https?://municipal\.utah\.gov[^"]+\.pdf)"', data, re.I):
            raw = html.unescape(m.group(1))
            # normalize backslashes to slashes, force https, then percent-encode path
            u = raw.replace("\\", "/")
            u = re.sub(r"^http://", "https://", u)
            parts = u.split("municipal.utah.gov/", 1)
            enc = "https://municipal.utah.gov/" + urllib.parse.quote(parts[1])
            base = parts[1].rsplit("/", 1)[-1][:-4]  # filename without .pdf
            name = f"{year}_state_{slug(base)}.pdf"
            out.append((enc, name))
    return out


# 2025 city-hosted mapping: (candidate, office, {label: docid/ver})
CITY_2025 = [
    ("Mike Weichers", "mayor", [
        ("initial-financial-disclosure-statement", "9949/638844769357670000"),
        ("conflict-of-interest-disclosure", "9965/638847094677770000"),
        ("interim-oct-7-2025", "10363/638955155844770000"),
        ("interim-oct-28-2025", "10441/638974131322200000"),
        ("final-dec-4-2025", "10557/639005374448170000"),
    ]),
    ("Shawn Newell", "council-d3", [
        ("initial-financial-disclosure-statement", "9953/638845300283970000"),
        ("conflict-of-interest-disclosure", "9969/638847095094270000"),
        ("interim-oct-7-2025", "10365/638955156251600000"),
        ("interim-oct-28-2025", "10433/638974130453630000"),
        ("final-dec-4-2025", "10561/639005375376300000"),
    ]),
    ("Ellen Birrell", "council-d4", [
        ("initial-financial-disclosure-statement", "9947/638844769130770000"),
        ("conflict-of-interest-disclosure", "9979/638847922488200000"),
        ("interim-oct-7-2025", "10367/638955156500170000"),
        ("interim-oct-28-2025", "10435/638974130673830000"),
        ("final-dec-4-2025", "10563/639005375652300000"),
    ]),
    ("Randy Prazen", "council-d3", [
        ("initial-financial-disclosure-statement", "9975/638847419251470000"),
        ("conflict-of-interest-disclosure", "9977/638847915379530000"),
        ("interim-oct-7-2025", "10571/639007746782930000"),
        ("interim-oct-28-2025", "10569/639007746591300000"),
        ("final-dec-4-2025", "10567/639007746370330000"),
    ]),
    ("Ernie Kim", "council-d4", [
        ("initial-financial-disclosure-statement", "9991/638848270058130000"),
        ("conflict-of-interest-disclosure", "9993/638848270241230000"),
        ("interim-oct-7-2025", "10369/638955156827200000"),
        ("interim-oct-28-2025", "10437/638974130889070000"),
        ("final-dec-4-2025", "10565/639005375828670000"),
    ]),
    ("Gay Lynn Bennion", "mayor", [
        ("initial-financial-disclosure-statement", "9987/638848266601930000"),
        ("conflict-of-interest-disclosure", "9989/638848266892770000"),
        ("interim-oct-7-2025", "10371/638955157086400000"),
        ("interim-oct-28-2025", "10439/638974131107800000"),
        ("final-dec-4-2025", "10559/639005374925530000"),
    ]),
]


def city_rows():
    base = "https://www.cottonwoodheights.utah.gov/home/showpublisheddocument/"
    out = []
    for cand, office, docs in CITY_2025:
        last = slug(cand.split()[-1])
        for label, docid in docs:
            out.append((base + docid, f"2025_city_{last}_{label}.pdf"))
    return out


if __name__ == "__main__":
    rows = city_rows() if len(sys.argv) > 1 and sys.argv[1] == "city" else state_rows()
    for u, n in rows:
        print(f"{u},{n}")
