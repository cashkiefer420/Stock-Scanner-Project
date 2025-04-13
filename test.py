import json

# File paths
stock_data_export_path = "json/stock_data_export.json"
formatted_tickers_path = "json/formatted_tickers.json"

def format_tickers():
    try:
        # Read the stock_data_export.json file
        with open(stock_data_export_path, "r") as stock_data_file:
            stock_data = json.load(stock_data_file)

        # Extract the tickers from the stock data
        tickers = [stock["Ticker"] for stock in stock_data]

        # Create the formatted tickers structure
        formatted_tickers = {"tickers": tickers}

        # Write to formatted_tickers.json
        with open(formatted_tickers_path, "w") as formatted_tickers_file:
            json.dump(formatted_tickers, formatted_tickers_file, indent=4)

        print(f"Formatted tickers saved to {formatted_tickers_path}")
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON - {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    format_tickers()
