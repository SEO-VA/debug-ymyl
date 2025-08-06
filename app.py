#!/usr/bin/env python3
"""
Minimal JSON Extraction Test with Header-Based Detection and Detailed Logging

1. Extracts page content from a provided URL using BeautifulSoup.
2. Sends the extracted content to chunk.dejan.ai via Selenium.
3. Waits for the "Raw JSON Output" <h3> header to appear (no fetch detection).
4. Copies all text following the header.
5. Signals run completion immediately after extraction.
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
from selenium.common.exceptions import TimeoutException, WebDriverException
import html
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

# Streamlit page config
st.set_page_config(page_title="JSON Fetch Test - Header Detection", page_icon="🔍", layout="wide")


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
    """Initialize Chrome WebDriver."""
    logger.debug("Starting Chrome WebDriver...")
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    logger.info("WebDriver started.")
    return driver


def extract_after_raw_header(driver):
    """
    Poll until the Raw JSON Output header appears, then extract following sibling text.
    No fixed timeout; checks every 0.5 seconds until found.
    """
    logger.info("Polling for 'Raw JSON Output' header...")
    # Continuously poll for the header element
    while True:
        try:
            header = driver.find_element(
                By.XPATH,
                "//h3[normalize-space(text())='Raw JSON Output']"
            )
            logger.info("Header detected, extracting content...")
            break
        except WebDriverException:
            # Header not yet present; wait and retry
            time.sleep(0.5)
            continue
    # Once found, grab all following siblings
    siblings = driver.find_elements(
        By.XPATH,
        "//h3[normalize-space(text())='Raw JSON Output']/following-sibling::*"
    )
    texts = [e.text.strip() for e in siblings if e.text.strip()]
    combined = html.unescape("

".join(texts)))
        return None

    # 2. Launch browser
    st.write("🌐 Launching browser to chunk.dejan.ai...")
    driver = setup_driver()
    try:
        driver.get("https://chunk.dejan.ai/")
        st.write("✅ Page loaded")

        # 3. Send content
        textarea = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea'))
        )
        textarea.clear()
        textarea.send_keys(content[:5000])
        st.write(f"✅ Sent {min(len(content),5000)} chars to textarea")

        # 4. Click Generate
        btn = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="stBaseButton-secondary"]'))
        )
        driver.execute_script("arguments[0].click();", btn)
        st.write("✅ Generate clicked")

        # 5. Wait for header and extract
        result = extract_after_raw_header(driver)

        # 6. Completion signal
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
    st.title("🔍 JSON Fetch Test - Header Detection")
    url = st.text_input("Enter URL:")
    if st.button("Run Test"):
        if not url:
            st.error("Please enter a URL.")
        else:
            result = test_header_based_extraction(url)
            if result:
                st.text_area("Raw JSON Output:", value=result, height=400)

if __name__ == '__main__':
    main()
