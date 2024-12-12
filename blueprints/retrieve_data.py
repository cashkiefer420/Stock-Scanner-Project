import yfinance as yf
import json
from datetime import datetime, timedelta
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event

# Set up logging with log rotation
from logging.handlers import RotatingFileHandler
log_format = '%(asctime)s - %(levelname)s - %(message)s'
handler = RotatingFileHandler('stock_data.log', maxBytes=1_000_000, backupCount=3)
logging.basicConfig(level=logging.INFO, format=log_format, handlers=[handler])

logging.info("Stock data retrieval started")

# Path to your sample tickers JSON file
ticker_file_path = 'https://raw.githubusercontent.com/Toasterfire-come/Stock-Scanner-Project/refs/heads/main/json/Sample_tickers.json?token=GHSAT0AAAAAAC3JEC3OLXRRBOYVQU33357AZ2Z6CEA'
json_export_path = 'https://raw.githubusercontent.com/Toasterfire-come/Stock-Scanner-Project/refs/heads/main/json/stock_data_export.json?token=GHSAT0AAAAAAC3JEC3OCU3VHJYPKXEAGY42Z2Z6RBQ'

# Blocking event for graceful shutdown
shutdown_event = Event()

# Load tickers from the JSON file
def load_tickers_from_file():
    try:
        if not os.path.exists(ticker_file_path):
            logging.error(f"File not found: {ticker_file_path}")
            return []
        with open(ticker_file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.exception("Error loading tickers from file:")
        return []

# Calculate percentage change
def calculate_percent_change(new, old):
    try:
        return round(((new - old) / old) * 100, 4) if old != 'N/A' else 'N/A'
    except (TypeError, ZeroDivisionError):
        return 'N/A'

# Fetch historical data efficiently
def fetch_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist_data = stock.history(period="1mo")
        if hist_data.empty:
            return {'Ticker': ticker, 'Current Price': 'N/A'}

        current_price = hist_data['Close'].iloc[-1]
        prev_close = hist_data['Close'].iloc[-2] if len(hist_data) > 1 else 'N/A'
        prev_open = hist_data['Open'].iloc[0]

        volume_today = hist_data['Volume'].iloc[-1]
        avg_volume = stock.info.get('averageVolume', 'N/A')
        market_cap = stock.info.get('marketCap', 'N/A')
        shares_outstanding = stock.info.get('sharesOutstanding', 'N/A')

        # Calculate percent gains
        start_of_week = datetime.today() - timedelta(days=datetime.today().weekday())
        week_data = stock.history(start=start_of_week)
        percent_gain_week = calculate_percent_change(current_price, week_data['Close'].iloc[0]) if not week_data.empty else 'N/A'

        start_of_year = datetime(datetime.now().year, 1, 1)
        year_data = stock.history(start=start_of_year)
        percent_gain_year = calculate_percent_change(current_price, year_data['Close'].iloc[0]) if not year_data.empty else 'N/A'

        return {
            'Ticker': ticker,
            'Current Price': round(current_price, 4),
            'Previous Open': round(prev_open, 4),
            'Previous Close': round(prev_close, 4) if prev_close != 'N/A' else 'N/A',
            'Volume Today': volume_today,
            'Average Volume': avg_volume,
            'Market Cap': market_cap,
            'Shares Outstanding': shares_outstanding,
            'Percent Gain This Week': percent_gain_week,
            'Percent Gain This Year': percent_gain_year
        }
    except Exception as e:
        logging.exception(f"Error fetching data for {ticker}:")
        return {'Ticker': ticker, 'Current Price': 'N/A'}

# Load existing JSON data
def load_existing_data():
    try:
        if os.path.exists(json_export_path):
            with open(json_export_path, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        logging.exception("Error loading existing JSON data:")
        return []

# Compare and update data
def update_json_data(new_data, existing_data):
    updated = False
    existing_data_dict = {entry['Ticker']: entry for entry in existing_data}

    for new_entry in new_data:
        ticker = new_entry['Ticker']
        if ticker not in existing_data_dict or existing_data_dict[ticker] != new_entry:
            existing_data_dict[ticker] = new_entry
            updated = True

    return list(existing_data_dict.values()), updated

# Export all stock data
def export_all_stock_data():
    stock_list = load_tickers_from_file()
    if not stock_list:
        logging.error("No tickers found to process.")
        return

    existing_data = load_existing_data()
    result = []

    with ThreadPoolExecutor() as executor:
        for stock_data in executor.map(fetch_price, stock_list):
            result.append(stock_data)

    updated_data, data_changed = update_json_data(result, existing_data)

    if data_changed:
        try:
            with open(json_export_path, 'w') as json_file:
                json.dump(updated_data, json_file, indent=4)
            logging.info("Stock data exported to stock_data_export.json")
        except Exception as e:
            logging.exception("Error exporting stock data:")
    else:
        logging.info("No changes detected. JSON file not updated.")

if __name__ == '__main__':
    try:
        while not shutdown_event.is_set():
            export_all_stock_data()
            logging.info("Waiting for the next cycle (3 minutes)...")
            shutdown_event.wait(180)  # Block for 180 seconds or until shutdown_event is set
    except KeyboardInterrupt:
        logging.info("Shutdown signal received. Exiting...")
        shutdown_event.set()
