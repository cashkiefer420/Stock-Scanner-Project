import yfinance as yf
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from datetime import datetime, timedelta
import requests_cache
import boto3


# Base directory setup
base_dir = r"/home/ec2-user/Stock-Scanner-Project"
TICKER_FILE_PATH = os.path.join(base_dir, "json", "processed_tickers.json")
EXPORT_FILE_PATH = os.path.join(base_dir, "json", "stock_data_export.json")
PE_FILE_PATH = os.path.join(base_dir, "json", "PE_num.json")
MarketCap_FILE_PATH = os.path.join(base_dir, "json", "MC_num.json")
S3_BUCKET_NAME = "exportbucket--use2-az1--x-s3"
S3_EXPORT_FILE_KEY = "stock_data_export.json"

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
        dividend_yield = stock.info.get('dividendYield', 'N/A')
        one_year_target = stock.info.get('targetMeanPrice', 'N/A')
        bid = stock.info.get('bid', 'N/A')
        ask = stock.info.get('ask', 'N/A')
        day_range = f"{stock.info.get('dayLow', 'N/A')} - {stock.info.get('dayHigh', 'N/A')}"
        
        volume_over_shares = (
            round(volume_today / shares_outstanding, 4)
            if volume_today != 'N/A' and shares_outstanding not in [0, 'N/A']
            else 'N/A'
        )

        # Calculate bid-ask spread
        bid_ask_spread = f"{bid} - {ask}" if bid != 'N/A' and ask != 'N/A' else 'N/A'

        # Calculate percent change in P/E over the past three months
        if trailing_pe == 'N/A':
            logging.warning(f"[API] P/E ratio missing from Yahoo Finance for {ticker}.")

        # Calculate date 90 days ago
        target_date = datetime.now() - timedelta(days=90)

        closest_pe = 'N/A'

        try:
            with open(PE_FILE_PATH, 'r') as pe_file:
                pe_data = json.load(pe_file)
                ticker_data = pe_data.get(ticker, {})

                if not ticker_data:
                    logging.warning(f"[JSON] No historical P/E data found for {ticker}.")
                else:
                    # Convert date strings to datetime objects
                    sorted_dates = sorted(
                        (datetime.strptime(d, "%m/%d/%y"), d) for d in ticker_data.keys()
                    )

                    # Find the closest date to 90 days ago
                    closest_date = min(sorted_dates, key=lambda x: abs(x[0] - target_date))[1]
                    closest_pe = float(ticker_data[closest_date].get("PE", 'N/A')) if ticker_data[closest_date].get("PE", 'N/A') != 'N/A' else 'N/A'

                    if closest_pe == 'N/A':
                        logging.warning(f"[JSON] Closest available P/E data is still missing for {ticker}.")

        except Exception as e:
            logging.exception(f"[JSON] Error retrieving P/E data for {ticker}:")

        # Calculate P/E change using closest available data
        pe_change_3mo = calculate_percent_change(trailing_pe, closest_pe) if closest_pe != 'N/A' and trailing_pe != 'N/A' else 'N/A'

        # Add P/E ratio to the file
        add_pe_to_file(ticker, trailing_pe)

        # Calculate market cap change
        percent_market_cap_change = (
            calculate_percent_change(
                market_cap,
                (current_price * shares_outstanding) if current_price != 'N/A' else 'N/A',
            )
            if market_cap != 'N/A' and shares_outstanding != 'N/A'
            else 'N/A'
        )

        # Weekly and yearly percentage changes
        start_of_week = datetime.today() - timedelta(days=datetime.today().weekday())
        week_data = stock.history(start=start_of_week)
        percent_gain_week = (
            calculate_percent_change(current_price, week_data['Close'].iloc[0])
            if not week_data.empty else 'N/A'
        )

        start_of_year = datetime(datetime.now().year, 1, 1)
        year_data = stock.history(start=start_of_year)
        percent_gain_year = (
            calculate_percent_change(current_price, year_data['Close'].iloc[0])
            if not year_data.empty else 'N/A'
        )

        # DVAV (Day Volume Over Average Volume)
        dvav = round(volume_today / avg_volume, 4) if avg_volume not in [0, 'N/A'] else 'N/A'
        
        dvsa = (
            round(volume_today / shares_outstanding, 4)
            if volume_today not in [0, 'N/A'] and shares_outstanding not in [0, 'N/A']
            else 'N/A'
            )

        # Add Market Cap to the file
        if market_cap != 'N/A':
            add_market_cap_to_file(ticker, market_cap)

        # Check if the company is an ETF
        quote_type = stock.info.get('quoteType', 'N/A')
        is_etf = (quote_type == 'ETF')

        # Base result data
        result = {
            'Ticker': ticker,
            'Company Name': company_name,
            'Current Price': round(current_price, 4),
            'Price Change Today': calculate_percent_change(current_price, hist_data['Close'].iloc[-2]),
            'Price Change Week': percent_gain_week,
            'Price Change Month': calculate_percent_change(current_price, hist_data['Close'].iloc[0]),
            'Price Change Year': percent_gain_year,
            'Bid Ask Spread': bid_ask_spread,
            'Days Range': day_range,
            'Volume Today': volume_today,
            'Avg Volume (3 mon)': avg_volume,
            'DVAV (Day Volume Over Average Volume)': dvav,
            'P/E Ratio': trailing_pe,
            'P/E Change (3 Mon)': pe_change_3mo,
        }

        # Additional data for non-ETFs
        if not is_etf:
            result.update({
                'Shares Available': shares_outstanding,
                'Market Cap': market_cap,
                'Market Cap Change (3 Mon)': percent_market_cap_change,
                'Dividend Yield': dividend_yield,
                'One Year Target': one_year_target,
                'DVSA (Volume Today Over Shares Available)': dvsa,
            })

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
    
    try:
        s3_client = boto3.client('s3')
        s3_client.upload_file(EXPORT_FILE_PATH, S3_BUCKET_NAME, S3_EXPORT_FILE_KEY)
        logging.info(f"Stock data exported to S3 bucket {S3_BUCKET_NAME} with key {S3_EXPORT_FILE_KEY}")
    except Exception as e:
        logging.exception("Error exporting stock data to S3:")

if __name__ == '__main__':
    try:
        while not shutdown_event.is_set():
            export_all_stock_data()
            logging.info("Waiting for the next cycle (3 minutes)...")
            shutdown_event.wait(180)
    except KeyboardInterrupt:
        logging.info("Shutdown signal received. Exiting...")
        shutdown_event.set()
