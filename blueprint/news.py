import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Ensure NLTK resources are available
nltk.download('vader_lexicon')

# 🔹 Base directory setup
base_dir = r"/home/ec2-user/Stock-Scanner-Project/"
EXPORT_FILE_PATH = os.path.join(base_dir, "json", "news.json")

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

        # 🔹 Fixed selector: Selecting anchor tags inside article blocks
        articles = soup.select("div.js-stream-content h3 a")

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
        # Ensure elements exist before accessing them
        headline_tag = article  # Article link tag (h3 > a)
        link = f"https://finance.yahoo.com{headline_tag['href']}" if 'href' in headline_tag.attrs else None
        headline = headline_tag.text.strip()

        # 🔹 Fetch article summary (meta description)
        first_paragraph = fetch_article_summary(link) if link else None

        # 🔹 Extract date properly
        article_date = fetch_article_date(link) if link else datetime.today().strftime("%Y-%m-%d")

        # 🔹 Assign grade & score immediately
        grade, score = assign_grade(first_paragraph)

        all_articles.append({
            "headline": headline,
            "link": link,
            "first_paragraph": first_paragraph,
            "date": article_date,  # ✅ Fixed date extraction
            "grade": grade, 
            "score": score  
        })
    
    return all_articles  # ✅ Return extracted articles

# 🔹 Fetch date from article page if not found in meta tag
def fetch_article_date(url):
    """Fetches the article's publication date from its page."""
    if not url:
        return None

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        meta_date = soup.select_one('meta[property="article:published_time"]')

        if meta_date and "content" in meta_date.attrs:
            return meta_date["content"].split("T")[0]

    except Exception as e:
        print(f"⚠️ Error fetching date for {url}: {e}")

    return None  # Return None if date is not found

# 🔹 Fetch article summary from its page
def fetch_article_summary(url):
    """Fetches the article's summary or meta description."""
    if not url:
        return None

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Attempt to find meta description for summary
        meta_description = soup.select_one('meta[name="description"]')

        if meta_description and "content" in meta_description.attrs:
            return meta_description["content"]

    except Exception as e:
        print(f"⚠️ Error fetching summary for {url}: {e}")

    return None  # Return None if summary is not found

# 🔹 Run the scraper and save results
if __name__ == "__main__":
    extracted_articles = extract_articles()

    if extracted_articles:
        # Ensure directory exists before saving the file
        os.makedirs(os.path.dirname(EXPORT_FILE_PATH), exist_ok=True)

        with open(EXPORT_FILE_PATH, "w") as json_file:
            json.dump(extracted_articles, json_file, indent=4)
        
        print(f"✅ Saved {len(extracted_articles)} articles to {EXPORT_FILE_PATH}")
    else:
        print("❌ No valid articles found.")