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
        dividend_yield = stock.info.get('dividendYield', 'N/A')
        one_year_target = stock.info.get('targetMeanPrice', 'N/A')
        bid = stock.info.get('bid', 'N/A')
        ask = stock.info.get('ask', 'N/A')
        day_range = f"{stock.info.get('dayLow', 'N/A')} - {stock.info.get('dayHigh', 'N/A')}"

        # Calculate bid-ask spread
        bid_ask_spread = f"{bid} - {ask}" if bid != 'N/A' and ask != 'N/A' else 'N/A'

        # Calculate percent change in P/E over the past three months
        three_months_ago = datetime.today() - timedelta(days=90)
        formatted_date_90_days_ago = three_months_ago.strftime("%m/%d/%y")

        try:
            with open(PE_FILE_PATH, 'r') as pe_file:
                pe_data = json.load(pe_file)
                ticker_data = pe_data.get(ticker, {})

                # Check for data exactly 90 days ago
                if formatted_date_90_days_ago in ticker_data:
                    three_month_close = ticker_data[formatted_date_90_days_ago].get("PE", 'N/A')
                else:
                    # Use the oldest recorded data as a fallback
                    oldest_date = min(ticker_data.keys(), default=None)
                    if oldest_date:
                        three_month_close = ticker_data[oldest_date].get("PE", 'N/A')
                    else:
                        three_month_close = 'N/A'

        except Exception as e:
            logging.warning(f"Error retrieving P/E data for {ticker}: {e}")
            three_month_close = 'N/A'

        # Check if valid data was retrieved
        if three_month_close != 'N/A' and trailing_pe != 'N/A':
            try:
                # Calculate percent change in P/E ratio
                pe_change_3mo = calculate_percent_change(trailing_pe, float(three_month_close))
            except Exception as e:
                logging.warning(f"Error calculating P/E change for {ticker}: {e}")
                pe_change_3mo = 'N/A'
        else:
            pe_change_3mo = 'N/A'

        # Add P/E ratio to the file
        add_pe_to_file(ticker, trailing_pe)

        # Calculate market cap change
        percent_market_cap_change = (
            calculate_percent_change(
                market_cap,
                (current_price * shares_outstanding) if current_price != 'N/A' else 'N/A',
            )
            if market_cap != 'N/A' and shares_outstanding != 'N/A' else 'N/A'
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

        # Add Market Cap to the file
        if market_cap != 'N/A':
            add_market_cap_to_file(ticker, market_cap)

        # Check if the company is an ETF
        is_etf = "ETF" in company_name.upper()

        # Prepare the return data
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

        # Exclude certain fields if it's an ETF
        if not is_etf:
            result.update({
                'Shares Available': shares_outstanding,
                'Market Cap': market_cap,
                'Market Cap Change (3 Mon)': percent_market_cap_change,
                'Dividend Yield': dividend_yield,
                'One Year Target': one_year_target,
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

if __name__ == '__main__':
    try:
        while not shutdown_event.is_set():
            export_all_stock_data()
            logging.info("Waiting for the next cycle (3 minutes)...")
            shutdown_event.wait(180)
    except KeyboardInterrupt:
        logging.info("Shutdown signal received. Exiting...")
        shutdown_event.set()
