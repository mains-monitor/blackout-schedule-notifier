#!/bin/bash

# Default mode is image downloading
MODE="images"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --html)
      MODE="html"
      shift
      ;;
    --images)
      MODE="images"
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--html|--images]"
      echo "  --html    Download HTML and extract DisconSchedule.fact as JSON"
      echo "  --images  Download schedule images (default)"
      exit 0
      ;;
    *)
      echo "Unknown option $1"
      exit 1
      ;;
  esac
done

log() {
  local message="$1"
  echo "$(date '+%Y-%m-%d %H:%M:%S') [downloader] $message"
}

log "Starting downloader in $MODE mode"

# Create necessary directories
mkdir -p in/
mkdir -p out/
mkdir -p group_logs/

if [ "$MODE" = "html" ]; then
  log "Downloading HTML and extracting DisconSchedule.fact"
  
  # Download the HTML page
  HTML_CONTENT=$(curl -s https://www.dtek-oem.com.ua/ua/shutdowns)
  
  if [ $? -ne 0 ]; then
    log "Failed to download HTML from https://www.dtek-oem.com.ua/ua/shutdowns"
    exit 1
  fi
  
  # Extract DisconSchedule.fact using the same method as before
  FACT_JSON=$(echo "$HTML_CONTENT" | grep -o 'DisconSchedule\.fact = {.*}' | sed 's/DisconSchedule\.fact = //')
  
  if [ -z "$FACT_JSON" ]; then
    log "Failed to extract DisconSchedule.fact from HTML"
    exit 1
  fi
  
  # Calculate MD5 checksum of the JSON content
  MD5_SUM=$(echo "$FACT_JSON" | md5sum | awk '{print $1}')
  SAFE_MD5=$(echo "$MD5_SUM" | tr -cd 'a-f0-9')
  
  # Save JSON file
  OUTPUT_FILE="in/${SAFE_MD5}.json"
  
  if [ -e "$OUTPUT_FILE" ]; then
    log "File $OUTPUT_FILE already exists. Do nothing."
    exit 0
  fi
  
  echo "$FACT_JSON" > "$OUTPUT_FILE"
  log "DisconSchedule.fact saved as $OUTPUT_FILE"
  
  # Process the JSON file if needed
  log "Starting processing"
  python src/main.py --input_dir in --out_dir out --src "$OUTPUT_FILE" --group_log group_logs --mode json
  
else
  # Original image downloading mode
  image_src=$(curl -s https://www.dtek-oem.com.ua/ua/shutdowns | grep picture | grep -oP '(?<=<img src=")[^"]*')

  IFS=$'\n' read -rd '' -a image_src_array <<<"$image_src"

  for image_src in "${image_src_array[@]}"; do
    absolute_image_src="https://www.dtek-oem.com.ua$image_src"
    log "Downloading file from $absolute_image_src"
    # Temporary file to hold the downloaded content
    TEMP_FILE=$(mktemp)
    # Download the file content using wget
    curl -s -o "$TEMP_FILE" "$absolute_image_src"

    if [ $? -ne 0 ]; then
      log "Failed to download file from $FILE_URL"
      continue
    fi

    # Calculate the MD5 checksum
    MD5_SUM=$(md5sum "$TEMP_FILE" | awk '{print $1}')

    # Sanitize the MD5 checksum for safe use as a filename (just in case)
    SAFE_MD5=$(echo "$MD5_SUM" | tr -cd 'a-f0-9')

    # Save the file with the sanitized MD5 checksum as the filename
    OUTPUT_FILE="in/${SAFE_MD5}.png"

    if [ -e "$OUTPUT_FILE" ]; then
        log "File $OUTPUT_FILE already exists. Do nothing."
        rm "$TEMP_FILE"
        continue
    fi

    mv "$TEMP_FILE" "$OUTPUT_FILE"
    log "File saved as $OUTPUT_FILE"
    log "Starting processing"
    python src/main.py --input_dir in --out_dir out --src "$OUTPUT_FILE" --group_log group_logs
  done
fi