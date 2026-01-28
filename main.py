import smtplib
import ssl
from email.message import EmailMessage
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

def send_email(smtp_settings, recipient_email, subject, body):
    """Sends an email using the provided SMTP settings with fallback."""
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = smtp_settings['sender_email']
    msg['To'] = recipient_email
    
    context = ssl.create_default_context()
    
    # Attempt 1: As configured (usually SSL 465)
    try:
        with smtplib.SMTP_SSL(smtp_settings['server'], smtp_settings['port'], context=context) as smtp:
            smtp.login(smtp_settings['sender_email'], smtp_settings['password'])
            smtp.send_message(msg)
        return True, f"Email sent to {recipient_email}"
        
    except Exception as e_ssl:
        # Attempt 2: Fallback to TLS 587 (Common for Gmail if SSL fails)
        try:
            # Only try fallback if original port was 465 (SSL)
            if smtp_settings['port'] == 465:
                print(f"SSL failed ({e_ssl}), retrying TLS on port 587...")
                with smtplib.SMTP(smtp_settings['server'], 587) as smtp:
                    smtp.starttls(context=context)
                    smtp.login(smtp_settings['sender_email'], smtp_settings['password'])
                    smtp.send_message(msg)
                return True, f"Email sent to {recipient_email} (via TLS)"
            else:
                raise e_ssl # Re-raise if we weren't on 465
                
        except Exception as e_tls:
             return False, f"Failed to send to {recipient_email}. SSL Error: {str(e_ssl)} | TLS Error: {str(e_tls)}"

def process_messages(df, name_col, phone_col, email_col=None, 
                     enable_wa=True, enable_email=False,
                     custom_message="", custom_link="", 
                     email_subject="", email_body="", smtp_settings=None,
                     min_delay=10, max_delay=20, batch_size=0, batch_pause=0):
    """
    Generator function that processes the DataFrame and yields status updates.
    Yields: (index, status_text_for_log, status_value_for_df, type)
    """
    driver = None
    
    if enable_wa:
        yield "init", "Initializing Chrome Driver...", None, 'wa'
        try:
            driver = initialize_driver()
            yield "login", "Opening WhatsApp Web. Please scan the QR code within 60 seconds...", None, 'wa'
            driver.get("https://web.whatsapp.com")
            
            # Wait for login
            try:
                WebDriverWait(driver, WAIT_TIME_LOGIN).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#pane-side"))
                )
                yield "info", "WhatsApp Login successful!", None, 'wa'
            except Exception:
                yield "error", "WhatsApp Login timed out or failed.", None, 'wa'
                driver.quit()
                return
        except Exception as e:
            yield "error", f"Driver Init Failed: {e}", None, 'wa'
            return

    yield "info", "Starting processing...", None, 'system'

    try:
        messages_sent_in_batch = 0
        
        for index, row in df.iterrows():
            name = str(row[name_col]) if name_col in row else 'User'
            
            # --- WhatsApp Processing ---
            if enable_wa:
                # check if already sent
                if str(row.get('Status', '')).lower() != 'sent':
                    
                    if batch_size > 0 and messages_sent_in_batch >= batch_size:
                        yield "info", f"Batch limit reached. Pausing for {batch_pause}s...", None, 'wa'
                        time.sleep(batch_pause)
                        messages_sent_in_batch = 0

                    phone = str(row[phone_col]).strip()
                    
                    # Message Construction
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
                    
                    yield "progress", f"WA: Sending to {name} ({phone})...", None, 'wa'
                    
                    success, log_msg = send_whatsapp_message(driver, phone, msg_content, min_delay, max_delay)
                    
                    status_val = 'Sent' if success else 'Failed'
                    yield "update", log_msg, (index, 'Status', status_val), 'wa' # Added col name to tuple

                    if success:
                        messages_sent_in_batch += 1

            # --- Email Processing ---
            if enable_email and email_col and smtp_settings:
                # check if already sent
                if str(row.get('Email_Status', '')).lower() != 'sent':
                    email_addr = str(row[email_col]).strip()
                    
                    if email_addr and email_addr != 'nan':
                        # Email Body Construction
                        e_body = email_body.replace('{Name}', name)
                        e_subject = email_subject.replace('{Name}', name)
                        
                        yield "progress", f"Email: Sending to {name} ({email_addr})...", None, 'email'
                        
                        success, log_msg = send_email(smtp_settings, email_addr, e_subject, e_body)
                        
                        status_val = 'Sent' if success else 'Failed'
                        yield "update", log_msg, (index, 'Email_Status', status_val), 'email'
                        
                        # Small delay between emails to be safe
                        time.sleep(1) 
                    else:
                        yield "info", f"Skipping Email for {name} (No Email)", None, 'email'


    except Exception as e:
        yield "error", f"Critical Error in Loop: {str(e)}", None, 'system'
    finally:
        if driver:
            driver.quit()
        yield "done", "Automation finished.", None, 'system'

