import requests
import json
import os
import time
import schedule
from datetime import datetime, timedelta
import pytz

# Base directory and file paths
base_dir = r"/home/ec2-user/Stock-Scanner-Project/"
SEEN_FILE_PATH = os.path.join(base_dir, "json", "seen_articles.json")
EXPORT_FILE_PATH = os.path.join(base_dir, "json", "news.json")

# Define the updated keyword lists and scoring system
keywords = {
    1: ["bankruptcy", "fraud", "lawsuit", "default", "collapse", "crash", "scandal", "layoff", "downturn", "depression", 
        "crisis", "recession", "plummet", "failure", "losses", "penalty", "investigation", "misconduct", "closure", "downfall"],
    2: ["loss", "decline", "debt", "risk", "penalty", "diminish", "drop", "cut", "weak", "uncertain", 
        "fine", "volatile", "downgrade", "slowdown", "struggle", "pressure", "shortfall", "disruption", "negative", "warning"],
    3: ["neutral", "stable", "moderate", "average", "steady", "unchanged", "flat", "balanced", "constant", "status quo", 
        "midpoint", "middle", "unmoved", "normal", "equilibrium", "regular", "unaffected", "unchallenged", "intermediate", "consistent"],
    4: ["growth", "profit", "increase", "success", "expansion", "improvement", "gain", "progress", "advance", "upturn", 
        "positive", "strength", "opportunity", "recover", "stable growth", "resilience", "rise", "achievement", "promising", "favorable"],
    5: ["record-breaking", "booming", "outstanding", "surge", "innovative", "exceptional", "unprecedented", "thriving", "remarkable", "breakthrough", 
        "leading", "flourishing", "highly successful", "groundbreaking", "top-performing", "skyrocketing", "phenomenal", "milestone", "extraordinary", "peak performance"]
}

# Define grading brackets
brackets = {
    1: (-float('inf'), -20),
    2: (-19, -5),
    3: (-5, 5),
    4: (5, 19),
    5: (20, float('inf'))
}

# Scoring system for keyword levels
scores = {1: -2, 2: -1, 3: 0, 4: 1, 5: 2}

# Load seen articles from a JSON file
def load_seen_articles():
    if os.path.exists(SEEN_FILE_PATH):
        with open(SEEN_FILE_PATH, "r") as file:
            return set(json.load(file))
    return set()

# Save seen articles to a JSON file
def save_seen_articles(seen_articles):
    with open(SEEN_FILE_PATH, "w") as file:
        json.dump(list(seen_articles), file)

# Function to grade articles based on keywords
def grade_article(text):
    score = 0
    for level, words in keywords.items():
        count = sum(text.lower().count(word) for word in words)
        if count > 0:
            score += count * scores[level]
    for grade, (lower, upper) in brackets.items():
        if lower <= score < upper:
            return grade, score
    return 3, score  # Default to neutral if not graded

# Fetch all news articles
def fetch_all_news():
    url = "https://query2.finance.yahoo.com/v1/finance/search?q=finance&newsCount=50"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("news", [])
    return []

# Process and grade articles, skipping already seen ones
def process_news():
    seen_articles = load_seen_articles()
    news = fetch_all_news()
    new_articles = []
    for article in news:
        title = article.get("title", "")
        if title not in seen_articles:
            grade, score = grade_article(title)
            new_articles.append({"title": title, "grade": grade, "score": score})
            seen_articles.add(title)

    save_seen_articles(seen_articles)
    return new_articles

# Clear both files
def clear_files():
    print("Clearing files...")
    with open(SEEN_FILE_PATH, "w") as file:
        json.dump([], file)
    with open(EXPORT_FILE_PATH, "w") as file:
        json.dump([], file)
    print("Files cleared.")

# Sleep until 3 AM New York Time
def sleep_until_3am():
    ny_timezone = pytz.timezone("America/New_York")
    now = datetime.now(ny_timezone)
    next_3am = now.replace(hour=3, minute=0, second=0, microsecond=0)
    if now.hour >= 3:
        next_3am += timedelta(days=1)  # Move to the next day if past 3 AM
    sleep_time = (next_3am - now).total_seconds()
    print(f"Sleeping until 3 AM New York Time ({next_3am.strftime('%Y-%m-%d %H:%M:%S')}), {sleep_time/3600:.2f} hours remaining.")
    time.sleep(sleep_time)

# Main function to process news and schedule it every 5 minutes
def run_script():
    ny_timezone = pytz.timezone("America/New_York")
    now = datetime.now(ny_timezone)

    # Check if it's between 8 PM and 3 AM
    if 20 <= now.hour or now.hour < 3:
        clear_files()
        sleep_until_3am()
    else:
        print("Fetching all financial news...")
        new_results = process_news()

        if new_results:
            # Save new results to the export file
            if os.path.exists(EXPORT_FILE_PATH):
                with open(EXPORT_FILE_PATH, "r") as json_file:
                    existing_data = json.load(json_file)
            else:
                existing_data = []

            # Append new results to existing data
            existing_data.extend(new_results)

            with open(EXPORT_FILE_PATH, "w") as json_file:
                json.dump(existing_data, json_file, indent=4)
            print(f"Processed {len(new_results)} new articles. Results saved to {EXPORT_FILE_PATH}")
        else:
            print("No new articles found.")

# Schedule the script to run every 5 minutes
def main():
    schedule.every(5).minutes.do(run_script)
    print("Scheduled to run every 5 minutes. Press Ctrl+C to exit.")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()