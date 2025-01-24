import json
import os
import time
from datetime import datetime

# 🔹 File paths
BASE_DIR = r"/home/ec2-user/Stock-Scanner-Project/"
JSON_DIR = os.path.join(BASE_DIR, "json")
EXPORT_FILE_PATH = os.path.join(JSON_DIR, "news.json")

# 🔹 Keywords for sentiment grading
keywords = {
    1: ["sell", "underperform", "bearish", "collapse", "bankruptcy", "fraud", "lawsuit", "default", "crash", "failure",
        "penalty", "investigation", "misconduct", "SEC probe", "restructuring", "foreclosure", "delisting", "audit concern",
        "legal action", "crisis", "recession", "plummet", "scandal", "layoff", "downsizing", "market volatility", "negative forecast"],

    2: ["headwinds", "margin pressure", "earnings miss", "revenue decline", "cost-cutting", "restructuring", "soft demand",
        "uncertain outlook", "challenging environment", "adjusted guidance", "regulatory scrutiny", "shortfall", "slower growth",
        "deleveraging", "impairment charge", "litigation risk", "supply chain issues", "cybersecurity breach", "lower-than-expected",
        "slower growth", "negative impact", "difficult conditions"],

    3: ["neutral", "hold", "positioned for growth", "market share", "sector performance", "target price", "analyst rating",
        "investor confidence", "strategic investment", "market opportunity", "portfolio", "dividend yield", "long-term strategy",
        "strategic partnership", "steady performance", "stable outlook", "value investment", "balanced portfolio", "evaluating options"],

    4: ["buy", "outperform", "strong buy", "bullish", "positive momentum", "impressive results", "growth trajectory",
        "market leader", "scaling operations", "expansion strategy", "customer growth", "sustained performance", "product launch",
        "strategic investment", "positive earnings surprise", "bullish outlook", "strong growth", "acquisition success", "positive sentiment"],

    5: ["buy now", "breakthrough innovation", "disruptive technology", "record-breaking profits", "all-time high", "exceptional performance",
        "dominant market position", "trailblazing", "transformational growth", "skyrocketing stock", "outpacing competitors", "highest earnings ever",
        "industry-shifting", "game-changer", "phenomenal success", "category-defining", "best quarter ever", "leadership in innovation",
        "unprecedented demand", "buying opportunity", "rapid expansion", "leading the market", "outperforming expectations"]
}

# 🔹 Assign grades based on article content
def assign_grade(content):
    """Assigns a grade to an article based on its first two paragraphs"""
    if not content:
        return 3  # Neutral if no content

    desc_lower = content.lower()
    grade_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    # Check each keyword category and count its occurrences in the content
    for grade, words in keywords.items():
        grade_count[grade] = sum(word in desc_lower for word in words)

    # Determine the highest grade based on the word occurrences
    max_grade = max(grade_count, key=grade_count.get)

    # If extreme bias is detected (either very positive or very negative), return neutral (grade 3)
    if max_grade in [1, 5]:
        return 3

    return max_grade

# 🔹 Load existing articles from JSON file
def load_articles():
    """Load articles from the existing news.json file."""
    if os.path.exists(EXPORT_FILE_PATH):
        with open(EXPORT_FILE_PATH, "r") as file:
            return json.load(file)
    return []

# 🔹 Save updated articles to JSON file
def save_articles(articles):
    """Save the updated articles with grades to the news.json file."""
    with open(EXPORT_FILE_PATH, "w") as file:
        json.dump(articles, file, indent=4)

# 🔹 Grade the articles
def grade_articles():
    """Grading the articles and appending grades to each."""
    articles = load_articles()

    for article in articles:
        # Use the first two paragraphs as the excerpt
        content = article.get('content', "")
        excerpt = " ".join(content.split("\n")[:2])  # Use the first two paragraphs as an excerpt

        grade = assign_grade(excerpt)
        article['grade'] = grade  # Assign the grade to the article

    save_articles(articles)  # Save the articles with the grades

# 🔹 Continuous grading loop every 3 minutes
def continuously_grade():
    """Grade articles every 3 minutes."""
    while True:
        print(f"Grading articles at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        grade_articles()
        print("Articles graded and saved.")
        time.sleep(180)  # Wait for 3 minutes (180 seconds)

if __name__ == "__main__":
    continuously_grade()