
import json

# File paths
stock_data_export_path = "json/stock_data_export.json"
formatted_tickers_path = "json/formatted_tickers.json"

def reformat_tickers():
    try:
        # Read the stock_data_export.json file
        with open(stock_data_export_path, "r") as stock_data_file:
            stock_data = json.load(stock_data_file)

        # Extract the tickers into a list
        tickers = [stock["Ticker"] for stock in stock_data if "Ticker" in stock]

        # Create the single-line JSON structure
        formatted_tickers = {"tickers": tickers}

        # Write the output to formatted_tickers.json in a single line
        with open(formatted_tickers_path, "w") as formatted_tickers_file:
            json.dump(formatted_tickers, formatted_tickers_file, separators=(",", ":"), ensure_ascii=False)

        print(f"Formatted tickers saved to {formatted_tickers_path}")
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON - {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    reformat_tickers()
