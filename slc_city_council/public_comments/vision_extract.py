#!/usr/bin/env python3
"""
Phase 1: Extract public comments from PDF pages using Claude Vision API.

Renders each page as an image, sends to Claude via the Message Batches API,
and saves structured JSON output per PDF.

Usage:
    python3 vision_extract.py                    # Full batch run
    python3 vision_extract.py --force            # Ignore previous progress
    python3 vision_extract.py --file 2024/05082024_05142024.pdf  # Single file
    python3 vision_extract.py --year 2024        # Single year
"""

import argparse
import base64
import io
import json
import os
import sys
import time
from pathlib import Path

import anthropic
import pypdfium2 as pdfium
from PIL import Image

from config import (
    BASE_DIR, PROGRESS_DIR, RAW_DIR, PROGRESS_FILE,
    MODEL, MAX_TOKENS, RENDER_SCALE, JPEG_QUALITY, MAX_IMAGE_DIM, SYSTEM_PROMPT,
)


def discover_pdfs(year_filter=None, file_filter=None):
    """Find all PDFs to process, sorted by year/filename."""
    pdfs = []
    for year_dir in sorted(BASE_DIR.iterdir()):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        if year_filter and year_dir.name != str(year_filter):
            continue
        for pdf_path in sorted(year_dir.glob("*.pdf")):
            rel = f"{year_dir.name}/{pdf_path.name}"
            if file_filter and rel != file_filter:
                continue
            pdfs.append((rel, pdf_path))
    return pdfs


def get_page_count(pdf_path):
    """Get the number of pages in a PDF."""
    pdf = pdfium.PdfDocument(str(pdf_path))
    n = len(pdf)
    pdf.close()
    return n


def render_page_to_base64(pdf_path, page_idx):
    """Render a single PDF page to a base64-encoded JPEG."""
    pdf = pdfium.PdfDocument(str(pdf_path))
    page = pdf[page_idx]
    bitmap = page.render(scale=RENDER_SCALE)
    pil_image = bitmap.to_pil()
    pdf.close()

    # Downscale so the long edge fits the API limit (and matches its internal
    # downscale). Oversized pages (e.g. 8064px) otherwise raise invalid_request.
    longest = max(pil_image.size)
    if longest > MAX_IMAGE_DIM:
        ratio = MAX_IMAGE_DIM / longest
        new_size = (round(pil_image.size[0] * ratio), round(pil_image.size[1] * ratio))
        pil_image = pil_image.resize(new_size, Image.LANCZOS)

    buf = io.BytesIO()
    pil_image.save(buf, format="JPEG", quality=JPEG_QUALITY)
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def load_progress():
    """Load existing progress or return empty state."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"batch_id": None, "completed_pages": {}}


def save_progress(progress):
    """Save progress state."""
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def is_page_done(progress, rel_path, page_idx):
    """Check if a specific page has already been successfully processed."""
    status = progress.get("completed_pages", {}).get(rel_path, {}).get(str(page_idx))
    return status == "done"


def save_raw_result(rel_path, page_idx, result_data):
    """Save a single page's result to the raw JSON file for that PDF."""
    year = rel_path.split("/")[0]
    stem = Path(rel_path).stem
    out_dir = RAW_DIR / year
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{stem}.json"

    if out_file.exists():
        with open(out_file) as f:
            data = json.load(f)
    else:
        data = {"source_file": rel_path, "pages": {}}

    data["pages"][str(page_idx)] = result_data

    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)


def build_batch_requests(pdfs, progress, force=False):
    """Build the list of batch API requests for all pages."""
    requests = []
    total_pages = 0
    skipped = 0

    for rel_path, pdf_path in pdfs:
        n_pages = get_page_count(pdf_path)
        year = rel_path.split("/")[0]
        filename = Path(rel_path).name

        for page_idx in range(n_pages):
            total_pages += 1

            if not force and is_page_done(progress, rel_path, page_idx):
                skipped += 1
                continue

            print(f"  Rendering {rel_path} page {page_idx + 1}/{n_pages}...", end="\r")
            image_b64 = render_page_to_base64(pdf_path, page_idx)

            # custom_id must match ^[a-zA-Z0-9_-]{1,64}$
            safe_id = rel_path.replace("/", "_").replace(".pdf", "")
            custom_id = f"{safe_id}_p{page_idx}"
            requests.append({
                "custom_id": custom_id,
                "params": {
                    "model": MODEL,
                    "max_tokens": MAX_TOKENS,
                    "system": SYSTEM_PROMPT,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": (
                                    f"Extract all public comment rows from this page. "
                                    f"Source: {filename}, page {page_idx + 1} of {n_pages}, year {year}."
                                ),
                            },
                        ],
                    }],
                },
            })

    print(f"\nTotal pages: {total_pages}, to process: {len(requests)}, skipped (already done): {skipped}")
    return requests


