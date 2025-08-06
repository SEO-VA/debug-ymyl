#!/usr/bin/env python3
"""
Content Processing Automation Project - JSON Extraction Test App (REVISED)

Purpose:
To systematically test multiple JSON retrieval methods from chunk.dejan.ai
and definitively identify the one that extracts the complete, non-truncated output.

This script directly addresses the hypotheses outlined in the project's final report.
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import json
import html
import re
import time
import pandas as pd

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="JSON Extraction Test",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 JSON Extraction Methods Test")
st.markdown("""
This application is designed to solve the **critical JSON incompleteness issue**.
It systematically runs multiple extraction methods after the 4th fetch request is detected,
allowing us to identify exactly which method can retrieve the full JSON payload.
""")

# --- Core Classes & Functions ---

def get_stable_chrome_options():
    """Returns a set of ultra-stable Chrome options for Streamlit Cloud."""
    chrome_options = Options()
    # Core stability flags from the main project report
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--single-process')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--window-size=1280,720')
    # Enable performance logging to monitor network requests (for 4-fetch detection)
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    return chrome_options

def setup_driver():
    """Initializes and returns a stable Selenium WebDriver instance."""
    try:
        driver = webdriver.Chrome(options=get_stable_chrome_options())
        driver.set_page_load_timeout(60)
        return driver
    except WebDriverException as e:
        st.error(f"❌ WebDriver Initialization Failed: {e}")
        st.error("This may be due to a problem with the chromium-driver in the Streamlit Cloud environment. Please try redeploying.")
        return None

def extract_test_content(url):
    """A simple content extractor for test purposes. Grabs up to 5000 chars."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # Use a larger content chunk to better simulate the real use case
        return soup.get_text(separator='\n', strip=True)[:5000]
    except requests.RequestException as e:
        st.warning(f"Could not fetch URL: {e}. Using default test content.")
        return "This is default test content used when a URL fails to load. It is designed to be long enough to trigger chunking and test JSON extraction methods thoroughly."

def wait_for_fourth_fetch(driver, status_placeholder):
    """
    Monitors network logs for the 4th fetch request to the processing endpoint,
    which indicates that processing is complete.
    """
    endpoint_pattern = "index.NJ4tUjPs809"
    fetch_count = 0
    seen_requests = set()
    max_wait_seconds = 180  # 3-minute timeout
    start_time = time.time()

    status_placeholder.info(f"⏳ Monitoring for 4 fetch requests to `{endpoint_pattern}`...")

    while fetch_count < 4:
        if time.time() - start_time > max_wait_seconds:
            status_placeholder.warning("⚠️ Timed out waiting for 4th fetch. Proceeding anyway.")
            return True # Assume it's done and proceed

        try:
            logs = driver.get_log('performance')
            for log_entry in logs:
                log_message = json.loads(log_entry['message'])['message']
                if (endpoint_pattern in log_message.get('params', {}).get('request', {}).get('url', '') and
                    log_message.get('method') == 'Network.responseReceived'):
                    
                    request_id = log_message.get('params', {}).get('requestId')
                    if request_id not in seen_requests:
                        seen_requests.add(request_id)
                        fetch_count += 1
                        status_placeholder.info(f"✅ Fetch request {fetch_count}/4 detected.")
        except (WebDriverException, json.JSONDecodeError):
            continue # Ignore errors reading logs, just try again

        if fetch_count >= 4:
            status_placeholder.success("🎯 4th fetch request detected! Processing is complete.")
            # Add the user-preferred buffer time
            status_placeholder.info("Applying 1.5-second buffer for DOM update...")
            time.sleep(1.5)
            return True

        time.sleep(0.2) # Poll every 200ms
    return False

