import json
import os
import yfinance as yf
from datetime import datetime

# Base directory and file paths
BASE_DIR = r"/home/ec2-user/Stock-Scanner-Project/"
JSON_DIR = os.path.join(BASE_DIR, "json")
EXPORT_FILE_PATH = os.path.join(JSON_DIR, "news.json")
LEVEL_1_EXPORT_PATH = os.path.join(JSON_DIR, "level_1_news.json")
LEVEL_5_EXPORT_PATH = os.path.join(JSON_DIR, "level_5_news.json")
LOG_FILE_PATH = os.path.join(BASE_DIR, "news_processing.log")

# Ensure the json directory exists
os.makedirs(JSON_DIR, exist_ok=True)

# Get today's date in YYYY-MM-DD format
TODAY_DATE = datetime.today().strftime("%Y-%m-%d")

def log_message(message):
    """Logs messages to a log file with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    
    with open(LOG_FILE_PATH, "a") as log_file:
        log_file.write(log_entry)
    
    print(log_entry.strip())  # Also print to console

def ensure_json_file(filepath, default_data):
    """Ensure the given JSON file exists and is initialized with default data if missing or corrupted."""
    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            json.dump(default_data, f, indent=4)
        log_message(f"Created missing file: {filepath}")
    else:
        try:
            with open(filepath, "r") as f:
                json.load(f)  # Try loading JSON to check if it's valid
        except (json.JSONDecodeError, IOError):
            log_message(f"Error reading {filepath}. Resetting with default data.")
            with open(filepath, "w") as f:
                json.dump(default_data, f, indent=4)

# Ensure all required JSON files exist
ensure_json_file(EXPORT_FILE_PATH, [])
ensure_json_file(LEVEL_1_EXPORT_PATH, [])
ensure_json_file(LEVEL_5_EXPORT_PATH, [])

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
        history = stock.history(period="1d")
        if history.empty:
            raise ValueError("No price data available")
        return round(history["Close"].iloc[-1], 2)
    except Exception as e:
        log_message(f"Error fetching price for {ticker}: {e}")
        return None

def process_and_filter_articles():
    """Process only today's articles, add stock prices, and filter into level 1 and 5 JSON files."""
    
    # Load existing articles
    try:
        with open(EXPORT_FILE_PATH, "r") as file:
            articles = json.load(file)
    except json.JSONDecodeError:
        log_message(f"Error decoding JSON from {EXPORT_FILE_PATH}. Resetting with empty list.")
        articles = []

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

    if filtered_articles:
        log_message(f"Found {len(filtered_articles)} new articles for {TODAY_DATE}.")
    
    # Ensure all data is serializable before writing to JSON files
    serializable_articles = ensure_serializable(filtered_articles)
    serializable_level_1 = ensure_serializable(level_1_articles)
    serializable_level_5 = ensure_serializable(level_5_articles)

    # Write to respective JSON files
    with open(LEVEL_1_EXPORT_PATH, "w") as file:
        json.dump(serializable_level_1, file, indent=4)
    log_message(f"Level 1 articles saved: {len(level_1_articles)}")

    with open(LEVEL_5_EXPORT_PATH, "w") as file:
        json.dump(serializable_level_5, file, indent=4)
    log_message(f"Level 5 articles saved: {len(level_5_articles)}")

    with open(EXPORT_FILE_PATH, "w") as file:
        json.dump(serializable_articles, file, indent=4)
    log_message(f"Updated total articles (only today's) saved: {len(serializable_articles)}")

if __name__ == "__main__":
    process_and_filter_articles()