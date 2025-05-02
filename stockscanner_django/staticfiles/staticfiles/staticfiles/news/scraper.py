import os
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXPORT_FILE_PATH = os.path.join(base_dir, "..", "json", "news.json")
JSON_FOLDER = os.path.join(base_dir, "..", "..", "..", "json")
os.makedirs(JSON_FOLDER, exist_ok=True)

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import os

# Ensure NLTK resources are available
nltk.download('vader_lexicon')

# 🔹 Function to analyze sentiment and assign a grade & score
def assign_grade(text):
    if not text:
        return "N/A", 0  # Return default values if text is None
    
    try:
        text = text.encode('utf-8', 'ignore').decode('utf-8')  # Remove problematic characters
    except Exception as e:
        print(f"❌ Encoding error: {e}")
        return "N/A", 0  # Return default grade and score

    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(text)
    compound_score = sentiment['compound']  # Overall sentiment score

    # Assign grade based on compound score
    if compound_score >= 0.6:
        grade, score = 'A', int((compound_score + 1) * 55)  
    elif 0.3 <= compound_score < 0.6:
        grade, score = 'B', int((compound_score + 1) * 50)
    elif 0.1 <= compound_score < 0.3:
        grade, score = 'C', int((compound_score + 1) * 45)
    elif -0.1 <= compound_score < 0.1:
        grade, score = 'D', int((compound_score + 1) * 40)
    else:
        grade, score = 'F', int((compound_score + 1) * 35)

    return grade, score

# 🔹 Fetch the latest articles from Yahoo Finance
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
    """Extracts stock news articles and assigns grades & scores."""
    all_articles = []  # Stores all extracted articles

    # 🔹 Fetch all articles first
    articles = fetch_news()

    for article in articles:
        headline_tag = article.select_one("h3")  # Extract headline
        link_tag = article.select_one("a.subtle-link")  # Extract link
        paragraph_tag = article.select_one("p")  # Extract first paragraph
        

        headline = headline_tag.text.strip() if headline_tag else None
        link = f"{link_tag['href']}" if link_tag and 'href' in link_tag.attrs else None
        first_paragraph = paragraph_tag.text.strip() if paragraph_tag else None
        

        # 🔹 Assign grade & score immediately
        grade, score = assign_grade(first_paragraph)

        all_articles.append({
            "headline": headline,
            "link": link,
            "first_paragraph": first_paragraph,
            "grade": grade, 
            "score": score  
        })
    
    return all_articles  # ✅ Corrected return statement


if not os.path.exists(EXPORT_FILE_PATH):
    print(f"Warning: {EXPORT_FILE_PATH} not found.")


def main():
    extracted_articles = extract_articles()
    if extracted_articles:
        with open(EXPORT_FILE_PATH, "w", encoding="utf-8") as json_file:
            json.dump(extracted_articles, json_file, indent=4)
        print(f"✅ Saved {len(extracted_articles)} articles to {EXPORT_FILE_PATH}")
    else:
        print("❌ No articles found.")

if __name__ == "__main__":
    main()
