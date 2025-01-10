import json
from flask import Flask, request, jsonify, render_template  # Import render_template
import os

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

    # Handle case when stock is not found
    if not stock:
        return {"error": "Stock or company not found"}

    # Extract the ticker and company name
    ticker = stock["Ticker"]
    company_name = stock.get("Company Name", "N/A")

    # Include both ticker and company name in the response and add all other fields
    response = {
        "Ticker": ticker,
        "Company Name": company_name,
        "Current Price": stock.get("Current Price", "N/A"),
        "Price Change Today": stock.get("Price Change Today", "N/A"),
        "Price Change Week": stock.get("Price Change Week", "N/A"),
        "Price Change Month": stock.get("Price Change Month", "N/A"),
        "Price Change Year": stock.get("Price Change Year", "N/A"),
        "Previous Close": stock.get("Previous Close", "N/A"),
        "Previous Open": stock.get("Previous Open", "N/A"),
        "Bid (Buy price Currently)": stock.get("Bid (Buy price Currently)", "N/A"),
        "Ask (Sell Price Currently)": stock.get("Ask (Sell Price Currently)", "N/A"),
        "Days Range": stock.get("Days Range", "N/A"),
        "Shares Available": stock.get("Shares Available", "N/A"),
        "Volume Today": stock.get("Volume Today", "N/A"),
        "Avg Volume (3 mon)": stock.get("Avg Volume (3 mon)", "N/A"),
        "DVAV (Day Volume Over Average Volume)": stock.get("DVAV (Day Volume Over Average Volume)", "N/A"),
        "Market Cap": stock.get("Market Cap", "N/A"),
        "Market Cap Change (3 Mon)": stock.get("Market Cap Change (3 Mon)", "N/A"),
        "Beta": stock.get("Beta", "N/A"),
        "P/E Ratio": stock.get("P/E Ratio", "N/A"),
        "P/E Change (3 Mon)": stock.get("P/E Change (3 Mon)", "N/A"),
        "Earnings Per Share": stock.get("Earnings Per Share", "N/A"),
        "Earnings Date": stock.get("Earnings Date", "N/A"),
        "Dividend Yield": stock.get("Dividend Yield", "N/A"),
        "Ex-Dividend Date": stock.get("Ex-Dividend Date", "N/A"),
        "One Year Target": stock.get("One Year Target", "N/A"),
    }

    return response

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
