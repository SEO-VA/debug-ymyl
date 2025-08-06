#!/usr/bin/env python3
"""
Content Processing Automation Project - JSON Extraction Test (H3 Logic)

Purpose:
To test a single, direct extraction method by locating the 'Raw JSON Output'
heading and copying all content from the code block immediately following it.
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
import time

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="JSON H3 Extraction Test",
    page_icon="📄",
    layout="wide",
)

st.title("📄 JSON Extraction via H3 Heading")
st.markdown("""
This is a simplified test with a single objective: find the `<h3>Raw JSON Output</h3>` heading and extract the complete content of the code block that follows it.
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

def setup_driver():
    """Initializes and returns a stable Selenium WebDriver instance."""
    try:
        driver = webdriver.Chrome(options=get_stable_chrome_options())
        driver.set_page_load_timeout(60)
        return driver
    except WebDriverException as e:
        st.error(f"❌ WebDriver Initialization Failed: {e}")
        st.error("This may be due to a problem with the chromium-driver. Please try redeploying.")
        return None

def extract_test_content(url):
    """A simple content extractor for test purposes. Grabs up to 5000 chars."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text(separator='\n', strip=True)[:5000]
    except requests.RequestException as e:
        st.warning(f"Could not fetch URL: {e}. Using default test content.")
        return "This is default test content used when a URL fails to load. It is designed to be long enough to trigger chunking and test the new JSON extraction method."

def extract_json_after_h3(driver, status_placeholder):
    """
    Finds the H3 heading and extracts text from the subsequent code block.
    """
    try:
        status_placeholder.info("🔎 Searching for 'Raw JSON Output' heading...")
        wait = WebDriverWait(driver, 30)

        # Step 1: Define the XPath to locate the H3 heading. This is our anchor.
        h3_xpath = "//h3[text()='Raw JSON Output']"
        
        # Step 2: Wait until the heading is present in the DOM.
        wait.until(EC.presence_of_element_located((By.XPATH, h3_xpath)))
        status_placeholder.success("✅ Found 'Raw JSON Output' heading.")
        
        # Step 3: Define the XPath to find the code block that follows the heading.
        # This looks for the H3, then finds its following sibling div (which Streamlit
        # uses to wrap code blocks), and gets the code content within it.
        code_block_xpath = f"{h3_xpath}/following-sibling::div[@data-testid='stCodeBlock']//code"
        
        status_placeholder.info("📦 Locating the code block that follows the heading...")
        code_element = wait.until(EC.presence_of_element_located((By.XPATH, code_block_xpath)))
        
        # Step 4: Extract the text content from the code block.
        json_content = code_element.get_attribute('textContent')
        return json_content

    except TimeoutException:
        status_placeholder.error("❌ Test Failed: Could not find the 'Raw JSON Output' heading or the code block after it within the 30-second timeout.")
        return None
    except Exception as e:
        status_placeholder.error(f"❌ An unexpected error occurred during extraction: {e}")
        return None

def main_workflow(url, status_placeholder, results_placeholder):
    """Orchestrates the entire test from setup to results display."""
    driver = None
    try:
        # Step 1: Get test content
        status_placeholder.info("📄 Extracting test content from URL...")
        content_to_process = extract_test_content(url)

        # Step 2: Setup Selenium WebDriver
        status_placeholder.info("🚀 Initializing secure browser instance...")
        driver = setup_driver()
        if not driver: return

        # Step 3: Navigate and submit content
        status_placeholder.info("🌐 Navigating to `chunk.dejan.ai` and submitting content...")
        driver.get("https://chunk.dejan.ai/")
        wait = WebDriverWait(driver, 30)

        input_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[aria-label="Text to chunk:"]')))
        input_field.send_keys(content_to_process)
        time.sleep(0.5)

        submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="stBaseButton-secondary"]')))
        submit_button.click()
        status_placeholder.info("🤖 Submitted. Waiting for processing to complete...")
        
        # Step 4: Run the extraction logic
        # Instead of complex timing, we will now simply wait for the target H3 to appear.
        json_output = extract_json_after_h3(driver, status_placeholder)

        # Step 5: Display results
        with results_placeholder.container():
            if json_output:
                try:
                    # Validate if the extracted content is valid JSON
                    json.loads(json_output)
                    is_valid = True
                    st.success(f"🎉 **Test Successful!**")
                except json.JSONDecodeError:
                    is_valid = False
                    st.warning("⚠️ **Extraction Successful, but content is not valid JSON.**")
                
                st.metric("Characters Extracted", f"{len(json_output):,}")
                st.metric("Is Valid JSON?", "✅ Yes" if is_valid else "❌ No")
                
                st.subheader("📋 Extracted Content Preview")
                st.code(json_output[:2000] + '...', language='json')

                st.download_button(
                    label="💾 Download Full Extracted Content",
                    data=json_output,
                    file_name="extracted_h3_content.json",
                    mime="application/json"
                )
            else:
                # Error message is already displayed by the extraction function
                pass

    except TimeoutException as e:
        status_placeholder.error(f"❌ A timeout occurred during navigation or submission: {e}. The site `chunk.dejan.ai` may be slow or has changed.")
    except Exception as e:
        status_placeholder.error(f"💥 An unexpected error occurred in the main workflow: {e}")
    finally:
        if driver:
            driver.quit()
            status_placeholder.info("🧹 Browser instance closed.")

# --- Streamlit UI ---

col1, col2 = st.columns([2, 1])
with col1:
    url_to_test = st.text_input(
        "Enter a URL to provide content for the test:",
        "https://techcrunch.com/2024/02/21/google-releases-gemma-a-family-of-open-source-llms/",
        help="Content from this URL will be sent to chunk.dejan.ai for processing."
    )
    
    if st.button("🧪 Run H3 Extraction Test", type="primary", use_container_width=True):
        if url_to_test:
            status_placeholder = st.empty()
            results_placeholder = st.empty()
            with st.spinner("Test in progress..."):
                main_workflow(url_to_test, status_placeholder, results_placeholder)
        else:
            st.error("Please provide a URL.")
            
with col2:
    with st.expander("ℹ️ How This Test Works", expanded=True):
        st.markdown("""
        1.  **Navigate & Submit**: A headless browser navigates to `chunk.dejan.ai`, pastes content from the URL, and clicks submit.
        2.  **Wait & Locate Anchor**: It waits up to 30 seconds for an `<h3>` heading with the exact text `Raw JSON Output` to appear on the page.
        3.  **Positional Extraction**: Once the heading is found, it uses an XPath query to find the very next `<code>` block.
        4.  **Extract & Verify**: It copies all text from that code block and checks if it's valid JSON.
        5.  **Report**: The result (success or failure) is displayed.
        """)
