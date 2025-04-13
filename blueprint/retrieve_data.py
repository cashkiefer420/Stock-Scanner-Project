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
    """Reads JSON data from a local file."""
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
    """Writes JSON data to a local file."""
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4, default=convert_to_serializable)
    except Exception as e:
        logger.error(f"Error writing to {file_path}: {e}")

def convert_to_serializable(obj):
    """Converts non-serializable objects to serializable ones."""
    if isinstance(obj, (np.int64, np.float64)):
        return obj.item()  # Convert numpy types to Python int/float
    if isinstance(obj, np.ndarray):
        return obj.tolist()  # Convert numpy arrays to lists
    raise TypeError(f"Type {type(obj)} not serializable")

def calculate_percent_change(new, old):
    """Calculates the percentage change between two values."""
    try:
        if old == 0 or old == 'N/A':
            return 'N/A'
        return round(((new - old) / old) * 100, 2)
    except Exception as e:
        logger.error(f"Error calculating percent change: {e}")
        return 'N/A'

def update_daily_value(data, ticker, value, today):
    """Updates daily value for a ticker in the data."""
    if ticker not in data or today not in data[ticker]:
        if ticker not in data:
            data[ticker] = {}
        data[ticker][today] = value
    return data[ticker][today]

def get_historical_value(data, ticker, days_ago):
    """Gets the historical value of a ticker from a specified number of days ago."""
    target_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    return data.get(ticker, {}).get(target_date, 'N/A')

def fetch_price(ticker, pe_data, mc_data, export_data, today):
    """Fetches the latest price and other information for a given ticker."""
    try:
        stock = yf.Ticker(ticker)
        hist_data = stock.history(period="3mo")
        
        # Check if the DataFrame is empty or doesn't contain the required columns
        if hist_data.empty or 'Close' not in hist_data.columns or hist_data.shape[0] < 2:
            logger.warning(f"Not enough data for ticker {ticker}. Skipping.")
            return None

        # Safely retrieve the required data
        current_price = hist_data['Close'].iloc[-1]
        prev_price = hist_data['Close'].iloc[-2]
        volume_today = hist_data['Volume'].iloc[-1] if 'Volume' in hist_data.columns else 'N/A'
        avg_volume = stock.info.get('averageVolume', 'N/A')

        export_entry = next((item for item in export_data if item['Ticker'] == ticker), {})
        last_update = export_entry.get("Last Update", "")[:10]

        # Preserve existing values for specific fields
        shares = export_entry.get('Shares Available', 'N/A')

        # Update only if the last update is not today
        if today != last_update:
            shares = stock.info.get('sharesOutstanding', 'N/A')

        company_name = export_entry.get('Company Name', 'N/A')  # Preserve the existing company name

        pe = update_daily_value(pe_data, ticker, stock.info.get('trailingPE', 'N/A'), today)
        mc = update_daily_value(mc_data, ticker, stock.info.get('marketCap', 'N/A'), today)

        bid_ask = f"{stock.info.get('bid', 'N/A')} - {stock.info.get('ask', 'N/A')}"
        day_range = f"{stock.info.get('dayLow', 'N/A')} - {stock.info.get('dayHigh', 'N/A')}"
        dvav = round(volume_today / avg_volume, 4) if avg_volume not in [0, 'N/A'] else 'N/A'
        dvsa = round(volume_today / shares, 4) if shares not in [0, 'N/A'] else 'N/A'
        pe_change = calculate_percent_change(pe, get_historical_value(pe_data, ticker, 90))
        mc_change = calculate_percent_change(mc, current_price * shares if current_price != 'N/A' and shares != 'N/A' else 'N/A')

        week_data = stock.history(start=datetime.today() - timedelta(days=7))
        week_change = calculate_percent_change(current_price, week_data['Close'].iloc[0]) if not week_data.empty else 'N/A'

        return {
            'Ticker': ticker,
            'Company Name': company_name,  # Preserve the existing company name
            'Current Price': round(current_price, 2),
            'Price Change Today': calculate_percent_change(current_price, prev_price),
            'Price Change Week': week_change,
            'Price Change Month': calculate_percent_change(current_price, hist_data['Close'].iloc[0]),
            'Volume Today': volume_today,
            'Avg Volume (3 mon)': avg_volume,
            'DVAV (Day Volume Over Average Volume)': dvav,
            'P/E Ratio': pe,
            'P/E Change (3 Mon)': pe_change,
            'Shares Available': shares,
            'Market Cap': mc,
            'Market Cap Change (3 Mon)': mc_change,
            'DVSA (Volume Today Over Shares Available)': dvsa,
            'Last Update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        logger.exception(f"Error processing {ticker}")
        return None

def main():
    """Main function to process tickers locally."""
    today = datetime.now().strftime("%Y-%m-%d")

    # Read tickers from formatted_tickers.json
    formatted_tickers_data = read_json_file(FORMATTED_TICKERS_FILE_PATH)
    tickers = formatted_tickers_data.get("tickers", [])  # Safely extract tickers list

    # Read additional data files
    pe_data = read_json_file(PE_FILE_PATH)
    mc_data = read_json_file(MarketCap_FILE_PATH)
    export_data = read_json_file(EXPORT_FILE_PATH)

    results = []
    processed_count = 0  # Counter to track processed tickers

    for ticker in tickers:
        data = fetch_price(ticker, pe_data, mc_data, export_data, today)
        if data:
            results.append(data)
        
        processed_count += 1

        # Log progress and update JSON files every 100 tickers
        if processed_count % 100 == 0:
            logger.info(f"Processed {processed_count} tickers so far. Writing intermediate results to JSON files.")
            write_json_file(EXPORT_FILE_PATH, results)
            write_json_file(PE_FILE_PATH, pe_data)
            write_json_file(MarketCap_FILE_PATH, mc_data)

    # Write final results after processing all tickers
    logger.info(f"Processing completed. Total tickers processed: {processed_count}. Writing final results to JSON files.")
    write_json_file(EXPORT_FILE_PATH, results)
    write_json_file(PE_FILE_PATH, pe_data)
    write_json_file(MarketCap_FILE_PATH, mc_data)

if __name__ == "__main__":
    main()
