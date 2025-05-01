import os
import json
import re

# Base directory and file path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FOLDER = os.path.join(BASE_DIR, "..", "json")
FILE_PATH = os.path.join(JSON_FOLDER, "stock_data_export.json")

os.makedirs(JSON_FOLDER, exist_ok=True)
def normalize_field_name(field_name):
    import re
    return re.sub(r'[^a-zA-Z0-9]', '_', field_name).lower()

def load_json_data():
    if not os.path.exists(FILE_PATH):
        return []
    try:
        with open(FILE_PATH, 'r', encoding="utf-8") as file:
            data = json.load(file)
            if isinstance(data, list):
                return [
                    {normalize_field_name(k): v for k, v in row.items()}
                    for row in data
                ]
            else:
                return []
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return []
# Normalize field names to match HTML input