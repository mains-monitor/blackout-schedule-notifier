#!/bin/bash

log() {
  local message="$1"
  echo "$(date '+%Y-%m-%d %H:%M:%S') [downloader] $message"
}

log "Starting downloader"

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

  mkdir -p in/
  mkdir -p out/
  mkdir -p group_logs/

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