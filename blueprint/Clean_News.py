import json
import os

# Define file path
base_dir = r"/home/ec2-user/Stock-Scanner-Project/json/"
file_path = os.path.join(base_dir, "news.json")

# Load the JSON data
try:
    with open(file_path, "r") as json_file:
        articles = json.load(json_file)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"❌ Error reading the JSON file: {e}")
    exit(1)

# Remove articles where "headline" is None
cleaned_articles = [article for article in articles if article.get("headline") is not None]

# Save the cleaned data back to the JSON file
with open(file_path, "w") as json_file:
    json.dump(cleaned_articles, json_file, indent=4)

print(f"✅ Cleaned JSON saved. Removed {len(articles) - len(cleaned_articles)} entries.")
