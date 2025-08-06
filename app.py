#!/usr/bin/env python3
"""
Content Processing Automation Project - H3 Detection After Minimal Input (Corrected)

Purpose:
To load chunk.dejan.ai, input the simple string "test", click submit,
and then check if the 'Raw JSON Output' heading appears as a result.
This version fixes a SyntaxError and adds local timezone logging.
"""

import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
import time
from datetime import datetime
import pytz # A library to handle timezones

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="H3 Detection After 'test' Input",
    page_icon="🧪",
    layout="wide",
)

st.title("🧪 H3 Detection After Inputting 'test'")
st.markdown("""
This test checks if submitting a minimal input (`"test"`) causes the `<h3>Raw JSON Output</h3>` heading to appear.
It will poll for the heading every 5 seconds after clicking the submit button.
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

def check_for_h3_with_polling(driver, log_callback):
    """
    Checks for the H3 heading every 5 seconds for a total of 2 minutes.
    """
    total_wait_time = 120  # 2 minutes
    poll_interval = 5      # 5 seconds
    start_time = time.time()
    
    h3_xpath = "//h3[text()='Raw JSON Output']"
    attempt = 1

    log_callback("🔄 Starting to poll for 'Raw JSON Output' heading...")
    
    while time.time() - start_time < total_wait_time:
        elapsed_time = int(time.time() - start_time)
        log_callback(f"Attempt #{attempt} (Elapsed: {elapsed_time}s): Searching for H3 heading...")
        
        try:
            driver.find_element(By.XPATH, h3_xpath)
            log_callback("✅ SUCCESS: Found 'Raw JSON Output' heading!")
            return True

        except NoSuchElementException:
            log_callback(f"Attempt #{attempt}: Heading not found. Will try again in {poll_interval} seconds.")
            attempt += 1
            time.sleep(poll_interval)
            
        except Exception as e:
            log_callback(f"❌ An unexpected error occurred during polling: {e}")
            return False

    log_callback(f"❌ Test Failed: Timed out after {total_wait_time} seconds. The 'Raw JSON Output' heading never appeared.")
    return False

def main_workflow():
    """Orchestrates the test of submitting "test" and checking for the H3."""
    driver = None
    log_messages = []
    
    log_container = st.container()
    
    def log_callback(message):
        """Helper function to print logs with both UTC and local CEST time."""
        utc_now = datetime.now(pytz.utc)
        cest_tz = pytz.timezone('Europe/Malta')
        cest_now = utc_now.astimezone(cest_tz)
        
        utc_time_str = utc_now.strftime('%H:%M:%S')
        cest_time_str = cest_now.strftime('%H:%M:%S')
        
        log_messages.append(f"`{cest_time_str} (CEST) / {utc_time_str} (UTC)`: {message}")
        with log_container:
            st.info("\n\n".join(log_messages))

    try:
        log_callback("Starting new test workflow...")
        driver = setup_driver()
        if not driver:
            log_callback("Driver setup failed. Aborting.")
            return

        log_callback("Navigating to `chunk.dejan.ai`...")
        driver.get("https://chunk.dejan.ai/")
        
        wait = WebDriverWait(driver, 20)
        
        log_callback("Locating the text input area...")
        input_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[aria-label="Text to chunk:"]')))
        
        # CORRECTED LINE: Ensured the string is on one line.
        log_callback("✅ Found text area. Inputting the word 'test'...")
        input_field.send_keys("test")
        
        log_callback("Locating the submit button...")
        submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="stBaseButton-secondary"]')))
        
        # CORRECTED LINE: Ensured the string is on one line.
        log_callback("✅ Found submit button. Clicking to generate chunks...")
        submit_button.click()
        
        was_found = check_for_h3_with_polling(driver, log_callback)

        # Final Report
        if was_found:
            st.success("🎉 **Test Result: PASS** - Submitting 'test' successfully caused the 'Raw JSON Output' heading to appear.")
        else:
            st.error("🔥 **Test Result: FAIL** - The heading did not appear even after submitting 'test' and waiting.")

    except TimeoutException as e:
        log_callback(f"❌ A timeout occurred while finding form elements: {e}. The site may have changed or is slow to load.")
    except Exception as e:
        log_callback(f"💥 An unexpected error occurred: {e}")
    finally:
        if driver:
            log_callback("Cleaning up and closing browser instance.")
            driver.quit()
            log_callback("✅ Test finished.")

# --- Streamlit UI ---

col1, col2 = st.columns([2, 1])

with col1:
    if st.button("🧪 Run 'test' Input Test", type="primary", use_container_width=True):
        st.subheader("📋 Real-time Processing Log")
        main_workflow()

with col2:
    with st.expander("ℹ️ How This Test Works", expanded=True):
        st.markdown("""
        1.  **Navigate**: Opens `chunk.dejan.ai`.
        2.  **Input 'test'**: Finds the text area and types the word "test".
        3.  **Submit**: Clicks the 'Generate Chunks' button.
        4.  **Poll for H3**: After submission, it checks every 5 seconds to see if the `<h3>Raw JSON Output</h3>` heading has been added to the page.
        5.  **Report**: It reports `PASS` if the heading is found within 2 minutes, or `FAIL` if it is not.
        """)
