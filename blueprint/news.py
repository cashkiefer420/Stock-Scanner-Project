import json
import os
import yfinance as yf
from datetime import datetime

# Base directory and file paths
base_dir = r"/home/ec2-user/Stock-Scanner-Project/"
EXPORT_FILE_PATH = os.path.join(base_dir, "json", "news.json")
LEVEL_1_EXPORT_PATH = os.path.join(base_dir, "json", "level_1_news.json")
LEVEL_5_EXPORT_PATH = os.path.join(base_dir, "json", "level_5_news.json")

# Get today's date in YYYY-MM-DD format
TODAY_DATE = datetime.today().strftime("%Y-%m-%d")

def ensure_serializable(data):
    """Convert non-serializable values to serializable format."""
    if isinstance(data, (list, tuple)):
        return [ensure_serializable(item) for item in data]
    elif isinstance(data, dict):
        return {key: ensure_serializable(value) for key, value in data.items()}
    elif isinstance(data, (int, float, str)) or data is None:
        return data
    else:
        return str(data)  # Convert non-serializable objects to strings

def fetch_ticker_price(ticker):
    """Fetch the current price of a stock using yfinance."""
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")["Close"].iloc[-1]
        return round(price, 2)
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return None

def process_and_filter_articles():
    """Process only today's articles, add stock prices, and filter into level 1 and 5 JSON files."""
    
    articles = []

    # Load the main JSON file if it exists
    if os.path.exists(EXPORT_FILE_PATH):
        try:
            with open(EXPORT_FILE_PATH, "r") as file:
                articles = json.load(file)
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {EXPORT_FILE_PATH}. Proceeding with an empty list.")

    filtered_articles = []
    level_1_articles = []
    level_5_articles = []

    for article in articles:
        article_date = article.get("date", "").strip()  # Ensure date is a string and strip whitespace
        
        # Skip articles without a valid date or not from today
        if not article_date or article_date != TODAY_DATE:
            continue  

        grade = article.get("grade")
        ticker = article.get("ticker", "").strip()
        score = article.get("score", None)

        # Fetch stock price if a valid ticker is provided
        article["price"] = fetch_ticker_price(ticker) if ticker else None
        article["score"] = score  # Ensure score is included

        filtered_articles.append(article)

        # Sort articles into level 1 or 5
        if grade == 1:
            level_1_articles.append(article)
        elif grade == 5:
            level_5_articles.append(article)

    # Ensure all data is serializable before writing to JSON files
    serializable_articles = ensure_serializable(filtered_articles)
    serializable_level_1 = ensure_serializable(level_1_articles)
    serializable_level_5 = ensure_serializable(level_5_articles)

    # Write to respective JSON files
    with open(LEVEL_1_EXPORT_PATH, "w") as file:
        json.dump(serializable_level_1, file, indent=4)
    print(f"Level 1 articles saved to {LEVEL_1_EXPORT_PATH}")

    with open(LEVEL_5_EXPORT_PATH, "w") as file:
        json.dump(serializable_level_5, file, indent=4)
    print(f"Level 5 articles saved to {LEVEL_5_EXPORT_PATH}")

    with open(EXPORT_FILE_PATH, "w") as file:
        json.dump(serializable_articles, file, indent=4)
    print(f"Updated articles (only today's) saved to {EXPORT_FILE_PATH}")

if __name__ == "__main__":
    process_and_filter_articles()