def submit_batch(client, requests):
    """Submit a batch of requests to the Anthropic Batches API with retry."""
    print(f"Submitting batch with {len(requests)} requests...")
    for attempt in range(3):
        try:
            batch = client.messages.batches.create(
                requests=requests,
                timeout=600.0,  # 10 min timeout for large payloads
            )
            print(f"Batch submitted: {batch.id}")
            print(f"Status: {batch.processing_status}")
            return batch
        except (anthropic.APIConnectionError, anthropic.APITimeoutError, anthropic.InternalServerError) as e:
            if attempt < 2:
                wait = 30 * (attempt + 1)
                print(f"\n  Connection error, retrying in {wait}s... ({e})")
                time.sleep(wait)
            else:
                raise


def fix_unescaped_quotes(s):
    """
    Re-escape double-quotes that appear *inside* JSON string values.

    Long verbatim comment text often contains quotes (e.g. the "rule of law")
    that the model leaves unescaped, breaking json.loads. A quote is treated as
    structural if, scanning the value, the next non-space char after it is one of
    , : } ]  (i.e. it closes the string); otherwise it is an interior quote and
    gets escaped. Handles the common case well; genuinely ambiguous text is rare.
    """
    out = []
    i, n, in_str = 0, len(s), False
    while i < n:
        ch = s[i]
        if not in_str:
            out.append(ch)
            if ch == '"':
                in_str = True
        else:
            if ch == "\\" and i + 1 < n:
                out.append(ch)
                out.append(s[i + 1])
                i += 2
                continue
            if ch == '"':
                j = i + 1
                while j < n and s[j] in " \t\r\n":
                    j += 1
                if j >= n or s[j] in ",:}]":
                    out.append('"')
                    in_str = False
                else:
                    out.append('\\"')   # interior quote -> escape
            else:
                out.append(ch)
        i += 1
    return "".join(out)


def poll_batch(client, batch_id):
    """Poll for batch completion."""
    print(f"Polling batch {batch_id}...")
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        counts = batch.request_counts
        total = counts.processing + counts.succeeded + counts.errored + counts.canceled + counts.expired
        done = counts.succeeded + counts.errored + counts.canceled + counts.expired
        print(
            f"  Status: {batch.processing_status} | "
            f"Done: {done}/{total} | "
            f"Succeeded: {counts.succeeded} | "
            f"Errored: {counts.errored}",
            end="\r",
        )
        if batch.processing_status == "ended":
            print()
            return batch
        time.sleep(60)


def process_batch_results(client, batch_id, progress):
    """Download and parse results from a completed batch."""
    succeeded = 0
    failed = 0
    table_pages = 0
    non_table_pages = 0
    total_comments = 0

    for result in client.messages.batches.results(batch_id):
        custom_id = result.custom_id
        # Parse "2020_filename_p0" back to rel_path and page_idx
        # Format: {year}_{stem}_p{page_idx}
        parts = custom_id.rsplit("_p", 1)
        page_idx = int(parts[1])
        id_part = parts[0]
        # Reconstruct: "2020_filename" -> "2020/filename.pdf"
        year = id_part[:4]
        stem = id_part[5:]
        rel_path = f"{year}/{stem}.pdf"

        if result.result.type == "succeeded":
            response_text = result.result.message.content[0].text

            # Parse JSON response
            text = response_text.strip()
            # Strip markdown fences if Claude added them
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None

                # Strategy 0: re-escape unescaped quotes inside comment text
                # (the most common failure on long verbatim comments).
                try:
                    parsed = json.loads(fix_unescaped_quotes(text))
                    print(f"\n  REPAIRED unescaped quotes for {custom_id}")
                except json.JSONDecodeError:
                    pass

                # Strategy 1: repair truncated JSON (output hit max_tokens) by
                # closing after the last complete comment object "}, {".
                last_complete = text.rfind("},")
                if not parsed and last_complete > 0:
                    repaired = text[:last_complete + 1] + "]}"
                    try:
                        parsed = json.loads(repaired)
                        print(f"\n  REPAIRED truncated JSON for {custom_id} (dropped last partial comment)")
                    except json.JSONDecodeError:
                        pass

                # Strategy 2: Close the last truncated comment with [TRUNCATED] marker
                if not parsed:
                    import re
                    last_quote = text.rfind('"')
                    if last_quote > 0:
                        patched = (text[:last_quote] + ' [TRUNCATED]"'
                                   + ', "has_attachment": false, "is_continuation": false,'
                                   + ' "is_partial": true, "continuation_marker": ""'
                                   + '}]}')
                        try:
                            parsed = json.loads(patched)
                            print(f"\n  SALVAGED truncated comment for {custom_id}")
                        except json.JSONDecodeError:
                            pass

                if not parsed:
                    print(f"\n  WARN: Unparseable JSON for {custom_id}, saving raw text")
                    parsed = {
                        "page_type": "error",
                        "columns_detected": [],
                        "comments": [],
                        "_raw_text": response_text[:20000],
                    }
                    failed += 1
                    save_raw_result(rel_path, page_idx, parsed)
                    continue

            save_raw_result(rel_path, page_idx, parsed)

            # Track stats
            if parsed.get("page_type") == "table":
                table_pages += 1
                n_comments = len(parsed.get("comments", []))
                total_comments += n_comments
            else:
                non_table_pages += 1

            # Update progress
            if rel_path not in progress["completed_pages"]:
                progress["completed_pages"][rel_path] = {}
            progress["completed_pages"][rel_path][str(page_idx)] = "done"

            succeeded += 1
        else:
            error_type = result.result.type
            print(f"\n  ERROR: {custom_id} -> {error_type}")
            failed += 1

    save_progress(progress)

    print(f"\nResults processed:")
    print(f"  Succeeded:     {succeeded}")
    print(f"  Failed:        {failed}")
    print(f"  Table pages:   {table_pages}")
    print(f"  Non-table:     {non_table_pages}")
    print(f"  Comments:      {total_comments}")

    return succeeded, failed


