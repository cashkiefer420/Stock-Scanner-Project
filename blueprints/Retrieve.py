import os
import json

# Navigate to the base directory of the "Stock-Scanner-Project"
current_dir = os.path.dirname(os.path.abspath(__file__))

while os.path.basename(current_dir) != "Stock-Scanner-Project":
    current_dir = os.path.dirname(current_dir)
    if current_dir == "/":
        raise FileNotFoundError("Base directory 'Stock-Scanner-Project' not found!")

base_dir = current_dir

# Define the absolute path to the JSON file
TICKER_FILE_PATH = os.path.join(base_dir, "json", "Sample_ticker.json")

# Function to read the content of the Sample_ticker.json file
def load_ticker_data():
    try:
        with open(TICKER_FILE_PATH, 'r') as f:
            ticker_data = json.load(f)
            return ticker_data
    except FileNotFoundError:
        print(f"File not found: {TICKER_FILE_PATH}")
        return None
    except json.JSONDecodeError:
        print("Error decoding JSON from the file.")
        return None

# Function to print tickers from the JSON file
def print_tickers(ticker_data):
    if ticker_data and "tickers" in ticker_data:
        print("List of tickers:")
        for ticker_symbol in ticker_data["tickers"]:
            print(ticker_symbol)
    else:
        print("No tickers found in the data.")

# Main execution
if __name__ == "__main__":
    ticker_data = load_ticker_data()  # Load the data from the JSON file
    print_tickers(ticker_data)  # Print the tickers