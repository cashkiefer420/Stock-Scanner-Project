import yfinance as yf
import json
import logging
import os
from datetime import datetime, timedelta
import numpy as np

# Logging setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Base directory and file paths
base_dir = r"/home/ec2-user/Stock-Scanner-Project"
FORMATTED_TICKERS_FILE_PATH = os.path.join(base_dir, "json", "formatted_tickers.json")
PE_FILE_PATH = os.path.join(base_dir, "json", "PE_num.json")
MarketCap_FILE_PATH = os.path.join(base_dir, "json", "MC_num.json")
EXPORT_FILE_PATH = os.path.join(base_dir, "json", "stock_data_export.json")

def read_json_file(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                return json.load(file)
        else:
            logger.warning(f"File {file_path} not found. Returning empty.")
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
        if old == 0 or old == 'N/A':
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

def fetch_price(ticker, pe_data, mc_data, export_data, today):
    try:
        stock = yf.Ticker(ticker)
        hist_data = stock.history(period="3mo")

        if hist_data.empty or 'Close' not in hist_data.columns or hist_data.shape[0] < 2:
            logger.warning(f"{ticker} skipped due to not enough data.")
            return "SKIPPED"

        current_price = hist_data['Close'].iloc[-1]
        prev_price = hist_data['Close'].iloc[-2]
        volume_today = hist_data['Volume'].iloc[-1] if 'Volume' in hist_data.columns else 'N/A'
        avg_volume = stock.info.get('averageVolume', 'N/A')

        export_entry = next((item for item in export_data if item['Ticker'] == ticker), {})
        last_update = export_entry.get("Last Update", "")[:10]
        is_etf = export_entry.get('Is ETF', False)

        result = {
            'Ticker': ticker,
            'Company Name': export_entry.get('Company Name', 'N/A'),
            'Is ETF': is_etf,
            'Current Price': round(current_price, 2),
            'Price Change Today': calculate_percent_change(current_price, prev_price),
            'Price Change Week': calculate_percent_change(current_price, hist_data['Close'].iloc[-6]),
            'Price Change Month': calculate_percent_change(current_price, hist_data['Close'].iloc[0]),
            'Volume Today': volume_today,
            'Avg Volume (3 mon)': avg_volume,
            'DVAV (Day Volume Over Average Volume)': round(volume_today / avg_volume, 4) if avg_volume not in ['N/A', 0] else 'N/A',
            'DVSA (Volume Today Over Shares Available)': 'N/A',  # to be updated later
            'Last Update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        if not is_etf:
            shares = export_entry.get('Shares Available', 'N/A')
            if today != last_update:
                shares = stock.info.get('sharesOutstanding', 'N/A')
            pe = update_daily_value(pe_data, ticker, stock.info.get('trailingPE', 'N/A'), today)
            mc = update_daily_value(mc_data, ticker, stock.info.get('marketCap', 'N/A'), today)
            pe_change = calculate_percent_change(pe, get_historical_value(pe_data, ticker, 90))
            mc_change = calculate_percent_change(mc, current_price * shares if current_price != 'N/A' and shares != 'N/A' else 'N/A')

            result.update({
                'P/E Ratio': pe,
                'P/E Change (3 Mon)': pe_change,
                'Shares Available': shares,
                'Market Cap': mc,
                'Market Cap Change (3 Mon)': mc_change,
                'DVSA (Volume Today Over Shares Available)': round(volume_today / shares, 4) if shares not in ['N/A', 0] else 'N/A'
            })

        return result

    except Exception as e:
        logger.warning(f"{ticker} may be delisted or errored: {e}")
        return "DELISTED"

def main():
    today = datetime.now().strftime("%Y-%m-%d")

    formatted_data = read_json_file(FORMATTED_TICKERS_FILE_PATH)
    pe_data = read_json_file(PE_FILE_PATH)
    mc_data = read_json_file(MarketCap_FILE_PATH)
    export_data = read_json_file(EXPORT_FILE_PATH)

    tickers = formatted_data.get("tickers", [])
    new_tickers = []
    new_export_data = []
    processed_count = 0

    for ticker in tickers:
        data = fetch_price(ticker, pe_data, mc_data, export_data, today)

        if data == "DELISTED":
            logger.info(f"{ticker} removed from list due to delisting.")
            continue
        elif data == "SKIPPED":
            new_tickers.append(ticker)
            existing = next((item for item in export_data if item['Ticker'] == ticker), None)
            if existing:
                new_export_data.append(existing)
            continue

        new_tickers.append(ticker)
        new_export_data.append(data)

        processed_count += 1
        if processed_count % 100 == 0:
            logger.info(f"Processed {processed_count} tickers so far.")
            write_json_file(EXPORT_FILE_PATH, new_export_data)
            write_json_file(FORMATTED_TICKERS_FILE_PATH, {"tickers": new_tickers})
            write_json_file(PE_FILE_PATH, pe_data)
            write_json_file(MarketCap_FILE_PATH, mc_data)

    logger.info(f"All tickers processed. Finalizing...")
    write_json_file(EXPORT_FILE_PATH, new_export_data)
    write_json_file(FORMATTED_TICKERS_FILE_PATH, {"tickers": new_tickers})
    write_json_file(PE_FILE_PATH, pe_data)
    write_json_file(MarketCap_FILE_PATH, mc_data)

if __name__ == "__main__":
    main()