#!/usr/bin/env bash
# Phase 0 gate (CHAT_PLAN.md §4) — every check runs through curl against a
# running server.py, so what passes here is the same surface the browser and
# the agent will use. No API key, no spend.
#
#   python3 interface_prototype/server.py &
#   bash interface_prototype/verify_phase0.sh
#
# Exits non-zero if any gate fails.

set -uo pipefail
BASE="${BASE:-http://127.0.0.1:8787}"
PASS=0; FAIL=0

# check <name> <curl-args...> -- <python expression over `d` (parsed JSON) and `code`>
check() {
  local name="$1"; shift
  local expr="${!#}"; set -- "${@:1:$#-1}"
  local out code body
  out=$(curl -s -w '\n%{http_code}' "$@")
  code=$(printf '%s' "$out" | tail -n1)
  body=$(printf '%s' "$out" | sed '$d')
  local verdict
  verdict=$(CODE="$code" python3 -c '
import json, os, sys
body = sys.stdin.read()
code = int(os.environ["CODE"])
try:
    d = json.loads(body)
except Exception as e:
    print("FAIL|not JSON (%s): %s" % (e, body[:120])); raise SystemExit
try:
    ok = bool(eval(sys.argv[1]))
except Exception as e:
    print("FAIL|assertion raised %s: %s" % (type(e).__name__, e)); raise SystemExit
detail = d.get("reason") or d.get("error") or ""
print(("PASS|" if ok else "FAIL|") + "HTTP %d %s" % (code, str(detail)[:90]))
' "$expr" <<<"$body")
  if [[ "$verdict" == PASS* ]]; then
    PASS=$((PASS+1)); printf '  \033[32mPASS\033[0m  %-52s %s\n' "$name" "${verdict#PASS|}"
  else
    FAIL=$((FAIL+1)); printf '  \033[31mFAIL\033[0m  %-52s %s\n' "$name" "${verdict#FAIL|}"
  fi
}

q() { curl -s -X POST "$BASE/api/query" -H 'content-type: application/json' -d "$1"; }

echo
echo "Phase 0 gate — $BASE"
echo

echo "-- the six tools are exercisable over HTTP"
check "/api/health"      "$BASE/api/health" \
      'd["ok"] and d["entities"] == 44 and d["caveat_rows"] == 104 and code == 200'
check "/api/query"       -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"SELECT city, COUNT(*) n FROM motion GROUP BY city ORDER BY n DESC"}' \
      'd["row_count"] == 39 and d["rows"][0][0] == "utah_county" and code == 200'
check "/api/search"      "$BASE/api/search?q=%22accessory+dwelling%22&limit=3" \
      'd["result_count"] == 3 and all(r["path"] for r in d["results"]) and ">>" in d["results"][0]["passage"]'
check "/api/document"    "$BASE/api/document?path=CLAUDE.md&max_chars=300" \
      'd["chars_returned"] == 300 and d["truncated"] and d["next_offset"] == 300'
check "/api/schema"      "$BASE/api/schema?tables=caveat&counts=1" \
      'd["objects"][0]["rows"] == 104 and d["objects"][0]["columns"] == ["city","dataset","code","caveat"]'
check "/api/coverage"    "$BASE/api/coverage?entity=nephi" \
      'd["row_count"] == 2 and d["has_vote_db"] is True'
check "/api/entity"      "$BASE/api/entity?name=Salt+Lake" \
      'd["ambiguous"] and {c["slug"] for c in d["candidates"][:2]} == {"slc","salt_lake_county"} and "disambiguation" in d'

echo
echo "-- caveats arrive unbidden (the mechanism the design rests on)"
check "nephi count -> tally-only caveat" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"SELECT COUNT(*) AS motions FROM motion WHERE city='"'"'nephi'"'"'"}' \
      '"tally-only" in [c["code"] for c in d["caveats"]] and d["rows"][0][0] == 1319'
check "31-city sweep -> ceilings ranked first" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"SELECT city, COUNT(*) n FROM motion WHERE gov_level='"'"'city'"'"' GROUP BY city"}' \
      'd["caveat_count"] > 40 and d["caveats_truncated"] and {"tally-only","dissent-only","vote-ceiling"} <= {c["code"] for c in d["caveats"]}'
check "search result carries its entity caveats" "$BASE/api/search?q=zoning&entity=nephi&limit=2" \
      '"tally-only" in [c["code"] for c in d["caveats"]]'
check "read_document carries its entity caveats" \
      "$BASE/api/document?path=nephi_city_council/CLAUDE.md&max_chars=100" \
      'd["entity"] == "nephi" and "tally-only" in [c["code"] for c in d["caveats"]]'

echo
echo "-- the documented traps raise a note"
check "SUM(cf_filing) -> never-sum note" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"SELECT city, SUM(stated_total_contributions) FROM cf_filing GROUP BY city"}' \
      'any("NEVER sum cf_filing" in n for n in d["notes"])'
check "cross-tier provenance filter -> tier note" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"SELECT city, COUNT(*) FROM motion WHERE provenance='"'"'minutes'"'"' GROUP BY city"}' \
      'any("TWO vocabularies by tier" in n for n in d["notes"])'
check "raw result_raw across cities -> no-aggregate note" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"SELECT city, result_raw, COUNT(*) FROM motion GROUP BY city, result_raw"}' \
      'any("VERBATIM city-native labels" in n for n in d["notes"])'
check "MPO vote query -> empty-by-source note" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"SELECT COUNT(*) FROM vote WHERE city='"'"'wfrc_mpo'"'"'"}' \
      'd["rows"][0][0] == 0 and any("empty BY SOURCE" in n for n in d["notes"])'
