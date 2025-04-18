import yfinance as yf
import json
import logging
import os
import random
from datetime import datetime, timedelta
import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor
import orjson
from tenacity import retry, wait_exponential, stop_after_attempt
from itertools import cycle


# Logging setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Base directory and file paths
BASE_DIR = os.getenv("BASE_DIR", "/home/ec2-user/Stock-Scanner-Project")
FORMATTED_TICKERS_FILE_PATH = os.path.join(BASE_DIR, "json", "formatted_tickers.json")
PE_FILE_PATH = os.path.join(BASE_DIR, "json", "PE_num.json")
MARKETCAP_FILE_PATH = os.path.join(BASE_DIR, "json", "MC_num.json")
EXPORT_FILE_PATH = os.path.join(BASE_DIR, "json", "stock_data_export.json")

# Random User-Agent list
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
    "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)",
    "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; U; Android 11; en-us; Pixel 5 Build/RQ3A.210705.001) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 8.0.0; SM-G950F Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.84 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 12_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile Safari/604.1",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; Mi A2 Build/PKQ1.180904.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.80 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 7.1.2; Nexus 6P Build/NJH47F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.125 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0 Safari/604.1"
]


### Utility Functions ###
def is_number(val):
    return isinstance(val, (int, float, np.integer, np.floating))


