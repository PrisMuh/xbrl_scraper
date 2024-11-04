from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def setup_driver():
    """Setup and return Chrome webdriver with options"""
    options = webdriver.ChromeOptions()
    
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)

def get_entity_links(driver, url):
    """Extract entity links directly from the webpage"""
    # Navigate to the page
    driver.get(url)
    
    # Wait for the table to be present
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "filing.clickable"))
    )
    
    # Get the page source after JavaScript has loaded
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')
    entities = []
    
    # Find all rows in the table
    for row in soup.find_all('tr', class_='filing clickable'):
        # Get the entity link
        entity_link = row.find('td', class_='entity').find('a')
        if entity_link:
            entities.append({
                'name': entity_link.get_text(),
                'url': entity_link['href']
            })
    
    return entities

def clean_text(text):
    """Clean extracted text by removing extra whitespace and newlines"""
    if text:
        return ' '.join(text.strip().split())
    return ''

def extract_entity_name(text):
    """Extract entity name from text that might include '(X filings)'"""
    if text:
        return re.sub(r'\s*\(\d+\s*filings\)', '', text).strip()
    return ''

def scrape_entity_page(driver, entity):
    """Scrape specific data from individual entity page"""
    try:
        base_url = "https://filings.xbrl.org"
        full_url = base_url + entity['url']
        
        driver.get(full_url)
        
        # Wait for the details table to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "details"))
        )
        
        # Get the page source after JavaScript has loaded
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find the details table
        table = soup.find('table', class_='details')
        
        # Initialize dictionary for data
        data = {
            'Entity': None,
            'LEI': None,
            'Period_End': None,
            'Language': None,
            'Country': None,
            'Hash': None
        }
        
        # Extract data from table
        if table:
            rows = table.find_all('tr')
            for row in rows:
                header = row.find('th')
                value = row.find('td')
                
                if header and value:
                    header_text = clean_text(header.get_text())
                    
                    if header_text == 'Entity':
                        data['Entity'] = extract_entity_name(value.get_text())
                    elif header_text == 'LEI':
                        lei_link = value.find('a')
                        if lei_link:
                            data['LEI'] = clean_text(lei_link.get_text())
                    elif header_text == 'Period end':
                        data['Period_End'] = clean_text(value.get_text())
                    elif header_text == 'Language':
                        data['Language'] = clean_text(value.get_text())
                    elif header_text == 'Country':
                        country_text = clean_text(value.get_text())
                        data['Country'] = re.sub(r'\s*\([A-Z]{2}\)', '', country_text).strip()
                    elif header_text == 'Hash':
                        hash_span = value.find('span', class_='hash')
                        if hash_span:
                            data['Hash'] = clean_text(hash_span.get_text())
        
        return data
        
    except Exception as e:
        print(f"Error scraping {entity['name']}: {str(e)}")
        return None

def main():
    # URL of the main page with the entity table
    main_url = "https://filings.xbrl.org"  # Replace with the actual URL
    
    # Setup the webdriver
    driver = setup_driver()
    
    try:
        # Get all entity links directly from the webpage
        entities = get_entity_links(driver, main_url)
        
        # List to store all scraped data
        all_data = []
        
        # Process each entity
        for entity in entities:
            print(f"Scraping data for: {entity['name']}")
            
            # Scrape the entity page
            data = scrape_entity_page(driver, entity)
            
            if data:
                all_data.append(data)
                print("Successfully scraped:", data)
            
            # Be nice to the server
            time.sleep(2)
        
        # Convert to DataFrame and save
        df = pd.DataFrame(all_data)
        df.to_csv('entity_data.csv', index=False)
        print(f"\nSuccessfully scraped {len(all_data)} entities")
        print("Data saved to 'entity_data.csv'")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()