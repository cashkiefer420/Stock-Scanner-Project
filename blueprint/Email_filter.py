import json
import os
import time
import pytz
from datetime import datetime

# Base directory for the project
base_dir = r"/home/ec2-user/Stock-Scanner-Project/"
output_directory = os.path.join(base_dir, "json")
Stock_data_export = os.path.join(output_directory, "stock_data_export.json")

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
    {"name": "Filtered_pe_10_in.json", "key": "P/E Change (3 Mon)", "condition": lambda x: safe_float(x) > 10},
    {"name": "Filtered_pe_20_in.json", "key": "P/E Change (3 Mon)", "condition": lambda x: safe_float(x) > 20},
    {"name": "Filtered_pe_30_in.json", "key": "P/E Change (3 Mon)", "condition": lambda x: safe_float(x) > 30},
    {"name": "Filtered_pe_10_de.json", "key": "P/E Change (3 Mon)", "condition": lambda x: safe_float(x) < -10},
    {"name": "Filtered_pe_20_de.json", "key": "P/E Change (3 Mon)", "condition": lambda x: safe_float(x) < -20},
    {"name": "Filtered_pe_30_de.json", "key": "P/E Change (3 Mon)", "condition": lambda x: safe_float(x) < -30},
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
        print("\n[INFO] Midnight in New York detected. Resetting filtered files...")
        for filter_item in filters:
            file_path = os.path.join(output_directory, filter_item["name"])
            with open(file_path, 'w') as file:
                json.dump({"stocks": []}, file, indent=4)  # Ensuring correct format
            print(f"  - {filter_item['name']} has been reset.")
        print("[INFO] Reset complete.\n")

def filter_data():
    """Processes stock data and filters it based on predefined conditions."""
    try:
        with open(Stock_data_export, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print("[ERROR] Stock data file not found. Skipping filtering.")
        return
    except json.JSONDecodeError:
        print("[ERROR] Stock data file is not valid JSON. Skipping filtering.")
        return

    print("\n[INFO] Starting data filtering...")

    for filter_item in filters:
        filtered_stocks = [
            item for item in data if filter_item["condition"](item.get(filter_item["key"], 0))
        ]

        file_path = os.path.join(output_directory, filter_item["name"])
        with open(file_path, 'w') as outfile:
            json.dump({"stocks": filtered_stocks}, outfile, indent=4)  # Ensuring correct format

        print(f"  - {filter_item['name']} updated with {len(filtered_stocks)} stocks.")

    print("[INFO] Filtering complete.\n")
    
def main():
    """Main loop that resets and filters data every 5 minutes."""
    while True:
        reset_filtered_files()
        filter_data()
        print("[INFO] Sleeping for 5 minutes...\n")
        time.sleep(300)  # Sleep for 5 minutes

if __name__ == "__main__":
    main()