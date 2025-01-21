import json
import os
import requests
from datetime import datetime

# 🔹 API Key (Replace with your actual API Key)
NEWS_API_KEY = "c246a255265745ec9c42318fdc6195cd"

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

# 🔹 List of press release sources (Benzinga Removed)
press_release_sources = [
    "prnewswire.com", "businesswire.com", "globenewswire.com", "newswire.com",
    "marketwatch.com/press-release"
]

# 🔹 Source credibility scores
news_source_scores = {
    "reuters.com": 5,
    "wsj.com": 5,
    "nytimes.com": 5,
    "bloomberg.com": 5,
    "ft.com": 5,
    "cnbc.com": 4,
    "forbes.com": 4,
    "marketwatch.com": 4,
    "seekingalpha.com": 3,
    "investopedia.com": 3,
    "thestreet.com": 3
}

# 🔹 Load tickers from JSON file
def load_tickers():
    """Load stock tickers from the processed_tickers.json file."""
    if os.path.exists(TICKER_FILE_PATH):
        with open(TICKER_FILE_PATH, "r") as file:
            data = json.load(file)
            return data.get("tickers", [])
    return []

# 🔹 Fetch news from NewsAPI
def fetch_news():
    """Fetch latest news for given stock tickers from NewsAPI.org, filtering for US & English."""
    tickers = load_tickers()
    all_articles = []

    if not tickers:
        print("No tickers found in the file.")
        return []

    for ticker in tickers:
        print(f"Fetching news for {ticker}...")
        url = f"https://newsapi.org/v2/everything?q={ticker}&language=en&apiKey={NEWS_API_KEY}"

        try:
            response = requests.get(url)
            data = response.json()

            if "articles" in data:
                for article in data["articles"]:
                    if is_press_release(article) or has_high_reputation(article):
                        all_articles.append({
                            "ticker": ticker,
                            "date": article["publishedAt"][:10],  # Extract YYYY-MM-DD
                            "headline": article["title"],
                            "link": article["url"],
                            "content": article.get("description", ""),
                            "grade": assign_grade(article.get("description", "")),  # Rate description
                            "source": article["source"]["name"],
                            "credibility": get_source_score(article)
                        })
        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")

    return all_articles

# 🔹 Check if an article is a press release
def is_press_release(article):
    """Determine if an article is likely a press release based on source and URL."""
    url = article.get("url", "").lower()
    source = article.get("source", {}).get("name", "").lower()

    if any(domain in url for domain in press_release_sources):
        return True
    if "press-release" in url:
        return True
    if "newswire" in url or "prnewswire" in source or "businesswire" in source:
        return True

    return False

# 🔹 Check if a source has a high reputation
def has_high_reputation(article):
    """Checks if the news source is reputable."""
    url = article.get("url", "").lower()
    return any(domain in url for domain in news_source_scores.keys())

# 🔹 Get credibility score for a news source
def get_source_score(article):
    """Assigns a credibility score based on the news source."""
    url = article.get("url", "").lower()
    for domain, score in news_source_scores.items():
        if domain in url:
            return score
    return 1  # Default low score

# 🔹 Assign grades based on description content
def assign_grade(description):
    """Assigns a grade to an article based on its description content"""
    if not description:
        return 3  # Neutral if no description

    desc_lower = description.lower()

    for grade, words in keywords.items():
        if any(word in desc_lower for word in words):
            return grade

    return 3  # Default to neutral

# 🔹 Run script
if __name__ == "__main__":
    process_news()