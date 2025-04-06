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
import pytz

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
    
