import json
import os

# 🔹 File paths
BASE_DIR = r"/home/ec2-user/Stock-Scanner-Project/"
JSON_DIR = os.path.join(BASE_DIR, "json")
EXPORT_FILE_PATH = os.path.join(JSON_DIR, "news.json")
NEW_EXPORT_FILE_PATH = os.path.join(JSON_DIR, "news2.json")

# 🔹 Extract and export titles and summaries
def extract_and_export_titles_summaries():
    """Extracts headlines and summaries from news.json and saves to news2.json."""
    if not os.path.exists(EXPORT_FILE_PATH):
        print("❌ Error: news.json not found!")
        return

    with open(EXPORT_FILE_PATH, "r") as file:
        articles = json.load(file)

    if not articles:
        print("❌ No articles found in news.json.")
        return

    extracted_data = []

    for article in articles:
        title = article.get("headline")
        summary = article.get("first_paragraph")

        if title and summary:  # 🔹 Exclude null values
            extracted_data.append({
                "headline": title,
                "summary": summary
            })

    # 🔹 Save extracted data to news2.json
    with open(NEW_EXPORT_FILE_PATH, "w") as new_file:
        json.dump(extracted_data, new_file, indent=4)

    print(f"✅ Successfully saved {len(extracted_data)} articles to {NEW_EXPORT_FILE_PATH}")

# 🔹 Run the function
if __name__ == "__main__":
    extract_and_export_titles_summaries()