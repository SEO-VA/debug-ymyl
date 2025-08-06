#!/usr/bin/env python3
"""
Content Processing Automation Project - DOM Stabilization Test

Purpose:
To test if forcing a DOM re-evaluation after the H3 heading is found
solves the final extraction error, mimicking a manual "re-inspect".
"""

import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
import json
import time
from datetime import datetime
import pytz

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="DOM Stabilization Test",
    page_icon="⚓",
    layout="wide",
)

st.title("⚓ DOM Stabilization & Extraction Test")
st.markdown("""
Based on your observation, this test adds a **Stabilization Step** after the `<h3>` is found to ensure the page is settled before extracting content.
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

def find_and_extract_content(driver, log_callback):
    """
    Polls for the H3 heading, stabilizes the DOM, and then extracts content.
    """
    total_wait_time = 120
    poll_interval = 5
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
            
            # --- NEW STABILIZATION STEP ---
            # Based on the "re-inspect" observation, we force a pause and re-sync.
            log_callback("⚓ Stabilizing DOM... (Pausing for 1 second to let rendering settle)")
            time.sleep(1)
            driver.execute_script("return true;") # Forces a sync with the JS engine
            log_callback("✅ DOM stabilized.")
            # --- END OF STABILIZATION STEP ---

            log_callback("📦 Now locating the code block that follows the heading...")
            code_block_xpath = f"{h3_xpath}/following-sibling::div[@data-testid='stCodeBlock']//code"
            
            wait = WebDriverWait(driver, 30)
            code_element = wait.until(EC.presence_of_element_located((By.XPATH, code_block_xpath)))
            
            log_callback("📋 Extracting text content from the code block...")
            json_content = code_element.get_attribute('textContent')
            
            log_callback(f"✅ Extraction complete. Retrieved {len(json_content):,} characters.")
            return json_content

        except NoSuchElementException:
            log_callback(f"Attempt #{attempt}: Heading not found yet. Will try again in {poll_interval} seconds.")
            attempt += 1
            time.sleep(poll_interval)
            
        except Exception as e:
            log_callback(f"❌ An error occurred during the final extraction step: {e}")
            return None

    log_callback(f"❌ Test Failed: Timed out. The 'Raw JSON Output' heading never appeared.")
    return None

def main_workflow():
    """Orchestrates the test of submitting "test" and extracting the result."""
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
        log_callback("✅ Found text area. Inputting the word 'test'...")
        input_field.send_keys("test")
        
        log_callback("Locating the submit button...")
        submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="stBaseButton-secondary"]')))
        log_callback("✅ Found submit button. Clicking to generate chunks...")
        submit_button.click()
        
        extracted_content = find_and_extract_content(driver, log_callback)

        # Final Report
        if extracted_content is not None:
            st.success("🎉 **Test Result: PASS** - Heading was found and content was extracted.")
            is_valid_json = False
            try:
                json.loads(extracted_content)
                is_valid_json = True
            except json.JSONDecodeError:
                pass
            
            col1, col2 = st.columns(2)
            col1.metric("Characters Extracted", f"{len(extracted_content):,}")
            col2.metric("Is Valid JSON?", "✅ Yes" if is_valid_json else "❌ No")
            
            with st.expander("📋 View Extracted Content Preview"):
                st.code(extracted_content[:2000] + '...', language='json')
            
            st.download_button(
                "💾 Download Full Extracted Content",
                data=extracted_content,
                file_name="extracted_content.json",
                mime="application/json"
            )
        else:
            st.error("🔥 **Test Result: FAIL** - The heading did not appear or content could not be extracted. See logs for details.")

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
    if st.button("🧪 Run Stabilization Test", type="primary", use_container_width=True):
        st.subheader("📋 Real-time Processing Log")
        main_workflow()

with col2:
    with st.expander("ℹ️ How This Test Works", expanded=True):
        st.markdown("""
        1.  **Submit**: Opens `chunk.dejan.ai`, inputs "test", and clicks submit.
        2.  **Poll for H3**: Checks every 5 seconds for the `<h3>Raw JSON Output</h3>` heading.
        3.  **Stabilize DOM**: Once the heading is found, it **pauses for 1 second** to let the page settle, mimicking a manual "re-inspect".
        4.  **Extract Content**: It then waits up to 30 seconds for the `<code>` block to appear and copies its text.
        5.  **Report**: It reports `PASS` or `FAIL` based on whether the content was successfully extracted.
        """)
