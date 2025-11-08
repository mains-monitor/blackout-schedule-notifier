# Controlled Browser Test

This directory contains an automated test that uses Selenium WebDriver to control Google Chrome and extract the power outage schedule JSON from the website.

## Features

- **Automated Browser Control**: Uses Selenium WebDriver to control Chrome
- **JSON Extraction**: Extracts `DisconSchedule.fact` JSON from the website
- **MD5 Verification**: Saves files with MD5 hash to avoid duplicates
- **Headless Mode**: Can run with or without GUI
- **Logging**: Detailed timestamped logs for debugging

## Installation

Install the required dependencies:

```bash
cd controlled-browser
pip install -r requirements.txt
```

## Usage

### Run the test (headless mode):

```bash
python test_schedule_extractor.py
```

### Run with visible browser (for debugging):

Edit `test_schedule_extractor.py` and change:
```python
extractor = ScheduleExtractor(headless=False, output_dir="..")
```

## How it works

1. **Setup**: Initializes Chrome WebDriver with appropriate options
2. **Navigate**: Opens the website
3. **Wait**: Waits for the page to fully load
4. **Extract**: Uses regex to find `DisconSchedule.fact` in page source
5. **Validate**: Parses JSON to ensure it's valid
6. **Save**: Saves to file with MD5 hash as filename
7. **Cleanup**: Closes the browser

## Output

The extracted JSON files are saved in the parent directory with MD5 hash as filename:
- Format: `{md5_hash}.json`
- Example: `7c4886495959ac272346046ddd1fbbff.json`

## Requirements

- Python 3.7+
- Google Chrome browser installed
- Internet connection
