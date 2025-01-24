import scrapy
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
        "slower growth", "negative impact", "difficult conditions"],

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

# 🔹 Assign grades based on article content
def assign_grade(content):
    """Assigns a grade to an article based on its first two paragraphs"""
    if not content:
        return 3  # Neutral if no content

    desc_lower = content.lower()
    grade_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    for grade, words in keywords.items():
        grade_count[grade] = sum(word in desc_lower for word in words)

    max_grade = max(grade_count, key=grade_count.get)

    if max_grade in [1, 5]:
        return 3  # Neutral if extreme bias

    return max_grade

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

# 🔹 Grade articles based on first two paragraphs and update the JSON file
def grade_articles():
    """Grading the articles and appending grades to each."""
    if os.path.exists(EXPORT_FILE_PATH):
        with open(EXPORT_FILE_PATH, "r") as file:
            articles = json.load(file)

        for article in articles:
            # Use the first two paragraphs as the excerpt
            content = article.get('first_paragraph', "")
            grade = assign_grade(content)
            article['grade'] = grade  # Assign the grade to the article

        with open(EXPORT_FILE_PATH, "w") as file:
            json.dump(articles, file, indent=4)
        print("Articles graded and saved.")

# 🔹 Continuous grading loop every 3 minutes
def continuously_grade():
    """Grade articles every 3 minutes."""
    while True:
        print(f"Grading articles at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        grade_articles()
        print("Articles graded and saved.")
        time.sleep(180)  # Wait for 3 minutes (180 seconds)

if __name__ == "__main__":
    continuously_grade()