import json
import os

# File paths
base_dir = r"/home/ec2-user/Stock-Scanner-Project"
TICKERS_FILE_PATH = os.path.join(base_dir, "json", "formatted_tickers.json")
EXPORT_FILE_PATH = os.path.join(base_dir, "json", "stock_data_export.json")

def read_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def write_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def remove_etfs():
    # Load data
    tickers_data = read_json(TICKERS_FILE_PATH)
    export_data = read_json(EXPORT_FILE_PATH)

    # Find all non-ETF tickers
    non_etf_export = [entry for entry in export_data if not entry.get("Is ETF", False)]
    non_etf_tickers = [entry["Ticker"] for entry in non_etf_export]

    # Filter the ticker list to only include non-ETFs
    filtered_ticker_list = [ticker for ticker in tickers_data.get("tickers", []) if ticker in non_etf_tickers]

    # Write the cleaned data back
    write_json(EXPORT_FILE_PATH, non_etf_export)
    write_json(TICKERS_FILE_PATH, {"tickers": filtered_ticker_list})

    print(f"Removed {len(export_data) - len(non_etf_export)} ETFs from both files.")

if __name__ == "__main__":
    remove_etfs()