def main():
    parser = argparse.ArgumentParser(description="Extract public comments using Claude Vision")
    parser.add_argument("--force", action="store_true", help="Ignore previous progress")
    parser.add_argument("--file", type=str, help="Process single PDF (e.g., 2024/05082024_05142024.pdf)")
    parser.add_argument("--year", type=str, help="Process single year (e.g., 2024)")
    args = parser.parse_args()

    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        print("Run: export ANTHROPIC_API_KEY='sk-ant-...'")
        sys.exit(1)

    client = anthropic.Anthropic()

    # Discover PDFs
    pdfs = discover_pdfs(year_filter=args.year, file_filter=args.file)
    print(f"Found {len(pdfs)} PDFs to process")

    if not pdfs:
        print("No PDFs found matching filters.")
        sys.exit(0)

    # Load or reset progress
    if args.force:
        progress = {"batch_id": None, "completed_pages": {}}
    else:
        progress = load_progress()

    # Check if we have an active batch to resume
    if progress.get("batch_id") and not args.force:
        batch_id = progress["batch_id"]
        print(f"Found existing batch: {batch_id}")
        batch = client.messages.batches.retrieve(batch_id)

        if batch.processing_status != "ended":
            print("Batch still processing, polling...")
            batch = poll_batch(client, batch_id)

        print("Processing batch results...")
        process_batch_results(client, batch_id, progress)

        # Clear batch_id so we can submit a new batch for remaining pages
        progress["batch_id"] = None
        save_progress(progress)

    # Build requests for any remaining pages
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    requests = build_batch_requests(pdfs, progress, force=args.force)

    if not requests:
        print("All pages already processed. Use --force to reprocess.")
        print("\nDone! Run merge_vision_output.py to generate the unified CSV.")
        return

    # Submit in chunks to avoid payload size limits
    CHUNK_SIZE = 250  # ~250 pages per batch to keep payload manageable
    for chunk_start in range(0, len(requests), CHUNK_SIZE):
        chunk = requests[chunk_start:chunk_start + CHUNK_SIZE]
        chunk_num = chunk_start // CHUNK_SIZE + 1
        total_chunks = (len(requests) + CHUNK_SIZE - 1) // CHUNK_SIZE

        if total_chunks > 1:
            print(f"\n--- Chunk {chunk_num}/{total_chunks} ({len(chunk)} requests) ---")

        batch = submit_batch(client, chunk)
        progress["batch_id"] = batch.id
        save_progress(progress)

        # Poll for completion
        batch = poll_batch(client, batch.id)

        # Process results
        process_batch_results(client, batch.id, progress)

        # Clear batch_id before next chunk
        progress["batch_id"] = None
        save_progress(progress)

    print("\nDone! Run merge_vision_output.py to generate the unified CSV.")


if __name__ == "__main__":
    main()
