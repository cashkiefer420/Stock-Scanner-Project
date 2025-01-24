import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import scrapy

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

# 🔹 Function to fetch and parse Yahoo Finance news using BeautifulSoup
def fetch_news():
    """Fetches Yahoo Finance stock market news and extracts relevant articles."""
    url = "https://finance.yahoo.com/topic/stock-market-news/"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    
    if response.status_code != 200:
        print(f"Failed to fetch Yahoo Finance news. Status Code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.select("div:has(>h3>a)")
    
    return articles

# 🔹 Scrapy Spider for Yahoo Finance Stock Market News
class YahooFinanceNewsSpider(scrapy.Spider):
    name = "yfinance_news"
    allowed_domains = ["finance.yahoo.com"]
    start_urls = ["https://finance.yahoo.com/topic/stock-market-news/"]

    def parse(self, response):
        """Parse Yahoo Finance stock market news page using BeautifulSoup."""
        tickers = load_tickers()
        today_date = datetime.today().strftime("%Y-%m-%d")
        found_articles = []
        
        # 🔹 Fetch articles using BeautifulSoup
        articles = fetch_news()
        total_articles = len(articles)  # Count total articles searched

        for article in articles:
            headline = article.h3.text if article.h3 else None
            link = article.h3.a["href"] if article.h3 and article.h3.a else None
            first_paragraph = article.p.text if article.p else None
            article_date = article.find("time")["datetime"].split("T")[0] if article.find("time") else None

            # Extract tickers from blue tags under the article
            tagged_tickers = [span.text for span in article.select("a span")]
            matched_tickers = [ticker for ticker in tickers if ticker in tagged_tickers]

            # ✅ Only include articles that match today's date
            if matched_tickers and article_date == today_date:
                found_articles.append({
                    "tickers": matched_tickers,
                    "headline": headline,
                    "link": f"https://finance.yahoo.com{link}" if link else None,
                    "first_paragraph": first_paragraph,
                    "date": article_date
                })

        # 🔹 Log summary of search results
        self.logger.info(f"Total articles searched: {total_articles}")
        self.logger.info(f"Total articles found with matching tickers: {len(found_articles)}")

        # 🔹 If no articles match the tickers **AND** today's date, log "Not Found"
        if not found_articles:
            self.logger.info("Not Found")
            yield {"status": "Not Found"}
        else:
            for article in found_articles:
                yield article