check "same query, safe shape -> silent" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"SELECT city, COUNT(*) FROM motion WHERE gov_level='"'"'city'"'"' AND provenance='"'"'minutes'"'"' GROUP BY city"}' \
      'd["notes"] == []'

echo
echo "-- the guard holds"
check "DROP rejected" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"DROP TABLE motion"}' 'code == 400 and d["error"] == "rejected"'
check "ATTACH rejected" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"ATTACH DATABASE '"'"'/tmp/x.db'"'"' AS x"}' 'code == 400 and d["error"] == "rejected"'
check "multi-statement rejected" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"SELECT 1; DROP TABLE motion"}' \
      'code == 400 and "multiple statements" in d["reason"]'
check "comment-hidden 2nd statement rejected" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"SELECT 1 /* x */ ; DELETE FROM motion"}' \
      'code == 400 and "multiple statements" in d["reason"]'
check "PRAGMA rejected" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"PRAGMA table_info(motion)"}' 'code == 400 and d["error"] == "rejected"'
check "UPDATE rejected" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"UPDATE motion SET city='"'"'x'"'"'"}' 'code == 400 and d["error"] == "rejected"'
check "CREATE TABLE AS rejected" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"CREATE TABLE evil AS SELECT * FROM motion"}' 'code == 400 and d["error"] == "rejected"'
check "load_extension rejected" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"SELECT load_extension('"'"'/tmp/x.so'"'"')"}' 'code == 400 and d["error"] == "rejected"'
check "string containing DELETE still runs" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"SELECT COUNT(*) FROM fts_minutes WHERE fts_minutes MATCH '"'"'delete'"'"'"}' \
      'code == 200 and d["rows"][0][0] > 0'

echo
echo "-- caps hold and truncation is reported honestly"
check "200-row default cap" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"SELECT motion_id FROM motion"}' \
      'd["row_count"] == 200 and d["truncated"] and "row cap" in d["truncation_reason"]'
check "user LIMIT above cap is still capped" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"SELECT motion_id FROM motion LIMIT 5000"}' \
      'd["row_count"] == 200 and d["truncated"]'
check "limit param honoured up to the max" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"SELECT motion_id FROM motion","limit":5000}' \
      'd["row_count"] == 1000 and d["truncated"]'
check "exact-fit result is NOT flagged truncated" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"SELECT * FROM v_coverage WHERE city='"'"'nephi'"'"'"}' \
      'd["row_count"] == 2 and d["truncated"] is False'
check "byte cap on huge text rows" -X POST "$BASE/api/query" -H 'content-type: application/json' \
      -d '{"sql":"SELECT city, text FROM fts_minutes","limit":1000}' \
      'd["truncated"] and "byte cap" in d["truncation_reason"]'

echo
echo "-- read_document is confined to the repo"
check "parent-dir escape blocked"  "$BASE/api/document?path=../../../../etc/passwd" \
      'code == 403 and d["error"] == "outside_repo"'
check "absolute path escape blocked" "$BASE/api/document?path=/etc/passwd" \
      'code == 403 and d["error"] == "outside_repo"'
check "traversal through a real dir blocked" "$BASE/api/document?path=slc_city_council/../../etc/hosts" \
      'code == 403 and d["error"] == "outside_repo"'
check "binary refused"             "$BASE/api/document?path=gov.db" \
      'code == 415 and d["error"] == "not_text"'
check "missing file is honest"     "$BASE/api/document?path=nope/missing.md" \
      'code == 404 and d["error"] == "not_found"'

echo
echo "-- grep_repo reaches the layer FTS does not index"
check "finds repo documentation" "$BASE/api/grep?pattern=Never+fabricate&glob=CLAUDE.md&limit=5" \
      'd["match_count"] > 0 and d["matches"][0]["line_no"] > 0'
check "scoped grep carries entity caveats" \
      "$BASE/api/grep?pattern=tally-only&path=nephi_city_council&limit=3" \
      '"tally-only" in [c["code"] for c in d["caveats"]]'
check "a partial sweep says so" "$BASE/api/grep?pattern=the&limit=2" \
      'd["truncated"] is True and d["truncation_reason"] in ("limit","deadline","bytes")'
check "grep is confined to the repo" "$BASE/api/grep?pattern=root&path=/etc" \
      'code == 403 and d["error"] == "outside_repo"'
check "invalid regex rejected"    "$BASE/api/grep?pattern=(unclosed&regex=1" \
      'code == 400 and d["error"] == "rejected"'
check "empty pattern rejected"    "$BASE/api/grep?pattern=" \
      'code == 400 and d["error"] == "empty_query"'
check "matched lines are capped"  "$BASE/api/grep?pattern=a&limit=5" \
      'all(len(m["line"]) <= 420 for m in d["matches"])'

echo
echo "-- honest gaps report as properties, not errors"
check "db-less county coverage" "$BASE/api/coverage?entity=washington_county" \
      'd["has_vote_db"] is False and d["rows"][0]["dataset"] == "(no vote layer)"'
check "unknown entity is a clean 404" "$BASE/api/entity?name=Kanab" \
      'code == 404 and d["error"] == "no_match"'
check "unknown corpus is a clean 400" "$BASE/api/search?q=x&corpus=bogus" \
      'code == 400 and d["error"] == "bad_corpus"'
check "unknown endpoint lists the real ones" "$BASE/api/nope" \
      'code == 404 and "query" in d["endpoints"]'

echo
printf '  %d passed, %d failed\n\n' "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]]
