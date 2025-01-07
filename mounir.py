import requests
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

spreadsheet_name = "Products Monitor" # Update with your Google Sheet name
worksheet_name = "Sheet1"
monitoring_interval = 120  # in seconds

# Set up Google Sheets API credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope) # Update with path to your credentials file
client = gspread.authorize(creds)

# Open the Google Sheet
sheet = client.open(spreadsheet_name).worksheet(worksheet_name)

def fetch_products(products_url):
    response = requests.get(products_url)
    if response.status_code == 200:
        data = response.json()
        return data.get('products', [])
    else:
        print(f"Failed to retrieve products data: {response.status_code}")
        return []

def format_dates(published_at, updated_at):
    published_at_formatted = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%S%z").strftime("%y-%m-%d")
    updated_at_formatted = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%S%z").strftime("%y-%m-%d | %H:%M")
    return published_at_formatted, updated_at_formatted

def write_to_sheet(products, url):
    existing_products = read_sheet()
    headers = ["Handle", "Published At", "Updated At", "Times Updated At Changed"]
    rows = [headers]
    for product in products:
        handle, published_at, updated_at = product["handle"], product["published_at"], product["updated_at"]
        handle = f"{url}/products/{handle}"
        published_at, updated_at = format_dates(published_at, updated_at)
        if handle not in existing_products:
            product["updated_at_changes"] = 0
        else:
            existing_product = existing_products[handle]
            if (existing_product["Published At"] != published_at or
                existing_product["Updated At"] != updated_at):
                product["updated_at_changes"] = int(existing_product["Times Updated At Changed"]) + 1
            else:
                product["updated_at_changes"] = int(existing_product["Times Updated At Changed"])
        rows.append([handle, published_at, updated_at, product["updated_at_changes"]])
    sheet.clear()
    sheet.append_rows(rows)

def read_sheet():
    records = sheet.get_all_records()
    return {record["Handle"]: record for record in records}

def monitor_products(url):
    products_url = url + "/products.json?page=1&limit=2000"
    
    # Initial fetch and write to Google Sheets
    products = fetch_products(products_url)
    write_to_sheet(products, url)

    # Monitor changes
    while True:
        time.sleep(monitoring_interval)  # Wait for 2 minutes
        products = fetch_products(products_url)
        existing_products = read_sheet()
        
        updated_products = []
        for product in products:
            handle, published_at, updated_at = product["handle"], product["published_at"], product["updated_at"]
            handle = f"{url}/products/{handle}"
            published_at, updated_at = format_dates(published_at, updated_at)
            if handle in existing_products:
                existing_product = existing_products[handle]
                if (existing_product["Published At"] != published_at or
                    existing_product["Updated At"] != updated_at):
                    product["updated_at_changes"] = int(existing_product["Times Updated At Changed"]) + 1
                else:
                    product["updated_at_changes"] = int(existing_product["Times Updated At Changed"])
            else:
                product["updated_at_changes"] = 0
            updated_products.append(product)

        write_to_sheet(updated_products, url)


if __name__ == "__main__":
    url = "https://sqinwear.com"
    monitor_products(url)