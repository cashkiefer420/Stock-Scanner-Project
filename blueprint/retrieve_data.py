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
    "Mozilla/5.0 (Linux; Android 8.0.0; SM-G950F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.84 Mobile Safari/537.36",
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

@retry(wait=wait_exponential(multiplier=1.5, min=10, max=20), stop=stop_after_attempt(100))
def fetch_stock_data(ticker):
    logger.info(f"Fetching historical data for ticker: {ticker}")
    return yf.Ticker(ticker).history(period="3mo")

def fetch_price(ticker, pe_data, mc_data, export_data, today):
    try:
        t = yf.Ticker(ticker)
        hist_data = t.history(period="3mo")

        if hist_data.empty or 'Close' not in hist_data.columns or hist_data.shape[0] < 2:
            logger.warning(f"Not enough data for ticker {ticker}. Skipping.")
            return None

        current_price = hist_data['Close'].iloc[-1]
        prev_price = hist_data['Close'].iloc[-2]
        volume_today = hist_data['Volume'].iloc[-1] if 'Volume' in hist_data.columns else 'N/A'
        avg_volume = t.info.get('averageVolume', 'N/A')
        shares = t.info.get('sharesOutstanding', 'N/A')
        company_name = t.info.get('shortName', 'Unknown')

        export_entry = next((item for item in export_data if item.get('Ticker') == ticker), {})
        last_update = export_entry.get("Last Update", "")[:10]

        if today == last_update:
            shares = export_entry.get('Shares Available', shares)

        pe = update_daily_value(pe_data, ticker, t.info.get('trailingPE', 'N/A'), today)
        mc = update_daily_value(mc_data, ticker, t.info.get('marketCap', 'N/A'), today)

        result = {
            'Ticker': ticker,
            'Company Name': company_name,
            'Current Price': round(current_price, 2),
            'Price Change Today': calculate_percent_change(current_price, prev_price),
            'Price Change Week': calculate_percent_change(current_price, hist_data['Close'].iloc[-6]) if hist_data.shape[0] >= 7 else 'N/A',
            'Price Change Month': calculate_percent_change(current_price, hist_data['Close'].iloc[0]),
            'Volume Today': volume_today,
            'Avg Volume (3 mon)': avg_volume,
            'DVAV (Day Volume Over Avg Volume)': round(volume_today / avg_volume, 4)
                if is_number(volume_today) and is_number(avg_volume) and avg_volume != 0 else 'N/A',
            'Shares Available': shares,
            'DVSA (Volume / Shares Available)': round(volume_today / shares, 4)
                if is_number(volume_today) and is_number(shares) and shares != 0 else 'N/A',
            'P/E Ratio': pe,
            'P/E Change (3 Mon)': calculate_percent_change(pe, get_historical_value(pe_data, ticker, 90)),
            'Market Cap': mc,
            'Market Cap Change (3 Mon)': calculate_percent_change(mc, current_price * shares
                if is_number(current_price) and is_number(shares) else 'N/A'),
            'Last Update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return result

    except Exception as e:
        logger.exception(f"Error processing {ticker}")
        return None

### Main Function ###
def main():
    start_time = datetime.now()
    logger.info(f"Script started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    today = datetime.now().strftime("%Y-%m-%d")
    formatted_tickers_data = read_json_file(FORMATTED_TICKERS_FILE_PATH)
    tickers = formatted_tickers_data.get("tickers", [])
    pe_data = read_json_file(PE_FILE_PATH)
    mc_data = read_json_file(MARKETCAP_FILE_PATH)
    export_data = read_json_file(EXPORT_FILE_PATH)
    existing_data_map = {item['Ticker']: item for item in export_data if isinstance(item, dict)}

    def process(ticker):
        try:
            user_agent = random.choice(USER_AGENTS)
            session = requests.Session()
            session.headers.update({"User-Agent": user_agent})
            yf.shared._requests_session = session
            return fetch_price(ticker, pe_data, mc_data, export_data, today)
        except Exception as e:
            logger.error(f"Failed to process ticker {ticker}: {e}")
            return None

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process, tickers))

    for data in filter(None, results):
        existing_data_map[data['Ticker']] = data

    write_json_file(EXPORT_FILE_PATH, list(existing_data_map.values()))
    write_json_file(PE_FILE_PATH, pe_data)
    write_json_file(MARKETCAP_FILE_PATH, mc_data)

    end_time = datetime.now()
    elapsed_time = end_time - start_time
    logger.info(f"Script finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Total execution time: {elapsed_time}")

if __name__ == "__main__":
    main()