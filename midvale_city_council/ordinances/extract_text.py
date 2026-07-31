#!/usr/bin/env python3
"""Extract a text sidecar for every raw ordinance document.

Born-digital PDFs -> `pdftotext -layout`. Scanned/image PDFs (no text layer) ->
tesseract OCR at 300 dpi (pages rasterized with pdftoppm into a scratchpad temp dir,
NOT /tmp). .doc/.docx publication notices -> macOS `textutil`. Each sidecar is written
to text/<stem>.txt; per-file method + char count logged to text/_extraction_log.csv.

Idempotent, no network. macOS `timeout` is not on PATH, so every subprocess uses the
Python `subprocess` timeout. Source typos / OCR noise are preserved verbatim.
"""
import csv, glob, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'raw')
TXT = os.path.join(HERE, 'text')
SCRATCH = os.environ.get('MV_SCRATCH',
    '/private/tmp/claude-501/-Users-tysonwelsh-civic-data/8fb286a3-d584-4f76-9af3-7bf139a225b8/scratchpad')
MIN_TEXT = 200  # chars of real text below which a PDF is treated as scanned


def run(cmd, timeout, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kw)


def pdftotext(path):
    try:
        return run(['pdftotext', '-layout', path, '-'], 120).stdout
    except Exception:
        return ''


PAGE_CAP = 15  # OCR only the first N pages; a signed ordinance's operative text is at the
               # front — pages beyond this are image-only map/plat exhibits (no useful text).


def pdf_pages(path):
    try:
        r = run(['pdfinfo', path], 30)
        m = re.search(r'Pages:\s*(\d+)', r.stdout)
        return int(m.group(1)) if m else 0
    except Exception:
        return 0


def ocr_pdf(path, stem):
    """Rasterize the first PAGE_CAP pages to PNG in a scratchpad temp dir, OCR each."""
    npages = pdf_pages(path)
    last = min(npages, PAGE_CAP) if npages else PAGE_CAP
    with tempfile.TemporaryDirectory(dir=SCRATCH, prefix=f'ocr_{stem}_') as td:
        try:
            run(['pdftoppm', '-r', '300', '-png', '-f', '1', '-l', str(last),
                 path, os.path.join(td, 'p')], 600)
        except Exception as e:
            return '', f'pdftoppm-fail:{e}'
        pages = sorted(glob.glob(os.path.join(td, 'p*.png')))
        out = []
        for pg in pages:
            try:
                r = run(['tesseract', pg, '-', '--psm', '6', '-l', 'eng'], 300)
                out.append(r.stdout)
            except Exception as e:
                out.append(f'[[OCR-ERROR {os.path.basename(pg)}: {e}]]')
        cap = f', first {last} of {npages}pp' if npages > PAGE_CAP else f', {len(pages)}pg'
        return '\n'.join(out), cap.lstrip(', ')


def doc_text(path):
    try:
        return run(['textutil', '-convert', 'txt', '-stdout', path], 120).stdout
    except Exception as e:
        return f'[[textutil-fail:{e}]]'


def main():
    os.makedirs(TXT, exist_ok=True)
    files = sorted(glob.glob(os.path.join(RAW, '*.pdf')) +
                   glob.glob(os.path.join(RAW, '*.doc')) +
                   glob.glob(os.path.join(RAW, '*.docx')))
    only = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else None
    force = '--force' in sys.argv
    logp0 = os.path.join(TXT, '_extraction_log.csv')
    done = {}
    if os.path.exists(logp0):
        for r in csv.DictReader(open(logp0)):
            done[r['file']] = r
    log = []
    for path in files:
        base = os.path.basename(path)
        stem, ext = os.path.splitext(base)
        if only and only not in base:
            continue
        # skip if already extracted (sidecar on disk + logged) unless forced
        if not force and not only and base in done and \
                os.path.exists(os.path.join(TXT, stem + '.txt')):
            log.append(done[base])
            continue
        ext = ext.lower()
        if ext in ('.doc', '.docx'):
            text = doc_text(path)
            method, fmt = 'textutil', 'text'
        else:
            text = pdftotext(path)
            if len(text.strip()) >= MIN_TEXT:
                method, fmt = 'pdftotext -layout', 'text'
            else:
                text, note = ocr_pdf(path, stem)
                method, fmt = f'tesseract 5 OCR @300dpi ({note})', 'scanned'
        outp = os.path.join(TXT, stem + '.txt')
        with open(outp, 'w') as f:
            f.write(text)
        row = dict(file=base, sidecar=stem + '.txt', chars=len(text.strip()),
                   format=fmt, extraction_method=method)
        log.append(row)
        done[base] = row
        print(f'{base:32} {fmt:8} {len(text.strip()):>7} chars  {method}', flush=True)
        # persist the log after every file so a kill is resumable
        with open(logp0, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['file', 'sidecar', 'chars', 'format', 'extraction_method'])
            w.writeheader()
            for k in sorted(done):
                w.writerow(done[k])
    n_text = sum(1 for r in log if r['format'] == 'text')
    n_scan = sum(1 for r in log if r['format'] == 'scanned')
    print(f'\n{len(log)} sidecars: {n_text} born-digital, {n_scan} OCR')


if __name__ == '__main__':
    main()
