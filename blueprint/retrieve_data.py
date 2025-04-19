import yfinance as yf
import orjson
import os
import logging
import random
from datetime import datetime, timedelta
import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, wait_exponential, stop_after_attempt

# Logging setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# File paths
BASE_DIR = os.getenv("BASE_DIR", "/home/ec2-user/Stock-Scanner-Project")
FORMATTED_TICKERS_FILE_PATH = os.path.join(BASE_DIR, "json", "formatted_tickers.json")
PE_FILE_PATH = os.path.join(BASE_DIR, "json", "PE_num.json")
MC_FILE_PATH = os.path.join(BASE_DIR, "json", "MC_num.json")
EXPORT_FILE_PATH = os.path.join(BASE_DIR, "json", "stock_data_export.json")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
    "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)",
    "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F)",
    "Mozilla/5.0 (Linux; Android 8.0.0; SM-G950F)"
]

def is_number(val):
    return isinstance(val, (int, float, np.integer, np.floating))

def read_json_file(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return orjson.loads(f.read())
    return {}

def write_json_file(path, data):
    with open(path, "wb") as f:
        f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))

def calculate_percent_change(new, old):
    try:
        if not is_number(new) or not is_number(old) or old == 0:
            return 'N/A'
        return round(((new - old) / old) * 100, 2)
    except:
        return 'N/A'

def update_daily_value(data, ticker, value, today):
    if ticker not in data or today not in data[ticker]:
        data.setdefault(ticker, {})[today] = value
    return data[ticker][today]

def get_historical_value(data, ticker, days_ago):
    date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    return data.get(ticker, {}).get(date, 'N/A')

@retry(wait=wait_exponential(min=10, max=20), stop=stop_after_attempt(100))
def fetch_stock_data(ticker, session):
    return yf.Ticker(ticker, session=session).history(period="3mo")

def fetch_price(ticker, pe_data, mc_data, export_data, today, company_name, session):
    try:
        hist_data = fetch_stock_data(ticker, session)
        if hist_data.empty or 'Close' not in hist_data.columns or len(hist_data) < 2:
            return None

        current_price = hist_data['Close'].iloc[-1]
        prev_price = hist_data['Close'].iloc[-2]
        volume_today = hist_data['Volume'].iloc[-1]
        avg_volume = yf.Ticker(ticker, session=session).info.get('averageVolume', 'N/A')

        export_entry = next((x for x in export_data if x.get("Ticker") == ticker), {})
        last_update = export_entry.get("Last Update", "")[:10]
        shares = export_entry.get("Shares Available", "N/A")

        if today != last_update:
            info = yf.Ticker(ticker, session=session).info
            shares = info.get("sharesOutstanding", shares)
            pe = update_daily_value(pe_data, ticker, info.get("trailingPE", 'N/A'), today)
            mc = update_daily_value(mc_data, ticker, info.get("marketCap", 'N/A'), today)
        else:
            pe = pe_data.get(ticker, {}).get(today, 'N/A')
            mc = mc_data.get(ticker, {}).get(today, 'N/A')

        return {
            "Ticker": ticker,
            "Company Name": company_name,
            "Current Price": round(current_price, 2),
            "Price Change Today": calculate_percent_change(current_price, prev_price),
            "Price Change Week": calculate_percent_change(current_price, hist_data['Close'].iloc[-6]) if len(hist_data) >= 7 else "N/A",
            "Price Change Month": calculate_percent_change(current_price, hist_data['Close'].iloc[0]),
            "Volume Today": volume_today,
            "Avg Volume (3 mon)": avg_volume,
            "DVAV (Day Volume Over Avg Volume)": round(volume_today / avg_volume, 4)
                if is_number(volume_today) and is_number(avg_volume) and avg_volume != 0 else "N/A",
            "Shares Available": shares,
            "DVSA (Volume / Shares Available)": round(volume_today / shares, 4)
                if is_number(volume_today) and is_number(shares) and shares != 0 else "N/A",
            "P/E Ratio": pe,
            "P/E Change (3 Mon)": calculate_percent_change(pe, get_historical_value(pe_data, ticker, 90)),
            "Market Cap": mc,
            "Market Cap Change (3 Mon)": calculate_percent_change(mc, current_price * shares
                if is_number(current_price) and is_number(shares) else 'N/A'),
            "Last Update": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        logger.warning(f"Error processing {ticker}: {e}")
        return None

def main():
    start_time = datetime.now()
    today = start_time.strftime("%Y-%m-%d")

    formatted = read_json_file(FORMATTED_TICKERS_FILE_PATH)
    tickers = [t for t in formatted.get("tickers", []) if isinstance(t, str)]
    pe_data = read_json_file(PE_FILE_PATH)
    mc_data = read_json_file(MC_FILE_PATH)
    export_data = read_json_file(EXPORT_FILE_PATH)
    existing_map = {item["Ticker"]: item for item in export_data if isinstance(item, dict)}

    def process(ticker):
        try:
            user_agent = random.choice(USER_AGENTS)
            session = requests.Session()
            session.headers.update({"User-Agent": user_agent})
            info = yf.Ticker(ticker, session=session).info
            company_name = info.get("shortName", "Unknown")
            return fetch_price(ticker, pe_data, mc_data, export_data, today, company_name, session)
        except Exception as e:
            logger.warning(f"Failed to process {ticker}: {e}")
            return None

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process, tickers))

    for data in filter(None, results):
        existing_map[data["Ticker"]] = data

    write_json_file(EXPORT_FILE_PATH, list(existing_map.values()))
    write_json_file(PE_FILE_PATH, pe_data)
    write_json_file(MC_FILE_PATH, mc_data)

    logger.info(f"Script ran in {datetime.now() - start_time}")

if __name__ == "__main__":
    main()