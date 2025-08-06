#!/usr/bin/env python3
"""
Minimal JSON Extraction Test with Logging

Waits for the 4th fetch to complete, logs key steps, and copies
all text following the "Raw JSON Output" header.
"""

import streamlit as st
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import html
import time

# Configure logging to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(page_title="Minimal JSON Fetch Test", page_icon="🔍", layout="wide")


def setup_driver():
    logger.info("Setting up Chrome WebDriver...")
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    logger.info("WebDriver ready.")
    return driver


def wait_for_fourth_fetch(driver, endpoint="index.NJ4tUjPs809", timeout=180):
    logger.info("Waiting for 4 fetch requests to detect completion...")
    fetch_count = 0
    seen = set()
    start = time.time()
    while fetch_count < 4 and time.time() - start < timeout:
        for entry in driver.get_log('performance'):
            msg = str(entry)
            if endpoint in msg and 'fetch' in msg.lower():
                tag = (entry.get('timestamp'), hash(msg))
                if tag not in seen:
                    seen.add(tag)
                    fetch_count += 1
                    logger.info(f"Fetch {fetch_count}/4 detected")
                    st.write(f"🕵️ Fetch {fetch_count}/4 detected")
                    if fetch_count == 4:
                        logger.info("4th fetch detected, waiting 1s buffer...")
                        time.sleep(1)  # buffer
                        return True
        time.sleep(0.5)
    logger.warning("Did not detect 4 fetches within timeout, proceeding anyway...")
    st.warning("⏰ Did not detect 4 fetches within timeout, proceeding anyway...")
    return True


def extract_after_raw_header(driver):
    logger.info("Extracting text after 'Raw JSON Output' header...")
    try:
        header = driver.find_element(By.XPATH, "//h3[normalize-space(text())='Raw JSON Output']")
        elems = driver.find_elements(By.XPATH, "//h3[normalize-space(text())='Raw JSON Output']/following-sibling::*")
        texts = []
        for e in elems:
            txt = e.text.strip()
            if txt:
                texts.append(txt)
        combined = html.unescape("\n\n".join(texts))
        logger.info(f"Extracted {len(combined)} characters after header.")
        st.write(f"✅ Extracted {len(combined)} chars after header.")
        return combined
    except Exception as e:
        logger.error(f"Error extracting JSON: {e}")
        st.error(f"Error extracting JSON: {e}")
        return None


def test_fetch_and_copy(input_text):
    logger.info("Starting fetch-and-copy workflow...")
    st.write("🌐 Launching browser and navigating to chunk.dejan.ai...")
    driver = setup_driver()
    try:
        driver.get("https://chunk.dejan.ai/")
        logger.info("Page loaded, waiting 5 seconds for app initialization...")
        time.sleep(5)

        st.write("📝 Locating textarea and sending input...")
        textarea = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea'))
        )
        textarea.clear()
        textarea.send_keys(input_text)
        logger.info(f"Input sent ({len(input_text)} chars)")
        st.write(f"✅ Input sent ({len(input_text)} chars)")

        st.write("🚀 Clicking Generate button...")
        btn = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="stBaseButton-secondary"]'))
        )
        driver.execute_script("arguments[0].click();", btn)
        logger.info("Generate button clicked.")

        # Wait for fetch pattern
        wait_for_fourth_fetch(driver)

        st.write("🔍 Extracting JSON from page...")
        return extract_after_raw_header(driver)

    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        st.error(f"❌ Workflow failed: {e}")
        return None

    finally:
        driver.quit()
        logger.info("Browser closed.")


def main():
    st.title("🔍 Minimal JSON Fetch Test with Logs")
    st.markdown("Enter any text or URL to process and see logs of each step.")
    input_text = st.text_input("Input to chunk.dejan.ai:")
    if st.button("Run Test"):
        if not input_text:
            st.error("Please enter some text or URL.")
        else:
            result = test_fetch_and_copy(input_text)
            if result:
                st.text_area("Raw JSON Output:", value=result, height=400)

if __name__ == '__main__':
    main()
