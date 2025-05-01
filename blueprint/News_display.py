import os
import json

# Correct base path to match project root
base_dir = os.path.dirname(os.path.abspath(__file__))
EXPORT_FILE_PATH = os.path.abspath(os.path.join(base_dir, "..", "json", "news.json"))

def get_articles():
    if not os.path.exists(EXPORT_FILE_PATH):
        print(f"Warning: news.json not found at {EXPORT_FILE_PATH}")
        return []

    try:
        with open(EXPORT_FILE_PATH, 'r', encoding='utf-8') as f:
            articles = json.load(f)
            if isinstance(articles, list):
                return articles
            else:
                print("Warning: news.json is not a list")
                return []
    except Exception as e:
        print(f"Error reading news.json: {e}")
        return []