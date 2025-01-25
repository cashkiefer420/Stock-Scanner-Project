import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time

# 🔹 File paths
BASE_DIR = r"/home/ec2-user/Stock-Scanner-Project/"
JSON_DIR = os.path.join(BASE_DIR, "json")
TICKER_FILE_PATH = os.path.join(JSON_DIR, "processed_tickers.json")
EXPORT_FILE_PATH = os.path.join(JSON_DIR, "news.json")

# 🔹 Ensure the json directory exists
os.makedirs(JSON_DIR, exist_ok=True)

# 🔹 Keywords for sentiment grading
keywords = {
    1: ["sell", "underperform", "bearish", "collapse", "bankruptcy", "fraud", "lawsuit", "default", "crash", "failure",
        "penalty", "investigation", "misconduct", "SEC probe", "restructuring", "foreclosure", "delisting", "audit concern",
        "legal action", "crisis", "recession", "plummet", "scandal", "layoff", "downsizing", "market volatility", "negative forecast"],

    2: ["headwinds", "margin pressure", "earnings miss", "revenue decline", "cost-cutting", "restructuring", "soft demand",
        "uncertain outlook", "challenging environment", "adjusted guidance", "regulatory scrutiny", "shortfall", "slower growth",
        "deleveraging", "impairment charge", "litigation risk", "supply chain issues", "cybersecurity breach", "lower-than-expected",
        "negative impact", "difficult conditions"],

    3: ["neutral", "hold", "positioned for growth", "market share", "sector performance", "target price", "analyst rating",
        "investor confidence", "strategic investment", "market opportunity", "portfolio", "dividend yield", "long-term strategy",
        "strategic partnership", "steady performance", "stable outlook", "value investment", "balanced portfolio", "evaluating options"],

    4: ["buy", "outperform", "strong buy", "bullish", "positive momentum", "impressive results", "growth trajectory",
        "market leader", "scaling operations", "expansion strategy", "customer growth", "sustained performance", "product launch",
        "strategic investment", "positive earnings surprise", "bullish outlook", "strong growth", "acquisition success", "positive sentiment"],

    5: ["buy now", "breakthrough innovation", "disruptive technology", "record-breaking profits", "all-time high", "exceptional performance",
        "dominant market position", "trailblazing", "transformational growth", "skyrocketing stock", "outpacing competitors", "highest earnings ever",
        "industry-shifting", "game-changer", "phenomenal success", "category-defining", "best quarter ever", "leadership in innovation",
        "unprecedented demand", "buying opportunity", "rapid expansion", "leading the market", "outperforming expectations"]
}

# 🔹 Load tickers from JSON file
def load_tickers():
    """Load stock tickers from the processed_tickers.json file."""
    if os.path.exists(TICKER_FILE_PATH):
        with open(TICKER_FILE_PATH, "r") as file:
            data = json.load(file)
            return set(data.get("tickers", []))  # Convert to set for faster lookup
    return set()

# 🔹 Assign grades and scores based on article content
def assign_grade(content):
    """Assigns a grade and score to an article based on its first paragraph"""
    if not content:
        return 3, 0  # Neutral if no content, score = 0

    desc_lower = content.lower()
    grade_count = {grade: sum(word in desc_lower for word in words) for grade, words in keywords.items()}

    max_grade = max(grade_count, key=grade_count.get)
    score = grade_count[max_grade]

    if max_grade in [1, 5]:  # Adjust for extreme bias
        return 3, score  # Neutral grade, but keep score

    return max_grade, score

# 🔹 Function to fetch all Yahoo Finance stock market news
def fetch_news():
    """Fetches Yahoo Finance stock market news from multiple sources."""
    urls = [
        "https://finance.yahoo.com/topic/stock-market-news/",
        "https://finance.yahoo.com/topic/latest-news/",
        "https://finance.yahoo.com/topic/earnings/",
        "https://finance.yahoo.com/topic/morning-brief/"
    ]
    
    headers = {"User-Agent": "Mozilla/5.0"}
    all_articles = []

    for url in urls:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to fetch Yahoo Finance news from {url}. Status Code: {response.status_code}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.select("li.stream-item")  # Select all news articles
        print(f"🔍 {len(articles)} articles fetched from {url}")

        all_articles.extend(articles)

    return all_articles

# 🔹 Extract, filter, and grade articles
def extract_articles():
    """Extracts stock news articles, filters based on tickers, and assigns grades & scores."""
    tickers = load_tickers()
    today_date = datetime.today().strftime("%Y-%m-%d")
    all_articles = []  # Stores all extracted articles before filtering

    # 🔹 Fetch all articles first
    articles = fetch_news()

    for article in articles:
        headline_tag = article.select_one("h3")  # Extract headline
        link_tag = article.select_one("a.subtle-link")  # Extract link
        paragraph_tag = article.select_one("p")  # Extract first paragraph
        time_tag = article.select_one("time")  # Extract article date

        headline = headline_tag.text.strip() if headline_tag else None
        link = f"https://finance.yahoo.com{link_tag['href']}" if link_tag and 'href' in link_tag.attrs else None
        first_paragraph = paragraph_tag.text.strip() if paragraph_tag else None
        article_date = time_tag["datetime"].split("T")[0] if time_tag and "datetime" in time_tag.attrs else None

        # Extract tickers from blue tags under the article
        tagged_tickers = [span.text for span in article.select("a span")]

        # 🔹 Assign grade & score immediately
        grade, score = assign_grade(first_paragraph)

        all_articles.append({
            "tickers": tagged_tickers,
            "headline": headline,
            "link": link,
            "first_paragraph": first_paragraph,
            "date": article_date,
            "grade": grade,  # ✅ Added grade
            "score": score   # ✅ Added score
        })

    print(f"📌 Total articles before filtering: {len(all_articles)}")

    # 🔹 Now filter out articles that don't match any tickers
    filtered_articles = [article for article in all_articles if any(ticker in tickers for ticker in article["tickers"])]

    print(f"✅ Total articles matching tickers: {len(filtered_articles)}")

    return filtered_articles

# 🔹 Run the scraper and save results
if __name__ == "__main__":
    extracted_articles = extract_articles()

    if extracted_articles:
        with open(EXPORT_FILE_PATH, "w") as json_file:
            json.dump(extracted_articles, json_file, indent=4)
        print(f"✅ Saved {len(extracted_articles)} articles to {EXPORT_FILE_PATH}")
    else:
        print("❌ No matching articles found today.")