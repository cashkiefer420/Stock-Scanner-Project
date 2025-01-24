import scrapy
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

# 🔹 Scrapy Spider for Yahoo Finance Stock Market News
class YahooFinanceNewsSpider(scrapy.Spider):
    name = "yahoo_finance_news"
    allowed_domains = ["finance.yahoo.com"]
    start_urls = ["https://finance.yahoo.com/topic/stock-market-news/"]

    def parse(self, response):
        """Parse the stock market news page and check for tickers listed under articles."""
        tickers = load_tickers()
        today_date = datetime.today().strftime("%Y-%m-%d")
        found_articles = []

        for article in response.css("li.js-stream-content"):
            headline = article.css("h3 a::text").get()
            link = article.css("h3 a::attr(href)").get()
            first_paragraph = article.css("p::text").get()  # Extracts the first paragraph
            article_date = article.css("time::attr(datetime)").get()

            # Convert article date to YYYY-MM-DD format
            if article_date:
                article_date = article_date.split("T")[0]  # Extract just the date part

            # Extract tickers explicitly listed under the article (blue tags)
            tagged_tickers = article.css("a span::text").getall()
            matched_tickers = [ticker for ticker in tickers if ticker in tagged_tickers]

            # ✅ Only include articles that match today's date
            if matched_tickers and article_date == today_date:
                found_articles.append({
                    "tickers": matched_tickers,  # Store matched tickers
                    "headline": headline,
                    "link": response.urljoin(link),
                    "first_paragraph": first_paragraph,  # Add first paragraph
                    "date": article_date  # Store article's actual date
                })

        # 🔹 If no articles match the tickers **AND** today's date, log "Not Found"
        if not found_articles:
            self.logger.info("Not Found")
            yield {"status": "Not Found"}
        else:
            for article in found_articles:
                yield article