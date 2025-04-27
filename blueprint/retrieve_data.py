import yfinance as yf
import json
import logging
import os
import random
import time
from datetime import datetime, timedelta
import numpy as np
import requests_cache
from concurrent.futures import ThreadPoolExecutor
import orjson
from tenacity import retry, wait_exponential, stop_after_attempt

# Logging setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Paths
BASE_DIR = os.getenv("BASE_DIR", "/home/ec2-user/Stock-Scanner-Project")
FORMATTED_TICKERS_FILE_PATH = os.path.join(BASE_DIR, "Json", "formatted_tickers.json")
PE_FILE_PATH = os.path.join(BASE_DIR, "Json", "PE_num.json")
MARKETCAP_FILE_PATH = os.path.join(BASE_DIR, "Json", "MC_num.json")
EXPORT_FILE_PATH = os.path.join(BASE_DIR, "Json", "stock_data_export.json")
TICKERS_NAMES_PATH = os.path.join(BASE_DIR, "Json", "Tickers&Names.json")

# User-Agents and IPs
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edge/91.0.864.67",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 14_4_2 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.0.3 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edge/91.0.864.59",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0",
    "Mozilla/5.0 (Linux; U; Android 10; en-US; Pixel 3a Build/QP1A.190711.020) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; rv:46.0) Gecko/20100101 Firefox/46.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; rv:40.0) Gecko/20100101 Firefox/40.0",
    "Mozilla/5.0 (Linux; Android 10; SM-A505FN) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36"
]
 # Your existing list of User-Agents
CUSTOM_HEADERS = ["X-Forwarded-Host", "X-Host", "X-Originating-IP", "X-Client-IP", "X-Remote-Addr"]
IPV6_LIST = [f"2001:0db8:85a3:0000:0000:8a2e:0370:{str(i).zfill(4)}" for i in range(1, 21)]

# Cached Session
session = requests_cache.CachedSession('yfinance.cache')

### Utility Functions ###
def is_number(val):
    return isinstance(val, (int, float, np.integer, np.floating))

def read_json_file(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "rb") as file:
                return orjson.loads(file.read())
        return {}
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return {}

def write_json_file(file_path, data):
    try:
        # Convert numpy types to native Python types
        def convert_numpy(obj):
            if isinstance(obj, (np.integer, int)):
                return int(obj)
            elif isinstance(obj, (np.floating, float)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()  # Convert numpy arrays to lists
            raise TypeError(f"Type {type(obj)} not serializable")
        
        with open(file_path, "wb") as file:
            file.write(orjson.dumps(data, default=convert_numpy, option=orjson.OPT_INDENT_2))
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

def sync_tickers_and_names():
    tickers_names = read_json_file(TICKERS_NAMES_PATH)
    formatted_tickers = read_json_file(FORMATTED_TICKERS_FILE_PATH)
    names_dict = {item["Ticker"]: item["Company Name"] for item in tickers_names}
    tickers_list = formatted_tickers.get("tickers", [])
    updated_tickers = [{"Ticker": (t.get("Ticker") if isinstance(t, dict) else t),
                        "Company Name": names_dict.get((t.get("Ticker") if isinstance(t, dict) else t), "")}
                       for t in tickers_list]
    write_json_file(FORMATTED_TICKERS_FILE_PATH, {"tickers": updated_tickers})

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(5))
def fetch_stock_data(ticker):
    logger.info(f"Fetching data for {ticker}")
    return yf.Ticker(ticker, session=session).history(period="3mo")

def fetch_price(ticker, pe_data, mc_data, export_data, today):
    try:

        user_agent = random.choice(USER_AGENTS)
        session.headers.update({"User-Agent": user_agent})

        # Inject random custom header
        header_key = random.choice(CUSTOM_HEADERS)
        header_value = random.choice(IPV6_LIST)
        session.headers.update({header_key: header_value})

        hist_data = fetch_stock_data(ticker)
        if hist_data.empty or 'Close' not in hist_data.columns or hist_data.shape[0] < 2:
            return None

        current_price = hist_data['Close'].iloc[-1]
        prev_price = hist_data['Close'].iloc[-2]
        volume_today = hist_data['Volume'].iloc[-1]
        avg_volume = yf.Ticker(ticker, session=session).info.get('averageVolume', 'N/A')

        export_entry = next((item for item in export_data if item.get('Ticker') == ticker), {})
        last_update = export_entry.get("Last Update", "")[:10]
        shares = export_entry.get('Shares Available', 'N/A')
        if today != last_update:
            shares = yf.Ticker(ticker, session=session).info.get('sharesOutstanding', 'N/A')

        pe = update_daily_value(pe_data, ticker, yf.Ticker(ticker, session=session).info.get('trailingPE', 'N/A'), today)
        mc = update_daily_value(mc_data, ticker, yf.Ticker(ticker, session=session).info.get('marketCap', 'N/A'), today)

        return {
            'Ticker': ticker,
            'Company Name': export_entry.get('Company Name', yf.Ticker(ticker, session=session).info.get('shortName', 'N/A')),
            'Current Price': round(current_price, 2),
            'Price Change Today': calculate_percent_change(current_price, prev_price),
            'Price Change Week': calculate_percent_change(current_price, hist_data['Close'].iloc[-6])
                if hist_data.shape[0] >= 7 else 'N/A',
            'Price Change Month': calculate_percent_change(current_price, hist_data['Close'].iloc[0]),
            'Volume Today': volume_today,
            'Avg Volume (3 mon)': avg_volume,
            'DVAV (Day Volume Over Avg Volume)': round(volume_today / avg_volume, 4)
                if is_number(volume_today) and is_number(avg_volume) and avg_volume != 0 else 'N/A',
            'Shares Available': shares,
            'DVSA (Volume/Share)': round(volume_today / shares, 4)
                if is_number(volume_today) and is_number(shares) and shares != 0 else 'N/A',
            'P/E Ratio': pe,
            'P/E Change (3 Mon)': calculate_percent_change(pe, get_historical_value(pe_data, ticker, 90)),
            'Market Cap': mc,
            'Market Cap Change (3 Mon)': calculate_percent_change(mc, current_price * shares
                if is_number(current_price) and is_number(shares) else 'N/A'),
            'Last Update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        logger.error(f"Error processing {ticker}: {e}")
        return None

def main():
    start_time = datetime.now()
    logger.info(f"Started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    today = datetime.now().strftime("%Y-%m-%d")
    sync_tickers_and_names()

    tickers = read_json_file(FORMATTED_TICKERS_FILE_PATH).get("tickers", [])
    tickers = [t["Ticker"] if isinstance(t, dict) else t for t in tickers]
    pe_data = read_json_file(PE_FILE_PATH)
    mc_data = read_json_file(MARKETCAP_FILE_PATH)
    export_data = read_json_file(EXPORT_FILE_PATH)
    existing_data_map = {item['Ticker']: item for item in export_data if isinstance(item, dict)}

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda t: fetch_price(t, pe_data, mc_data, export_data, today), tickers))

    for result in filter(None, results):
        existing_data_map[result['Ticker']] = result

    write_json_file(EXPORT_FILE_PATH, list(existing_data_map.values()))
    write_json_file(PE_FILE_PATH, pe_data)
    write_json_file(MARKETCAP_FILE_PATH, mc_data)

    logger.info(f"Finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, duration: {datetime.now() - start_time}")

if __name__ == "__main__":
    main()
