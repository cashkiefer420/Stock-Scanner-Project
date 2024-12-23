import yfinance as yf
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from datetime import datetime, timedelta
from shutil import copyfile

# Base directory setup
current_dir = os.path.dirname(os.path.abspath(__file__))
while os.path.basename(current_dir) != "Stock-Scanner-Project":
    current_dir = os.path.dirname(current_dir)
    if current_dir == "/":
        raise FileNotFoundError("Base directory 'Stock-Scanner-Project' not found!")
base_dir = current_dir

# Define paths
TICKER_FILE_PATH = os.path.join(base_dir, "json", "Sample_ticker.json")
EXPORT_FILE_PATH = os.path.join(base_dir, "json", "stock_data_export.json")

# Ensure the JSON directory exists
os.makedirs(os.path.dirname(TICKER_FILE_PATH), exist_ok=True)
if not os.path.exists(TICKER_FILE_PATH):
    with open(TICKER_FILE_PATH, 'w') as file:
        json.dump({"tickers": []}, file, indent=4)

# Logging setup
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format, filename='/home/ec2-user/stock_data.log', filemode='a')

logging.info("Stock data retrieval started")

# Shutdown event for graceful exit
shutdown_event = Event()

# Helper functions
def calculate_percent_change(new, old):
    """Calculate the percentage change between two values."""
    try:
        if old == 0 or old == 'N/A':
            return 'N/A'
        return round(((new - old) / old) * 100, 2)
    except Exception as e:
        logging.exception("Error calculating percent change:")
        return 'N/A'


def load_tickers():
    """Load ticker symbols from the JSON file."""
    try:
        with open(TICKER_FILE_PATH, 'r') as file:
            data = json.load(file)
            return data.get("tickers", [])
    except Exception as e:
        logging.exception("Error loading tickers from file:")
        return []


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
        prev_close = hist_data['Close'].iloc[-2] if len(hist_data) > 1 else 'N/A'
        prev_open = hist_data['Open'].iloc[0] if len(hist_data) > 0 else 'N/A'
        volume_today = hist_data['Volume'].iloc[-1] if 'Volume' in hist_data.columns else 'N/A'
        avg_volume = stock.info.get('averageVolume', 'N/A')
        market_cap = stock.info.get('marketCap', 'N/A')
        shares_outstanding = stock.info.get('sharesOutstanding', 'N/A')
        trailing_pe = stock.info.get('trailingPE', 'N/A')
        eps = stock.info.get('trailingEps', 'N/A')
        earnings_date = stock.info.get('earningsDate', ['N/A'])[0] if stock.info.get('earningsDate') else 'N/A'
        dividend_yield = stock.info.get('dividendYield', 'N/A')
        ex_dividend_date = stock.info.get('exDividendDate', 'N/A')
        one_year_target = stock.info.get('targetMeanPrice', 'N/A')
        bid = stock.info.get('bid', 'N/A')
        ask = stock.info.get('ask', 'N/A')
        day_range = f"{stock.info.get('dayLow', 'N/A')} - {stock.info.get('dayHigh', 'N/A')}"

        # Percent changes
        three_months_ago = datetime.today() - timedelta(days=90)
        three_month_data = stock.history(start=three_months_ago)
        three_month_close = (
            three_month_data['Close'].iloc[0] if not three_month_data.empty else 'N/A'
        )
        percent_market_cap_change = (
            calculate_percent_change(
                market_cap,
                (three_month_close * shares_outstanding) if three_month_close != 'N/A' else 'N/A',
            )
            if market_cap != 'N/A' and shares_outstanding != 'N/A' else 'N/A'
        )
        percent_pe_change = (
            calculate_percent_change(trailing_pe, stock.info.get('trailingPE', 'N/A'))
            if trailing_pe != 'N/A' else 'N/A'
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

        return {
            'Ticker': ticker,
            'Company Name': company_name,
            'Current Price': round(current_price, 4),
            'Price Change Today': calculate_percent_change(current_price, prev_close),
            'Price Change Week': percent_gain_week,
            'Price Change Month': calculate_percent_change(current_price, three_month_close),
            'Price Change Year': percent_gain_year,
            'Previous Close': round(prev_close, 4) if prev_close != 'N/A' else 'N/A',
            'Previous Open': round(prev_open, 4),
            'Bid (Buy price Currently)': bid,
            'Ask (Sell Price Currently)': ask,
            'Days Range': day_range,
            'Shares Available': shares_outstanding,
            'Volume Today': volume_today,
            'Avg Volume (3 mon)': avg_volume,
            'DVAV (Day Volume Over Average Volume)': dvav,
            'Market Cap': market_cap,
            'Market Cap Change (3 Mon)': percent_market_cap_change,
            'Beta': stock.info.get('beta', 'N/A'),
            'P/E Ratio': trailing_pe,
            'P/E Change (3 Mon)': percent_pe_change,
            'Earnings Per Share': eps,
            'Earnings Date': earnings_date,
            'Dividend Yield': dividend_yield,
            'Ex-Dividend Date': ex_dividend_date,
            'One Year Target': one_year_target,
        }
    except Exception as e:
        logging.exception(f"Error fetching data for {ticker}:")
        return {'Ticker': ticker, 'Current Price': 'N/A'}


def export_all_stock_data():
    """Fetch and export stock data for all tickers."""
    stock_list = load_tickers()
    if not stock_list:
        logging.error("No tickers found to process.")
        return

    logging.info(f"Processing {len(stock_list)} tickers.")
    result = []

    with ThreadPoolExecutor() as executor:
        for stock_data in executor.map(fetch_price, stock_list):
            result.append(stock_data)

    # Create a backup of the previous file, if it exists
    if os.path.exists(EXPORT_FILE_PATH):
        backup_path = f"{EXPORT_FILE_PATH}.backup"
        copyfile(EXPORT_FILE_PATH, backup_path)
        logging.info(f"Backup created at {backup_path}")

    # Write results to the JSON file
    try:
        os.makedirs(os.path.dirname(EXPORT_FILE_PATH), exist_ok=True)
        with open(EXPORT_FILE_PATH, 'w') as json_file:
            json.dump(result, json_file, indent=4)
        logging.info("Stock data exported to stock_data_export.json")
    except Exception as e:
        logging.exception("Error exporting stock data:")


if __name__ == '__main__':
    try:
        while not shutdown_event.is_set():
            export_all_stock_data()
            logging.info("Waiting for the next cycle (3 minutes)...")
            shutdown_event.wait(180)  # Block for 180 seconds or until shutdown_event is set
    except KeyboardInterrupt:
        logging.info("Shutdown signal received. Exiting...")
        shutdown_event.set()
