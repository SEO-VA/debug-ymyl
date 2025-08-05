#!/usr/bin/env python3
"""
Selenium Timing Test App for chunk.dejan.ai

A dedicated Streamlit app to test and find the optimal timing
for extracting complete JSON from chunk.dejan.ai after processing.

This app helps debug the exact delay needed after the copy button appears
to get complete JSON content from the stCodeCopyButton element.
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
import html
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Timing Test App",
    page_icon="🧪",
    layout="wide"
)

# Initialize session state
if 'test_results' not in st.session_state:
    st.session_state.test_results = []
if 'current_test' not in st.session_state:
    st.session_state.current_test = None

def extract_content_for_testing(url):
    """Extract content using the same bookmarklet logic for consistent testing"""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        content_parts = []
        
        # Find main container
        selectors = ['article', 'main', '.content', '#content', '[role="main"]']
        main_container = None
        for selector in selectors:
            main_container = soup.select_one(selector)
            if main_container:
                break
        
        if not main_container:
            paragraphs = soup.find_all('p')
            if len(paragraphs) > 3:
                main_container = paragraphs[0].parent
            else:
                main_container = soup.find('body')
        
        # Extract H1s
        h1_elements = soup.find_all('h1')
        for h1 in h1_elements:
            text = h1.get_text(separator='\n', strip=True)
            if text.strip():
                content_parts.append(f'H1: {text.strip()}')
        
        # Extract subtitles
        subtitles = soup.select('.sub-title,.subtitle,[class*="sub-title"],[class*="subtitle"]')
        for subtitle in subtitles:
            class_names = ' '.join(subtitle.get('class', []))
            if 'd-block' in class_names or subtitle.find_parent(class_='d-block'):
                text = subtitle.get_text(separator='\n', strip=True)
                if text.strip():
                    content_parts.append(f'SUBTITLE: {text.strip()}')
        
        # Extract leads
        leads = soup.select('.lead,[class*="lead"]')
        for lead in leads:
            text = lead.get_text(separator='\n', strip=True)
            if text.strip():
                content_parts.append(f'LEAD: {text.strip()}')
        
        # Extract main content
        if main_container:
            main_text = main_container.get_text(separator='\n', strip=True)
            if main_text.strip():
                content_parts.append(f'CONTENT: {main_text.strip()}')
        
        final_content = '\n\n'.join(content_parts) if content_parts else 'No content found'
        return True, final_content, None
        
    except Exception as e:
        return False, None, str(e)

def setup_test_driver():
    """Setup Chrome driver for testing"""
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--window-size=1280,720')
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        return driver, None
    except Exception as e:
        return None, str(e)

def monitor_network_activity(driver, status_placeholder, log_placeholder):
    """Monitor network activity and copy button appearance"""
    start_time = time.time()
    endpoint_requests = 0
    copy_button_time = None
    
    status_placeholder.info("🔍 Monitoring network activity...")
    
    while time.time() - start_time < 120:  # 2 minute timeout
        elapsed = time.time() - start_time
        
        # Check for copy button
        if copy_button_time is None:
            copy_buttons = driver.find_elements(By.CSS_SELECTOR, '[data-testid="stCodeCopyButton"]')
            if copy_buttons:
                copy_button_time = elapsed
                status_placeholder.success(f"📋 Copy button appeared at {elapsed:.1f}s")
                log_placeholder.text(f"📋 Copy button detected at {elapsed:.1f} seconds")
                return True, copy_button_time, endpoint_requests
        
        # Monitor network logs
        try:
            logs = driver.get_log('performance')
            for log in logs:
                log_str = str(log)
                if "index.NJ4tUjPs809" in log_str and 'fetch' in log_str.lower():
                    endpoint_requests += 1
                    log_placeholder.text(f"🎯 Endpoint request #{endpoint_requests} at {elapsed:.1f}s")
        except:
            pass
        
        # Update status
        if elapsed % 5 < 0.5:  # Every 5 seconds
            status_placeholder.info(f"🔍 Monitoring... ({elapsed:.0f}s elapsed, {endpoint_requests} requests)")
        
        time.sleep(0.5)
    
    status_placeholder.error("⏰ Timeout - copy button never appeared")
    return False, None, endpoint_requests

def test_extraction_timing(driver, test_delays, progress_bar, status_placeholder):
    """Test extraction at different delays after copy button appears"""
    results = []
    
    try:
        copy_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="stCodeCopyButton"]')
        
        for i, delay in enumerate(test_delays):
            progress_bar.progress((i + 1) / len(test_delays))
            status_placeholder.info(f"⏱️ Testing {delay}s delay... ({i+1}/{len(test_delays)})")
            
            if i > 0:
                sleep_time = delay - test_delays[i-1]
                time.sleep(sleep_time)
            
            try:
                # Get content
                raw_content = copy_button.get_attribute('data-clipboard-text')
                
                if raw_content:
                    decoded_content = html.unescape(raw_content)
                    
                    # Try to parse JSON
                    try:
                        json_data = json.loads(decoded_content)
                        big_chunks = len(json_data.get('big_chunks', []))
                        total_small = sum(len(chunk.get('small_chunks', [])) 
                                        for chunk in json_data.get('big_chunks', []))
                        
                        results.append({
                            'delay': delay,
                            'length': len(decoded_content),
                            'valid_json': True,
                            'big_chunks': big_chunks,
                            'small_chunks': total_small,
                            'error': None
                        })
                        
                    except json.JSONDecodeError as e:
                        results.append({
                            'delay': delay,
                            'length': len(decoded_content),
                            'valid_json': False,
                            'big_chunks': 0,
                            'small_chunks': 0,
                            'error': f"Invalid JSON: {str(e)[:50]}"
                        })
                else:
                    results.append({
                        'delay': delay,
                        'length': 0,
                        'valid_json': False,
                        'big_chunks': 0,
                        'small_chunks': 0,
                        'error': "No content found"
                    })
                    
            except Exception as e:
                results.append({
                    'delay': delay,
                    'length': 0,
                    'valid_json': False,
                    'big_chunks': 0,
                    'small_chunks': 0,
                    'error': str(e)
                })
        
        progress_bar.progress(1.0)
        status_placeholder.success("✅ All timing tests completed!")
        return results
        
    except Exception as e:
        status_placeholder.error(f"❌ Testing failed: {e}")
        return []

def run_timing_test(url, content, test_delays):
    """Run the complete timing test"""
    
    # Create UI elements
    col1, col2 = st.columns([1, 1])
    
    with col1:
        status_placeholder = st.empty()
        log_placeholder = st.empty()
    
    with col2:
        progress_bar = st.progress(0)
        progress_text = st.empty()
    
    results = {
        'url': url,
        'content_length': len(content),
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'copy_button_time': None,
        'endpoint_requests': 0,
        'timing_results': [],
        'optimal_delay': None,
        'success': False
    }
    
    # Setup driver
    status_placeholder.info("🔧 Setting up Chrome driver...")
    driver, error = setup_test_driver()
    
    if not driver:
        status_placeholder.error(f"❌ Driver setup failed: {error}")
        return results
    
    try:
        # Navigate to chunk.dejan.ai
        status_placeholder.info("🌐 Navigating to chunk.dejan.ai...")
        driver.get("https://chunk.dejan.ai/")
        time.sleep(5)
        
        # Find and fill input
        status_placeholder.info("📝 Finding input field...")
        wait = WebDriverWait(driver, 30)
        input_field = wait.until(EC.presence_of_element_located((By.ID, "text_area_1")))
        input_field.clear()
        input_field.send_keys(content[:3000])  # Limit content for faster testing
        
        # Click submit
        status_placeholder.info("🚀 Clicking submit button...")
        submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="stBaseButton-secondary"]')))
        submit_button.click()
        
        # Monitor network activity
        success, copy_button_time, endpoint_requests = monitor_network_activity(driver, status_placeholder, log_placeholder)
        
        results['copy_button_time'] = copy_button_time
        results['endpoint_requests'] = endpoint_requests
        
        if not success:
            return results
        
        # Test extraction timing
        timing_results = test_extraction_timing(driver, test_delays, progress_bar, status_placeholder)
        results['timing_results'] = timing_results
        
        # Find optimal delay
        valid_results = [r for r in timing_results if r['valid_json']]
        if valid_results:
            optimal = max(valid_results, key=lambda x: x['length'])
            results['optimal_delay'] = optimal['delay']
            results['success'] = True
        
        return results
        
    except Exception as e:
        status_placeholder.error(f"❌ Test failed: {e}")
        return results
    
    finally:
        if driver:
            driver.quit()

def main():
    """Main app interface"""
    st.title("🧪 Selenium Timing Test App")
    st.markdown("**Find the optimal delay for extracting complete JSON from chunk.dejan.ai**")
    st.markdown("---")
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Test Configuration")
        
        # Test delays
        st.subheader("Timing Intervals")
        delay_preset = st.selectbox(
            "Choose preset delays:",
            ["Quick Test (0-10s)", "Comprehensive (0-20s)", "Extended (0-30s)", "Custom"]
        )
        
        if delay_preset == "Quick Test (0-10s)":
            test_delays = [0, 1, 2, 3, 5, 8, 10]
        elif delay_preset == "Comprehensive (0-20s)":
            test_delays = [0, 1, 2, 3, 5, 8, 10, 15, 20]
        elif delay_preset == "Extended (0-30s)":
            test_delays = [0, 1, 2, 3, 5, 8, 10, 15, 20, 25, 30]
        else:
            custom_delays = st.text_input("Custom delays (comma-separated):", "0,1,2,3,5,8,10")
            try:
                test_delays = [int(x.strip()) for x in custom_delays.split(',')]
            except:
                test_delays = [0, 1, 2, 3, 5, 8, 10]
        
        st.write(f"Testing delays: {test_delays}")
        
        # Clear results
        if st.button("🗑️ Clear All Results"):
            st.session_state.test_results = []
            st.rerun()
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 URL to Test")
        url = st.text_input(
            "Enter URL:",
            placeholder="https://example.com/article",
            help="URL to extract content from for testing"
        )
        
        # Run test button
        if st.button("🚀 Run Timing Test", type="primary", use_container_width=True):
            if not url:
                st.error("Please enter a URL to test")
            else:
                with st.spinner("Extracting content..."):
                    success, content, error = extract_content_for_testing(url)
                    
                if not success:
                    st.error(f"Content extraction failed: {error}")
                else:
                    st.success(f"Content extracted: {len(content)} characters")
                    
                    with st.spinner("Running timing test..."):
                        st.session_state.current_test = run_timing_test(url, content, test_delays)
                        st.session_state.test_results.append(st.session_state.current_test)
                    
                    st.rerun()
    
    with col2:
        st.subheader("ℹ️ How it works")
        st.markdown("""
        1. **Extract** content from URL
        2. **Submit** to chunk.dejan.ai  
        3. **Monitor** for copy button
        4. **Test** extraction at different delays
        5. **Find** optimal timing
        """)
        
        if test_delays:
            st.info(f"Will test {len(test_delays)} different delays: {min(test_delays)}s to {max(test_delays)}s")
    
    # Results section
    if st.session_state.current_test and st.session_state.current_test['success']:
        st.markdown("---")
        st.subheader("📊 Latest Test Results")
        
        result = st.session_state.current_test
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Copy Button Time", f"{result['copy_button_time']:.1f}s")
        with col2:
            st.metric("Endpoint Requests", result['endpoint_requests'])
        with col3:
            st.metric("Optimal Delay", f"{result['optimal_delay']}s")
        with col4:
            valid_count = len([r for r in result['timing_results'] if r['valid_json']])
            st.metric("Valid Results", f"{valid_count}/{len(result['timing_results'])}")
        
        # Detailed results table
        st.subheader("📋 Timing Test Results")
        df = pd.DataFrame(result['timing_results'])
        df['Status'] = df['valid_json'].apply(lambda x: '✅' if x else '❌')
        df = df[['delay', 'Status', 'length', 'big_chunks', 'small_chunks', 'error']]
        df.columns = ['Delay (s)', 'Valid', 'JSON Length', 'Big Chunks', 'Small Chunks', 'Error']
        
        st.dataframe(df, use_container_width=True)
        
        # Recommendation
        if result['optimal_delay'] is not None:
            st.success(f"🎯 **Recommendation**: Use {result['optimal_delay']} seconds delay after copy button appears")
        else:
            st.error("❌ No valid JSON found at any timing")
    
    # Historical results
    if len(st.session_state.test_results) > 1:
        st.markdown("---")
        st.subheader("📈 Historical Results")
        
        history_data = []
        for test in st.session_state.test_results:
            if test['success']:
                history_data.append({
                    'Timestamp': test['timestamp'],
                    'URL': test['url'][:50] + '...',
                    'Copy Button Time': f"{test['copy_button_time']:.1f}s",
                    'Optimal Delay': f"{test['optimal_delay']}s",
                    'Endpoint Requests': test['endpoint_requests']
                })
        
        if history_data:
            history_df = pd.DataFrame(history_data)
            st.dataframe(history_df, use_container_width=True)
            
            # Download results
            if st.button("💾 Download All Results"):
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(['timestamp', 'url', 'copy_button_time', 'optimal_delay', 'endpoint_requests'])
                
                for test in st.session_state.test_results:
                    if test['success']:
                        writer.writerow([
                            test['timestamp'], test['url'], test['copy_button_time'], 
                            test['optimal_delay'], test['endpoint_requests']
                        ])
                
                st.download_button(
                    "📥 Download CSV",
                    output.getvalue(),
                    "timing_test_results.csv",
                    "text/csv"
                )

if __name__ == "__main__":
    main()
