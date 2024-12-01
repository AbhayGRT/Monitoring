import os
import time
import logging
import re
import json
import pandas as pd
import boto3
from openpyxl import load_workbook
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from io import BytesIO

# Load environment variables
load_dotenv()
username = os.getenv("USER_EMAIL")
password = os.getenv("PASSWORD")
aws_access_key = os.getenv("AWS_ACCESS_KEY")
aws_secret_key = os.getenv("AWS_SECRET_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Selenium options
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--incognito')
options.add_argument('window-size=1200x600')
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)

# Initialize the WebDriver
driver = webdriver.Chrome(options=options)
cookies = []

# Load JSON metadata
with open('localMetaInfo.json', 'r') as file:
    data = json.load(file)

# Extract metadata
host_name_meta = data.get("host_name", [])
panel_meta = data.get("panel", [])
no_of_rows_to_scrape_meta = data.get("no_of_rows_to_scrape", 10)
duration_meta = data.get("duration", "6h")
output_directory_name_meta = data.get("output_directory_name","si-grafana-labs")


s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)

def login(LOGIN_URL):
    """Logs in to Grafana and saves cookies."""
    logger.info("Navigating to login page...")
    driver.get(LOGIN_URL)
    try:
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "user"))
        )
        password_field = driver.find_element(By.NAME, "password")
        logger.info("Login form found. Proceeding to login.")
    except Exception as e:
        logger.error(f"Error finding the login fields: {e}")
        driver.quit()
        exit()

    username_field.send_keys(username)
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "css-8tk2dk-input-input"))
        )
        logger.info("Login successful. Saving cookies...")
        time.sleep(5)
        global cookies
        cookies = driver.get_cookies()
        logger.info(f"Cookies saved: {cookies}")
    except Exception as e:
        logger.error(f"Error during login: {e}")
        driver.quit()
        exit()

def extract_column_header(html_content):
    """Extracts column header data from the given HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    header_divs = soup.find_all('div', class_='css-1plr551')
    column_header = [header.find('button').find('div').text for header in header_divs if header.find('button')]
    return column_header

def extract_main_content(html_content):
    """Extracts main content data from the given HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    rows = soup.find_all('div', class_='css-1e8ylo6-row')
    if not rows:
        logger.info("No rows found.")
        return []

    logger.info(f"Found {len(rows)} rows.")
    rows_to_process = rows[:no_of_rows_to_scrape_meta]
    extracted_data = []

    for i, row_div in enumerate(rows_to_process, start=1):
        cell_divs = row_div.find_all('div', class_='css-jacnc-cellContainerOverflow')
        extracted_text = [cell.get_text(strip=True) for cell in cell_divs]
        extracted_data.append(extracted_text)

    return extracted_data

def navigate_to_panel(url):
    """Navigates to the specified panel URL and checks for success."""
    driver.get(url)
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get(url)

    if driver.current_url != url:
        logger.error(f"Navigation failed. Current URL is: {driver.current_url}")
        return False

    logger.info(f"Navigation successful to {url}")
    return True

def extract_panel_title():
    """Extracts the panel title from the page."""
    try:
        title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "css-1ej1m3x-panel-title"))
        )
        title_text = title_element.text
        logger.info(f"Extracted panel title: {title_text}")
        return title_text
    except Exception as e:
        logger.error(f"Error extracting panel title: {e}")
        return None

def extract_column_header_data():
    """Extracts the column header data from the page."""
    try:
        header_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "css-1y4sadw-row"))
        )
        header = extract_column_header(header_element.get_attribute('outerHTML'))
        return header
    except Exception as e:
        logger.error(f"Error extracting column header: {e}")
        return None

def extract_main_content_data():
    """Extracts main content data from the page."""
    try:
        content_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "scrollbar-view"))
        )
        if content_elements:
            last_element = content_elements[-1]
            full_html_content = last_element.get_attribute('outerHTML')
            main_content_data = extract_main_content(full_html_content)
            return main_content_data
        else:
            logger.info("No elements found with the class 'scrollbar-view'.")
            return None
    except Exception as e:
        logger.error(f"Error extracting main content: {e}")
        return None

def save_data_to_excel(host, title_text, header, main_content_data, output_dir):
    """Saves extracted data to an Excel file with specific sheets for each host."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    if header and main_content_data:
        df = pd.DataFrame(main_content_data, columns=header)
        file_name = f"{host}.xlsx".replace(' ', '_')
        file_path = os.path.join(output_dir, file_name)
        
        if os.path.exists(file_path):
            with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                sheet_name = title_text[:31]
                df.to_excel(writer, index=False, sheet_name=sheet_name)
        else:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                sheet_name = title_text[:31]
                df.to_excel(writer, index=False, sheet_name=sheet_name)
        
        print(f"Data for host '{host}' saved to Excel file: {file_path}")


 
def navigate_and_scrape(host,output_dir,PANEL_NUMBERS,BASE_URL):
    """Navigates to panels and extracts data."""
    for panel in PANEL_NUMBERS:
        full_url = f"{BASE_URL}{panel}"
        logger.info(f"Attempting to navigate to: {full_url}")
        
        if not navigate_to_panel(full_url):
            continue
        
        title_text = extract_panel_title()
        if not title_text:
            continue
        
        header = extract_column_header_data()
        if not header:
            continue
        
        main_content_data = extract_main_content_data()
        if not main_content_data:
            continue
        
        save_data_to_excel(host, title_text, header, main_content_data,output_dir)
        time.sleep(10)

def upload_excel_files_to_s3(output_dir):
    """Uploads all Excel files from the output directory to an S3 bucket."""
    if not os.path.exists(output_dir):
        print(f"Directory '{output_dir}' does not exist.")
        return

    for file_name in os.listdir(output_dir):
        if file_name.endswith('.xlsx'):
            file_path = os.path.join(output_dir, file_name)
            try:
                with open(file_path, 'rb') as file_data:
                    s3_client.put_object(
                        Bucket=output_dir,
                        Key=file_name,
                        Body=file_data,
                        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                print(f"File '{file_name}' uploaded to S3 bucket '{output_dir}'.")
            except Exception as e:
                print(f"Error uploading file '{file_name}': {e}")
                
def main():
    start_time = time.time()    
    try:
        LOGIN_URL = "https://grafana-apj.trafficpeak.live/login"
        login(LOGIN_URL)

        for host in host_name_meta:
            BASE_URL = f"https://grafana-apj.trafficpeak.live/d/be2way1ysetc0d/error-insights?orgId=431&var-AND_reqHost=IN&var-reqHost={host}&from=now-{duration_meta}&to=now&viewPanel="
            PANEL_NUMBERS = panel_meta
            OUTPUT_DIR = output_directory_name_meta
            logger.info(f"Starting scraping for host: {host}")
            navigate_and_scrape(host,OUTPUT_DIR,PANEL_NUMBERS,BASE_URL)
            logger.info(f"Scraping completed for host: {host}. Moving to the next host if defined.")            
        
        logger.info("Script completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred during script execution: {e}")
    finally:
        upload_excel_files_to_s3(output_directory_name_meta)
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Total runtime: {total_time:.2f} seconds")
        print(f"Total runtime: {total_time:.2f} seconds")
        driver.quit()

if __name__ == "__main__":
    main()