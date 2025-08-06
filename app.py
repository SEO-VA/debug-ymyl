#!/usr/bin/env python3
"""
Content Processing Automation Project - JSON Extraction Test (Polling & Logging)

Purpose:
To test a direct extraction method by actively polling for the 'Raw JSON Output'
heading every 5 seconds and providing a verbose log of every action.
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import json
import time

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="JSON H3 Polling Test",
    page_icon="📡",
    layout="wide",
)

st.title("📡 JSON Extraction via H3 Polling")
st.markdown("""
This test actively polls the page every 5 seconds to find the `<h3>Raw JSON Output</h3>` heading.
It provides a detailed, real-time log of every action for maximum visibility.
""")

# --- Core Classes & Functions ---

def get_stable_chrome_options():
    """Returns a set of ultra-stable Chrome options for Streamlit Cloud."""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1280,720')
    return chrome_options

def setup_driver(log_callback):
    """Initializes and returns a stable Selenium WebDriver instance with logging."""
    try:
        log_callback("🚀 Initializing new Chrome browser instance in the cloud...")
        driver = webdriver.Chrome(options=get_stable_chrome_options())
        driver.set_page_load_timeout(60)
        log_callback("✅ Browser instance is ready.")
        return driver
    except WebDriverException as e:
        log_callback(f"❌ WebDriver Initialization Failed: {e}")
        st.error("This may be due to a problem with the chromium-driver. Please try redeploying.")
        return None

def extract_test_content(url, log_callback):
    """A simple content extractor for test purposes with logging."""
    try:
        log_callback(f"📄 Fetching content from URL: {url[:70]}...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        log_callback("✅ Content fetched successfully.")
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.get_text(separator='\n', strip=True)[:5000]
        log_callback(f"Extracted {len(content)} characters for the test.")
        return content
    except requests.RequestException as e:
        log_callback(f"⚠️ Could not fetch URL: {e}. Using default test content.")
        return "This is default test content used when a URL fails to load. It is designed to be long enough to trigger chunking and test the new JSON extraction method."

def extract_json_with_polling(driver, log_callback):
    """
    Checks for the H3 heading every 5 seconds for a total of 3 minutes.
    """
    total_wait_time = 180  # 3 minutes
    poll_interval = 5      # 5 seconds
    start_time = time.time()
    
    h3_xpath = "//h3[text()='Raw JSON Output']"
    attempt = 1

    log_callback("🔄 Starting to poll for 'Raw JSON Output' heading...")
    
    while time.time() - start_time < total_wait_time:
        elapsed_time = int(time.time() - start_time)
        log_callback(f"Attempt #{attempt} (Elapsed: {elapsed_time}s): Searching for H3 heading...")
        
        try:
            # Check if the element exists without waiting long
            driver.find_element(By.XPATH, h3_xpath)
            
            # If it exists, we found it!
            log_callback("✅ SUCCESS: Found 'Raw JSON Output' heading!")
            
            # Now, get the code block that follows it
            log_callback("📦 Locating the code block that follows the heading...")
            code_block_xpath = f"{h3_xpath}/following-sibling::div[@data-testid='stCodeBlock']//code"
            code_element = driver.find_element(By.XPATH, code_block_xpath)
            
            log_callback("📋 Extracting text content from the code block...")
            json_content = code_element.get_attribute('textContent')
            log_callback(f"✅ Extracted {len(json_content)} characters.")
            return json_content

        except NoSuchElementException:
            # This is the expected case when the element isn't there yet
            log_callback(f"Attempt #{attempt}: Heading not found. Will try again in {poll_interval} seconds.")
            attempt += 1
            time.sleep(poll_interval)
            
        except Exception as e:
            log_callback(f"❌ An unexpected error occurred during polling: {e}")
            return None

    log_callback("❌ Test Failed: Timed out after 3 minutes. The 'Raw JSON Output' heading never appeared.")
    return None

def main_workflow(url, status_placeholder):
    """Orchestrates the entire test with detailed, real-time logging."""
    driver = None
    log_messages = []
    
    def log_callback(message):
        """Helper function to print logs to the Streamlit UI."""
        timestamp = time.strftime('%H:%M:%S')
        log_messages.append(f"`{timestamp}`: {message}")
        status_placeholder.markdown("\n\n".join(log_messages[-15:])) # Show the last 15 log messages

    try:
        log_callback("Starting new test workflow...")
        
        # Step 1: Get test content
        content_to_process = extract_test_content(url, log_callback)

        # Step 2: Setup Selenium WebDriver
        driver = setup_driver(log_callback)
        if not driver: return

        # Step 3: Navigate and submit content
        log_callback("🌐 Navigating to `chunk.dejan.ai`...")
        driver.get("https://chunk.dejan.ai/")
        
        wait = WebDriverWait(driver, 30)
        
        log_callback("✍️ Looking for the text input area...")
        input_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[aria-label="Text to chunk:"]')))
        log_callback("✅ Found text area. Pasting content...")
        input_field.send_keys(content_to_process)
        
        log_callback("🖱️ Looking for the submit button...")
        submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="stBaseButton-secondary"]')))
        log_callback("✅ Found submit button. Clicking to generate chunks...")
        submit_button.click()
        
        # Step 4: Run the extraction logic with the new polling mechanism
        json_output = extract_json_with_polling(driver, log_callback)

        # Step 5: Display final results
        if json_output:
            try:
                json.loads(json_output)
                is_valid = True
                st.success(f"🎉 **Test Complete & Successful!**")
            except json.JSONDecodeError:
                is_valid = False
                st.warning("⚠️ **Extraction was successful, but the content is not valid JSON.**")
            
            st.metric("Characters Extracted", f"{len(json_output):,}")
            st.metric("Is Valid JSON?", "✅ Yes" if is_valid else "❌ No")
            
            with st.expander("📋 View Full Extracted Content", expanded=False):
                st.code(json_output, language='json')

            st.download_button(
                label="💾 Download Full Extracted Content",
                data=json_output,
                file_name="extracted_polling_content.json",
                mime="application/json"
            )
        else:
            st.error("❌ Test Failed. See logs above for details.")

    except TimeoutException as e:
        log_callback(f"❌ A timeout occurred during navigation or submission: {e}. The site `chunk.dejan.ai` may be slow or has changed.")
    except Exception as e:
        log_callback(f"💥 An unexpected error occurred in the main workflow: {e}")
    finally:
        if driver:
            log_callback("🧹 Closing browser instance.")
            driver.quit()
            log_callback("✅ Browser instance closed.")

# --- Streamlit UI ---

col1, col2 = st.columns([2, 1])
with col1:
    url_to_test = st.text_input(
        "Enter a URL to provide content for the test:",
        "https://www.theverge.com/2022/7/26/23278447/google-maps-new-features-immersive-view-3d-previews-location-sharing",
        help="Content from this URL will be sent to chunk.dejan.ai for processing."
    )
    
    if st.button("🧪 Run Polling Test", type="primary", use_container_width=True):
        if url_to_test:
            st.subheader("📋 Real-time Processing Log")
            status_placeholder = st.empty()
            main_workflow(url_to_test, status_placeholder)
        else:
            st.error("Please provide a URL.")
            
with col2:
    with st.expander("ℹ️ How This Test Works", expanded=True):
        st.markdown("""
        1.  **Navigate & Submit**: A browser navigates to `chunk.dejan.ai` and submits the content.
        2.  **Start Polling**: The script immediately begins a 3-minute loop.
        3.  **Check Every 5s**: Inside the loop, it checks for the `<h3>Raw JSON Output</h3>` heading.
        4.  **Log Everything**: The result of *every* check is printed to the log on the left.
        5.  **Extract on Success**: If the heading is found, it extracts the content from the code block below it.
        6.  **Timeout on Failure**: If the heading isn't found after 3 minutes, the test fails.
        """)
