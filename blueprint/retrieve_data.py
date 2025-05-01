import os
import json
import numpy as np
import yfinance as yf
import pandas as pd
import orjson
import logging
import signal
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Timeout setup
class TimeoutException(Exception): pass

def timeout_handler(signum, frame):
    raise TimeoutException()

signal.signal(signal.SIGALRM, timeout_handler)

# Local JSON storage directory
LOCAL_JSON_DIR = os.path.join(os.path.dirname(__file__), "..", "json")
os.makedirs(LOCAL_JSON_DIR, exist_ok=True)

def read_local_json_file(filename):
    path = os.path.join(LOCAL_JSON_DIR, filename)
    try:
        with open(path, "rb") as f:
            return orjson.loads(f.read())
    except FileNotFoundError:
        return {}
    except Exception as e:
        logger.error(f"Failed to read {filename}: {e}")
        return {}

def write_local_json_file(filename, data):
    path = os.path.join(LOCAL_JSON_DIR, filename)
    try:
        def convert_numpy(obj):
            if isinstance(obj, (np.integer, int)): return int(obj)
            if isinstance(obj, (np.floating, float)): return float(obj)
            if isinstance(obj, np.ndarray): return obj.tolist()
            raise TypeError(f"Type {type(obj)} not serializable")

        with open(path, "wb") as f:
            f.write(orjson.dumps(data, default=convert_numpy, option=orjson.OPT_INDENT_2))

        logger.info(f"✅ Saved {len(data)} records to {filename}")
        if len(data) < 100:
            logger.warning(f"⚠️ WARNING: {filename} contains fewer than 100 records.")
    except Exception as e:
        logger.error(f"Failed to write {filename}: {e}")

def is_number(value):
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False

def calculate_percent_change(current, previous):
    try:
        if is_number(current) and is_number(previous) and previous != 0:
            return round(((current - previous) / previous) * 100, 2)
        return 'N/A'
    except Exception:
        return 'N/A'

def get_stock_data(ticker_symbol):
    try:
        print(f"📈 Fetching history for {ticker_symbol}...")
        ticker = yf.Ticker(ticker_symbol)
        signal.alarm(10)
        hist = ticker.history(period="1y")
        signal.alarm(0)
        print(f"✅ Fetched history for {ticker_symbol}")
        return hist if not hist.empty else pd.DataFrame()
    except TimeoutException:
        print(f"⏰ Timeout getting history for {ticker_symbol}")
        return pd.DataFrame()
    except Exception as e:
        signal.alarm(0)
        print(f"❌ Failed to get history for {ticker_symbol}: {e}")
        return pd.DataFrame()

def get_stock_info(ticker_obj, ticker):
    try:
        print(f"🧠 Fetching info for {ticker}...")
        signal.alarm(10)
        info = ticker_obj.info
        signal.alarm(0)
        print(f"✅ Got info for {ticker}")
        return info
    except TimeoutException:
        print(f"⏰ Timeout getting info for {ticker}")
        return None
    except Exception as e:
        signal.alarm(0)
        print(f"❌ Failed to get info for {ticker}: {e}")
        return None

def main():
    tickers_json = read_local_json_file("formatted_tickers.json")
    latest_data = read_local_json_file("stock_data_export.json")
    export_data = {entry['Ticker']: entry for entry in latest_data} if isinstance(latest_data, list) else {}

    tickers_data = {
        entry["Ticker"]: {"name": entry.get("Company Name", "")} 
        for entry in tickers_json.get("tickers", []) 
        if "Ticker" in entry
    }

    if not tickers_data:
        print("🚫 No valid tickers found in formatted_tickers.json — exiting.")
        return

    print(f"🔍 Processing {len(tickers_data)} tickers...")

    for ticker, metadata in tickers_data.items():
        try:
            print(f"\n➡️  Ticker: {ticker}")
            ticker_obj = yf.Ticker(ticker)
            hist_data = get_stock_data(ticker)
            if hist_data.empty:
                print(f"⚠️ No history data for {ticker}")
                continue

            info = get_stock_info(ticker_obj, ticker)
            if not info:
                print(f"⚠️ Skipping {ticker} due to missing info")
                continue

            current_price = hist_data['Close'].iloc[-1]
            prev_price = hist_data['Close'].iloc[-2] if hist_data.shape[0] >= 2 else current_price
            volume_today = hist_data['Volume'].iloc[-1]
            avg_volume = info.get('averageVolume', 0)
            shares = info.get('sharesOutstanding', 0)
            pe = info.get('trailingPE')
            mc = info.get('marketCap')

            export_data[ticker] = {
                'Ticker': ticker,
                'Company Name': info.get('shortName', 'N/A'),
                'Current Price': round(current_price, 2),
                'Price Change Today': calculate_percent_change(current_price, prev_price),
                'Price Change Week': calculate_percent_change(current_price, hist_data['Close'].iloc[-6]) if hist_data.shape[0] >= 7 else 'N/A',
                'Price Change Month': calculate_percent_change(current_price, hist_data['Close'].iloc[0]),
                'Volume Today': volume_today,
                'Avg Volume (3 mon)': avg_volume,
                'DVAV (Day Volume Over Avg Volume)': round(volume_today / avg_volume, 4) if is_number(volume_today) and is_number(avg_volume) and avg_volume != 0 else 'N/A',
                'Shares Available': shares,
                'DVSA (Volume/Share)': round(volume_today / shares, 4) if is_number(volume_today) and is_number(shares) and shares != 0 else 'N/A',
                'P/E Ratio': pe,
                'Market Cap': mc,
                'Last Update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            print(f"✅ Finished processing {ticker}")

        except Exception as e:
            print(f"❌ Error processing {ticker}: {e}")

    print(f"\n💾 Saving data for {len(export_data)} tickers to stock_data_export.json")
    write_local_json_file("stock_data_export.json", list(export_data.values()))
    print("✅ Done.")

if __name__ == "__main__":
    main()
