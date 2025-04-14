import json
import logging
import os
import random
import time
from datetime import datetime, timedelta
import numpy as np
import requests  # Added requests import

# Logging setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Base directory and file paths
base_dir = r"/home/ec2-user/Stock-Scanner-Project"
FORMATTED_TICKERS_FILE_PATH = os.path.join(base_dir, "json", "formatted_tickers.json")
PE_FILE_PATH = os.path.join(base_dir, "json", "PE_num.json")
MarketCap_FILE_PATH = os.path.join(base_dir, "json", "MC_num.json")
EXPORT_FILE_PATH = os.path.join(base_dir, "json", "stock_data_export.json")
TICKERS_NAMES_PATH = os.path.join(base_dir, "json", "Tickers&Names.json")

# Random User-Agent list
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
    "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)"
]

def is_number(val):
    return isinstance(val, (int, float, np.integer, np.floating))

def read_json_file(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                return json.load(file)
        else:
            logger.warning(f"File {file_path} not found. Returning empty dictionary.")
            return {}
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return {}

def write_json_file(file_path, data):
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4, default=convert_to_serializable)
    except Exception as e:
        logger.error(f"Error writing to {file_path}: {e}")

def convert_to_serializable(obj):
    if isinstance(obj, (np.int64, np.float64)):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Type {type(obj)} not serializable")

def calculate_percent_change(new, old):
    try:
        if not is_number(new) or not is_number(old) or old == 0:
            return 'N/A'
        return round(((new - old) / old) * 100, 2)
    except Exception as e:
        logger.error(f"Error calculating percent change: {e}")
        return 'N/A'

def get_historical_value(data, ticker, days_ago):
    target_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    return data.get(ticker, {}).get(target_date, 'N/A')

def sync_tickers_and_names():
    tickers_names = read_json_file(TICKERS_NAMES_PATH)
    formatted_tickers = read_json_file(FORMATTED_TICKERS_FILE_PATH)

    names_dict = {item["Ticker"]: item["Company Name"] for item in tickers_names}

    tickers_list = formatted_tickers.get("tickers", [])
    updated_tickers = []

    for ticker in tickers_list:
        if isinstance(ticker, dict):
            ticker_symbol = ticker.get("Ticker", "")
        else:
            ticker_symbol = ticker
        company_name = names_dict.get(ticker_symbol, "")
        updated_tickers.append({
            "Ticker": ticker_symbol,
            "Company Name": company_name,
            "Is ETF": False
        })

    updated_data = {"tickers": updated_tickers}
    write_json_file(FORMATTED_TICKERS_FILE_PATH, updated_data)
    logger.info("Formatted tickers updated with company names.")

def fetch_price(ticker, pe_data, mc_data, export_data, today):
    try:
        user_agent = random.choice(USER_AGENTS)
        # Use requests to set up a session with custom headers
        session = requests.Session()
        session.headers.update({"User-Agent": user_agent})

        # Retrieve PE and Market Cap directly from JSON files
        pe = pe_data.get(ticker, {}).get(today, 'N/A')
        mc = mc_data.get(ticker, {}).get(today, 'N/A')

        export_entry = next((item for item in export_data if item.get('Ticker') == ticker), {})
        result = {
            'Ticker': ticker,
            'Company Name': export_entry.get('Company Name', 'N/A'),
            'Is ETF': export_entry.get('Is ETF', False),
            'P/E Ratio': pe,
            'Market Cap': mc,
        }

        # Calculate changes if historical data exists
        pe_change = calculate_percent_change(pe, get_historical_value(pe_data, ticker, 90))
        mc_change = calculate_percent_change(mc, get_historical_value(mc_data, ticker, 90))
        result.update({
            'P/E Change (3 Mon)': pe_change,
            'Market Cap Change (3 Mon)': mc_change
        })

        result['Last Update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return result

    except Exception as e:
        logger.exception(f"Error processing {ticker}")
        return None

def main():
    start_time = time.time()
    today = datetime.now().strftime("%Y-%m-%d")

    sync_tickers_and_names()

    formatted_tickers_data = read_json_file(FORMATTED_TICKERS_FILE_PATH)
    tickers = formatted_tickers_data.get("tickers", [])

    pe_data = read_json_file(PE_FILE_PATH)
    mc_data = read_json_file(MarketCap_FILE_PATH)
    export_data = read_json_file(EXPORT_FILE_PATH)

    existing_data_map = {item['Ticker']: item for item in export_data if isinstance(item, dict)}
    processed_count = 0

    for entry in tickers:
        ticker = entry["Ticker"] if isinstance(entry, dict) else entry
        data = fetch_price(ticker, pe_data, mc_data, export_data, today)
        if data:
            existing_data_map[ticker] = data

        processed_count += 1
        if processed_count % 100 == 0:
            logger.info(f"Processed {processed_count} tickers. Saving intermediate results.")
            write_json_file(EXPORT_FILE_PATH, list(existing_data_map.values()))

    logger.info(f"Processing complete. Total tickers: {processed_count}")
    write_json_file(EXPORT_FILE_PATH, list(existing_data_map.values()))

    elapsed_time = round(time.time() - start_time, 2)
    logger.info(f"Execution time: {elapsed_time} seconds")

if __name__ == "__main__":
    main()
