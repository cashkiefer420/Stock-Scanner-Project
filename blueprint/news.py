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

        # Updated selector for news articles
        articles = soup.select("li.stream-item")

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
        headline_tag = article.select_one("h3 a")
        link_tag = article.select_one("h3 a")
        paragraph_tag = article.select_one("p")
        meta_date_tag = article.select_one('meta[itemprop="datePublished"]')

        if not headline_tag or not link_tag:  
            continue  # Skip invalid articles

        headline = headline_tag.text.strip()
        link = f"https://finance.yahoo.com{link_tag['href']}" if 'href' in link_tag.attrs else None
        first_paragraph = paragraph_tag.text.strip() if paragraph_tag else None

        article_date = meta_date_tag["content"].split("T")[0] if meta_date_tag and "content" in meta_date_tag.attrs else datetime.today().strftime("%Y-%m-%d")

        # 🔹 Assign grade & score immediately
        grade, score = assign_grade(first_paragraph)

        all_articles.append({
            "headline": headline,
            "link": link,
            "first_paragraph": first_paragraph,
            "date": publishing_div,  # ✅ Now correctly extracted
            "grade": grade, 
            "score": score  
        })
    
    return all_articles  # ✅ Corrected return statement

# 🔹 Fetch date from article page if not found in meta tag
def fetch_article_date(url):
    """Fetches the article's publication date from its page."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        publishing_div = soup.select_one("div.publishing")
        if publishing_div:
            text = publishing_div.get_text(strip=True)
            parts = text.split("•")  # Separate source name and time info
            if len(parts) > 1:
                raw_date = parts[-1].strip()  # Extract the last part (e.g., "19 hours ago")
                
                # Convert relative time to actual date
                if "hour" in raw_date or "minute" in raw_date:
                    return datetime.today().strftime("%Y-%m-%d")  # Today’s date
                elif "day" in raw_date:
                    days_ago = int(raw_date.split()[0])
                    return (datetime.today() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        

    except Exception as e:
        print(f"⚠️ Error fetching date for {url}: {e}")

    return None  # Return None if date is not found

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
