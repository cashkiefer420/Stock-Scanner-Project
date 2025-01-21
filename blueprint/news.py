import json
import os
import requests
from datetime import datetime

# Base directory and file paths
BASE_DIR = r"/home/ec2-user/Stock-Scanner-Project/"
JSON_DIR = os.path.join(BASE_DIR, "json")
EXPORT_FILE_PATH = os.path.join(JSON_DIR, "news.json")
LEVEL_1_EXPORT_PATH = os.path.join(JSON_DIR, "level_1_news.json")
LEVEL_5_EXPORT_PATH = os.path.join(JSON_DIR, "level_5_news.json")
TICKER_FILE_PATH = os.path.join(JSON_DIR, "processed_tickers.json")  # Ticker file path

# NewsCatcher API Key (replace with your actual API key)
NEWSCATCHER_API_KEY = "your_newscatcher_api_key_here"
NEWSCATCHER_URL = "https://api.newscatcherapi.com/v2/search"

# Ensure the json directory exists
os.makedirs(JSON_DIR, exist_ok=True)

# Get today's date in YYYY-MM-DD format
TODAY_DATE = datetime.today().strftime("%Y-%m-%d")

# Keyword-based filtering logic
keywords = {
    1: ["bankruptcy", "fraud", "lawsuit", "default", "collapse", "crash", "scandal", "layoff", "downturn", "depression",
        "crisis", "recession", "plummet", "failure", "losses", "penalty", "investigation", "misconduct", "closure", "downfall"],
    2: ["loss", "decline", "debt", "risk", "penalty", "diminish", "drop", "cut", "weak", "uncertain",
        "fine", "volatile", "downgrade", "slowdown", "struggle", "pressure", "shortfall", "disruption", "negative", "warning"],
    3: ["neutral", "stable", "moderate", "average", "steady", "unchanged", "flat", "balanced", "constant", "status quo",
        "midpoint", "middle", "unmoved", "normal", "equilibrium", "regular", "unaffected", "unchallenged", "intermediate", "consistent"],
    4: ["growth", "profit", "increase", "success", "expansion", "improvement", "gain", "progress", "advance", "upturn",
        "positive", "strength", "opportunity", "recover", "stable growth", "resilience", "rise", "achievement", "promising", "favorable"],
    5: ["record-breaking", "booming", "outstanding", "surge", "innovative", "exceptional", "unprecedented", "thriving", "remarkable", "breakthrough",
        "leading", "flourishing", "highly successful", "groundbreaking", "top-performing", "skyrocketing", "phenomenal", "milestone", "extraordinary", "peak performance"]
}

# Scoring system for keyword levels
scores = {1: -2, 2: -1, 3: 0, 4: 1, 5: 2}

# Grading brackets based on the score
brackets = {
    1: (-float('inf'), -20),
    2: (-19, -5),
    3: (-5, 5),
    4: (5, 19),
    5: (20, float('inf'))
}

def log_message(message):
    """Logs messages to the console with timestamps."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    print(log_entry)  # Print to console only

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
ensure_json_file(TICKER_FILE_PATH, {"tickers": []})

def load_tickers():
    """Load stock tickers from processed_tickers.json."""
    try:
        with open(TICKER_FILE_PATH, "r") as file:
            data = json.load(file)
            return data.get("tickers", [])
    except json.JSONDecodeError:
        log_message(f"Error decoding JSON from {TICKER_FILE_PATH}. Resetting with empty list.")
        return []

def analyze_sentiment(title):
    """Analyze the sentiment of the headline based on keyword occurrences."""
    score = 0
    for level, words in keywords.items():
        if any(word in title.lower() for word in words):
            score += scores[level]
    return score

def determine_grade(score):
    """Determine the grade based on the score and predefined brackets."""
    for grade, (low, high) in brackets.items():
        if low <= score <= high:
            return grade
    return 3  # Default to neutral if no match

def fetch_stock_news():
    """Fetch news for stocks listed in processed_tickers.json using NewsCatcher API."""
    tickers = load_tickers()
    if not tickers:
        log_message("No tickers found in processed_tickers.json.")
        return []

    news_articles = []
    headers = {
        "x-api-key": NEWSCATCHER_API_KEY
    }

    for ticker in tickers:
        params = {
            "query": ticker,
            "lang": "en",
            "sort_by": "published",
            "page_size": 50  # Fetch up to 50 articles per ticker
        }

        try:
            response = requests.get(NEWSCATCHER_URL, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "ok":
                for article in data.get("articles", []):
                    article_date = article["published_date"].split("T")[0]

                    if article_date == TODAY_DATE:
                        score = analyze_sentiment(article["title"])
                        grade = determine_grade(score)

                        news_articles.append({
                            "date": article_date,
                            "headline": article.get("title", "No Title"),
                            "link": article.get("link", ""),
                            "ticker": ticker,
                            "grade": grade,
                            "score": score
                        })

        except requests.RequestException as e:
            log_message(f"Error fetching news for {ticker}: {e}")

    return news_articles

def process_and_filter_articles():
    """Fetch stock-specific news, process it, and filter into level 1 and 5 JSON files."""
    news_articles = fetch_stock_news()
    
    if not news_articles:
        log_message("No stock news articles found for today.")
        return
    
    log_message(f"Fetched {len(news_articles)} articles.")

    level_1_articles = [a for a in news_articles if a["grade"] == 1]
    level_5_articles = [a for a in news_articles if a["grade"] == 5]

    with open(LEVEL_1_EXPORT_PATH, "w") as file:
        json.dump(level_1_articles, file, indent=4)
    log_message(f"Level 1 articles saved: {len(level_1_articles)}")

    with open(LEVEL_5_EXPORT_PATH, "w") as file:
        json.dump(level_5_articles, file, indent=4)
    log_message(f"Level 5 articles saved: {len(level_5_articles)}")

if __name__ == "__main__":
    process_and_filter_articles()