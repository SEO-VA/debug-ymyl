#!/usr/bin/env python3
"""
Content Processing Automation Project - Final Extraction Logic

Purpose:
To definitively extract the complete JSON from the data-clipboard-text
attribute of the copy button, including a polling mechanism to ensure
the attribute is fully populated before reading.
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
import html # Required to decode HTML entities like &quot;

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Button Attribute Extraction",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 Final Extraction Logic: Button Attribute")
st.markdown("""
This script uses the definitive method: it finds the copy button and polls its `data-clipboard-text` attribute until it's fully populated, then decodes it.
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

def extract_from_button_attribute(driver, log_callback):
    """
    Finds the copy button and robustly extracts the complete JSON from its attribute.
    """
    try:
        # Step 1: Wait for the H3 heading as a signal that the results area is ready.
        h3_xpath = "//h3[text()='Raw JSON Output']"
        wait = WebDriverWait(driver, 120) # Wait up to 2 minutes for the whole process
        log_callback("🔄 Waiting for results section to appear (by finding H3 heading)...")
        wait.until(EC.presence_of_element_located((By.XPATH, h3_xpath)))
        log_callback("✅ Found H3 heading. The results section is now visible.")

        # Step 2: Now wait specifically for the copy button to exist.
        button_selector = "button[data-testid='stCodeCopyButton']"
        log_callback("...Waiting for the copy button to be added to the page...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, button_selector)))
        copy_button = driver.find_element(By.CSS_SELECTOR, button_selector)
        log_callback("✅ Found the copy button element.")

        # Step 3: Poll the button's attribute to ensure it's fully populated.
        # This solves the "partial content" race condition.
        log_callback("...Polling the button's 'data-clipboard-text' attribute for completeness...")
        timeout = time.time() + 10  # Poll for up to 10 seconds
        final_content = ""
        while time.time() < timeout:
            raw_content = copy_button.get_attribute('data-clipboard-text')
            # A complete JSON string will start with { and end with }
            if raw_content and raw_content.strip().startswith('{') and raw_content.strip().endswith('}'):
                final_content = raw_content
                break # Exit the loop as soon as we have a complete string
            time.sleep(0.2) # Check 5 times per second

        if not final_content:
            log_callback("❌ Timed out polling the attribute. It never became a complete JSON string.")
            return None

        log_callback("✅ Attribute is fully populated.")

        # Step 4: Decode the HTML entities from the string.
        log_callback("...Decoding HTML entities (e.g., &quot; to \")...")
        decoded_content = html.unescape(final_content)
        log_callback(f"✅ Extraction and decoding complete. Retrieved {len(decoded_content):,} characters.")
        
        return decoded_content

    except TimeoutException:
        log_callback(f"❌ Test Failed: Timed out waiting for the H3 heading or the copy button to appear.")
        return None
    except Exception as e:
        log_callback(f"❌ An unexpected error occurred during extraction: {e}")
        return None

def main_workflow():
    """Orchestrates the test using the definitive button extraction method."""
    driver = None
    log_messages = []
    
    log_container = st.container()
    
    def log_callback(message):
        timestamp = time.strftime('%H:%M:%S', time.gmtime())
        log_messages.append(f"`{timestamp} (UTC)`: {message}")
        with log_container:
            st.info("\n\n".join(log_messages))

    try:
        log_callback("Starting final test workflow...")
        driver = setup_driver()
        if not driver: return

        log_callback("Navigating to `chunk.dejan.ai`...")
        driver.get("https://chunk.dejan.ai/")
        
        wait = WebDriverWait(driver, 20)
        
        log_callback("Locating the text input area...")
        input_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[aria-label="Text to chunk:"]')))
        log_callback("Inputting the word 'test'...")
        input_field.send_keys("test")
        
        log_callback("Locating and clicking the submit button...")
        submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="stBaseButton-secondary"]')))
        submit_button.click()
        
        extracted_content = extract_from_button_attribute(driver, log_callback)

        # Final Report
        if extracted_content:
            st.success("🎉 **Test Result: PASS** - Content was successfully extracted from the button attribute.")
            is_valid_json = False
            try:
                json.loads(extracted_content)
                is_valid_json = True
            except json.JSONDecodeError:
                pass
            
            col1, col2 = st.columns(2)
            col1.metric("Characters Extracted", f"{len(extracted_content):,}")
            col2.metric("Is Valid JSON?", "✅ Yes" if is_valid_json else "❌ No")
            
            with st.expander("📋 View Extracted JSON"):
                st.code(extracted_content, language='json')
            
            st.download_button(
                "💾 Download Full Extracted JSON",
                data=extracted_content,
                file_name="extracted_content.json",
                mime="application/json"
            )
        else:
            st.error("🔥 **Test Result: FAIL** - Could not extract content. See logs for details.")

    except Exception as e:
        log_callback(f"💥 An unexpected error occurred in the main workflow: {e}")
    finally:
        if driver:
            log_callback("Cleaning up and closing browser instance.")
            driver.quit()
            log_callback("✅ Test finished.")

# --- Streamlit UI ---

if st.button("🧪 Run Final Extraction Test", type="primary", use_container_width=True):
    st.subheader("📋 Real-time Processing Log")
    main_workflow()
