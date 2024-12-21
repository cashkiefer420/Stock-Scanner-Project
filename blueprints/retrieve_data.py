import yfinance as yf
import json
from datetime import datetime, timedelta
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event

# Define the absolute path to the JSON file
TICKER_FILE_PATH = json/stock_data_export.json
EXPORT_FILE_PATH = json/Sample_tickers.json

# Ensure the JSON file exists locally
if not os.path.exists(TICKER_FILE_PATH):
    with open(TICKER_FILE_PATH, 'w') as file:
        json.dump({"tickers": []}, file, indent=4)

# Logging setup with rotation
from logging.handlers import RotatingFileHandler
log_format = '%(asctime)s - %(levelname)s - %(message)s'
handler = RotatingFileHandler('stock_data.log', maxBytes=1_000_000, backupCount=3)
logging.basicConfig(level=logging.INFO, format=log_format, handlers=[handler])

logging.info("Stock data retrieval started")

# Blocking event for graceful shutdown
shutdown_event = Event()

# Load tickers from the JSON file
def load_tickers():
    try:
        with open(TICKER_FILE_PATH, 'r') as file:
            data = json.load(file)
            return data.get("tickers", [])
    except Exception as e:
        logging.exception("Error loading tickers from file:")
        return []

# Calculate percentage change
def fetch_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist_data = stock.history(period="3mo")
        if hist_data.empty:
            return {'Ticker': ticker, 'Current Price': 'N/A'}

        company_name  = stock.info.get('longName', 'N/A')
        current_price = hist_data['Close'].iloc[-1]
        prev_close = hist_data['Close'].iloc[-2] if len(hist_data) > 1 else 'N/A'
        prev_open = hist_data['Open'].iloc[0]

        volume_today = hist_data['Volume'].iloc[-1]
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

        # Percent gains
        start_of_week = datetime.today() - timedelta(days=datetime.today().weekday())
        week_data = stock.history(start=start_of_week)
        percent_gain_week = calculate_percent_change(current_price, week_data['Close'].iloc[0]) if not week_data.empty else 'N/A'

        start_of_year = datetime(datetime.now().year, 1, 1)
        year_data = stock.history(start=start_of_year)
        percent_gain_year = calculate_percent_change(current_price, year_data['Close'].iloc[0]) if not year_data.empty else 'N/A'

        # Historical market cap and P/E ratio changes
        three_months_ago = datetime.today() - timedelta(days=90)
        three_month_data = stock.history(start=three_months_ago)
        
        if not three_month_data.empty:
            three_month_close = three_month_data['Close'].iloc[0]
            three_month_market_cap = three_month_close * shares_outstanding if shares_outstanding != 'N/A' else 'N/A'
            percent_market_cap_change = calculate_percent_change(market_cap, three_month_market_cap) if three_month_market_cap != 'N/A' else 'N/A'
            percent_pe_change = calculate_percent_change(trailing_pe, stock.info.get('trailingPE', 'N/A'))
        else:
            percent_market_cap_change = 'N/A'
            percent_pe_change = 'N/A'

        # DVAV (Day Volume Over Average Volume)
        dvav = round(volume_today / avg_volume, 4) if avg_volume != 'N/A' and avg_volume != 0 else 'N/A'

        return {
            'Ticker': ticker,
            'Company Name': company_name,
            'Current Price': round(current_price, 4),
            'Price Change Today': calculate_percent_change(current_price, prev_close),
            'Price Change Week': percent_gain_week,
            'Price Change Month': calculate_percent_change(current_price, three_month_close) if three_month_data else 'N/A',
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
            'One Year Target': one_year_target
        }
    except Exception as e:
        logging.exception(f"Error fetching data for {ticker}:")
        return {'Ticker': ticker, 'Current Price': 'N/A'}

# Load existing JSON data
def load_existing_data():
    try:
        if os.path.exists(EXPORT_FILE_PATH):
            with open(EXPORT_FILE_PATH, 'r') as file:
                return json.load(file)
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
    stock_list = load_tickers()
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
            with open(EXPORT_FILE_PATH, 'w') as json_file:
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
