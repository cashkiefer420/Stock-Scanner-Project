import json
import os
import yfinance as yf
from datetime import datetime

# 🔹 File paths
BASE_DIR = r"/home/ec2-user/Stock-Scanner-Project/"
JSON_DIR = os.path.join(BASE_DIR, "json")
TICKER_FILE_PATH = os.path.join(JSON_DIR, "processed_tickers.json")
EXPORT_FILE_PATH = os.path.join(JSON_DIR, "news.json")
LEVEL_1_EXPORT_PATH = os.path.join(JSON_DIR, "level_1_news.json")
LEVEL_5_EXPORT_PATH = os.path.join(JSON_DIR, "level_5_news.json")

# 🔹 Ensure the json directory exists
os.makedirs(JSON_DIR, exist_ok=True)

# 🔹 Get today's date in YYYY-MM-DD format
TODAY_DATE = datetime.today().strftime("%Y-%m-%d")

# 🔹 Keywords for sentiment grading
keywords = {
    1: ["bankruptcy", "fraud", "lawsuit", "default", "collapse", "crash", "scandal", "layoff", "downsizing",
        "crisis", "recession", "plummet", "failure", "penalty", "investigation", "misconduct", "SEC probe",
        "restructuring", "foreclosure", "recall", "delisting", "governance issue", "audit concern", "legal action"],

    2: ["headwinds", "margin pressure", "earnings miss", "revenue decline", "cost-cutting", "restructuring",
        "soft demand", "uncertain outlook", "challenging environment", "adjusted guidance", "regulatory scrutiny",
        "shortfall", "market volatility", "lower-than-expected", "slower growth", "deleveraging", "impairment charge",
        "litigation risk", "negative forecast", "supply chain issues", "cybersecurity breach"],

    3: ["positioned for growth", "long-term strategy", "strategic realignment", "ongoing evaluation",
        "enhancing shareholder value", "business as usual", "steady performance", "prudent approach",
        "balanced portfolio", "disciplined execution", "corporate governance", "operational efficiency",
        "risk management", "neutral impact", "macro environment", "stable conditions", "cautious optimism",
        "maintaining our commitment", "status quo", "aligned with industry trends"],

    4: ["record revenue", "strong quarter", "exceeding expectations", "impressive results", "robust earnings",
        "growth trajectory", "market leader", "scaling operations", "expansion strategy", "customer growth",
        "acquisition success", "milestone achievement", "sustained performance", "bullish outlook",
        "industry-leading", "positive momentum", "product launch", "strategic investment", "partnership growth",
        "new market entry"],

    5: ["breakthrough innovation", "disruptive technology", "record-breaking profits", "all-time high",
        "groundbreaking development", "unprecedented demand", "exceptional performance", "dominant market position",
        "trailblazing", "transformational growth", "skyrocketing stock", "outpacing competitors",
        "highest earnings ever", "industry-shifting", "game-changer", "phenomenal success", "category-defining",
        "best quarter ever", "leadership in innovation"]
}

# 🔹 Load tickers from JSON file
def load_tickers():
    """Load stock tickers from the processed_tickers.json file."""
    if os.path.exists(TICKER_FILE_PATH):
        with open(TICKER_FILE_PATH, "r") as file:
            data = json.load(file)
            return data.get("tickers", [])
    return []

# 🔹 Fetch news from yfinance
def fetch_yfinance_news(ticker):
    """Fetch latest news for a ticker from Yahoo Finance using yfinance API."""
    stock = yf.Ticker(ticker)
    news_articles = stock.news  # Fetch the latest news articles

    # Create a list to store article information
    articles = []
    for article in news_articles:
        # Extract the article information and assign a grade based on the description
        grade = assign_grade(article.get("summary", ""))  # Assign sentiment grade
        articles.append({
            "headline": article.get("title", ""),
            "link": article.get("link", ""),
            "ticker": ticker,
            "date": TODAY_DATE,  # Use today's date
            "content": article.get("summary", ""),  # Using summary as content
            "grade": grade  # Include the sentiment grade
        })
    
    return articles

# 🔹 Assign grades based on description content
def assign_grade(description):
    """Assigns a grade to an article based on its description content"""
    if not description:
        return 3  # Neutral if no description

    desc_lower = description.lower()
    grade_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}  # Keep count of matched words for each grade

    # Count the applicable words for each grade
    for grade, words in keywords.items():
        grade_count[grade] = sum(word in desc_lower for word in words)

    # Determine if one grade has the most applicable words
    max_grade = max(grade_count, key=grade_count.get)  # Grade with the most applicable words

    # If grade 1 or 5 has the most words, discount all grades
    if max_grade in [1, 5]:
        return 3  # Neutral grade for all words discounted

    # Return the grade with the highest count of applicable words
    return max_grade

# 🔹 Fetch news for all tickers
def fetch_news():
    """Fetch latest news for given stock tickers from Yahoo Finance using yfinance."""
    tickers = load_tickers()
    all_articles = []

    if not tickers:
        print("No tickers found in the file.")
        return []

    for ticker in tickers:
        print(f"Fetching news for {ticker}...")
        try:
            articles = fetch_yfinance_news(ticker)
            all_articles.extend(articles)
        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")

    return all_articles

# 🔹 Run script
if __name__ == "__main__":
    articles = fetch_news()

    # Export the fetched news with scores (grades) as needed
    with open(EXPORT_FILE_PATH, "w") as file:
        json.dump(articles, file, indent=4)