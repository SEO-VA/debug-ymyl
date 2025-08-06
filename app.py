#!/usr/bin/env python3
"""
Minimal JSON Extraction Test with Pure Fetch Detection and Detailed Logging

1. Extracts page content from a provided URL using BeautifulSoup.
2. Sends the extracted content to chunk.dejan.ai via Selenium.
3. Waits strictly for the 4th fetch (no timer fallback).
4. Copies all text following the "Raw JSON Output" header.
5. Signals run completion immediately after 4th fetch and extraction.
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import html
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

# Streamlit page config
st.set_page_config(page_title="JSON Fetch Test - Pure Detection", page_icon="🔍", layout="wide")


def extract_content_simple(url):
    """Scrape raw text content from the URL."""
    logger.debug(f"Extracting content from URL: {url}")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        text = soup.get_text(separator='\n')
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        content = "\n\n".join(lines)
        logger.info(f"Extracted {len(content)} characters of content")
        return content
    except Exception as e:
        logger.error(f"Content extraction failed: {e}")
        st.error(f"❌ Content extraction failed: {e}")
        return None


def setup_driver():
    """Initialize Chrome WebDriver with performance logs enabled."""
    logger.debug("Initializing Chrome WebDriver...")
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    logger.info("WebDriver started.")
    return driver


def wait_for_fourth_fetch(driver, endpoint="index.NJ4tUjPs809"):
    """Blocks until exactly 4 distinct fetch requests to the endpoint are observed."""
    logger.info("Waiting for 4th fetch (pure detection)...")
    fetch_count = 0
    seen = set()
    while fetch_count < 4:
        try:
            logs = driver.get_log('performance')
            for entry in logs:
                msg = str(entry)
                if endpoint in msg and 'fetch' in msg.lower():
                    tag = (entry.get('timestamp'), hash(msg))
                    if tag not in seen:
                        seen.add(tag)
                        fetch_count += 1
                        elapsed = time.time()
                        logger.info(f"Fetch {fetch_count}/4 detected")
                        st.write(f"🕵️ Fetch {fetch_count}/4 detected")
                        if fetch_count == 4:
                            return
        except WebDriverException as e:
            logger.warning(f"Error reading performance logs: {e}")
        time.sleep(0.3)


def extract_after_raw_header(driver):
    """Extracts all following sibling text after the Raw JSON Output header."""
    logger.info("Extracting text after 'Raw JSON Output' header...")
    try:
        siblings = driver.find_elements(By.XPATH,
            "//h3[normalize-space(text())='Raw JSON Output']/following-sibling::*")
        texts = [e.text.strip() for e in siblings if e.text.strip()]
        combined = html.unescape("\n\n".join(texts))
        logger.info(f"Extracted {len(combined)} characters after header.")
        st.write(f"✅ Extracted {len(combined)} chars after header.")
        return combined
    except WebDriverException as e:
        logger.error(f"Extraction failed: {e}")
        st.error(f"❌ Extraction failed: {e}")
        return None


def test_fetch_and_copy(url):
    # Step 1: Content extraction
    content = extract_content_simple(url)
    if not content:
        st.write("🏁 Run finished: no content extracted.")
        return None

    # Step 2: Launch browser
    st.write("🌐 Launching browser to chunk.dejan.ai...")
    driver = setup_driver()
    try:
        driver.get("https://chunk.dejan.ai/")
        st.write("✅ Page loaded")

        # Step 3: Send content
        textarea = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea'))
        )
        textarea.clear()
        textarea.send_keys(content[:5000])
        st.write(f"✅ Sent {min(len(content),5000)} chars to textarea")

        # Step 4: Click Generate
        btn = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="stBaseButton-secondary"]'))
        )
        driver.execute_script("arguments[0].click();", btn)
        st.write("✅ Generate clicked")

        # Step 5: Wait for 4th fetch
        wait_for_fourth_fetch(driver)

        # Step 6: Extract JSON
        result = extract_after_raw_header(driver)

        # Step 7: Completion signal
        if result:
            st.success("🎉 Run completed successfully!")
        else:
            st.warning("⚠️ Run completed but no JSON extracted.")
        st.write("🏁 Run finished.")
        return result

    finally:
        driver.quit()
        logger.info("Browser session closed.")


def main():
    st.title("🔍 JSON Fetch Test - Pure Detection")
    url = st.text_input("Enter URL:")
    if st.button("Run Test"):
        if not url:
            st.error("Please enter a URL.")
        else:
            result = test_fetch_and_copy(url)
            if result:
                st.text_area("Raw JSON Output:", value=result, height=400)

if __name__ == '__main__':
    main()
