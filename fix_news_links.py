import os
import json

# Adjust the path below to match your project structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NEWS_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "json", "news.json"))

def clean_links():
    if not os.path.exists(NEWS_PATH):
        print(f"news.json not found at {NEWS_PATH}")
        return

    with open(NEWS_PATH, "r", encoding="utf-8") as f:
        try:
            articles = json.load(f)
        except json.JSONDecodeError:
            print("Error: news.json is not valid JSON.")
            return

    modified = False
    for article in articles:
        link = article.get("link", "")
        if "https://finance.yahoo.comhttps://" in link:
            article["link"] = link.replace("https://finance.yahoo.comhttps://", "https://")
            modified = True
        elif link.startswith("https://finance.yahoo.comhttps"):
            article["link"] = link.replace("https://finance.yahoo.comhttps", "https")
            modified = True

    if modified:
        with open(NEWS_PATH, "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=2)
        print("✅ news.json links cleaned.")
    else:
        print("No malformed links found.")

if __name__ == "__main__":
    clean_links()