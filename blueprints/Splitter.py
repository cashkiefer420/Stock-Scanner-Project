import json
import logging
import threading
import time

# Function to calculate price change (already defined)
def calculate_price_change(current_price, previous_close):
    return ((current_price - previous_close) / previous_close) * 100

# Function to calculate volume change (already defined)
def calculate_volume_change(current_volume, volume_three_months_ago):
    return ((current_volume - volume_three_months_ago) / volume_three_months_ago) * 100

# Function to calculate P/E change (already defined)
def calculate_pe_change(pe_current, pe_three_months_ago):
    return ((pe_current - pe_three_months_ago) / pe_three_months_ago) * 100

# Function to calculate market cap change (already defined)
def calculate_market_cap_change(market_cap_current, market_cap_three_months_ago):
    return ((market_cap_current - market_cap_three_months_ago) / market_cap_three_months_ago) * 100

# Function to process and split the stock data
def split_json(input_json):
    ticker = input_json.get('ticker')
    current_price = input_json.get('Current Price')
    previous_close = input_json.get('Previous Close')
    current_volume = input_json.get('Volume Today')
    volume_three_months_ago = input_json.get('Volume Three Months Ago')
    pe_current = input_json.get('P/E Ratio')
    pe_three_months_ago = input_json.get('P/E Ratio Three Months Ago')
    market_cap_current = input_json.get('Market Cap')
    market_cap_three_months_ago = input_json.get('Market Cap Three Months Ago')

    # Calculating the required changes
    price_change_today = calculate_price_change(current_price, previous_close)
    volume_change_three_months = calculate_volume_change(current_volume, volume_three_months_ago)
    pe_change_three_months = calculate_pe_change(pe_current, pe_three_months_ago)
    market_cap_change_three_months = calculate_market_cap_change(market_cap_current, market_cap_three_months_ago)
    
    # Prepare the output JSONs
    return {
        'Price Change Today': {
            'ticker': ticker,
            'Price Change Today (%)': price_change_today
        },
        'Volume Change Today': {
            'ticker': ticker,
            'Volume Change (3mo) (%)': volume_change_three_months
        },
        'P/E Change (3mo)': {
            'ticker': ticker,
            'P/E Change (3mo) (%)': pe_change_three_months
        },
        'Market Cap Change (3mo)': {
            'ticker': ticker,
            'Market Cap Change (3mo) (%)': market_cap_change_three_months
        }
    }

# Function to save data to a JSON file
def save_json(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

# Function to export all stock data
def export_all_stock_data():
    input_file_path = 'json/stock_data_export.json'

    # Read the input JSON from the file
    with open(input_file_path, 'r') as f:
        input_json = json.load(f)

    # Process the input and get the calculated results
    output = split_json(input_json)

    # Define output file paths
    price_change_file_path = 'json/Split_price.json'
    volume_change_file_path = 'json/Split_volume.json'
    pe_change_file_path = 'json/Split_pe.json'
    market_cap_change_file_path = 'json/Split_mc.json'

    # Save each result type to its own file
    save_json(output['Price Change Today'], price_change_file_path)
    save_json(output['Volume Change Today'], volume_change_file_path)
    save_json(output['P/E Change (3mo)'], pe_change_file_path)
    save_json(output['Market Cap Change (3mo)'], market_cap_change_file_path)

    logging.info(f"Output saved to {price_change_file_path}, {volume_change_file_path}, {pe_change_file_path}, {market_cap_change_file_path}")

# Function for the main execution loop
def main():
    # Event for graceful shutdown
    shutdown_event = threading.Event()

    try:
        while not shutdown_event.is_set():
            export_all_stock_data()
            shutdown_event.wait(180)  # Block for 180 seconds or until shutdown_event is set
    except KeyboardInterrupt:
        shutdown_event.set()

if __name__ == '__main__':
    main()
