import json
from flask import Flask, request, jsonify

app = Flask(__name__)

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
        "Previous Open": stock.get("Previous Open", "N/A"),
        "Previous Close": stock.get("Previous Close", "N/A"),
        "Volume Today": stock.get("Volume Today", "N/A"),
        "Average Volume": stock.get("Average Volume", "N/A"),
        "Market Cap": stock.get("Market Cap", "N/A"),
        "Shares Available": stock.get("Shares Available", "N/A"),
        "3-Month Volume": stock.get("3-Month Volume", "N/A"),
        "Percent Gain Today": stock.get("Percent Gain Today", "N/A"),
        "Percent Gain This Week": stock.get("Percent Gain This Week", "N/A"),
        "Percent Gain This Month": stock.get("Percent Gain This Month", "N/A"),
        "Percent Gain This Year": stock.get("Percent Gain This Year", "N/A"),
        # Add any other specific fields here
        **stock  # Include any remaining fields from the stock data
    }

    return response

@app.route('/Fetch_data_ticker', methods=['GET'])
def get_stock():
    search_query = request.args.get('query', '').strip()
    filepath = "json/stock_data_export.json"
    
    if not search_query:
        return jsonify({"error": "No query provided"}), 400
    
    stock_data = get_stock_metrics(search_query, filepath)
    
    return jsonify(stock_data)

if __name__ == "__main__":
    app.run(debug=True)

