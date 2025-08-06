#!/usr/bin/env python3
"""
Minimal JSON Extraction Test with Content Extraction and Verbose Selenium Logging

1. Extracts page content from a provided URL using BeautifulSoup.
2. Sends the extracted content to chunk.dejan.ai via Selenium.
3. Waits for the 4th fetch to complete, logs all key Selenium actions,
4. Copies all text following the "Raw JSON Output" header.
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
st.set_page_config(page_title="JSON Fetch Test w/ Extraction & Logs", page_icon="🔍", layout="wide")


def extract_content_simple(url):
    """Quickly scrape raw text content from the URL."""
    logger.debug(f"Extracting content from URL: {url}")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        # Simplest: all text, limited to avoid overload
        text = soup.get_text(separator='\n')
        # Collapse whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        content = "\n\n".join(lines)
        logger.info(f"Extracted {len(content)} characters of content")
        return content
    except Exception as e:
        logger.error(f"Content extraction failed: {e}")
        st.error(f"❌ Content extraction failed: {e}")
        return None


def setup_driver():
    logger.debug("Initializing Chrome WebDriver with performance & browser logs...")
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL', 'browser': 'ALL'})
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    logger.info("WebDriver started successfully.")
    return driver


def log_browser_console(driver):
    """Retrieve and log browser console entries."""
    try:
        for entry in driver.get_log('browser'):
            level = entry.get('level')
            msg = entry.get('message')
            logger.debug(f"Browser console [{level}]: {msg}")
    except Exception as e:
        logger.warning(f"Could not retrieve browser console logs: {e}")


def wait_for_fourth_fetch(driver, endpoint="index.NJ4tUjPs809", timeout=180):
    logger.debug("Starting fetch detection loop...")
    fetch_count = 0
    seen = set()
    start = time.time()
    while fetch_count < 4 and time.time() - start < timeout:
        try:
            for entry in driver.get_log('performance'):
                msg = str(entry)
                if endpoint in msg and 'fetch' in msg.lower():
                    tag = (entry.get('timestamp'), hash(msg))
                    if tag not in seen:
                        seen.add(tag)
                        fetch_count += 1
                        elapsed = time.time() - start
                        logger.info(f"Fetch {fetch_count}/4 detected at {elapsed:.1f}s")
                        st.write(f"🕵️ Fetch {fetch_count}/4 detected ({elapsed:.1f}s)")
                        if fetch_count == 4:
                            logger.debug("4th fetch detected, applying 1s buffer...")
                            time.sleep(1)
                            return True
        except WebDriverException as e:
            logger.warning(f"Error reading performance logs: {e}")
        time.sleep(0.5)
    logger.warning("Timeout reached or fewer than 4 fetches; proceeding anyway...")
    st.warning("⏰ Did not detect 4 fetches; proceeding anyway...")
    return True


def extract_after_raw_header(driver):
    logger.debug("Locating 'Raw JSON Output' header...")
    try:
        header = driver.find_element(By.XPATH, "//h3[normalize-space(text())='Raw JSON Output']")
        logger.info("Header found; extracting subsequent content...")
        siblings = driver.find_elements(By.XPATH, "//h3[normalize-space(text())='Raw JSON Output']/following-sibling::*")
        texts = [e.text.strip() for e in siblings if e.text.strip()]
        combined = html.unescape("\n\n".join(texts))
        logger.info(f"Extracted {len(combined)} chars after header")
        st.write(f"✅ Extracted {len(combined)} chars after header.")
        return combined
    except WebDriverException as e:
        logger.error(f"Extraction after header failed: {e}")
        st.error(f"❌ Extraction failed: {e}")
        return None


def test_fetch_and_copy(url):
    # 1. Content extraction
    content = extract_content_simple(url)
    if not content:
        return None

    # 2. Launch browser
    st.write("🌐 Launching browser and navigating to chunk.dejan.ai...")
    driver = setup_driver()
    try:
        driver.get("https://chunk.dejan.ai/")
        logger.info("Navigated to chunk.dejan.ai; waiting 5s for load...")
        time.sleep(5)
        log_browser_console(driver)

        # 3. Input content
        st.write("📝 Sending extracted content to Streamlit app...")
        textarea = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea'))
        )
        textarea.clear()
        textarea.send_keys(content[:5000])
        logger.info(f"Sent {len(content[:5000])} chars to textarea")
        st.write(f"✅ Content sent ({min(len(content),5000)} chars)")

        # 4. Click generate
        st.write("🚀 Clicking Generate button...")
        btn = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="stBaseButton-secondary"]'))
        )
        driver.execute_script("arguments[0].click();", btn)
        logger.info("Generate clicked via JS")
        st.write("✅ Generate clicked")

        # 5. Wait for 4th fetch
        wait_for_fourth_fetch(driver)
        log_browser_console(driver)

        # 6. Extract JSON output
        st.write("🔍 Extracting JSON output from page...")
        return extract_after_raw_header(driver)

    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        st.error(f"❌ Workflow failed: {e}")
        return None

    finally:
        driver.quit()
        logger.info("Browser session ended.")


def main():
    st.title("🔍 JSON Fetch Test with Extraction & Logs")
    st.markdown("Provide a URL to scrape and see detailed logs through the process.")
    url = st.text_input("URL to process:")
    if st.button("Run Test"):
        if not url:
            st.error("Enter a URL first.")
        else:
            result = test_fetch_and_copy(url)
            if result:
                st.text_area("Raw JSON Output:", value=result, height=400)

if __name__ == '__main__':
    main()
