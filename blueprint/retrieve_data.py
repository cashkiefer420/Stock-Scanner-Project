import yfinance as yf
import json
import logging
import os
import random
import time
from datetime import datetime, timedelta
import numpy as np
from yfinance import shared

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
    # (same list as before)
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

def update_daily_value(data, ticker, value, today):
    if ticker not in data or today not in data[ticker]:
        if ticker not in data:
            data[ticker] = {}
        data[ticker][today] = value
    return data[ticker][today]

def get_historical_value(data, ticker, days_ago):
    target_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    return data.get(ticker, {}).get(target_date, 'N/A')

def sync_tickers_and_names():
    tickers_names = read_json_file(TICKERS_NAMES_PATH)
    formatted_tickers = read_json_file(FORMATTED_TICKERS_FILE_PATH)

    names_dict = {item["Ticker"]: item["Company Name"] for item in tickers_names}

    updated_tickers = []
    for ticker in formatted_tickers.get("tickers", []):
        company_name = names_dict.get(ticker, "")
        updated_tickers.append({
            "Ticker": ticker,
            "Company Name": company_name,
            "Is ETF": False
        })

    updated_data = {"tickers": updated_tickers}
    write_json_file(FORMATTED_TICKERS_FILE_PATH, updated_data)
    logger.info("Formatted tickers updated with company names.")
    
def fetch_price(ticker, pe_data, mc_data, export_data, today):
    try:
        user_agent = random.choice(USER_AGENTS)
        shared._requests_session.headers.update({"User-Agent": user_agent})

        stock = yf.Ticker(ticker)
        hist_data = stock.history(period="3mo")

        if hist_data.empty or 'Close' not in hist_data.columns or hist_data.shape[0] < 2:
            logger.warning(f"Not enough data for ticker {ticker}. Skipping.")
            return None

        current_price = hist_data['Close'].iloc[-1]
        prev_price = hist_data['Close'].iloc[-2]
        volume_today = hist_data['Volume'].iloc[-1] if 'Volume' in hist_data.columns else 'N/A'
        avg_volume = stock.info.get('averageVolume', 'N/A')

        export_entry = next((item for item in export_data if item['Ticker'] == ticker), {})
        last_update = export_entry.get("Last Update", "")[:10]

        result = {
            'Ticker': export_entry.get('Ticker', ticker),
            'Company Name': export_entry.get('Company Name', stock.info.get('shortName', 'N/A')),
            'Is ETF': export_entry.get('Is ETF', False)
        }

        result.update({
            'Current Price': round(current_price, 2),
            'Price Change Today': calculate_percent_change(current_price, prev_price),
            'Price Change Week': calculate_percent_change(current_price, hist_data['Close'].iloc[-6]) if hist_data.shape[0] >= 7 else 'N/A',
            'Price Change Month': calculate_percent_change(current_price, hist_data['Close'].iloc[0]),
            'Volume Today': volume_today,
            'Avg Volume (3 mon)': avg_volume,
            'DVAV (Day Volume Over Average Volume)': round(volume_today / avg_volume, 4) if is_number(volume_today) and is_number(avg_volume) and avg_volume != 0 else 'N/A'
        })

        if not result['Is ETF']:
            shares = export_entry.get('Shares Available', 'N/A')
            if today != last_update:
                shares = stock.info.get('sharesOutstanding', 'N/A')

            pe = update_daily_value(pe_data, ticker, stock.info.get('trailingPE', 'N/A'), today)
            mc = update_daily_value(mc_data, ticker, stock.info.get('marketCap', 'N/A'), today)

            pe_change = calculate_percent_change(pe, get_historical_value(pe_data, ticker, 90))
            mc_change = calculate_percent_change(mc, current_price * shares if is_number(current_price) and is_number(shares) else 'N/A')

            result.update({
                'Shares Available': shares,
                'DVSA (Volume Today Over Shares Available)': round(volume_today / shares, 4) if is_number(volume_today) and is_number(shares) and shares != 0 else 'N/A',
                'P/E Ratio': pe,
                'P/E Change (3 Mon)': pe_change,
                'Market Cap': mc,
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

    existing_data_map = {item['Ticker']: item for item in export_data}
    processed_count = 0

    for ticker in tickers:
        data = fetch_price(ticker, pe_data, mc_data, export_data, today)
        if data:
            existing_data_map[ticker] = data

        processed_count += 1
        if processed_count % 100 == 0:
            logger.info(f"Processed {processed_count} tickers. Saving intermediate results.")
            write_json_file(EXPORT_FILE_PATH, list(existing_data_map.values()))
            write_json_file(PE_FILE_PATH, pe_data)
            write_json_file(MarketCap_FILE_PATH, mc_data)

    logger.info(f"Processing complete. Total tickers: {processed_count}")
    write_json_file(EXPORT_FILE_PATH, list(existing_data_map.values()))
    write_json_file(PE_FILE_PATH, pe_data)
    write_json_file(MarketCap_FILE_PATH, mc_data)

    elapsed_time = round(time.time() - start_time, 2)
    logger.info(f"Execution time: {elapsed_time} seconds")

if __name__ == "__main__":
    main()