def read_json_file(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as file:
                return orjson.loads(file.read())
        else:
            logger.warning(f"File {file_path} not found. Returning empty dictionary.")
            return {}
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return {}


def write_json_file(file_path, data):
    try:
        with open(file_path, "wb") as file:
            file.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
    except Exception as e:
        logger.error(f"Error writing to {file_path}: {e}")


def calculate_percent_change(new, old):
    try:
        if not is_number(new) or not is_number(old) or old == 0:
            return 'N/A'
        return round(((new - old) / old) * 100, 2)
    except Exception as e:
        logger.error(f"Error calculating percent change: {e}")
        return 'N/A'


def update_daily_value(data, ticker, value, today):
    if ticker not in data or today not in data[ticker]:
        data.setdefault(ticker, {})[today] = value
    return data[ticker][today]


def get_historical_value(data, ticker, days_ago):
    target_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    return data.get(ticker, {}).get(target_date, 'N/A')


def convert_to_serializable(obj):
    if isinstance(obj, (np.int64, np.float64)):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Type {type(obj)} not serializable")


def sync_tickers_and_names(export_data_path, formatted_tickers_path):
    """
    Synchronizes tickers and company names from the export file and formatted tickers file.
    """
    # Read export data
    export_data = read_json_file(export_data_path)

    # Extract tickers and company names from export data
    export_tickers_and_names = {
        item["Ticker"]: item.get("Company Name", "Unknown")
        for item in export_data if "Ticker" in item
    }

    # Read formatted tickers data
    formatted_tickers = read_json_file(formatted_tickers_path)

    # Extract tickers from formatted tickers file
    formatted_tickers_list = formatted_tickers.get("tickers", [])

    # Merge the tickers and company names
    tickers_and_names = {}
    for ticker in formatted_tickers_list:
        if ticker in export_tickers_and_names:
            # Use company name from export data if available
            tickers_and_names[ticker] = export_tickers_and_names[ticker]
        else:
            # Fallback to formatted tickers data without a company name
            tickers_and_names[ticker] = "Unknown"

    # Return synchronized tickers and company names
    return tickers_and_names


@retry(wait=wait_exponential(multiplier=1.5, min=10, max=20), stop=stop_after_attempt(100))
def fetch_stock_data(ticker):
    """
    Fetch historical stock data for the given ticker using yfinance.
    Retries automatically on failure with exponential backoff.
    """
    logger.info(f"Fetching historical data for ticker: {ticker}")
    return yf.Ticker(ticker).history(period="3mo")


def fetch_price(ticker, pe_data, mc_data, export_data, today):
    try:
        # Randomly select a User-Agent
        user_agent = random.choice(USER_AGENTS)
        headers = {"User-Agent": user_agent}

        hist_data = fetch_stock_data(ticker)

        if hist_data.empty or 'Close' not in hist_data.columns or hist_data.shape[0] < 2:
            logger.warning(f"Not enough data for ticker {ticker}. Skipping.")
            return None

        current_price = hist_data['Close'].iloc[-1]
        prev_price = hist_data['Close'].iloc[-2]
        volume_today = hist_data['Volume'].iloc[-1] if 'Volume' in hist_data.columns else 'N/A'
        avg_volume = yf.Ticker(ticker).info.get('averageVolume', 'N/A')

        export_entry = next((item for item in export_data if item.get('Ticker') == ticker), {})
        last_update = export_entry.get("Last Update", "")[:10]

        result = {
            'Ticker': ticker,
            'Company Name': export_entry.get('Company Name', yf.Ticker(ticker).info.get('shortName', 'N/A')),
            'Is ETF': export_entry.get('Is ETF', False),
            'Current Price': round(current_price, 2),
            'Price Change Today': calculate_percent_change(current_price, prev_price),
            'Price Change Week': calculate_percent_change(
                current_price, hist_data['Close'].iloc[-6]) if hist_data.shape[0] >= 7 else 'N/A',
            'Price Change Month': calculate_percent_change(current_price, hist_data['Close'].iloc[0]),
            'Volume Today': volume_today,
            'Avg Volume (3 mon)': avg_volume,
            'DVAV (Day Volume Over Average Volume)': round(volume_today / avg_volume, 4)
                if is_number(volume_today) and is_number(avg_volume) and avg_volume != 0 else 'N/A'
        }

        if not result['Is ETF']:
            shares = export_entry.get('Shares Available', 'N/A')
            if today != last_update:
                shares = yf.Ticker(ticker).info.get('sharesOutstanding', 'N/A')

            pe = update_daily_value(pe_data, ticker, yf.Ticker(ticker).info.get('trailingPE', 'N/A'), today)
            mc = update_daily_value(mc_data, ticker, yf.Ticker(ticker).info.get('marketCap', 'N/A'), today)

            result.update({
                'Shares Available': shares,
                'DVSA (Volume Today Over Shares Available)': round(volume_today / shares, 4)
                    if is_number(volume_today) and is_number(shares) and shares != 0 else 'N/A',
                'P/E Ratio': pe,
                'P/E Change (3 Mon)': calculate_percent_change(pe, get_historical_value(pe_data, ticker, 90)),
                'Market Cap': mc,
                'Market Cap Change (3 Mon)': calculate_percent_change(mc, current_price * shares
                    if is_number(current_price) and is_number(shares) else 'N/A')
            })

        result['Last Update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return result

    except Exception as e:
        logger.exception(f"Error processing {ticker}")
        return None


### Main Function ###
def main():
    # Start the timer
    start_time = datetime.now()
    logger.info(f"Script started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    today = datetime.now().strftime("%Y-%m-%d")
    sync_tickers_and_names()

    formatted_tickers_data = read_json_file(FORMATTED_TICKERS_FILE_PATH)
    tickers = formatted_tickers_data.get("tickers", [])
    pe_data = read_json_file(PE_FILE_PATH)
    mc_data = read_json_file(MARKETCAP_FILE_PATH)
    export_data = read_json_file(EXPORT_FILE_PATH)

    existing_data_map = {item['Ticker']: item for item in export_data if isinstance(item, dict)}

    # Corrected ThreadPoolExecutor block
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda entry: fetch_price(
            entry["Ticker"] if isinstance(entry, dict) else entry, pe_data, mc_data, export_data, today), tickers))

    for data in filter(None, results):
        existing_data_map[data['Ticker']] = data

    write_json_file(EXPORT_FILE_PATH, list(existing_data_map.values()))
    write_json_file(PE_FILE_PATH, pe_data)
    write_json_file(MARKETCAP_FILE_PATH, mc_data)

    # End the timer
    end_time = datetime.now()
    elapsed_time = end_time - start_time
    logger.info(f"Processing complete. Script finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Total execution time: {elapsed_time}")

if __name__ == "__main__":
    main()
