import pandas as pd
import json
import os
import re
import argparse

# Set base directory
base_dir = r"C:\Users\Carte\Documents\Stock-Scanner-Project-Windows"
FILE_PATH = os.path.join(base_dir, "json", "stock_data_export.json")

# Function to load JSON data
def load_json_data():
    if not os.path.exists(FILE_PATH):
        return []
    try:
        with open(FILE_PATH, 'r', encoding="utf-8") as file:
            data = json.load(file)
            if isinstance(data, list):
                return data  # Ensure it's a list of dictionaries
            else:
                print("Error: JSON data is not a list")
                return []
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return []

# Normalize field names to match HTML input
def normalize_field_name(field_name):
    return re.sub(r'[^a-zA-Z0-9]', '_', field_name).lower()

# Abbreviations for filters
filter_abbrevs = {
    "cp": "Current Price",
    "pct": "Price Change Today",
    "pcw": "Price Change Week",
    "pcm": "Price Change Month",
    "pcy": "Price Change Year",
    "vt": "Volume Today",
    "av3m": "Avg Volume (3 mon)",
    "dvav": "DVAV (Day Volume Over Average Volume)",
    "pe": "P/E Ratio",
    "pec3m": "P/E Change (3 Mon)",
    "sa": "Shares Available",
    "mc": "Market Cap",
    "mcc3m": "Market Cap Change (3 Mon)",
    "dy": "Dividend Yield",
    "dvsa": "DVSA (Volume Today Over Shares Available)"
}

# Function to parse filter arguments
def parse_filters(args):
    filters = {}
    for arg in args:
        match = re.match(r"([a-zA-Z0-9]+)([+-])\s*(-?\d+(\.\d+)?)", arg)
        if not match:
            continue
        abbrev, condition, value = match.groups()[:3]
        if abbrev in filter_abbrevs:
            field = filter_abbrevs[abbrev]
            if condition == '+':
                filters[field] = {"type": "greater_than", "value": value}
            elif condition == '-':
                filters[field] = {"type": "less_than", "value": value}
    return filters

# Function to filter data
def filter_data(data, filters):
    df = pd.DataFrame(data)
    df.columns = [normalize_field_name(col) for col in df.columns]

    for field, condition in filters.items():
        normalized_field = normalize_field_name(field)

        if normalized_field not in df.columns:
            print(f"Skipping unknown field: {normalized_field}")
            continue  # Skip fields not in the dataset

        value = condition.get("value")
        condition_type = condition.get("type")

        if value is None or condition_type is None:
            print(f"Skipping invalid filter for field: {field}")
            continue  # Skip if filter is incomplete

        # Apply numeric filters
        if condition_type in ["greater_than", "less_than"]:
            try:
                value = float(value)  # Ensure value is numeric
                df[normalized_field] = pd.to_numeric(df[normalized_field], errors="coerce")

                if condition_type == "greater_than":
                    df = df[df[normalized_field].notna() & (df[normalized_field] > value)]
                elif condition_type == "less_than":
                    df = df[df[normalized_field].notna() & (df[normalized_field] < value)]

            except ValueError:
                print(f"Skipping field {field}: Cannot convert to float")
                continue  # Skip if conversion fails

        # Apply string-based filters
        elif condition_type == "equal_to":
            df = df[df[normalized_field].astype(str) == str(value)]
        elif condition_type == "contains":
            df = df[df[normalized_field].astype(str).str.contains(str(value), case=False, na=False)]

    return df.to_dict(orient="records")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Filter stock data")
    parser.add_argument('filters', metavar='F', type=str, nargs='+', help='Filter conditions')
    args = parser.parse_args()

    data = load_json_data()
    if not data:
        print("No stock data available")
        exit(1)

    filters = parse_filters(args.filters)
    if not filters:
        print("No valid filters provided")
        exit(1)

    filtered_data = filter_data(data, filters)
    if not filtered_data:
        print("No data matches the applied filters")
        exit(1)

    # Output the filtered data
    print(json.dumps(filtered_data, indent=4))
