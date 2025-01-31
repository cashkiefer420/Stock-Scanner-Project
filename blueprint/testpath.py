import os
import json
import requests
import schedule
import time
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime

# Base directory and export file path
base_dir = r"/home/ec2-user/Stock-Scanner-Project/"
EXPORT_FILE_PATH = os.path.join(base_dir, "json", "news.json")

# Yahoo Finance URLs
urls = [
    "https://finance.yahoo.com/topic/stock-market-news/",
    "https://finance.yahoo.com/topic/latest-news/",
    "https://finance.yahoo.com/topic/earnings/",
    "https://finance.yahoo.com/topic/morning-brief/"
]

# Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

def fetch_news():
    all_news = load_existing_data()
    existing_links = {article["link"] for article in all_news}

    for url in urls:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.find_all("li", class_="stream-item story-item")

            for article in articles:
                headline_tag = article.find("h3")
                link_tag = article.find("a", class_="subtle-link")
                paragraph_tag = article.find("p")

                if headline_tag and link_tag:
                    headline = headline_tag.text.strip()
                    link = link_tag["href"]
                    if not link.startswith("http"):
                        link = "https://finance.yahoo.com" + link
                    paragraph = paragraph_tag.text.strip() if paragraph_tag else ""

                    # Avoid duplicates
                    if link in existing_links:
                        continue

                    # Sentiment analysis
                    sentiment_score = analyzer.polarity_scores(headline)["compound"]
                    grade = get_sentiment_grade(sentiment_score)

                    news_item = {
                        "headline": headline,
                        "link": link,
                        "paragraph": paragraph,
                        "sentiment_score": sentiment_score,
                        "grade": grade,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    all_news.append(news_item)

    save_to_json(all_news)


def get_sentiment_grade(score):
    """Assigns an A-F grade based on sentiment score."""
    if score >= 0.6:
        return "A"
    elif score >= 0.3:
        return "B"
    elif score >= 0.05:
        return "C"
    elif score <= -0.05:
        return "D"
    elif score <= -0.3:
        return "E"
    else:
        return "F"


def load_existing_data():
    """Loads existing JSON data or returns an empty list if the file doesn't exist."""
    if os.path.exists(EXPORT_FILE_PATH):
        with open(EXPORT_FILE_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_to_json(data):
    """Saves data to JSON file."""
    os.makedirs(os.path.dirname(EXPORT_FILE_PATH), exist_ok=True)

    with open(EXPORT_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def clear_json():
    """Clears the JSON file at 8 PM daily."""
    if os.path.exists(EXPORT_FILE_PATH):
        with open(EXPORT_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)
        print(f"Cleared news.json at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


# Schedule tasks
schedule.every(3).minutes.do(fetch_news)  # Scans for new news every 3 minutes
schedule.every().day.at("20:00").do(clear_json)  # Clears JSON at 8 PM

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(30)  # Check every 30 seconds