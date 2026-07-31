#!/usr/bin/env python3
"""OCR every EasyVote PDF (scanned) into campaign_finance/text/<name>.txt."""
import os, subprocess, glob, tempfile
RAW="/Users/tysonwelsh/civic-data/sandy_city_council/campaign_finance/raw/easyvote"
TXT="/Users/tysonwelsh/civic-data/sandy_city_council/campaign_finance/text"
os.makedirs(TXT, exist_ok=True)
pdfs=sorted(glob.glob(os.path.join(RAW,"*.pdf")))
for i,p in enumerate(pdfs,1):
    base=os.path.splitext(os.path.basename(p))[0]
    out=os.path.join(TXT, base+".txt")
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm","-r","200","-png",p,os.path.join(td,"pg")],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        texts=[]
        for img in sorted(glob.glob(os.path.join(td,"pg*.png"))):
            r=subprocess.run(["tesseract",img,"stdout"],capture_output=True,text=True)
            texts.append(r.stdout)
    with open(out,"w") as f: f.write("\n\f\n".join(texts))
    print(f"[{i}/{len(pdfs)}] {base}  ({sum(len(t) for t in texts)} chars)")
print("OCR DONE")
