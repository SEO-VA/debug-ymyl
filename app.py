#!/usr/bin/env python3
"""
Content Processing Automation Project - H3 Detection After Minimal Input

Purpose:
To load chunk.dejan.ai, input the simple string "test", click submit,
and then check if the 'Raw JSON Output' heading appears as a result.
"""

import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
import time

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
            # Check if the element exists without a long wait
            driver.find_element(By.XPATH, h3_xpath)
            
            # If the above line does not throw an exception, we found it!
            log_callback("✅ SUCCESS: Found 'Raw JSON Output' heading!")
            return True

        except NoSuchElementException:
            # This is the expected case when the element isn't there yet
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
    
    # Placeholder for the real-time log
    log_container = st.container()
    
    def log_callback(message):
        """Helper function to print logs to the Streamlit UI in a running list."""
        # Note: All times are UTC as they run on the server. Current time in Mosta, Malta is {current_time}.
        timestamp = time.strftime('%H:%M:%S')
        log_messages.append(f"`{timestamp}` (UTC): {message}")
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
        
        # Use an explicit wait for robustness
        wait = WebDriverWait(driver, 20)
        
        log_callback("Locating the text input area...")
        input_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[aria-label="Text to chunk:"]')))
        log_callback("✅ Found
