import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# 🔹 File paths
BASE_DIR = r"/home/ec2-user/Stock-Scanner-Project/"
JSON_DIR = os.path.join(BASE_DIR, "json")
TICKER_FILE_PATH = os.path.join(JSON_DIR, "processed_tickers.json")
EXPORT_FILE_PATH = os.path.join(JSON_DIR, "news.json")

# 🔹 Ensure the json directory exists
os.makedirs(JSON_DIR, exist_ok=True)

# 🔹 Load tickers from JSON file
def load_tickers():
    """Load stock tickers from the processed_tickers.json file."""
    if os.path.exists(TICKER_FILE_PATH):
        with open(TICKER_FILE_PATH, "r") as file:
            data = json.load(file)
            return set(data.get("tickers", []))  # Convert to set for faster lookup
    return set()

# 🔹 Function to fetch all Yahoo Finance stock market news
def fetch_news():
    """Fetches Yahoo Finance stock market news and extracts all articles."""
    url = "https://finance.yahoo.com/topic/stock-market-news/" : "https://finance.yahoo.com/topic/latest-news/" : "https://finance.yahoo.com/topic/earnings/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to fetch Yahoo Finance news. Status Code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.select("li.stream-item")  # Select all news articles
    print(f"🔍 Total articles fetched: {len(articles)}")  # Log total articles found

    return articles

# 🔹 Function to extract and filter articles based on tickers
def extract_articles():
    """Extracts stock news articles and filters based on tickers."""
    tickers = load_tickers()
    today_date = datetime.today().strftime("%Y-%m-%d")
    all_articles = []  # Stores all articles before filtering

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

        all_articles.append({
            "tickers": tagged_tickers,
            "headline": headline,
            "link": link,
            "first_paragraph": first_paragraph,
            "date": article_date
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
