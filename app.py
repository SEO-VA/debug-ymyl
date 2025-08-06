#!/usr/bin/env python3
"""
Content Processing Automation Project - Initial Page State Test

Purpose:
To load chunk.dejan.ai, capture the initial page HTML as seen by Selenium,
and check if the 'Raw JSON Output' heading is present on landing,
WITHOUT submitting any content.
"""

import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import time

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Initial Page State Test",
    page_icon="🔎",
    layout="wide",
)

st.title("🔎 Initial Page State & H3 Detection")
st.markdown("""
This test simply loads `chunk.dejan.ai`, waits 10 seconds, and then shows you exactly what HTML Selenium sees.
It then checks if `<h3>Raw JSON Output</h3>` is present in that initial HTML.
""")

# --- Core Functions ---

def get_stable_chrome_options():
    """Returns a set of ultra-stable Chrome options for Streamlit Cloud."""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1280,720')
    return chrome_options

def setup_driver():
    """Initializes and returns a stable Selenium WebDriver instance."""
    try:
        driver = webdriver.Chrome(options=get_stable_chrome_options())
        return driver
    except WebDriverException as e:
        st.error(f"❌ WebDriver Initialization Failed: {e}")
        return None

def main_workflow():
    """Orchestrates the simple test of loading the page and checking its source."""
    driver = None
    st.subheader("📋 Real-time Log")
    log_placeholder = st.empty()

    def log(message):
        """Helper function to print logs to the Streamlit UI."""
        timestamp = time.strftime('%H:%M:%S', time.gmtime())
        log_placeholder.info(f"`{timestamp}` (UTC): {message}")

    try:
        log("Starting new test...")
        driver = setup_driver()
        if not driver:
            log("Driver setup failed. Aborting.")
            return

        log("Navigating to `chunk.dejan.ai`...")
        driver.get("https://chunk.dejan.ai/")

        log("Page navigation initiated. Waiting for 10 seconds for the site to fully load...")
        time.sleep(10)

        log("Wait complete. Capturing page source now...")
        page_source = driver.page_source
        log("✅ Page source captured successfully.")

        with st.expander("👁️ View Full Page HTML Source", expanded=False):
            st.code(page_source, language='html')

        log("Analyzing captured HTML for the heading 'Raw JSON Output'...")
        
        # Simple string check in the captured HTML
        if "Raw JSON Output" in page_source and "<h3>" in page_source:
             st.success("✅ FOUND: The text 'Raw JSON Output' was found in the initial page source.")
        else:
             st.error("❌ NOT FOUND: The text 'Raw JSON Output' was not present in the initial page source.")

    except Exception as e:
        st.error(f"💥 An unexpected error occurred: {e}")
    finally:
        if driver:
            log("Cleaning up and closing browser instance.")
            driver.quit()
            log("✅ Test finished.")

# --- Streamlit UI ---

col1, col2 = st.columns([2, 1])

with col1:
    if st.button("🧪 Run Initial Page Test", type="primary", use_container_width=True):
        main_workflow()

with col2:
    with st.expander("ℹ️ How This Test Works", expanded=True):
        st.markdown("""
        1.  **Launch Browser**: A new headless Chrome browser is started in the cloud.
        2.  **Navigate**: It opens `chunk.dejan.ai`.
        3.  **Wait**: It waits a fixed 10 seconds for the Streamlit application to render.
        4.  **Capture**: It copies the entire HTML of the page.
        5.  **Analyze & Report**: It checks the captured HTML for the required text and reports if it was found on the initial page load.
        """)
