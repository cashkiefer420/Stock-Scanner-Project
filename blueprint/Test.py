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
        grade, score = 'A', int((compound_score + 1) * 50)  
    elif 0.3 <= compound_score < 0.6:
        grade, score = 'B', int((compound_score + 1) * 45)
    elif 0.1 <= compound_score < 0.3:
        grade, score = 'C', int((compound_score + 1) * 40)
    elif -0.1 <= compound_score < 0.1:
        grade, score = 'D', int((compound_score + 1) * 35)
    else:
        grade, score = 'F', int((compound_score + 1) * 30)

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
        articles = soup.select("h3 a")  # Select article links
        print(f"🔍 {len(articles)} articles fetched from {url}")

        for link in articles:
            if link and 'href' in link.attrs:  # Safely check for href
                article_url = f"https://finance.yahoo.com{link['href']}"
                all_articles.append(article_url)

    return all_articles

# 🔹 Extract, filter, and grade articles
def extract_articles():
    """Extracts stock news articles and assigns grades & scores."""
    all_articles = []  # Stores all extracted articles
    articles = fetch_news()

    headers = {"User-Agent": "Mozilla/5.0"}

    for article_url in articles:
        response = requests.get(article_url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Failed to fetch article: {article_url}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract headline (safe access)
        headline_tag = soup.select_one("h1")
        headline = headline_tag.text.strip() if headline_tag else "No headline available"

        # Extract date (safe access)
        time_tag = soup.select_one('time')
        article_date = time_tag["datetime"].split("T")[0] if time_tag and time_tag.has_attr("datetime") else "Unknown date"

        # Extract first paragraph (safe access)
        paragraph_tag = soup.select_one("p")
        first_paragraph = paragraph_tag.text.strip() if paragraph_tag else "No content available"

        # 🔹 Assign grade & score immediately
        grade, score = assign_grade(first_paragraph)

        all_articles.append({
            "headline": headline,
            "link": article_url,
            "first_paragraph": first_paragraph,
            "date": article_date,
            "grade": grade, 
            "score": score  
        })
            
    return all_articles

# 🔹 Define export file path
base_dir = r"/home/ec2-user/Stock-Scanner-Project/"
EXPORT_FILE_PATH = os.path.join(base_dir, "json", "news.json")

# 🔹 Run the scraper and save results
if __name__ == "__main__":
    extracted_articles = extract_articles()

    if extracted_articles:
        with open(EXPORT_FILE_PATH, "w") as json_file:
            json.dump(extracted_articles, json_file, indent=4)
        print(f"✅ Saved {len(extracted_articles)} articles to {EXPORT_FILE_PATH}")
    else:
        print("❌ No articles found.")