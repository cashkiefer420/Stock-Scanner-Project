import yfinance as yf
import json
import logging
import os
import time
from datetime import datetime
from threading import Event

# Base directory setup
base_dir = r"/home/ec2-user/Stock-Scanner-Project"
TICKER_FILE_PATH = os.path.join(base_dir, "json", "formatted_tickers.json")
PE_FILE_PATH = os.path.join(base_dir, "json", "PE_num.json")
MarketCap_FILE_PATH = os.path.join(base_dir, "json", "MC_num.json")
EXPORT_FILE_PATH = os.path.join(base_dir, "json", "stock_data_export.json")

# Logging setup
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)

shutdown_event = Event()

def ensure_serializable(data):
    if isinstance(data, (list, tuple)):
        return [ensure_serializable(item) for item in data]
    elif isinstance(data, dict):
        return {key: ensure_serializable(value) for key, value in data.items()}
    elif isinstance(data, (int, float, str)) or data is None:
        return data
    else:
        return str(data)

def update_json_file(file_path, ticker, key, value):
    try:
        current_date = datetime.now().strftime("%m/%d/%y")

        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                except json.decoder.JSONDecodeError:
                    logging.warning(f"Invalid JSON in {file_path}. Reinitializing.")
                    data = {}
        else:
            data = {}

        if ticker not in data:
            data[ticker] = {}

        if current_date not in data[ticker]:
            data[ticker][current_date] = {key: value}

            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as file:
                json.dump(ensure_serializable(data), file, indent=4)

    except Exception:
        logging.exception(f"Error updating {file_path} for {ticker}.")

def fetch_pe_mc_and_name(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        company_name = info.get("longName", "N/A")
        pe = info.get("trailingPE", "N/A")
        mc = info.get("marketCap", "N/A")

        if pe != 'N/A':
            update_json_file(PE_FILE_PATH, ticker, "PE", pe)

        if mc != 'N/A':
            update_json_file(MarketCap_FILE_PATH, ticker, "Market Cap", mc)

        return {"Ticker": ticker, "Company Name": company_name}
    except Exception:
        logging.exception(f"Error fetching data for {ticker}")
        return {"Ticker": ticker, "Company Name": "N/A"}

def load_tickers():
    try:
        with open(TICKER_FILE_PATH, 'r') as file:
            data = json.load(file)
            return data.get("tickers", [])
    except Exception:
        logging.exception("Error loading tickers:")
        return []

def process_in_batches(ticker_list, batch_size=1000, sleep_time=30):
    all_export_data = []
    for i in range(0, len(ticker_list), batch_size):
        batch = ticker_list[i:i+batch_size]
        logging.info(f"Processing batch {i//batch_size + 1}: {len(batch)} tickers.")
        for ticker in batch:
            result = fetch_pe_mc_and_name(ticker)
            all_export_data.append(result)
        if i + batch_size < len(ticker_list):
            logging.info(f"Sleeping for {sleep_time} seconds before next batch...")
            time.sleep(sleep_time)

    # Export ticker + company name to file
    try:
        os.makedirs(os.path.dirname(EXPORT_FILE_PATH), exist_ok=True)
        with open(EXPORT_FILE_PATH, 'w') as export_file:
            json.dump(ensure_serializable(all_export_data), export_file, indent=4)
        logging.info(f"Exported basic data to {EXPORT_FILE_PATH}")
    except Exception:
        logging.exception("Error writing export file:")

if __name__ == '__main__':
    try:
        tickers = load_tickers()
        if not tickers:
            logging.error("No tickers found.")
        else:
            logging.info(f"Starting batch processing for {len(tickers)} tickers.")
            process_in_batches(tickers)
    except KeyboardInterrupt:
        logging.info("Shutdown requested.")
        shutdown_event.set()