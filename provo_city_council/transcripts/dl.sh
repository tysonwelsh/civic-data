#!/bin/bash
cd "$(dirname "$0")"
first=1
while read -r date body vid; do
  [ -z "$vid" ] && continue
  if [ $first -eq 0 ]; then sleep 35; fi
  first=0
  echo "=== $date $body $vid ===" >> dl_progress.log
  yt-dlp --js-runtimes node --write-auto-sub --sub-lang en-orig --sub-format vtt \
    --skip-download -o "raw/%(id)s" "https://www.youtube.com/watch?v=$vid" \
    >> dl_progress.log 2>&1
  echo "exit=$? for $vid" >> dl_progress.log
done < sample.txt
echo "ALL_DONE" >> dl_progress.log
