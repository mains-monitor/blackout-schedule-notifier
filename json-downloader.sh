#!/bin/bash

log() {
  local message="$1"
  echo "$(date '+%Y-%m-%d %H:%M:%S') [downloader] $message"
}

# Create necessary directories
mkdir -p ${INPUT_DIRECTORY}
mkdir -p ${OUTPUT_DIRECTORY}
mkdir -p ${GROUP_LOGS_DIRECTORY}

log "Downloading schedule JSON data"

# Download the HTML page
# Fetch raw JSON, then extract the "data" field (prefer jq, fallback to python3)
RAW_JSON=$(curl -sS "${SCHEDULE_SOURCE_URL}")
CURL_EXIT=$?
if [ $CURL_EXIT -ne 0 ]; then
    exit $CURL_EXIT
fi

if command -v jq >/dev/null 2>&1; then
    JSON_CONTENT=$(printf '%s' "$RAW_JSON" | jq -c '.fact // empty')
else
    JSON_CONTENT=$(printf '%s' "$RAW_JSON" | python3 -c 'import sys,json; obj=json.load(sys.stdin); d=obj.get("fact"); sys.stdout.write("" if d is None else json.dumps(d))' 2>/dev/null)
fi

if [ $? -ne 0 ]; then
    log "Failed to download JSON from ${SCHEDULE_SOURCE_URL}"
    exit 1
fi

if [ -z "$JSON_CONTENT" ]; then
    log "Failed to extract Schedule data from JSON"
    exit 1
fi

# Calculate MD5 checksum of the JSON content
MD5_SUM=$(echo "$JSON_CONTENT" | md5sum | awk '{print $1}')
SAFE_MD5=$(echo "$MD5_SUM" | tr -cd 'a-f0-9')

# Save JSON file
OUTPUT_FILE="${INPUT_DIRECTORY}/${SAFE_MD5}.json"

if [ -e "$OUTPUT_FILE" ]; then
    log "File $OUTPUT_FILE already exists. Run cleanup if needed."
    python src/main.py --input_dir "${INPUT_DIRECTORY}" --out_dir "${OUTPUT_DIRECTORY}" --src "$OUTPUT_FILE" --group_log "${GROUP_LOGS_DIRECTORY}" --mode cleanup
    exit 0
fi

echo "$JSON_CONTENT" > "$OUTPUT_FILE"
log "Schedule data saved as $OUTPUT_FILE"

# Process the JSON file if needed
log "Starting processing"
python src/main.py --input_dir "${INPUT_DIRECTORY}" --out_dir "${OUTPUT_DIRECTORY}" --src "$OUTPUT_FILE" --group_log "${GROUP_LOGS_DIRECTORY}" --mode json