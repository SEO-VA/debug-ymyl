#!/usr/bin/env python3
"""
Content Processing Automation Project - Final Application-Ready Script

Purpose:
This is the final, production-ready logic. It uses JavaScript injection
to handle large text inputs, preventing StaleElementReferenceExceptions,
and then uses the definitive button attribute polling method to extract the final JSON.
"""

import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException
import requests
from bs4 import BeautifulSoup
import json
import time
import html
from datetime import datetime
import pytz

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Content Processor",
    page_icon="🚀",
    layout="wide",
)

st.title("🚀 Content Processing Automation")
st.markdown("Enter a URL to scrape its content, process it through `chunk.dejan.ai`, and extract the resulting JSON.")

# --- Component 1: The Original Content Extractor Class ---
class ContentExtractor:
    """
    Handles content extraction from websites using the exact logic from the JavaScript bookmarklet.
    """
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def extract_content(self, url):
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            content_parts = []
            main_container_selectors = ['article', 'main', '.content', '#content', '[role="main"]']
            main_container = None
            for selector in main_container_selectors:
                main_container = soup.select_one(selector)
                if main_container:
                    break
            if not main_container:
                if len(soup.find_all('p')) > 3:
                    main_container = soup.find_all('p')[0].parent
                else:
                    main_container = soup.body
            for h1 in soup.find_all('h1'):
                text = h1.get_text(separator='\n', strip=True)
                if text: content_parts.append(f'H1: {text}')
            for st_element in soup.select('.sub-title,.subtitle,[class*="sub-title"],[class*="subtitle"]'):
                text = st_element.get_text(separator='\n', strip=True)
                if text: content_parts.append(f'SUBTITLE: {text}')
            for lead in soup.select('.lead,[class*="lead"]'):
                text = lead.get_text(separator='\n', strip=True)
                if text: content_parts.append(f'LEAD: {text}')
            if main_container:
                main_text = main_container.get_text(separator='\n', strip=True)
                if main_text: content_parts.append(f'CONTENT: {main_text}')
            return True, '\n\n'.join(content_parts) or "No content found", None
        except requests.RequestException as e:
            return False, None, f"Error fetching URL: {e}"

# --- Component 2: The Final Selenium Interaction Logic ---
def get_stable_chrome_options():
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return chrome_options

def setup_driver():
    try:
        return webdriver.Chrome(options=get_stable_chrome_options())
    except WebDriverException as e:
        st.error(f"❌ WebDriver Initialization Failed: {e}")
        return None

def extract_from_button_attribute(driver, log_callback):
    try:
        h3_xpath = "//h3[text()='Raw JSON Output']"
        wait = WebDriverWait(driver, 120)
        log_callback("🔄 Waiting for results section to appear (by finding H3 heading)...")
        wait.until(EC.presence_of_element_located((By.XPATH, h3_xpath)))
        log_callback("✅ Results section is visible.")
        button_selector = "button[data-testid='stCodeCopyButton']"
        log_callback("...Waiting for the copy button to be added to the page...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, button_selector)))
        copy_button = driver.find_element(By.CSS_SELECTOR, button_selector)
        log_callback("✅ Found the copy button element.")
        log_callback("...Polling the button's 'data-clipboard-text' attribute for completeness...")
        timeout = time.time() + 10
        final_content = ""
        while time.time() < timeout:
            raw_content = copy_button.get_attribute('data-clipboard-text')
            if raw_content and raw_content.strip().startswith('{') and raw_content.strip().endswith('}'):
                final_content = raw_content
                break
            time.sleep(0.2)
        if not final_content:
            log_callback("❌ Timed out polling the attribute. It never became a complete JSON string.")
            return None
        log_callback("...Decoding HTML entities (e.g., &quot; to \")...")
        decoded_content = html.unescape(final_content)
        log_callback(f"✅ Extraction complete. Retrieved {len(decoded_content):,} characters.")
        return decoded_content
    except Exception as e:
        log_callback(f"❌ An error occurred during extraction: {e}")
        return None

def main_workflow(url):
    driver = None
    log_messages = []
    log_container = st.empty()
    
    def log_callback(message):
        utc_now = datetime.now(pytz.utc)
        cest_tz = pytz.timezone('Europe/Malta')
        cest_now = utc_now.astimezone(cest_tz)
        log_messages.append(f"`{cest_now.strftime('%H:%M:%S')} (CEST) / {utc_now.strftime('%H:%M:%S')} (UTC)`: {message}")
        log_container.info("\n\n".join(log_messages))

    try:
        log_callback("Initializing ContentExtractor...")
        extractor = ContentExtractor()
        log_callback(f"Extracting content from: {url}")
        success, content_to_submit, error = extractor.extract_content(url)
        if not success:
            log_callback(f"🔥 FAILED to extract content: {error}"); return
        log_callback(f"✅ Content extracted successfully ({len(content_to_submit):,} chars).")
        
        log_callback("Initializing browser...")
        driver = setup_driver()
        if not driver: return

        log_callback("Navigating to `chunk.dejan.ai`...")
        driver.get("https://chunk.dejan.ai/")
        wait = WebDriverWait(driver, 20)
        
        log_callback("Locating text area...")
        input_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[aria-label="Text to chunk:"]')))
        
        # --- THIS IS THE CORRECTED SECTION ---
        # Use JavaScript to instantly set the text area value, preventing stale element errors.
        log_callback("Injecting content via JavaScript to handle large text...")
        js_script = """
            var el = arguments[0];
            var text = arguments[1];
            el.value = text;
            el.dispatchEvent(new Event('input', { bubbles: true }));
        """
        driver.execute_script(js_script, input_field, content_to_submit)
        log_callback("✅ Content injected successfully.")

        log_callback("Clicking submit button...")
        submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="stBaseButton-secondary"]')))
        submit_button.click()
        
        extracted_content = extract_from_button_attribute(driver, log_callback)

        if extracted_content:
            st.success("🎉 **Workflow Complete!** Content was scraped and JSON was extracted successfully.")
            is_valid_json = json.loads(extracted_content) is not None
            col1, col2 = st.columns(2)
            col1.metric("Characters Extracted", f"{len(extracted_content):,}")
            col2.metric("Is Valid JSON?", "✅ Yes" if is_valid_json else "❌ No")
            
            with st.expander("📋 View Extracted JSON", expanded=True):
                st.code(extracted_content, language='json')
            
            st.download_button("💾 Download Full Extracted JSON", data=extracted_content, file_name="extracted_content.json", mime="application/json")
        else:
            st.error("🔥 **Workflow Failed.** Could not extract content after submission. See logs for details.")
    except Exception as e:
        log_callback(f"💥 An unexpected error occurred in the main workflow: {e}")
    finally:
        if driver:
            log_callback("Cleaning up and closing browser instance."); driver.quit()
            log_callback("✅ Workflow finished.")

# --- Streamlit UI ---
st.subheader("Enter URL to Process")
url_to_process = st.text_input(
    "URL:", 
    "https://www.casinohawks.com/bonuses/bonus-code",
    help="Enter a full URL of an article to scrape and process."
)

if st.button("🚀 Run Full Workflow", type="primary", use_container_width=True):
    if url_to_process:
        st.subheader("📋 Real-time Processing Log")
        main_workflow(url_to_process)
    else:
        st.error("Please enter a URL to process.")
