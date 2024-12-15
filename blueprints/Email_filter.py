import json
import os

# Define the filters as separate conditions for each JSON file
filters = [
    {"file_name": "Filtered_pe_10_in.json", "condition": lambda ticker: ticker.get("P/E Change (3mo) (%)", 0) > 10},
    {"file_name": "Filtered_pe_20_in.json", "condition": lambda ticker: ticker.get("P/E Change (3mo) (%)", 0) > 20},
    {"file_name": "Filtered_pe_30_in.json", "condition": lambda ticker: ticker.get("P/E Change (3mo) (%)", 0) > 30},
    # Add 22 more filters as needed
]

# Define the output directory
output_directory = './json'

# Create the /json directory if it doesn't exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Load the JSON data from a file
with open('data.json', 'r') as file:
    data = json.load(file)

# Apply each filter and save to the corresponding file in the /json directory
for filter_item in filters:
    filtered_data = {}
    for item in data:
        if filter_item["condition"](item):  # Apply the condition for this filter
            filtered_data[item["ticker"]] = item

    # Save the filtered data to the new JSON file in the /json folder
    file_path = os.path.join(output_directory, filter_item["file_name"])
    with open(file_path, 'w') as outfile:
        json.dump(filtered_data, outfile, indent=4)

    print(f"Filtered tickers have been saved to {file_path}.")
