import json
import os
import time

# Define the filters as separate conditions for each JSON file
filters = [
    {"file_name": "Filtered_pe_10_in.json", "condition": lambda ticker: ticker.get("P/E Change (3mo)", 0) > 10, "field": "P/E Change (3mo)"},
    {"file_name": "Filtered_pe_20_in.json", "condition": lambda ticker: ticker.get("P/E Change (3mo)", 0) > 20, "field": "P/E Change (3mo)"},
    {"file_name": "Filtered_pe_30_in.json", "condition": lambda ticker: ticker.get("P/E Change (3mo)", 0) > 30, "field": "P/E Change (3mo)"},
    {"file_name": "Filtered_pe_10_de.json", "condition": lambda ticker: ticker.get("P/E Change (3mo)", 0) < -10, "field": "P/E Change (3mo)"},
    {"file_name": "Filtered_pe_20_de.json", "condition": lambda ticker: ticker.get("P/E Change (3mo)", 0) < -20, "field": "P/E Change (3mo)"},
    {"file_name": "Filtered_pe_30_de.json", "condition": lambda ticker: ticker.get("P/E Change (3mo)", 0) < -30, "field": "P/E Change (3mo)"},
    {"file_name": "Filtered_market_cap_10_in.json", "condition": lambda ticker: ticker.get("Market Cap Change (3 Mon)", 0) > 10, "field": "Market Cap Change (3 Mon)"},
    {"file_name": "Filtered_market_cap_20_in.json", "condition": lambda ticker: ticker.get("Market Cap Change (3 Mon)", 0) > 20, "field": "Market Cap Change (3 Mon)"},
    {"file_name": "Filtered_market_cap_30_in.json", "condition": lambda ticker: ticker.get("Market Cap Change (3 Mon)", 0) > 30, "field": "Market Cap Change (3 Mon)"},
    {"file_name": "Filtered_market_cap_10_de.json", "condition": lambda ticker: ticker.get("Market Cap Change (3 Mon)", 0) < -10, "field": "Market Cap Change (3 Mon)"},
    {"file_name": "Filtered_market_cap_20_de.json", "condition": lambda ticker: ticker.get("Market Cap Change (3 Mon)", 0) < -20, "field": "Market Cap Change (3 Mon)"},
    {"file_name": "Filtered_market_cap_30_de.json", "condition": lambda ticker: ticker.get("Market Cap Change (3 Mon)", 0) < -30, "field": "Market Cap Change (3 Mon)"},
    {"file_name": "Filtered_volume_10.json", "condition": lambda ticker: ticker.get("Volume Today", 0) > 10000000, "field": "Volume Today"},
    {"file_name": "Filtered_volume_20.json", "condition": lambda ticker: ticker.get("Volume Today", 0) > 20000000, "field": "Volume Today"},
    {"file_name": "Filtered_volume_50.json", "condition": lambda ticker: ticker.get("Volume Today", 0) > 50000000, "field": "Volume Today"},
    {"file_name": "Filtered_volume_100.json", "condition": lambda ticker: ticker.get("Volume Today", 0) > 100000000, "field": "Volume Today"},
    {"file_name": "Filtered_volume_150.json", "condition": lambda ticker: ticker.get("Volume Today", 0) > 150000000, "field": "Volume Today"},
    {"file_name": "Filtered_volume_2x.json", "condition": lambda ticker: ticker.get("DVAV (Day Volume Over Average Volume)", 0) > 2, "field": "DVAV (Day Volume Over Average Volume)"},
    {"file_name": "Filtered_volume_3x.json", "condition": lambda ticker: ticker.get("DVAV (Day Volume Over Average Volume)", 0) > 3, "field": "DVAV (Day Volume Over Average Volume)"},
    {"file_name": "Filtered_volume_5x.json", "condition": lambda ticker: ticker.get("DVAV (Day Volume Over Average Volume)", 0) > 5, "field": "DVAV (Day Volume Over Average Volume)"},
    {"file_name": "Filtered_price_20_in.json", "condition": lambda ticker: ticker.get("Price Change Today", 0) > 20, "field": "Price Change Today"},
    {"file_name": "Filtered_price_50_in.json", "condition": lambda ticker: ticker.get("Price Change Today", 0) > 50, "field": "Price Change Today"},
    {"file_name": "Filtered_price_75_in.json", "condition": lambda ticker: ticker.get("Price Change Today", 0) > 75, "field": "Price Change Today"},
    {"file_name": "Filtered_price_10_de.json", "condition": lambda ticker: ticker.get("Price Change Today", 0) < -10, "field": "Price Change Today"},
    {"file_name": "Filtered_price_15_de.json", "condition": lambda ticker: ticker.get("Price Change Today", 0) < -20, "field": "Price Change Today"},
    {"file_name": "Filtered_price_20_de.json", "condition": lambda ticker: ticker.get("Price Change Today", 0) < -30, "field": "Price Change Today"},
]

# Define the output directory
output_directory = './json'

# Create the /json directory if it doesn't exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Load the JSON data from a file
def process_data():
    with open('data.json', 'r') as file:
        data = json.load(file)

    # Apply each filter and save to the corresponding file in the /json directory
    for filter_item in filters:
        filtered_data = {}
        for item in data:
            average_volume = item.get("Average Volume", 0)
            current_price = item.get("Price", 0)
            current_volume = item.get("Volume Today", 0)

            # Check for specific volume-based conditions
            if filter_item["file_name"] == "Filtered_volume_10.json" and average_volume < 8000000 and current_price < 100 and current_volume > 10000000:
                if filter_item["condition"](item):
                    item[filter_item["field"]] = item.get(filter_item["field"], None)
                    filtered_data[item["ticker"]] = item

            elif filter_item["file_name"] == "Filtered_volume_20.json" and average_volume < 12000000 and current_price < 100 and current_volume > 20000000 and average_volume > 5000000:
                if filter_item["condition"](item):
                    item[filter_item["field"]] = item.get(filter_item["field"], None)
                    filtered_data[item["ticker"]] = item

            elif filter_item["file_name"] == "Filtered_volume_50.json" and average_volume < 35000000 and current_price < 150 and current_volume > 50000000 and average_volume > 15000000:
                if filter_item["condition"](item):
                    item[filter_item["field"]] = item.get(filter_item["field"], None)
                    filtered_data[item["ticker"]] = item

            elif filter_item["file_name"] == "Filtered_volume_100.json" and average_volume < 80000000 and current_price < 150 and current_volume > 100000000 and average_volume > 30000000:
                if filter_item["condition"](item):
                    item[filter_item["field"]] = item.get(filter_item["field"], None)
                    filtered_data[item["ticker"]] = item

            elif filter_item["file_name"] == "Filtered_volume_150.json" and average_volume < 100000000 and current_price < 150 and current_volume > 150000000 and average_volume > 50000000:
                if filter_item["condition"](item):
                    item[filter_item["field"]] = item.get(filter_item["field"], None)
                    filtered_data[item["ticker"]] = item

            else:
                # Apply the regular condition for all other filters
                if filter_item["condition"](item):
                    item[filter_item["field"]] = item.get(filter_item["field"], None)
                    filtered_data[item["ticker"]] = item

        # Save the filtered data to the new JSON file in the /json folder
        file_path = os.path.join(output_directory, filter_item["file_name"])
        with open(file_path, 'w') as outfile:
            json.dump(filtered_data, outfile, indent=4)

        print(f"Filtered tickers have been saved to {file_path}.")

# Run the process every 5 minutes (300 seconds)
while True:
    process_data()
    time.sleep(300)  # Sleep for 5 minutes