def run_all_extraction_methods(driver):
    """
    Executes all 6 defined extraction methods and returns their results.
    """
    results = []
    
    def is_valid_json(data):
        if not data or not isinstance(data, str): return False
        try:
            json.loads(data)
            return True
        except json.JSONDecodeError:
            return False

    # --- Method 1: Standard Selenium `get_attribute` ---
    try:
        copy_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="stCodeCopyButton"]')
        raw_json = copy_button.get_attribute('data-clipboard-text')
        content = html.unescape(raw_json) if raw_json else ""
        results.append({'Method': '1. Standard get_attribute', 'Characters': len(content), 'Valid JSON': is_valid_json(content), 'Preview': content[:200] + '...'})
    except Exception as e:
        results.append({'Method': '1. Standard get_attribute', 'Characters': 0, 'Valid JSON': False, 'Preview': f'Error: {e}'})

    # --- Method 2: JavaScript `getAttribute` ---
    try:
        js_script = "return document.querySelector('[data-testid=\"stCodeCopyButton\"]').getAttribute('data-clipboard-text');"
        raw_json = driver.execute_script(js_script)
        content = html.unescape(raw_json) if raw_json else ""
        results.append({'Method': '2. JavaScript get_attribute', 'Characters': len(content), 'Valid JSON': is_valid_json(content), 'Preview': content[:200] + '...'})
    except Exception as e:
        results.append({'Method': '2. JavaScript get_attribute', 'Characters': 0, 'Valid JSON': False, 'Preview': f'Error: {e}'})

    # --- Method 3: Visible Output Area Extraction ---
    try:
        # The JSON is often displayed in a <pre> or <code> block for viewing
        output_area = driver.find_element(By.CSS_SELECTOR, 'pre > code')
        content = output_area.get_attribute('textContent')
        results.append({'Method': '3. Visible Output Area', 'Characters': len(content), 'Valid JSON': is_valid_json(content), 'Preview': content[:200] + '...'})
    except Exception as e:
        results.append({'Method': '3. Visible Output Area', 'Characters': 0, 'Valid JSON': False, 'Preview': f'Not found or error: {e}'})

    # --- Method 4: Page Source Regex ---
    try:
        page_source = driver.page_source
        # A specific regex to find the encoded JSON within the data-clipboard-text attribute
        match = re.search(r'data-clipboard-text="({.*?})"', page_source, re.DOTALL)
        raw_json = match.group(1) if match else ""
        content = html.unescape(raw_json) if raw_json else ""
        results.append({'Method': '4. Page Source Regex', 'Characters': len(content), 'Valid JSON': is_valid_json(content), 'Preview': content[:200] + '...'})
    except Exception as e:
        results.append({'Method': '4. Page Source Regex', 'Characters': 0, 'Valid JSON': False, 'Preview': f'Error: {e}'})
        
    # --- Method 5: Polling `getAttribute` ---
    try:
        copy_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="stCodeCopyButton"]')
        content = ""
        for i in range(5): # Poll 5 times over 2.5 seconds
            raw_json = copy_button.get_attribute('data-clipboard-text')
            temp_content = html.unescape(raw_json) if raw_json else ""
            if len(temp_content) > len(content):
                content = temp_content
            time.sleep(0.5)
        results.append({'Method': '5. Polling get_attribute', 'Characters': len(content), 'Valid JSON': is_valid_json(content), 'Preview': content[:200] + '...'})
    except Exception as e:
        results.append({'Method': '5. Polling get_attribute', 'Characters': 0, 'Valid JSON': False, 'Preview': f'Error: {e}'})

    # --- Method 6: Parent Element innerHTML (JS) ---
    try:
        js_script = "return document.querySelector('[data-testid=\"stCodeCopyButton\"]').parentElement.innerHTML;"
        inner_html = driver.execute_script(js_script)
        # The JSON is often inside the data-clipboard-text attribute within this HTML
        match = re.search(r'data-clipboard-text="({.*?})"', inner_html, re.DOTALL)
        raw_json = match.group(1) if match else ""
        content = html.unescape(raw_json) if raw_json else ""
        results.append({'Method': '6. Parent innerHTML (JS)', 'Characters': len(content), 'Valid JSON': is_valid_json(content), 'Preview': content[:200] + '...'})
    except Exception as e:
        results.append({'Method': '6. Parent innerHTML (JS)', 'Characters': 0, 'Valid JSON': False, 'Preview': f'Error: {e}'})

    return pd.DataFrame(results)

