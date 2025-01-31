import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# 🔹 Ensure NLTK resources are available
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
        articles = soup.select("li.js-stream-content div")

        print(f"🔍 {len(articles)} articles fetched from {url}")

        all_articles.extend(articles)

    return all_articles

# 🔹 Fetch article summary
def fetch_article_summary(url):
    """Fetches the article's meta description as a summary."""
    if not url:
        return None

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        meta_desc = soup.select_one('meta[name="description"]')

        return meta_desc["content"] if meta_desc and "content" in meta_desc.attrs else None

    except Exception as e:
        print(f"⚠️ Error fetching summary for {url}: {e}")

    return None

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

        # 🔹 Try extracting from meta tag first
        meta_date = soup.select_one('meta[property="article:published_time"]')
        if meta_date and "content" in meta_date.attrs:
            return meta_date["content"].split("T")[0]  # Extract YYYY-MM-DD format
        
        # 🔹 If no meta tag found, try extracting from publishing div
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

# 🔹 Save extracted articles to a JSON file
def save_articles_to_json(articles):
    """Saves extracted articles to a JSON file."""
    try:
        with open(EXPORT_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=4)
        print(f"✅ Successfully saved {len(articles)} articles to {EXPORT_FILE_PATH}")

    except Exception as e:
        print(f"❌ Error saving JSON file: {e}")

# 🔹 Main execution
if __name__ == "__main__":
    print("🚀 Fetching Yahoo Finance news...")
    extracted_articles = extract_articles()
    
    if extracted_articles:
        save_articles_to_json(extracted_articles)
    else:
        print("⚠️ No articles found.")
