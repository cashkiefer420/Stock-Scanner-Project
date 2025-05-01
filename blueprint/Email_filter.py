import os
import json
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_DATA_DIR = os.path.join(BASE_DIR, "..", "..", "json")
LOCAL_INPUT_FILE = os.path.join(LOCAL_DATA_DIR, "email_input.json")
LOCAL_OUTPUT_FILE = os.path.join(LOCAL_DATA_DIR, "email_output.json")

os.makedirs(LOCAL_DATA_DIR, exist_ok=True)

def safe_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def reset_filtered_files():
    if os.path.exists(LOCAL_OUTPUT_FILE):
        os.remove(LOCAL_OUTPUT_FILE)

def filter_data():
    if not os.path.exists(LOCAL_INPUT_FILE):
        print(f"No input file found at {LOCAL_INPUT_FILE}")
        return []

    with open(LOCAL_INPUT_FILE, 'r', encoding='utf-8') as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            print("Failed to parse JSON")
            return []

    filtered = []
    for row in data:
        price = safe_float(row.get("price"))
        if price and price > 100:
            filtered.append(row)

    with open(LOCAL_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, indent=2)

    print(f"Filtered {len(filtered)} records and saved to {LOCAL_OUTPUT_FILE}")
    return filtered

def main():
    reset_filtered_files()
    return filter_data()