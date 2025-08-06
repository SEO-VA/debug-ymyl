#!/usr/bin/env python3
"""
Minimal JSON Extraction Test

Only waits for the 4th fetch to complete and then copies
all text following the "Raw JSON Output" header.
"""

import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import html
import time

# Page config
st.set_page_config(page_title="Minimal JSON Fetch Test", page_icon="🔍", layout="wide")


def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    # enable performance logs for fetch detection
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver


def wait_for_fourth_fetch(driver, endpoint="index.NJ4tUjPs809", timeout=180):
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
                    st.write(f"🕵️ Fetch {fetch_count}/4 detected")
                    if fetch_count == 4:
                        time.sleep(1)  # buffer
                        return True
        time.sleep(0.5)
    st.warning("⏰ Did not detect 4 fetches within timeout, proceeding anyway...")
    return True


def extract_after_raw_header(driver):
    try:
        # find the Raw JSON Output header
        header = driver.find_element(By.XPATH, "//h3[normalize-space(text())='Raw JSON Output']")
        # grab all siblings after header
        elems = driver.find_elements(By.XPATH, "//h3[normalize-space(text())='Raw JSON Output']/following-sibling::*")
        texts = [e.text for e in elems if e.text]
        return html.unescape("\n\n".join(texts))
    except Exception as e:
        st.error(f"Error extracting JSON: {e}")
        return None


def test_fetch_and_copy(url):
    driver = setup_driver()
    try:
        driver.get("https://chunk.dejan.ai/")
        time.sleep(5)

        # input area
        textarea = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea'))
        )
        textarea.clear()
        textarea.send_keys(url)  # feed URL directly

        # click generate
        btn = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="stBaseButton-secondary"]'))
        )
        driver.execute_script("arguments[0].click();", btn)

        # wait for fetches
        wait_for_fourth_fetch(driver)

        # extract JSON
        return extract_after_raw_header(driver)
    finally:
        driver.quit()


def main():
    st.title("🔍 Minimal JSON Fetch Test")
    url = st.text_input("Enter text or URL to send to chunk.dejan.ai:")
    if st.button("Run Test"):
        if not url:
            st.error("Please enter something to process.")
        else:
            result = test_fetch_and_copy(url)
            if result:
                st.text_area("Raw JSON Output:", value=result, height=400)

if __name__ == '__main__':
    main()
