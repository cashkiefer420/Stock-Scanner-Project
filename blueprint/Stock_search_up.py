import json
import os
from flask import Flask, request, jsonify, render_template
import yfinance as yf  # Import Yahoo Finance for additional data

app = Flask(__name__, template_folder='templates')

base_dir = r"C:\Users\Carter\Downloads\Stock-Scanner-Project-main\Stock-Scanner-Project-main"
filepath = os.path.join(base_dir, "json", "processed_tickers.json")

# Ensure required directories and files exist
os.makedirs(os.path.dirname(filepath), exist_ok=True)
if not os.path.exists(filepath):
    print("NOT FOUND")

# Load stock data from JSON file
def load_stocks(filepath):
    with open(filepath, "r") as file:
        return json.load(file)

# Function to fetch stock metrics by ticker or company name
def get_stock_metrics(search_query, filepath):
    # Load data from JSON file
    stocks = load_stocks(filepath)

    # Search for the stock by Ticker or Company Name
    stock = next(
        (
            s for s in stocks
            if s["Ticker"].lower() == search_query.lower() or s.get("Company Name", "").lower() == search_query.lower()
        ),
        None,
    )

    if not stock:
        return {"error": "Stock or company not found"}

    # Dynamically extract all available keys
    response = {key: stock.get(key, "N/A") for key in stock}

    # Fetch additional details from Yahoo Finance
    ticker = stock["Ticker"]
    yf_data = fetch_additional_data(ticker)
    response.update(yf_data)

    return response

# Fetch extra data from Yahoo Finance
def fetch_additional_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        stock_info = stock.info

        return {
            "52 Week High": stock_info.get("fiftyTwoWeekHigh", "N/A"),
            "52 Week Low": stock_info.get("fiftyTwoWeekLow", "N/A"),
            "Forward P/E": stock_info.get("forwardPE", "N/A"),
            "Trailing P/E": stock_info.get("trailingPE", "N/A"),
            "Profit Margin": stock_info.get("profitMargins", "N/A"),
            "Revenue": stock_info.get("totalRevenue", "N/A"),
            "Gross Profit": stock_info.get("grossProfits", "N/A"),
            "Operating Cash Flow": stock_info.get("operatingCashflow", "N/A"),
            "Free Cash Flow": stock_info.get("freeCashflow", "N/A"),
            "52 Week Change": stock_info.get("52WeekChange", "N/A"),
        }
    except Exception as e:
        print(f"Error fetching Yahoo Finance data: {e}")
        return {}

@app.route('/Fetch_data_ticker', methods=['GET'])
def get_stock():
    search_query = request.args.get('query', '').strip()
    
    if not search_query:
        return jsonify({"error": "No query provided"}), 400
    
    stock_data = get_stock_metrics(search_query, filepath)
    
    return jsonify(stock_data)

@app.route('/')
def home():
    return render_template('Look.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204  # No content response for favicon

if __name__ == "__main__":
    app.run(debug=True)