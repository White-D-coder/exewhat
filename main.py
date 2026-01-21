import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse
import time
import random
import os

# Configuration
WAIT_TIME_LOGIN = 60
DELAY_BETWEEN_MESSAGES = (10, 20)

def initialize_driver():
    """Initializes the Chrome WebDriver."""
    options = webdriver.ChromeOptions()
    
    # Check if we are running in a container/cloud (Environment Variable)
    if os.environ.get("HEADLESS_MODE") == "true":
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # User Agent is vital for Headless WhatsApp to work (prevents some blocks)
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def send_whatsapp_message(driver, phone, message, min_delay=10, max_delay=20):
    """Sends a WhatsApp message using button click or Enter key."""
    try:
        encoded_message = urllib.parse.quote(message)
        url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_message}"
        
        driver.get(url)
        
        # Wait for either the send button OR the input box to be ready
        # This handles cases where the text is pre-filled but button might take a split second
        try:
             WebDriverWait(driver, 30).until(
                EC.any_of(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "span[data-icon='send']")),
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Send']")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
                )
            )
        except Exception as e:
            print(f"Timeout waiting for chat to load: {e}")
            return False, f"Timeout loading chat for {phone}"

        time.sleep(random.uniform(2, 4)) # Wait for things to settle

        # Method 1: Try clicking the Send Button
        clicked = False
        try:
            # Try efficient selectors first
            send_btn = driver.find_element(By.CSS_SELECTOR, "span[data-icon='send']")
            send_btn.click()
            clicked = True
        except:
            try:
                # Fallback selector
                send_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Send']")
                send_btn.click()
                clicked = True
            except:
                pass # Proceed to Method 2 if click fails

        # Method 2: If click failed (or just to be sure), ensure focus is on input and hit Enter
        if not clicked:
            try:
                # Locate the chat input box
                # Usually has contenteditable="true"
                input_box = driver.find_element(By.CSS_SELECTOR, "div[contenteditable='true']")
                input_box.send_keys(Keys.ENTER)
                clicked = True
            except Exception as e:
                # Last resort: ActionChains Enter
                actions = ActionChains(driver)
                actions.send_keys(Keys.ENTER)
                actions.perform()
                clicked = True
        
        if clicked:
            # Random delay to minimize ban risk
            sleep_time = random.uniform(min_delay, max_delay)
            time.sleep(sleep_time)
            return True, f"Sent to {phone}. Waited {sleep_time:.1f}s."
        else:
            return False, f"Could not find Send button or Input box for {phone}"

    except Exception as e:
        return False, f"Failed to send to {phone}: {str(e)}"

def process_messages(df, name_col, phone_col, custom_message="", custom_link="", min_delay=10, max_delay=20, batch_size=0, batch_pause=0):
    """
    Generator function that processes the DataFrame and yields status updates.
    Yields: (index, status_text_for_log, status_value_for_df)
    """
    yield "init", "Initializing Chrome Driver...", None
    
    try:
        driver = initialize_driver()
        
        yield "login", "Opening WhatsApp Web. Please scan the QR code within 60 seconds...", None
        driver.get("https://web.whatsapp.com")
        
        # Wait for login
        try:
            WebDriverWait(driver, WAIT_TIME_LOGIN).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#pane-side"))
            )
            yield "info", "Login successful! Starting messaging...", None
        except Exception:
             yield "error", "Login timed out or failed. Please refresh and try again.", None
             driver.quit()
             return

        messages_sent_in_batch = 0

        for index, row in df.iterrows():
            if str(row.get('Status', '')).lower() == 'sent':
                continue
            
            # Batch Pause Logic
            if batch_size > 0 and messages_sent_in_batch >= batch_size:
                yield "info", f"Batch limit reached. Pausing for {batch_pause} seconds for safety...", None
                time.sleep(batch_pause)
                messages_sent_in_batch = 0 # Reset batch counter

            phone = str(row[phone_col]).strip()
            name = str(row[name_col]) if name_col in row else 'User'
            
            # Message Construction Logic
            msg_content = ""
            if 'Message' in row:
                msg_content = str(row['Message'])
                if msg_content == 'nan': msg_content = ''
            
            if not msg_content and custom_message:
                msg_content = custom_message.replace('{Name}', name)
            
            if not msg_content:
                msg_content = f"Hello {name}"
                
            if custom_link:
                msg_content = f"{msg_content}\n\n{custom_link}"
            
            yield "progress", f"Sending to {name} ({phone})...", None
            
            success, log_msg = send_whatsapp_message(driver, phone, msg_content, min_delay, max_delay)
            
            status_val = 'Sent' if success else 'Failed'
            yield "update", log_msg, (index, status_val)

            if success:
                messages_sent_in_batch += 1
            
    except Exception as e:
        yield "error", f"Critical Error: {str(e)}", None
    finally:
        if 'driver' in locals():
            driver.quit()
        yield "done", "Automation finished. Browser closed.", None

