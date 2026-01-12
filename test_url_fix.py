from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

def test_url():
    options = Options()
    # Use existing profile to skip login if possible, or just checking public/login page behavior
    options.add_argument(f"user-data-dir={os.getcwd()}/user_data")
    options.add_argument("--headless=new") # Headless for speed/check
    
    driver = webdriver.Chrome(options=options)
    
    target_symbol = "SBIN"
    # The proposed fix URL
    url = f"https://tv.dhan.co/chart/?symbol=NSE:{target_symbol}"
    
    print(f"Testing URL: {url}")
    try:
        driver.get(url)
        # Wait for title or some element
        time.sleep(5) # Simple wait for load
        
        page_title = driver.title
        print(f"Page Title: {page_title}")
        
        # Check standard TradingView legend elements
        # Usually checking the title or page source for the symbol
        page_source = driver.page_source
        
        if target_symbol in page_title or target_symbol in page_source:
             print("RESULT: SUCCESS (Symbol found)")
        else:
             print("RESULT: FAILURE (Symbol not found)")
             
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_url()
