#!/usr/bin/env python3
"""
JSON Extraction Methods Test App (Updated)

Tests different ways to extract complete JSON content from the
stCodeCopyButton element _and_ by selecting all text after the "Raw JSON Output" header
once the 4th fetch has been detected.
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import json
import html
import re
import time

# Page config
st.set_page_config(
    page_title="JSON Extraction Test",
    page_icon="🔍",
    layout="wide"
)


def extract_content_simple(url):
    """Quick content extraction for testing"""
    try:
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        text_content = soup.get_text()[:2000]
        return f"CONTENT: {text_content}"
    except:
        return "Test content for JSON extraction methods testing."


def setup_driver():
    """Setup Chrome driver with performance logging"""
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--single-process')
    options.add_argument('--window-size=1280,720')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(15)
    return driver


def wait_for_fourth_fetch(driver, endpoint="index.NJ4tUjPs809", timeout=180):
    """Detect 4 fetch requests to the given endpoint"""
    fetch_count = 0
    seen = set()
    start = time.time()
    while fetch_count < 4 and time.time() - start < timeout:
        try:
            for log in driver.get_log('performance'):
                msg = str(log)
                if endpoint in msg and 'fetch' in msg.lower():
                    tag = (log.get('timestamp'), hash(msg))
                    if tag not in seen:
                        seen.add(tag)
                        fetch_count += 1
                        st.write(f"🎯 Detected fetch {fetch_count}/4")
                        if fetch_count >= 4:
                            st.write("✅ 4th fetch complete, waiting 1s buffer...")
                            time.sleep(1)
                            return True
        except:
            pass
        time.sleep(0.5)
    st.warning("⏰ Timeout or fewer than 4 fetches detected, continuing anyway...")
    return True


def extract_after_raw_header(driver):
    """
    After the JSON has rendered, locate the <h3> with text "Raw JSON Output"
    and grab all following sibling elements' text.
    """
    try:
        header = driver.find_element(
            By.XPATH,
            "//h3[normalize-space(text())='Raw JSON Output']"
        )
        # Collect all following siblings
        siblings = driver.find_elements(
            By.XPATH,
            "//h3[normalize-space(text())='Raw JSON Output']/following-sibling::*"
        )
        full_text = []
        for elem in siblings:
            txt = elem.text
            if txt:
                full_text.append(txt)
        combined = "\n\n".join(full_text)
        return html.unescape(combined)
    except Exception as e:
        st.error(f"❌ Failed to extract after header: {e}")
        return None


def test_extraction_methods_workflow(url):
    st.write("🔍 Extracting content for testing...")
    content = extract_content_simple(url)
    st.success(f"Content ready: {len(content)} chars")

    st.write("🌐 Launching browser and processing...")
    driver = setup_driver()
    try:
        driver.get("https://chunk.dejan.ai/")
        time.sleep(8)
        wait = WebDriverWait(driver, 60)
        # Locate textarea with fallbacks
        input_field = None
        for by, sel in [
            (By.ID, "text_area_1"),
            (By.CSS_SELECTOR, 'textarea[aria-label="Text to chunk:"]'),
            (By.CSS_SELECTOR, 'textarea'),
        ]:
            try:
                input_field = wait.until(EC.presence_of_element_located((by, sel)))
                st.write(f"✅ Found input via {by} {sel}")
                break
            except TimeoutException:
                st.write(f"⚠️ No input with {by} {sel}")
        if not input_field:
            st.error("❌ Could not find input field, aborting.")
            return
        input_field.clear()
        input_field.send_keys(content[:1000])

        # Submit
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="stBaseButton-secondary"]')))
        submit.click()

        # Wait for fetch pattern
        wait_for_fourth_fetch(driver)

        # New: extract all text after Raw JSON Output
        raw_json_all = extract_after_raw_header(driver)
        if raw_json_all:
            st.write(f"✅ Extracted after header: {len(raw_json_all)} chars")
            st.download_button(
                "💾 Download Full Raw JSON Text",
                raw_json_all,
                f"raw_json_output_{int(time.time())}.txt",
                "text/plain"
            )
        else:
            st.warning("⚠️ No content extracted after header.")

        # Continue with other extraction tests if desired...

    except Exception as e:
        st.error(f"❌ Workflow failed: {e}")
    finally:
        driver.quit()


def main():
    st.title("🔍 JSON Extraction Methods Test (Updated)")
    st.markdown("**Now captures all text following the Raw JSON Output header.**")
    url = st.text_input("URL to test:")
    if st.button("Run Test"):
        if not url:
            st.error("Enter a URL first.")
        else:
            test_extraction_methods_workflow(url)

if __name__ == "__main__":
    main()