def main_workflow(url, status_placeholder, results_placeholder):
    """Orchestrates the entire test from setup to results display."""
    driver = None
    try:
        # Step 1: Get test content
        status_placeholder.info("📄 Extracting test content from URL...")
        content_to_process = extract_test_content(url)
        if not content_to_process:
            status_placeholder.error("❌ Could not get any content to test with.")
            return

        # Step 2: Setup Selenium WebDriver
        status_placeholder.info("🚀 Initializing secure browser instance...")
        driver = setup_driver()
        if not driver:
            # Error is already shown in setup_driver
            return

        # Step 3: Navigate and submit content to chunk.dejan.ai
        status_placeholder.info("🌐 Navigating to `chunk.dejan.ai`...")
        driver.get("https://chunk.dejan.ai/")
        wait = WebDriverWait(driver, 30)

        input_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[aria-label="Text to chunk:"]')))
        status_placeholder.info("✍️ Pasting content into text area...")
        input_field.send_keys(content_to_process)
        time.sleep(0.5) # Brief pause

        submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="stBaseButton-secondary"]')))
        submit_button.click()
        status_placeholder.info("🤖 Submitted content for processing.")

        # Step 4: Wait for processing to complete using the 4-fetch method
        processing_complete = wait_for_fourth_fetch(driver, status_placeholder)
        if not processing_complete:
            status_placeholder.error("❌ Processing did not complete within the time limit.")
            return

        # Step 5: Run all extraction tests
        status_placeholder.info("🔬 Running all 6 extraction methods...")
        results_df = run_all_extraction_methods(driver)
        status_placeholder.success("✅ All extraction tests complete!")

        # Step 6: Display results
        with results_placeholder.container():
            st.subheader("📊 Extraction Test Results")
            st.markdown("Compare the character count and validity. The highest character count for a valid JSON is the winner.")
            
            # Highlight the best valid result
            valid_results = results_df[results_df['Valid JSON'] == True]
            if not valid_results.empty:
                winner = valid_results.loc[valid_results['Characters'].idxmax()]
                st.success(f"🏆 **Winning Method: {winner['Method']}** with **{winner['Characters']}** characters.")

                def highlight_winner(row):
                    return ['background-color: #28a745; color: white'] * len(row) if row['Method'] == winner['Method'] else [''] * len(row)
                
                st.dataframe(results_df.style.apply(highlight_winner, axis=1), use_container_width=True)
            else:
                st.error("❌ No method was able to retrieve valid JSON.")
                st.dataframe(results_df, use_container_width=True)

    except TimeoutException as e:
        status_placeholder.error(f"❌ A timeout occurred: {e}. The target site `chunk.dejan.ai` might be slow or has changed its layout.")
    except Exception as e:
        status_placeholder.error(f"💥 An unexpected error occurred: {e}")
    finally:
        if driver:
            driver.quit()
            status_placeholder.info("🧹 Browser instance closed.")

# --- Streamlit UI ---

col1, col2 = st.columns([2, 1])
with col1:
    url_to_test = st.text_input(
        "Enter a URL to provide content for the test:",
        "https://www.google.com/about/our-story/",
        help="Content from this URL will be sent to chunk.dejan.ai for processing."
    )
    
    if st.button("🧪 Run Extraction Test", type="primary", use_container_width=True):
        if url_to_test:
            # Placeholders for dynamic updates
            status_placeholder = st.empty()
            results_placeholder = st.empty()
            with st.spinner("Test in progress..."):
                main_workflow(url_to_test, status_placeholder, results_placeholder)
        else:
            st.error("Please provide a URL.")
            
with col2:
    with st.expander("ℹ️ How This Test Works", expanded=True):
        st.markdown("""
        1.  **Content Fetch**: Grabs up to 5000 characters from the provided URL.
        2.  **Automation**: A headless browser navigates to `chunk.dejan.ai`, pastes the content, and clicks submit.
        3.  **Completion Detection**: It monitors network traffic and waits for the **4th fetch request**, confirming the backend processing is finished.
        4.  **Multi-Method Extraction**: It then immediately runs 6 different techniques to read the resulting JSON from the page.
        5.  **Analysis**: The results are displayed in a table, highlighting the most successful method. This will be the method implemented in the final application.
        """)
