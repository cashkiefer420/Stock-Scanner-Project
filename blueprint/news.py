import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Ensure NLTK resources are available
nltk.download('vader_lexicon')

# Define user-agent headers to prevent blocking
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

urls = [
    "https://finance.yahoo.com/topic/stock-market-news/",
    "https://finance.yahoo.com/topic/latest-news/",
    "https://finance.yahoo.com/topic/earnings/",
    "https://finance.yahoo.com/topic/morning-brief/"
]

# 🔹 Function to decode non-word characters like \u2019 to readable characters
def clean_text(text):
    if text:
        return text.encode('utf-8').decode('unicode_escape')
    return text

# 🔹 Function to analyze sentiment and assign a grade & score
def assign_grade(text):
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(text)
    compound_score = sentiment['compound']  # Overall sentiment score

    # Assign a grade and score based on sentiment strength
    if compound_score >= 0.6:
        grade, score = 'A', int((compound_score + 1) * 50)  # Scale from 0 to 100
    elif 0.3 <= compound_score < 0.6:
        grade, score = 'B', int((compound_score + 1) * 45)
    elif 0.1 <= compound_score < 0.3:
        grade, score = 'C', int((compound_score + 1) * 40)
    elif -0.1 <= compound_score < 0.1:
        grade, score = 'D', int((compound_score + 1) * 35)
    else:
        grade, score = 'F', int((compound_score + 1) * 30)  # Lower scores for negative sentiment

    return grade, score

# 🔹 Fetch the latest articles from Yahoo Finance
def fetch_news():
    articles = []
    for url in urls:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Example: Assuming articles are in <h3> elements
        articles += soup.find_all("h3")

    return articles

# 🔹 Function to extract articles and process them
def extract_articles():
    """Extracts stock news articles, assigns grades & scores."""
    today_date = datetime.today().strftime("%Y-%m-%d")
    extracted_articles = []

    # 🔹 Fetch all articles first
    articles = fetch_news()

    for article in articles:
        headline_tag = article.select_one("a")  # Assuming the headline is in <a>
        link = f"https://finance.yahoo.com{headline_tag['href']}" if headline_tag and 'href' in headline_tag.attrs else None
        headline = clean_text(headline_tag.text.strip()) if headline_tag else None

        # 🔹 Skip articles with missing crucial information
        if not headline or not link:
            continue

        # 🔹 Assign grade & score based on sentiment analysis
        grade, score = assign_grade(headline)

        extracted_articles.append({
            "headline": headline,
            "link": link,
            "date": today_date,
            "grade": grade,
            "score": score
        })

    print(f"✅ Extracted {len(extracted_articles)} articles.")

    return extracted_articles

# 🔹 Call the extract function and print the result
if __name__ == "__main__":
    articles = extract_articles()
    print(json.dumps(articles, indent=4))