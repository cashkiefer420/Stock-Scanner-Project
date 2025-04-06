import json
import os
import time
import pytz
from datetime import datetime
import boto3

# Base directory for the project
base_dir = r"/home/ec2-user/Stock-Scanner-Project"
output_directory = os.path.join(base_dir, "json")
Stock_data_export = os.path.join(output_directory, "stock_data_export.json")
S3_BUCKET_NAME = "exportbucket--use2-az1--x-s3"
S3_EXPORT_FILE_KEY = "stock_data_export.json"
# Create the /json directory if it doesn't exist
os.makedirs(output_directory, exist_ok=True)

# Time zone for New York City
new_york_tz = pytz.timezone("America/New_York")

def safe_float(value):
    """Safely converts a value to float, returning 0 if conversion fails."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0

# Define the filters
filters = [
    {"name": "Filtered_pe_10_in.json", "key": "P/E Change (3mo)", "condition": lambda x: safe_float(x) > 10},
    {"name": "Filtered_pe_20_in.json", "key": "P/E Change (3mo)", "condition": lambda x: safe_float(x) > 20},
    {"name": "Filtered_pe_30_in.json", "key": "P/E Change (3mo)", "condition": lambda x: safe_float(x) > 30},
    {"name": "Filtered_pe_10_de.json", "key": "P/E Change (3mo)", "condition": lambda x: safe_float(x) < -10},
    {"name": "Filtered_pe_20_de.json", "key": "P/E Change (3mo)", "condition": lambda x: safe_float(x) < -20},
    {"name": "Filtered_pe_30_de.json", "key": "P/E Change (3mo)", "condition": lambda x: safe_float(x) < -30},
    {"name": "Filtered_market_cap_10_in.json", "key": "Market Cap Change (3 Mon)", "condition": lambda x: safe_float(x) > 10},
    {"name": "Filtered_market_cap_20_in.json", "key": "Market Cap Change (3 Mon)", "condition": lambda x: safe_float(x) > 20},
    {"name": "Filtered_market_cap_30_in.json", "key": "Market Cap Change (3 Mon)", "condition": lambda x: safe_float(x) > 30},
    {"name": "Filtered_market_cap_10_de.json", "key": "Market Cap Change (3 Mon)", "condition": lambda x: safe_float(x) < -10},
    {"name": "Filtered_market_cap_20_de.json", "key": "Market Cap Change (3 Mon)", "condition": lambda x: safe_float(x) < -20},
    {"name": "Filtered_market_cap_30_de.json", "key": "Market Cap Change (3 Mon)", "condition": lambda x: safe_float(x) < -30},
    {"name": "Filtered_volume_2.5x.json", "key": "DVAV (Day Volume Over Average Volume)", "condition": lambda x: safe_float(x) > 2.5},
    {"name": "Filtered_volume_3x.json", "key": "DVAV (Day Volume Over Average Volume)", "condition": lambda x: safe_float(x) > 3},
    {"name": "Filtered_price_20_in.json", "key": "Price Change Today", "condition": lambda x: safe_float(x) > 20},
    {"name": "Filtered_price_50_in.json", "key": "Price Change Today", "condition": lambda x: safe_float(x) > 50},
    {"name": "Filtered_price_75_in.json", "key": "Price Change Today", "condition": lambda x: safe_float(x) > 75},
    {"name": "Filtered_price_10_de.json", "key": "Price Change Today", "condition": lambda x: safe_float(x) < -10},
    {"name": "Filtered_price_20_de.json", "key": "Price Change Today", "condition": lambda x: safe_float(x) < -20},
    {"name": "Filtered_DVSA_50.json", "key": "DVSA (Volume Today Over Shares Available)", "condition": lambda x: safe_float(x) > 50},
    {"name": "Filtered_DVSA_100.json", "key": "DVSA (Volume Today Over Shares Available)", "condition": lambda x: safe_float(x) > 100},
]

def reset_filtered_files():
    """Wipes all filtered JSON files at midnight New York time."""
    current_time = datetime.now(new_york_tz)
    if current_time.hour == 0 and current_time.minute == 0:
        print("It's midnight in New York. Wiping filtered files...")
        for filter_item in filters:
            file_path = os.path.join(output_directory, filter_item["name"])
            with open(file_path, 'w') as file:
                json.dump({}, file)
        print("Filtered files wiped.")

def filter_data():
    """Processes stock data and filters it based on predefined conditions."""
    try:
        with open(Stock_data_export, 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error: Could not load stock data.")
        return

    print("Filtering data...")

    for filter_item in filters:
        filtered_data = {
            item["Ticker"]: item
            for item in data
            if filter_item["condition"](item.get(filter_item["key"], 0))
        }

        # Save filtered results
        file_path = os.path.join(output_directory, filter_item["name"])
        with open(file_path, 'w') as outfile:
            json.dump(filtered_data, outfile, indent=4)

    print("Filtering complete.")

def download_from_s3():
    """Downloads the stock data export file from S3."""
    try:
        s3_client = boto3.client('s3')
        s3_client.download_file(S3_BUCKET_NAME, S3_EXPORT_FILE_KEY, Stock_data_export)
        print(f"[INFO] {S3_EXPORT_FILE_KEY} downloaded from S3 bucket {S3_BUCKET_NAME}")
    except Exception as e:
        print(f"[ERROR] Error downloading {S3_EXPORT_FILE_KEY} from S3: {e}")

def main():
    """Main loop that resets and filters data every 3 minutes."""
    while True:
        try:
            reset_filtered_files()
            download_from_s3()
            filter_data()
        except Exception as e:
            print(f"[ERROR] Exception occurred: {e}")
        print("Sleeping for 3 minutes...")
        time.sleep(180)  # Sleep for 3 minutes

if __name__ == "__main__":
    main()
