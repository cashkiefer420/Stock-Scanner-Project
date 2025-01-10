import json
import os
import time

base_dir = r"C:\Users\Carter\Downloads\Stock-Scanner-Project-main\Stock-Scanner-Project-main"
DATA_FILE_PATH = os.path.join(base_dir, "json", "stock_data_export.json") 
EXPORT_FILE_PATH = os.path.join(base_dir, "json", "split_data.json") 

# Ensure required directories and files exist
os.makedirs(os.path.dirname(DATA_FILE_PATH), exist_ok=True)
if not os.path.exists(DATA_FILE_PATH):
    with open(DATA_FILE_PATH, 'w') as file:
        json.dump([], file, indent=4)

def extract_important_info(data):
    """
    Extracts important information from the input JSON data.
    """
    important_info = {
        "Ticker": data.get("Ticker"),
        "Current Price": data.get("Current Price"),
        "Price Change Today": data.get("Price Change Today"),
        "Market Cap": data.get("Market Cap"),
        "Market Cap Change (3 Mon)": data.get("Market Cap Change (3 Mon)"),
        "P/E Ratio": data.get("P/E Ratio"),
        "P/E Change (3 Mon)": data.get("P/E Change (3 Mon)"),
        "Volume Today": data.get("Volume Today"),
        "Avg Volume (3 mon)": data.get("Avg Volume (3 mon)")
    }
    return important_info

def process_json(input_file, output_file):
    """
    Reads a JSON file, extracts important information, and writes it to another JSON file.
    Logs the time taken to complete the process.
    """
    start_time = time.time()

    try:
        # Read the input JSON file
        with open(input_file, "r") as infile:
            data = json.load(infile)

        # Extract important information
        if isinstance(data, list):
            important_data = [extract_important_info(item) for item in data]
        else:
            important_data = extract_important_info(data)

        # Write the important information to the output JSON file
        with open(output_file, "w") as outfile:
            json.dump(important_data, outfile, indent=4)

        print(f"Important information saved to {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")

    end_time = time.time()
    print(f"Process completed in {end_time - start_time:.10f} seconds.")

if __name__ == "__main__":
    input_file = DATA_FILE_PATH
    output_file = EXPORT_FILE_PATH

    process_json(input_file, output_file)
