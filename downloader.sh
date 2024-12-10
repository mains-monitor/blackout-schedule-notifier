#!/bin/bash

image_src=$(curl -s https://www.dtek-oem.com.ua/ua/shutdowns | grep picture | grep -oP '(?<=<img src=")[^"]*')
absolute_image_src="https://www.dtek-oem.com.ua$image_src"
# Temporary file to hold the downloaded content
TEMP_FILE=$(mktemp)

# Download the file content using wget
curl -s -o "$TEMP_FILE" "$absolute_image_src"

if [ $? -ne 0 ]; then
  echo "Failed to download file from $FILE_URL"
  exit 1
fi

# Calculate the MD5 checksum
MD5_SUM=$(md5sum "$TEMP_FILE" | awk '{print $1}')

# Sanitize the MD5 checksum for safe use as a filename (just in case)
SAFE_MD5=$(echo "$MD5_SUM" | tr -cd 'a-f0-9')

mkdir -p in/

# Save the file with the sanitized MD5 checksum as the filename
OUTPUT_FILE="in/${SAFE_MD5}.png"

if [ -e "$OUTPUT_FILE" ]; then
    echo "File exists. Do nothing."
    rm "$TEMP_FILE"
    exit 0
fi

mv "$TEMP_FILE" "$OUTPUT_FILE"

echo "File saved as $OUTPUT_FILE"