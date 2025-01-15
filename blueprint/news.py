import json
import os
import yfinance as yf

# Base directory and file paths
base_dir = r"/home/ec2-user/Stock-Scanner-Project/"
EXPORT_FILE_PATH = os.path.join(base_dir, "json", "news.json")
LEVEL_1_EXPORT_PATH = os.path.join(base_dir, "json", "level_1_news.json")
LEVEL_5_EXPORT_PATH = os.path.join(base_dir, "json", "level_5_news.json")

def fetch_ticker_price(ticker):
    """
    Fetch the current price of a stock using yfinance.
    """
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")["Close"].iloc[-1]
        return round(price, 2)
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return None

def process_and_filter_articles():
    """
    Add current price and score to the main export, 
    and filter articles into separate JSON files for level 1 and 5.
    """
    if not os.path.exists(EXPORT_FILE_PATH):
        print(f"Export file not found at {EXPORT_FILE_PATH}")
        return

    with open(EXPORT_FILE_PATH, "r") as file:
        articles = json.load(file)

    level_1_articles = []
    level_5_articles = []

    for article in articles:
        grade = article.get("grade")
        title = article.get("title", "")
        ticker = article.get("ticker", "")  # Assuming the ticker is part of the article data
        score = article.get("score", None)  # Assuming the score is part of the article data

        # Fetch and add price if ticker exists
        if ticker:
            price = fetch_ticker_price(ticker)
            article["price"] = price
        else:
            article["price"] = None

        # Include the score in the output
        article["score"] = score

        # Sort articles into level 1 or 5
        if grade == 1:
            level_1_articles.append(article)
        elif grade == 5:
            level_5_articles.append(article)

    # Save level 1 and 5 articles to their respective files
    with open(LEVEL_1_EXPORT_PATH, "w") as file:
        json.dump(level_1_articles, file, indent=4)
    print(f"Level 1 articles saved to {LEVEL_1_EXPORT_PATH}")

    with open(LEVEL_5_EXPORT_PATH, "w") as file:
        json.dump(level_5_articles, file, indent=4)
    print(f"Level 5 articles saved to {LEVEL_5_EXPORT_PATH}")

    # Overwrite the main export with updated articles (including prices and scores)
    with open(EXPORT_FILE_PATH, "w") as file:
        json.dump(articles, file, indent=4)
    print(f"Updated articles (with prices and scores) saved to {EXPORT_FILE_PATH}")

if __name__ == "__main__":
    process_and_filter_articles()
