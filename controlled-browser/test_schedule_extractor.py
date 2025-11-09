#!/usr/bin/env python3
"""
Automated test for extracting DisconSchedule.fact JSON from DTEK website.
This test uses Selenium WebDriver to control Chrome browser and extract JSON data.
"""

import json
import hashlib
import os
import re
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False


class ScheduleExtractor:
    """Extracts power outage schedule JSON from DTEK website using Chrome."""
    
    def __init__(self, headless=True, output_dir="."):
        """
        Initialize the schedule extractor.
        
        Args:
            headless: Run Chrome in headless mode (no GUI)
            output_dir: Directory to save extracted JSON files
        """
        self.url = "https://www.dtek-kem.com.ua/ua/shutdowns"
        self.output_dir = Path(output_dir)
        self.headless = headless
        self.driver = None
        
    def _setup_driver(self):
        """Configure and initialize Chrome WebDriver."""
        print(f"[{self._timestamp()}] Setting up Chrome WebDriver...")
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
            print(f"[{self._timestamp()}] Running in headless mode")
        
        # Additional Chrome options for stability and Docker compatibility
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        chrome_options.add_argument("--disable-software-rasterizer")
        
        # Check if running in Docker/Alpine with Chromium
        chromium_path = "/usr/bin/chromium-browser"
        chromedriver_path = "/usr/bin/chromedriver"
        
        if os.path.exists(chromium_path) and os.path.exists(chromedriver_path):
            # Using Chromium in Alpine
            print(f"[{self._timestamp()}] Using Chromium from Alpine")
            chrome_options.binary_location = chromium_path
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        elif WEBDRIVER_MANAGER_AVAILABLE:
            # Using Chrome with webdriver-manager
            print(f"[{self._timestamp()}] Using Chrome with webdriver-manager")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # Try using system chromedriver
            print(f"[{self._timestamp()}] Using system chromedriver")
            self.driver = webdriver.Chrome(options=chrome_options)
        
        self.driver.set_page_load_timeout(30)
        
        print(f"[{self._timestamp()}] Chrome WebDriver initialized successfully")
        
    def _timestamp(self):
        """Get formatted timestamp for logging."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _calculate_md5(self, content):
        """Calculate MD5 hash of content."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def extract_schedule_json(self):
        """
        Navigate to the website and extract DisconSchedule.fact JSON.
        
        Returns:
            dict: Extracted JSON data or None if extraction failed
        """
        try:
            print(f"[{self._timestamp()}] Navigating to {self.url}")
            self.driver.get(self.url)
            
            # Wait for page to load
            print(f"[{self._timestamp()}] Waiting for page to load...")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Give additional time for JavaScript to execute
            time.sleep(5)
            
            print(f"[{self._timestamp()}] Extracting page source...")
            page_source = self.driver.page_source

            # Dump page source to file for debugging
            debug_file = self.output_dir / f"page_source_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(page_source)
            print(f"[{self._timestamp()}] Page source saved to {debug_file.name}")
            
            # Extract DisconSchedule.fact using regex
            print(f"[{self._timestamp()}] Searching for DisconSchedule.fact...")
            pattern = r'DisconSchedule\.fact\s*=\s*(\{.*?\});?(\</script\>)'
            match = re.search(pattern, page_source, re.DOTALL)
            
            if not match:
                print(f"[{self._timestamp()}] ERROR: DisconSchedule.fact not found in page source")
                return None
            
            json_str = match.group(1)
            print(f"[{self._timestamp()}] DisconSchedule.fact extracted successfully")
            
            # Dump raw JSON string to file for debugging
            json_debug_file = self.output_dir / f"schedule_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_debug_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
            print(f"[{self._timestamp()}] Raw JSON saved to {json_debug_file.name}")

            # Parse JSON to validate
            try:
                json_data = json.loads(json_str)
                print(f"[{self._timestamp()}] JSON validation successful")
                return json_data
            except json.JSONDecodeError as e:
                print(f"[{self._timestamp()}] ERROR: Invalid JSON format: {e}")
                return None
                
        except Exception as e:
            print(f"[{self._timestamp()}] ERROR: Failed to extract schedule: {e}")
            return None
    
    def save_json(self, json_data):
        """
        Save JSON data to file with MD5 hash as filename.
        
        Args:
            json_data: Dictionary containing schedule data
            
        Returns:
            str: Path to saved file or None if file already exists
        """
        if json_data is None:
            print(f"[{self._timestamp()}] ERROR: No data to save")
            return None
        
        # Convert to JSON string for MD5 calculation
        json_str = json.dumps(json_data, ensure_ascii=False, separators=(',', ':'))
        
        # Calculate MD5 hash
        md5_hash = self._calculate_md5(json_str)
        safe_md5 = re.sub(r'[^a-f0-9]', '', md5_hash)
        
        # Create output file path
        output_file = self.output_dir / f"{safe_md5}.json"
        
        # Check if file already exists
        if output_file.exists():
            print(f"[{self._timestamp()}] File {output_file.name} already exists. Skipping save.")
            return None
        
        # Save JSON to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"[{self._timestamp()}] DisconSchedule.fact saved as {output_file.name}")
        return str(output_file)
    
    def run(self):
        """
        Main execution flow: setup driver, extract JSON, save to file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._setup_driver()
            json_data = self.extract_schedule_json()
            
            if json_data:
                saved_file = self.save_json(json_data)
                return saved_file is not None or json_data is not None
            
            return False
            
        except Exception as e:
            print(f"[{self._timestamp()}] ERROR: Execution failed: {e}")
            return False
            
        finally:
            if self.driver:
                print(f"[{self._timestamp()}] Closing Chrome WebDriver...")
                self.driver.quit()
                print(f"[{self._timestamp()}] Chrome WebDriver closed")


def main():
    """Entry point for the test."""
    print("=" * 70)
    print("Schedule Extractor Test - Starting")
    print("=" * 70)
    
    # Determine output directory (use /app/output in Docker, .. otherwise)
    output_dir = "/app/output" if os.path.exists("/app/output") else ".."
    
    # Initialize extractor
    # Set headless=False to see the browser in action
    extractor = ScheduleExtractor(headless=True, output_dir=output_dir)
    
    # Run extraction
    success = extractor.run()
    
    print("=" * 70)
    if success:
        print("Schedule Extractor Test - PASSED")
    else:
        print("Schedule Extractor Test - FAILED")
    print("=" * 70)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
