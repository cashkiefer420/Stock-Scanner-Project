import os
import json
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FOLDER = os.path.abspath(os.path.join(BASE_DIR, "..", "json"))
JSON_FILE_PATH = os.path.join(JSON_FOLDER, "stock_data_export.json")

def load_json_data():
    if not os.path.exists(JSON_FILE_PATH):
        return []
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error loading stock data: {e}")
        return []

def search_stocks(query):
    data = load_json_data()
    query = query.lower()

    def match(item):
        return any(query in str(value).lower() for value in item.values())

    return [item for item in data if match(item)]