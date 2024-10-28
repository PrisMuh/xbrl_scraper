import requests
import os

URL = 'https://filings.xbrl.org/api/filings?include=entity,language&filter=%5B%7B%22name%22%3A%22input_filing.filing_source.program%22%2C%22op%22%3A%22eq%22%2C%22val%22%3A%22ESEF%22%7D%5D&sort=-date_added&page%5Bsize%5D=20&page%5Bnumber%5D=1'
BASE_URL = 'https://filings.xbrl.org'
DOWNLOAD_FOLDER = "xbrl_downloads"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def download_xbrl_reports():
    response = requests.get(URL)
    if response.status_code == 200:
        filings = response.json()
        for filing in filings.get('data', []):
            report_url = filing['attributes'].get('report_url')
            if report_url:
                full_url = BASE_URL + report_url
                file_name = os.path.join(DOWNLOAD_FOLDER, report_url.split('/')[-1])
                with open(file_name, 'wb') as f:
                    f.write(requests.get(full_url).content)
                print(f"Downloaded {file_name}")
    else:
        print(f"Failed to retrieve filings. Status code: {response.status_code}")

download_xbrl_reports()
