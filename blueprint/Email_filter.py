import json
import os
import time
import pytz
from datetime import datetime

# Base directory for the project
base_dir = r"/home/ec2-user/Stock-Scanner-Project/"
Stock_data_export = os.path.join(base_dir, "json", "stock_data_export.json")
# Define the /json output directory
output_directory = os.path.join(base_dir, "json")

# Create the /json directory if it doesn't exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Time zone for New York City
new_york_tz = pytz.timezone("America/New_York")

def safe_float(value):
    # Check if the value is a string and contains a non-numeric value
    if isinstance(value, str) and not value.replace('.', '', 1).isdigit():
        return 0  # Return 0 if the value is a non-numeric string
    
    try:
        return float(value)  # Try to convert the value to float
    except (ValueError, TypeError):
        return 0  # Return 0 if conversion fails

# Define the filters as separate conditions for each JSON file
filters = [
    {"file_name": os.path.join(output_directory, "Filtered_pe_10_in.json"), "condition": lambda ticker: float(ticker.get("P/E Change (3mo)", 0)) > 10, "field": "P/E Change (3mo)"},
    {"file_name": os.path.join(output_directory, "Filtered_pe_20_in.json"), "condition": lambda ticker: float(ticker.get("P/E Change (3mo)", 0)) > 20, "field": "P/E Change (3mo)"},
    {"file_name": os.path.join(output_directory, "Filtered_pe_30_in.json"), "condition": lambda ticker: float(ticker.get("P/E Change (3mo)", 0)) > 30, "field": "P/E Change (3mo)"},
    {"file_name": os.path.join(output_directory, "Filtered_pe_10_de.json"), "condition": lambda ticker: float(ticker.get("P/E Change (3mo)", 0)) < -10, "field": "P/E Change (3mo)"},
    {"file_name": os.path.join(output_directory, "Filtered_pe_20_de.json"), "condition": lambda ticker: float(ticker.get("P/E Change (3mo)", 0)) < -20, "field": "P/E Change (3mo)"},
    {"file_name": os.path.join(output_directory, "Filtered_pe_30_de.json"), "condition": lambda ticker: float(ticker.get("P/E Change (3mo)", 0)) < -30, "field": "P/E Change (3mo)"},
    {"file_name": os.path.join(output_directory, "Filtered_market_cap_10_in.json"), "condition": lambda ticker: float(ticker.get("Market Cap Change (3 Mon)", 0)) > 10, "field": "Market Cap Change (3 Mon)"},
    {"file_name": os.path.join(output_directory, "Filtered_market_cap_20_in.json"), "condition": lambda ticker: float(ticker.get("Market Cap Change (3 Mon)", 0)) > 20, "field": "Market Cap Change (3 Mon)"},
    {"file_name": os.path.join(output_directory, "Filtered_market_cap_30_in.json"), "condition": lambda ticker: float(ticker.get("Market Cap Change (3 Mon)", 0)) > 30, "field": "Market Cap Change (3 Mon)"},
    {"file_name": os.path.join(output_directory, "Filtered_market_cap_10_de.json"), "condition": lambda ticker: float(ticker.get("Market Cap Change (3 Mon)", 0)) < -10, "field": "Market Cap Change (3 Mon)"},
    {"file_name": os.path.join(output_directory, "Filtered_market_cap_20_de.json"), "condition": lambda ticker: float(ticker.get("Market Cap Change (3 Mon)", 0)) < -20, "field": "Market Cap Change (3 Mon)"},
    {"file_name": os.path.join(output_directory, "Filtered_market_cap_30_de.json"), "condition": lambda ticker: float(ticker.get("Market Cap Change (3 Mon)", 0)) < -30, "field": "Market Cap Change (3 Mon)"},
    {"file_name": os.path.join(output_directory, "Filtered_volume_2.5x.json"), "condition": lambda ticker: float(ticker.get("DVAV (Day Volume Over Average Volume", 0)) > 2.5, "field": "Volume Today"},
    {"file_name": os.path.join(output_directory, "Filtered_volume_1.125x.json"), "condition": lambda ticker: float(ticker.get("DVAV (Day Volume Over Average Volume", 0)) > 1.125, "field": "Volume Today"},
    {"file_name": os.path.join(output_directory, "Filtered_volume_1.25x.json"), "condition": lambda ticker: float(ticker.get("DVAV (Day Volume Over Average Volume", 0)) > 1.25, "field": "Volume Today"},
    {"file_name": os.path.join(output_directory, "Filtered_volume_1.5x.json"), "condition": lambda ticker: float(ticker.get("DVAV (Day Volume Over Average Volume", 0)) > 1.5, "field": "Volume Today"},
    {"file_name": os.path.join(output_directory, "Filtered_volume_1.75x.json"), "condition": lambda ticker: float(ticker.get("DVAV (Day Volume Over Average Volume", 0)) > 1.75, "field": "Volume Today"},
    {"file_name": os.path.join(output_directory, "Filtered_volume_2x.json"), "condition": lambda ticker: float(ticker.get("DVAV (Day Volume Over Average Volume)", 0)) > 2, "field": "DVAV (Day Volume Over Average Volume)"},
    {"file_name": os.path.join(output_directory, "Filtered_volume_3x.json"), "condition": lambda ticker: float(ticker.get("DVAV (Day Volume Over Average Volume)", 0)) > 3, "field": "DVAV (Day Volume Over Average Volume)"},
    {"file_name": os.path.join(output_directory, "Filtered_volume_5x.json"), "condition": lambda ticker: float(ticker.get("DVAV (Day Volume Over Average Volume)", 0)) > 5, "field": "DVAV (Day Volume Over Average Volume)"},
    {"file_name": os.path.join(output_directory, "Filtered_price_20_in.json"), "condition": lambda ticker: float(ticker.get("Price Change Today", 0)) > 20, "field": "Price Change Today"},
    {"file_name": os.path.join(output_directory, "Filtered_price_50_in.json"), "condition": lambda ticker: float(ticker.get("Price Change Today", 0)) > 50, "field": "Price Change Today"},
    {"file_name": os.path.join(output_directory, "Filtered_price_75_in.json"), "condition": lambda ticker: float(ticker.get("Price Change Today", 0)) > 75, "field": "Price Change Today"},
    {"file_name": os.path.join(output_directory, "Filtered_price_10_de.json"), "condition": lambda ticker: float(ticker.get("Price Change Today", 0)) < -10, "field": "Price Change Today"},
    {"file_name": os.path.join(output_directory, "Filtered_price_15_de.json"), "condition": lambda ticker: float(ticker.get("Price Change Today", 0)) < -20, "field": "Price Change Today"},
    {"file_name": os.path.join(output_directory, "Filtered_price_20_de.json"), "condition": lambda ticker: float(ticker.get("Price Change Today", 0)) < -30, "field": "Price Change Today"},
    {"file_name": os.path.join(output_directory, "Filtered_DVSA_50.json"), "condition": lambda ticker: float(ticker.get("Volume Today Over Shares Available", 0)) > 50, "field": "Volume Today Over Shares Available"},
    {"file_name": os.path.join(output_directory, "Filtered_DVSA_100.json"), "condition": lambda ticker: float(ticker.get("Volume Today Over Shares Available", 0)) > 100, "field": "Volume Today Over Shares Available"},
    {"file_name": os.path.join(output_directory, "Filtered_DVSA_150.json"), "condition": lambda ticker: float(ticker.get("Volume Today Over Shares Available", 0)) > 150, "field": "Volume Today Over Shares Available"},
]

