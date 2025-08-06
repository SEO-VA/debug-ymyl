#!/usr/bin/env python3
"""
JSON Extraction Methods Test App

Tests different ways to extract complete JSON content from the 
stCodeCopyButton element after chunk.dejan.ai processing.

Focus: EXTRACTION METHODS, not timing
Goal: Find the method that gets 100% of the JSON content
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import json
import html
import re
import time

# Page config
st.set_page_config(
    page_title="JSON Extraction Test",
    page_icon="🔍",
    layout="wide"
)

def extract_content_simple(url):
    """Quick content extraction for testing"""
    try:
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Simple extraction
        text_content = soup.get_text()[:2000]  # First 2000 chars for testing
        return f"CONTENT: {text_content}"
    except:
        return "Test content for JSON extraction methods testing."

def setup_driver():
    """Setup Chrome driver with better error handling"""
    try:
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--single-process')
        options.add_argument('--window-size=1280,720')
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(15)
        return driver
    except Exception as e:
        st.error(f"Driver setup failed: {e}")
        return None

def test_extraction_methods_workflow(url):
    """Simplified workflow with better error handling"""
    
    # Extract content
    with st.spinner("Extracting content..."):
        content = extract_content_simple(url)
    
    st.success(f"Content ready: {len(content)} characters")
    
    # Setup driver
    driver = setup_driver()
    if not driver:
        return
    
    try:
        st.info("🌐 Navigating to chunk.dejan.ai...")
        driver.get("https://chunk.dejan.ai/")
        
        # Wait longer for Streamlit app to load
        st.info("⏳ Waiting for page to load...")
        time.sleep(10)
        
        # Try to find input field with extended timeout
        st.info("📝 Looking for input field...")
        wait = WebDriverWait(driver, 60)
        
        try:
            input_field = wait.until(EC.presence_of_element_located((By.ID, "text_area_1")))
            st.success("✅ Input field found!")
        except TimeoutException:
            st.error("❌ Input field not found - chunk.dejan.ai might be loading slowly")
            
            # Try alternative selectors
            st.info("🔍 Trying alternative selectors...")
            alternative_selectors = [
                'textarea[aria-label*="chunk"]',
                'textarea',
                '[data-testid*="text"]'
            ]
            
            input_field = None
            for selector in alternative_selectors:
                try:
                    input_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    st.success(f"✅ Found input with selector: {selector}")
                    break
                except:
                    continue
            
            if not input_field:
                st.error("❌ Could not find any input field")
                return
        
        # Fill the form
        st.info("✏️ Filling content...")
        input_field.clear()
        input_field.send_keys(content[:1000])  # Shorter content for faster testing
        
        # Find submit button
        st.info("🔍 Looking for submit button...")
        try:
            submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="stBaseButton-secondary"]')))
            st.success("✅ Submit button found!")
        except TimeoutException:
            st.error("❌ Submit button not found")
            
            # Try alternative button selectors
            button_selectors = [
                'button[kind="secondary"]',
                'button:contains("Generate")',
                'button'
            ]
            
            submit_button = None
            for selector in button_selectors:
                try:
                    submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                    if submit_button and submit_button.is_enabled():
                        st.success(f"✅ Found button with selector: {selector}")
                        break
                except:
                    continue
            
            if not submit_button:
                st.error("❌ No clickable button found")
                return
        
        # Click submit
        st.info("🚀 Clicking submit...")
        submit_button.click()
        
        # Simple wait approach - just wait 30 seconds
        st.info("⏳ Waiting 30 seconds for processing...")
        time.sleep(30)
        
        # Now test extraction methods
        st.info("🧪 Testing extraction methods...")
        methods = test_simple_extraction_methods(driver)
        
        # Show results
        display_extraction_results(methods)
        
    except Exception as e:
        st.error(f"❌ Test failed: {e}")
        st.error("This might be due to chunk.dejan.ai being slow or temporarily unavailable")
    
    finally:
        if driver:
            driver.quit()

def test_simple_extraction_methods(driver):
    """Simplified extraction testing"""
    methods = {}
    
    # Look for copy button
    st.write("🔍 Looking for copy button...")
    copy_buttons = driver.find_elements(By.CSS_SELECTOR, '[data-testid="stCodeCopyButton"]')
    
    if not copy_buttons:
        st.warning("⚠️ No copy button found - trying alternative selectors...")
        # Try other possible selectors
        alternative_selectors = [
            'button[title*="copy"]',
            'button[title*="Copy"]', 
            '[data-clipboard-text]',
            'button[data-testid*="copy"]'
        ]
        
        for selector in alternative_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                copy_buttons = elements
                st.info(f"Found copy elements with: {selector}")
                break
    
    if not copy_buttons:
        st.error("❌ No copy button found at all")
        return {'error': 'No copy button found'}
    
    copy_button = copy_buttons[0]
    st.success(f"✅ Found copy button: {copy_button.tag_name}")
    
    # Test Method 1: data-clipboard-text attribute
    st.write("**Method 1: data-clipboard-text attribute**")
    try:
        raw_content = copy_button.get_attribute('data-clipboard-text')
        if raw_content:
            decoded = html.unescape(raw_content)
            methods['Method 1'] = {
                'length': len(decoded),
                'preview': decoded[:200],
                'valid_json': is_valid_json(decoded),
                'full_content': decoded
            }
            st.write(f"   ✅ Found {len(decoded)} characters")
        else:
            methods['Method 1'] = {'error': 'No content in data-clipboard-text'}
            st.write("   ❌ No content found")
    except Exception as e:
        methods['Method 1'] = {'error': str(e)}
        st.write(f"   ❌ Error: {e}")
    
    # Test Method 2: All attributes
    st.write("**Method 2: Check all attributes**")
    try:
        all_attributes = {}
        # Get all attributes
        attrs = driver.execute_script("return arguments[0].attributes;", copy_button)
        for i in range(attrs['length']):
            attr = attrs[str(i)]
            if attr:
                name = attr.get('name', '')
                value = copy_button.get_attribute(name)
                if value and len(value) > 50:
                    all_attributes[name] = len(value)
        
        methods['Method 2'] = {'attributes': all_attributes}
        st.write(f"   Attributes with content: {all_attributes}")
        
        # Use the longest one
        if all_attributes:
            best_attr = max(all_attributes.keys(), key=lambda k: all_attributes[k])
            content = copy_button.get_attribute(best_attr)
            if 'clipboard' in best_attr:
                content = html.unescape(content)
            
            methods['Method 2'].update({
                'best_attribute': best_attr,
                'length': len(content),
                'valid_json': is_valid_json(content),
                'full_content': content
            })
            
    except Exception as e:
        methods['Method 2'] = {'error': str(e)}
        st.write(f"   ❌ Error: {e}")
    
    # Test Method 3: JavaScript approach
    st.write("**Method 3: JavaScript extraction**")
    try:
        js_result = driver.execute_script("""
            var button = document.querySelector('[data-testid="stCodeCopyButton"]');
            if (!button) button = document.querySelector('[data-clipboard-text]');
            if (button) {
                return button.getAttribute('data-clipboard-text');
            }
            return null;
        """)
        
        if js_result:
            decoded = html.unescape(js_result)
            methods['Method 3'] = {
                'length': len(decoded),
                'valid_json': is_valid_json(decoded),
                'full_content': decoded
            }
            st.write(f"   ✅ Found {len(decoded)} characters")
        else:
            methods['Method 3'] = {'error': 'JavaScript returned null'}
            st.write("   ❌ JavaScript returned null")
            
    except Exception as e:
        methods['Method 3'] = {'error': str(e)}
        st.write(f"   ❌ Error: {e}")
    
    return methods

def display_extraction_results(methods):
    """Display results of extraction testing"""
    st.write("\n📊 **EXTRACTION RESULTS**")
    st.write("=" * 50)
    
    if 'error' in methods:
        st.error(f"❌ {methods['error']}")
        return
    
    # Find working methods
    working_methods = {}
    for method_name, result in methods.items():
        if isinstance(result, dict) and 'full_content' in result and result.get('valid_json', False):
            working_methods[method_name] = result
    
    if working_methods:
        st.success(f"✅ Found {len(working_methods)} working method(s)!")
        
        # Show comparison
        for method_name, result in working_methods.items():
            st.write(f"**{method_name}**: {result['length']} characters, Valid JSON: ✅")
        
        # Show the best one
        best_method = max(working_methods.keys(), key=lambda k: working_methods[k]['length'])
        best_result = working_methods[best_method]
        
        st.success(f"🎯 **BEST METHOD: {best_method}** ({best_result['length']} characters)")
        
        # Show preview
        st.write("📋 **Content Preview:**")
        preview = best_result['full_content'][:300] + "..." if len(best_result['full_content']) > 300 else best_result['full_content']
        st.code(preview, language='json')
        
        # Download option
        st.download_button(
            "💾 Download Complete JSON",
            best_result['full_content'],
            f"complete_json_{int(time.time())}.json",
            "application/json"
        )
        
    else:
        st.error("❌ No working extraction methods found")
        
        # Show debug info
        st.write("🔍 **Debug Information:**")
        for method_name, result in methods.items():
            if isinstance(result, dict):
                if 'error' in result:
                    st.write(f"   {method_name}: ❌ {result['error']}")
                elif 'length' in result:
                    valid = "✅" if result.get('valid_json', False) else "❌"
                    st.write(f"   {method_name}: {result['length']} chars, Valid: {valid}")
                else:
                    st.write(f"   {method_name}: {result}")

def wait_for_processing_simple(driver):
    """Wait for processing with simple 4-fetch detection + 1 second"""
    endpoint = "index.NJ4tUjPs809"
    fetch_count = 0
    seen_requests = set()
    start_time = time.time()
    
    st.write("🔍 Monitoring for 4th fetch request...")
    
    while fetch_count < 4 and time.time() - start_time < 60:
        try:
            logs = driver.get_log('performance')
            for log in logs:
                if endpoint in str(log) and 'fetch' in str(log).lower():
                    log_id = f"{log.get('timestamp', 0)}_{hash(str(log))}"
                    if log_id not in seen_requests:
                        seen_requests.add(log_id)
                        fetch_count += 1
                        st.write(f"🎯 Fetch {fetch_count}/4 detected")
                        
                        if fetch_count >= 4:
                            st.write("✅ 4th fetch completed - waiting 1 second...")
                            time.sleep(1)  # Your preferred 1-second delay
                            return True
        except:
            pass
        time.sleep(0.3)
    
    # Fallback: wait for copy button + 1 second
    st.write("⚠️ Fallback: waiting for copy button + 1 second...")
    try:
        wait = WebDriverWait(driver, 60)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="stCodeCopyButton"]')))
        time.sleep(1)
        return True
    except:
        return False

def test_extraction_methods(driver):
    """Test multiple ways to extract JSON from the copy button"""
    st.write("🧪 Testing different extraction methods...")
    
    methods = {}
    
    # Method 1: Standard getAttribute
    st.write("\n**Method 1: Standard getAttribute('data-clipboard-text')**")
    try:
        copy_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="stCodeCopyButton"]')
        raw_content = copy_button.get_attribute('data-clipboard-text')
        if raw_content:
            decoded = html.unescape(raw_content)
            methods['Method 1'] = {
                'raw_length': len(raw_content),
                'decoded_length': len(decoded),
                'content': decoded,
                'valid_json': is_valid_json(decoded)
            }
            st.write(f"   Raw: {len(raw_content)} chars, Decoded: {len(decoded)} chars")
        else:
            methods['Method 1'] = {'error': 'No content found'}
            st.write("   ❌ No content found")
    except Exception as e:
        methods['Method 1'] = {'error': str(e)}
        st.write(f"   ❌ Error: {e}")
    
    # Method 2: JavaScript execution
    st.write("\n**Method 2: JavaScript execution**")
    try:
        js_script = """
            var button = document.querySelector('[data-testid="stCodeCopyButton"]');
            return button ? button.getAttribute('data-clipboard-text') : null;
        """
        raw_content = driver.execute_script(js_script)
        if raw_content:
            decoded = html.unescape(raw_content)
            methods['Method 2'] = {
                'raw_length': len(raw_content),
                'decoded_length': len(decoded),
                'content': decoded,
                'valid_json': is_valid_json(decoded)
            }
            st.write(f"   Raw: {len(raw_content)} chars, Decoded: {len(decoded)} chars")
        else:
            methods['Method 2'] = {'error': 'No content found'}
            st.write("   ❌ No content found")
    except Exception as e:
        methods['Method 2'] = {'error': str(e)}
        st.write(f"   ❌ Error: {e}")
    
    # Method 3: Multiple attribute checks
    st.write("\n**Method 3: Check multiple attributes**")
    try:
        copy_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="stCodeCopyButton"]')
        
        # Try different attributes
        attributes_to_check = [
            'data-clipboard-text',
            'data-clipboard-target', 
            'title',
            'aria-label',
            'innerHTML',
            'textContent'
        ]
        
        attribute_results = {}
        for attr in attributes_to_check:
            try:
                value = copy_button.get_attribute(attr)
                if value and len(value) > 100:  # Only show substantial content
                    if attr == 'data-clipboard-text':
                        decoded = html.unescape(value)
                        attribute_results[attr] = len(decoded)
                    else:
                        attribute_results[attr] = len(value)
                else:
                    attribute_results[attr] = 0
            except:
                attribute_results[attr] = 'error'
        
        st.write(f"   Attribute lengths: {attribute_results}")
        
        # Use the best one
        best_attr = max(attribute_results.keys(), key=lambda k: attribute_results[k] if isinstance(attribute_results[k], int) else 0)
        if attribute_results[best_attr] > 100:
            content = copy_button.get_attribute(best_attr)
            if best_attr == 'data-clipboard-text':
                content = html.unescape(content)
            methods['Method 3'] = {
                'best_attribute': best_attr,
                'length': len(content),
                'content': content,
                'valid_json': is_valid_json(content)
            }
        else:
            methods['Method 3'] = {'error': 'No substantial content in any attribute'}
            
    except Exception as e:
        methods['Method 3'] = {'error': str(e)}
        st.write(f"   ❌ Error: {e}")
    
    # Method 4: Element text content
    st.write("\n**Method 4: Element text and innerHTML**")
    try:
        copy_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="stCodeCopyButton"]')
        
        text_content = copy_button.text
        inner_html = copy_button.get_attribute('innerHTML')
        
        st.write(f"   Text content: {len(text_content)} chars")
        st.write(f"   innerHTML: {len(inner_html)} chars")
        
        # Check if either contains JSON-like content
        best_content = None
        if '"big_chunks"' in text_content:
            best_content = text_content
        elif '"big_chunks"' in inner_html:
            best_content = html.unescape(inner_html)
        
        if best_content:
            methods['Method 4'] = {
                'length': len(best_content),
                'content': best_content,
                'valid_json': is_valid_json(best_content)
            }
        else:
            methods['Method 4'] = {'error': 'No JSON content found in text or HTML'}
            
    except Exception as e:
        methods['Method 4'] = {'error': str(e)}
        st.write(f"   ❌ Error: {e}")
    
    # Method 5: Page source extraction
    st.write("\n**Method 5: Extract from page source**")
    try:
        page_source = driver.page_source
        
        # Look for JSON content in page source
        if '"big_chunks"' in page_source:
            # Try to extract JSON using regex
            patterns = [
                r'data-clipboard-text="([^"]*)"',
                r'"big_chunks":\s*\[.*?\]',
                r'\{[^{}]*"big_chunks"[^{}]*\[.*?\]\s*\}'
            ]
            
            best_match = None
            for pattern in patterns:
                matches = re.findall(pattern, page_source, re.DOTALL)
                if matches:
                    # Get the longest match
                    longest = max(matches, key=len)
                    if len(longest) > len(best_match or ''):
                        best_match = longest
            
            if best_match:
                decoded = html.unescape(best_match)
                methods['Method 5'] = {
                    'length': len(decoded),
                    'content': decoded,
                    'valid_json': is_valid_json(decoded)
                }
                st.write(f"   Found content: {len(decoded)} chars")
            else:
                methods['Method 5'] = {'error': 'No JSON pattern found in page source'}
                st.write("   ❌ No JSON pattern found")
        else:
            methods['Method 5'] = {'error': 'No big_chunks found in page source'}
            st.write("   ❌ No big_chunks found in page source")
            
    except Exception as e:
        methods['Method 5'] = {'error': str(e)}
        st.write(f"   ❌ Error: {e}")
    
    # Method 6: Wait and retry approach
    st.write("\n**Method 6: Multiple attempts with micro-delays**")
    try:
        copy_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="stCodeCopyButton"]')
        
        attempts = []
        for i in range(5):  # 5 attempts with small delays
            if i > 0:
                time.sleep(0.5)  # 500ms between attempts
            
            raw_content = copy_button.get_attribute('data-clipboard-text')
            if raw_content:
                decoded = html.unescape(raw_content)
                attempts.append({
                    'attempt': i + 1,
                    'length': len(decoded),
                    'valid': is_valid_json(decoded)
                })
        
        if attempts:
            # Find the best attempt (longest valid JSON)
            valid_attempts = [a for a in attempts if a['valid']]
            if valid_attempts:
                best = max(valid_attempts, key=lambda x: x['length'])
                # Get the content from the best attempt
                time.sleep(0.5 * (best['attempt'] - 1))
                final_content = html.unescape(copy_button.get_attribute('data-clipboard-text'))
                
                methods['Method 6'] = {
                    'attempts': attempts,
                    'best_attempt': best['attempt'],
                    'length': len(final_content),
                    'content': final_content,
                    'valid_json': True
                }
                st.write(f"   Best result: attempt {best['attempt']} with {len(final_content)} chars")
            else:
                methods['Method 6'] = {
                    'attempts': attempts,
                    'error': 'No valid JSON in any attempt'
                }
                st.write(f"   ❌ No valid JSON in {len(attempts)} attempts")
        else:
            methods['Method 6'] = {'error': 'No content found in any attempt'}
            st.write("   ❌ No content found in any attempt")
            
    except Exception as e:
        methods['Method 6'] = {'error': str(e)}
        st.write(f"   ❌ Error: {e}")
    
    return methods

def is_valid_json(content):
    """Check if content is valid JSON"""
    try:
        json.loads(content)
        return True
    except:
        return False

def analyze_methods(methods):
    """Analyze which method works best"""
    st.write("\n📊 **ANALYSIS RESULTS**")
    st.write("=" * 50)
    
    valid_methods = {}
    for method_name, result in methods.items():
        if 'content' in result and result.get('valid_json', False):
            valid_methods[method_name] = result
    
    if not valid_methods:
        st.write("❌ **NO VALID JSON FOUND WITH ANY METHOD**")
        st.write("\n🔍 Debug info:")
        for method_name, result in methods.items():
            if 'error' in result:
                st.write(f"   {method_name}: {result['error']}")
            elif 'content' in result:
                st.write(f"   {method_name}: {len(result['content'])} chars, valid: {result.get('valid_json', False)}")
        return None
    
    # Find the best method (most content)
    best_method = max(valid_methods.keys(), key=lambda k: len(valid_methods[k]['content']))
    best_result = valid_methods[best_method]
    
    st.write(f"🎯 **BEST METHOD: {best_method}**")
    st.write(f"📏 Content length: {len(best_result['content'])} characters")
    
    if 'raw_length' in best_result:
        st.write(f"📄 Raw vs Decoded: {best_result['raw_length']} → {best_result['decoded_length']}")
    
    # Show all valid methods comparison
    st.write(f"\n📈 **ALL VALID METHODS:**")
    for method_name in sorted(valid_methods.keys()):
        result = valid_methods[method_name]
        st.write(f"   {method_name}: {len(result['content'])} characters")
    
    # Show a preview of the best content
    st.write(f"\n📋 **PREVIEW OF BEST RESULT:**")
    preview = best_result['content'][:500] + "..." if len(best_result['content']) > 500 else best_result['content']
    st.code(preview, language='json')
    
    return best_method, best_result

def main():
    """Main app interface"""
    st.title("🔍 JSON Extraction Methods Test")
    st.markdown("**Test different ways to extract complete JSON from stCodeCopyButton**")
    st.markdown("Focus: EXTRACTION METHODS (not timing)")
    st.markdown("---")
    
    # URL input
    col1, col2 = st.columns([2, 1])
    
    with col1:
        url = st.text_input(
            "URL to test:",
            placeholder="https://example.com/article",
            help="URL to extract content from (will be processed by chunk.dejan.ai)"
        )
        
        if st.button("🧪 Test Extraction Methods", type="primary", use_container_width=True):
            if not url:
                st.error("Please enter a URL")
            else:
                test_extraction_methods_workflow(url)
    
    with col2:
        st.info("""
        **What this tests:**
        - getAttribute methods
        - JavaScript execution  
        - Multiple attributes
        - Element text content
        - Page source extraction
        - Retry strategies
        """)

def test_extraction_methods_workflow(url):
    """Run the complete extraction methods test"""
    
    # Extract content
    with st.spinner("Extracting content..."):
        content = extract_content_simple(url)
    
    st.success(f"Content ready: {len(content)} characters")
    
    # Setup and run test
    with st.spinner("Setting up browser..."):
        driver = setup_driver()
    
    try:
        with st.spinner("Processing with chunk.dejan.ai..."):
            # Navigate and submit
            driver.get("https://chunk.dejan.ai/")
            time.sleep(5)
            
            # Fill form
            wait = WebDriverWait(driver, 30)
            input_field = wait.until(EC.presence_of_element_located((By.ID, "text_area_1")))
            input_field.clear()
            input_field.send_keys(content)
            
            submit_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="stBaseButton-secondary"]')))
            submit_button.click()
            
            # Wait for processing (4th fetch + 1 second)
            processing_complete = wait_for_processing_simple(driver)
            
            if not processing_complete:
                st.error("❌ Processing timeout - copy button never appeared")
                return
        
        st.success("✅ Processing complete - testing extraction methods...")
        
        # Test all extraction methods
        methods = test_extraction_methods(driver)
        
        # Analyze results
        result = analyze_methods(methods)
        
        if result:
            method_name, best_result = result
            st.success(f"🎉 **WINNER: {method_name}** successfully extracted {len(best_result['content'])} characters!")
            
            # Offer to download the result
            st.download_button(
                "💾 Download Best Result JSON",
                best_result['content'],
                f"extracted_json_{int(time.time())}.json",
                "application/json"
            )
        else:
            st.error("❌ No method successfully extracted valid JSON")
            st.info("💡 Try a different URL or check the chunk.dejan.ai processing")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
