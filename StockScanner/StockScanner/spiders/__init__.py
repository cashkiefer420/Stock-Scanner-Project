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

# 🔹 Scrapy Spider for Yahoo Finance News
class YFinanceSpider(scrapy.Spider):
    name = "yfinance_news"
    allowed_domains = ["finance.yahoo.com"]
    
    def start_requests(self):
        """Start requests by searching Yahoo Finance for each ticker."""
        tickers = load_tickers()
        base_url = "https://finance.yahoo.com/quote/{}/news"
        
        for ticker in tickers:
            yield scrapy.Request(url=base_url.format(ticker), callback=self.parse, meta={'ticker': ticker})

    def parse(self, response):
        """Parse the Yahoo Finance news page for links and headlines."""
        ticker = response.meta['ticker']
        
        for article in response.css('li.js-stream-content'):
            headline = article.css('h3 a::text').get()
            link = article.css('h3 a::attr(href)').get()
            date = datetime.today().strftime("%Y-%m-%d")
            
            if link:
                # Follow the article link to extract more details
                yield response.follow(url=link, callback=self.parse_article, meta={'ticker': ticker, 'headline': headline, 'link': link, 'date': date})

    def parse_article(self, response):
        """Extract the first two paragraphs from the article and grade it."""
        ticker = response.meta['ticker']
        headline = response.meta['headline']
        link = response.meta['link']
        date = response.meta['date']
        
        paragraphs = response.css('p::text').getall()
        content = " ".join(paragraphs[:2])  # First two paragraphs
        
        grade = assign_grade(content)
        
        article_data = {
            "ticker": ticker,
            "headline": headline,
            "link": link,
            "date": date,
            "content": content,
            "grade": grade
        }

        yield article_data  # Scrapy will collect and store this data
