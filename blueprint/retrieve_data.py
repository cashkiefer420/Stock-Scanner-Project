import yfinance as yf
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from datetime import datetime, timedelta

# Base directory setup
base_dir = r"/home/ec2-user/Stock-Scanner-Project/"
TICKER_FILE_PATH = os.path.join(base_dir, "json", "processed_tickers.json")
EXPORT_FILE_PATH = os.path.join(base_dir, "json", "stock_data_export.json")
PE_FILE_PATH = os.path.join(base_dir, "json", "PE_num.json")
MarketCap_FILE_PATH = os.path.join(base_dir, "json", "MC_num.json")

# Logging setup for both file and console
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)

logging.info("Stock data retrieval started")

shutdown_event = Event()

# Track export status
last_export_dates = {"PE": None, "MC": None}

def ensure_serializable(data):
    """Convert non-serializable values to serializable format."""
    if isinstance(data, (list, tuple)):
        return [ensure_serializable(item) for item in data]
    elif isinstance(data, dict):
        return {key: ensure_serializable(value) for key, value in data.items()}
    elif isinstance(data, (int, float, str)) or data is None:
        return data
    else:
        return str(data)

def calculate_percent_change(new, old):
    """Calculate percentage change between two values."""
    try:
        if old == 0 or old == 'N/A':
            return 'N/A'
        return round(((new - old) / old) * 100, 2)
    except Exception as e:
        logging.exception("Error calculating percent change:")
        return 'N/A'

def update_json_file(file_path, ticker, key, value):
    """Generic function to update a JSON file with a new key-value pair."""
    try:
        current_date = datetime.now().strftime("%m/%d/%y")

        # Load existing data or initialize new structure
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                except json.decoder.JSONDecodeError:
                    logging.warning(f"Invalid JSON in {file_path}. Reinitializing file.")
                    data = {}
        else:
            data = {}

        # Ensure ticker entry exists
        if ticker not in data:
            data[ticker] = {}

        # Add or update the data for the current date
        if current_date not in data[ticker]:
            data[ticker][current_date] = {key: value}

            # Write updated data back to the file
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as file:
                json.dump(ensure_serializable(data), file, indent=4)

    except Exception as e:
        logging.exception(f"Error updating {file_path} for {ticker}:")

def add_market_cap_to_file(ticker, market_cap_value):
    """Add Market Cap to file with corresponding date."""
    update_json_file(MarketCap_FILE_PATH, ticker, "Market Cap", market_cap_value)

def add_pe_to_file(ticker, pe_value):
    """Add P/E ratio to PE file with corresponding date."""
    update_json_file(PE_FILE_PATH, ticker, "PE", pe_value)

def fetch_price(ticker):
    """Fetch stock price and other data for a given ticker."""
    try:
        stock = yf.Ticker(ticker)
        hist_data = stock.history(period="3mo")
        if hist_data.empty:
            return {'Ticker': ticker, 'Current Price': 'N/A'}

        # Fetch required data
        company_name = stock.info.get('longName', 'N/A')
        current_price = hist_data['Close'].iloc[-1]
        volume_today = hist_data['Volume'].iloc[-1] if 'Volume' in hist_data.columns else 'N/A'
        avg_volume = stock.info.get('averageVolume', 'N/A')
        market_cap = stock.info.get('marketCap', 'N/A')
        shares_outstanding = stock.info.get('sharesOutstanding', 'N/A')
        trailing_pe = stock.info.get('trailingPE', 'N/A')
        
        # Fetch P/E change over the past three months or use the oldest available data
        oldest_pe = 'N/A'
        pe_change_3mo = 'N/A'
        
        try:
            with open(PE_FILE_PATH, 'r') as pe_file:
                pe_data = json.load(pe_file)
                ticker_data = pe_data.get(ticker, {})

                if ticker_data:
                    # Convert date strings to datetime objects and sort them
                    sorted_dates = sorted(ticker_data.keys(), key=lambda d: datetime.strptime(d, "%m/%d/%y"))

                    # Get the oldest available P/E data
                    oldest_date = sorted_dates[0]
                    oldest_pe = float(ticker_data[oldest_date].get("PE", 'N/A')) if ticker_data[oldest_date].get("PE", 'N/A') != 'N/A' else 'N/A'

                    # Calculate P/E change using the oldest available data
                    if oldest_pe != 'N/A' and trailing_pe != 'N/A':
                        pe_change_3mo = calculate_percent_change(trailing_pe, oldest_pe)

        except Exception as e:
            logging.warning(f"Error retrieving P/E data for {ticker}: {e}")

        # Add P/E ratio to the file
        add_pe_to_file(ticker, trailing_pe)

        # Other calculations remain unchanged...
        result = {
            'Ticker': ticker,
            'Company Name': company_name,
            'Current Price': round(current_price, 4),
            'P/E Ratio': trailing_pe,
            'P/E Change (Using Oldest Data)': pe_change_3mo,
        }

        return result

    except Exception as e:
        logging.exception(f"Error fetching data for {ticker}:")
        return {'Ticker': ticker, 'Current Price': 'N/A'}
def load_tickers():
    """Load ticker symbols from the JSON file."""
    try:
        with open(TICKER_FILE_PATH, 'r') as file:
            data = json.load(file)
            return data.get("tickers", [])
    except Exception as e:
        logging.exception("Error loading tickers from file:")
        return []

def export_all_stock_data():
    """Fetch and export stock data for all tickers."""
    stock_list = load_tickers()
    if not stock_list:
        logging.error("No tickers found to process.")
        return

    logging.info(f"Processing {len(stock_list)} tickers.")
    result = []

    start_time = time.time()
    with ThreadPoolExecutor() as executor:
        for stock_data in executor.map(fetch_price, stock_list):
            result.append(stock_data)

    elapsed_time = time.time() - start_time
    logging.info(f"Processed {len(stock_list)} tickers in {elapsed_time:.2f} seconds.")

    # Save results to file
    try:
        os.makedirs(os.path.dirname(EXPORT_FILE_PATH), exist_ok=True)
        with open(EXPORT_FILE_PATH, 'w') as json_file:
            json.dump(ensure_serializable(result), json_file, indent=4)
        logging.info(f"Stock data exported to {EXPORT_FILE_PATH}")
    except Exception as e:
        logging.exception("Error exporting stock data:")

if __name__ == '__main__':
    try:
        while not shutdown_event.is_set():
            export_all_stock_data()
            logging.info("Waiting for the next cycle (3 minutes)...")
            shutdown_event.wait(180)
    except KeyboardInterrupt:
        logging.info("Shutdown signal received. Exiting...")
        shutdown_event.set()