def reset_filtered_files():
    """Wipes all filtered JSON files at midnight New York time."""
    current_time = datetime.now(new_york_tz)
    
    # Check if it's midnight (00:00) in New York time
    if current_time.hour == 0 and current_time.minute == 0:
        print("It's midnight in New York. Wiping filtered files...")
        for filter_item in filters:
            file_path = filter_item["file_name"]
            # Wipe the file content (create empty JSON object)
            with open(file_path, 'w') as file:
                json.dump({}, file)
        print("Filtered files wiped.")

# Load the JSON data from a file
def process_data():
    with open(Stock_data_export, 'r') as file:
        data = json.load(file)

    
    # Apply each filter and save to the corresponding file in the /json directory
    print("Filtering Data")
    for filter_item in filters:
        filtered_data = {}
        for item in data:
            # Retrieve values for Avg Volume, Current Price, Volume Today, DVAV, P/E Change, and Market Cap Change
            average_volume = item.get("Avg Volume (3 mon)", 0)
            current_price = item.get("Current Price", 0)
            current_volume = item.get("Volume Today", 0)
            dvav = item.get("DVAV (Day Volume Over Average Volume)", 0)
            pe_change = item.get("P/E Change (3mo)", 0)
            market_cap_change = item.get("Market Cap Change (3 Mon)", 0)
            
                # Apply the regular condition for all other filters
            if filter_item["condition"](item):
                    item[filter_item["field"]] = item.get(filter_item["field"], None)
                    filtered_data[item["Ticker"]] = item

        # Save the filtered data to the new JSON file in the /json folder
        file_path = os.path.join(output_directory, filter_item["file_name"])
        with open(file_path, 'w') as outfile:
            json.dump(filtered_data, outfile, indent=4)
        print("Sleeping")
        

        
# Run the process every 5 minutes (300 seconds)
while True:
    reset_filtered_files()  # Check if it's midnight and reset files
    process_data()
    time.sleep(300)  # Sleep for 5 minutes
    
