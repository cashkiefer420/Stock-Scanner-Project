import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Ensure NLTK resources are available
nltk.download('vader_lexicon')

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
response = requests.get(url, headers=headers)
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
    url = [
        "https://finance.yahoo.com/topic/stock-market-news/",
        "https://finance.yahoo.com/topic/latest-news/",
        "https://finance.yahoo.com/topic/earnings/",
        "https://finance.yahoo.com/topic/morning-brief/"
    ]
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Example: Assuming articles are in <li> elements with class 'js-stream-content'
    articles = soup.find_all("li", class_="js-stream-content")
    
    return articles

# 🔹 Function to extract articles and process them
def extract_articles():
    """Extracts stock news articles, assigns grades & scores."""
    today_date = datetime.today().strftime("%Y-%m-%d")
    extracted_articles = []

    # 🔹 Fetch all articles first
    articles = fetch_news()

    for article in articles:
        headline_tag = article.select_one("h3")  # Assuming the headline is in <h3>
        link_tag = article.select_one("a.subtle-link")  # Link in <a> with class 'subtle-link'
        paragraph_tag = article.select_one("p")  # Summary paragraph in <p>
        time_tag = article.select_one("time")  # Article time in <time>

        # Clean the headline text
        headline = clean_text(headline_tag.text.strip()) if headline_tag else None
        link = f"https://finance.yahoo.com{link_tag['href']}" if link_tag and 'href' in link_tag.attrs else None
        first_paragraph = paragraph_tag.text.strip() if paragraph_tag else None
        article_date = time_tag["datetime"].split("T")[0] if time_tag and "datetime" in time_tag.attrs else today_date

        # 🔹 Skip articles with missing crucial information
        if not headline or not link or not first_paragraph or not article_date:
            continue

        # 🔹 Assign grade & score based on sentiment analysis
        grade, score = assign_grade(first_paragraph)

        extracted_articles.append({
            "headline": headline,
            "link": link,
            "first_paragraph": first_paragraph,
            "date": article_date,
            "grade": grade,
            "score": score
        })

    print(f"✅ Extracted {len(extracted_articles)} articles.")

    return extracted_articles

# 🔹 Call the extract function and print the result
if __name__ == "__main__":
    articles = extract_articles()
    print(json.dumps(articles, indent=4))
