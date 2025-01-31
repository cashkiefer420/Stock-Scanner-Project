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

    # Adjusted grading scale for better differentiation
    if compound_score >= 0.6:
        grade, score = 'A', int(compound_score * 100)
    elif 0.3 <= compound_score < 0.6:
        grade, score = 'B', int(compound_score * 90)
    elif 0.1 <= compound_score < 0.3:
        grade, score = 'C', int(compound_score * 80)
    elif -0.1 <= compound_score < 0.1:
        grade, score = 'D', int(compound_score * 70)
    else:
        grade, score = 'F', int(compound_score * 60)

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

        # 🔹 Improved selector to target article links
        articles = soup.select("div.js-stream-content a.Ov(h)")

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
        try:
            # Ensure elements exist before accessing them
            headline_tag = article
            if not headline_tag:  
                continue  # Skip invalid articles

            headline = headline_tag.text.strip()
            link = f"https://finance.yahoo.com{headline_tag['href']}" if 'href' in headline_tag.attrs else None

            # 🔹 Extract first paragraph from the article page
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
        except Exception as e:
            print(f"⚠️ Error processing an article: {e}")
    
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
        
        # 🔹 Try multiple meta tags for better accuracy
        meta_date = soup.select_one('meta[property="article:published_time"]') or soup.select_one('meta[name="date"]')

        if meta_date and "content" in meta_date.attrs:
            return meta_date["content"].split("T")[0]

    except Exception as e:
        print(f"⚠️ Error fetching date for {url}: {e}")

    return None  # Return None if date is not found

# 🔹 Fetch summary from article page
def fetch_article_summary(url):
    """Fetches the first paragraph of the article for sentiment analysis."""
    if not url:
        return None

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # 🔹 Look for main article paragraph
        paragraphs = soup.select("p")
        for para in paragraphs:
            text = para.get_text().strip()
            if len(text) > 50:  # Avoid short metadata text
                return text

    except Exception as e:
        print(f"⚠️ Error fetching summary for {url}: {e}")

    return None  # Return None if no valid summary is found

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
