import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import yfinance as yf

# 🔹 File paths
BASE_DIR = r"/home/ec2-user/Stock-Scanner-Project/"
JSON_DIR = os.path.join(BASE_DIR, "json")
TICKER_FILE_PATH = os.path.join(JSON_DIR, "processed_tickers.json")
EXPORT_FILE_PATH = os.path.join(JSON_DIR, "news.json")

# 🔹 Ensure the json directory exists
os.makedirs(JSON_DIR, exist_ok=True)

# 🔹 Load tickers and fetch company names
def load_tickers():
    """Load stock tickers and fetch their corresponding company names from Yahoo Finance."""
    if not os.path.exists(TICKER_FILE_PATH):
        return {}

    with open(TICKER_FILE_PATH, "r") as file:
        tickers = json.load(file).get("tickers", [])

    ticker_dict = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            company_name = stock.info.get("shortName", "").lower()  # Get company name in lowercase
            ticker_dict[ticker.lower()] = company_name  # Store both ticker & name in lowercase
        except Exception as e:
            print(f"⚠️ Could not fetch data for {ticker}: {e}")

    return ticker_dict

# 🔹 Function to fetch Yahoo Finance stock market news
def fetch_news():
    """Fetch Yahoo Finance stock market news from multiple sources."""
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
    """Extracts stock news articles, filters based on tickers & company names, and assigns grades & scores."""
    ticker_dict = load_tickers()
    today_date = datetime.today().strftime("%Y-%m-%d")
    all_articles = []

    # 🔹 Fetch all articles first
    articles = fetch_news()

    for article in articles:
        headline_tag = article.select_one("h3")
        link_tag = article.select_one("a.subtle-link")
        paragraph_tag = article.select_one("p")
        time_tag = article.select_one("time")

        headline = headline_tag.text.strip().lower() if headline_tag else None
        link = f"https://finance.yahoo.com{link_tag['href']}" if link_tag and 'href' in link_tag.attrs else None
        first_paragraph = paragraph_tag.text.strip().lower() if paragraph_tag else None
        article_date = time_tag["datetime"].split("T")[0] if time_tag and "datetime" in time_tag.attrs else None

        # Extract tickers from article labels
        tagged_tickers = [span.text.lower() for span in article.select("a span")]

        all_articles.append({
            "tickers": tagged_tickers,
            "headline": headline,
            "link": link,
            "first_paragraph": first_paragraph,
            "date": article_date
        })

    print(f"📌 Total articles before filtering: {len(all_articles)}")

    # 🔹 Filter articles based on ticker or company name appearing in title or summary
    filtered_articles = [
        article for article in all_articles
        if any(
            ticker in (article["headline"] or "") or ticker in (article["first_paragraph"] or "") or
            company in (article["headline"] or "") or company in (article["first_paragraph"] or "")
            for ticker, company in ticker_dict.items()
        )
    ]

    print(f"✅ Total articles matching tickers or company names: {len(filtered_articles)}")

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