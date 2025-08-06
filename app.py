#!/usr/bin/env python3
"""
Content Processing Automation Project - H3 Detection & Content Extraction

Purpose:
To load chunk.dejan.ai, input "test", poll for the 'Raw JSON Output'
heading, and upon success, extract the content from the code block below it.
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

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="H3 Detection & Extraction Test",
    page_icon="✅",
    layout="wide",
)

st.title("✅ H3 Detection & Content Extraction Test")
st.markdown("""
This test submits `"test"`, polls for the `<h3>Raw JSON Output</h3>` heading, and then extracts the content from the code block that follows.
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
    Polls for the H3 heading, and upon finding it, extracts content from the
    subsequent code block. Returns the content or None.
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
            # Check if the H3 element exists
            driver.find_element(By.XPATH, h3_xpath)
            log_callback("✅ SUCCESS: Found 'Raw JSON Output' heading!")
            
            # Now, locate and extract content from the code block
            log_callback("📦 Locating the code block that follows the heading...")
            code_block_xpath = f"{h3_xpath}/following-sibling::div[@data-testid='stCodeBlock']//code"
            
            # Use a short wait to ensure the code block is available after the H3 appears
            wait = WebDriverWait(driver, 10)
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
            log_callback(f"❌ An error occurred during extraction: {e}")
            return None

    log_callback(f"❌ Test Failed: Timed out after {total_wait_time} seconds. The 'Raw JSON Output' heading never appeared.")
    return None

def main_workflow():
    """Orchestrates the test of submitting "test" and extracting the result."""
    driver = None
    log_messages = []
    
    log_container = st.container()
    
    def log_callback(message):
        """Helper function to print logs with a simple UTC timestamp."""
        timestamp = time.strftime('%H:%M:%S', time.gmtime())
        log_messages.append(f"`{timestamp} (UTC)`: {message}")
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
    if st.button("🧪 Run Full Extraction Test", type="primary", use_container_width=True):
        st.subheader("📋 Real-time Processing Log")
        main_workflow()

with col2:
    with st.expander("ℹ️ How This Test Works", expanded=True):
        st.markdown("""
        1.  **Navigate & Submit**: Opens `chunk.dejan.ai`, inputs "test", and clicks submit.
        2.  **Poll for H3**: Checks every 5 seconds for the `<h3>Raw JSON Output</h3>` heading.
        3.  **Extract Content**: Once the heading is found, it locates the `<code>` block below it and copies all its text.
        4.  **Report**: It reports `PASS` if content is extracted, showing character count and JSON validity. It reports `FAIL` if the heading is not found.
        """)
