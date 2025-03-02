from flask import Flask, request, jsonify, render_template, Response
import pandas as pd
import json
import os
import re

app = Flask(__name__)

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
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return []

# Normalize field names to match HTML input
def normalize_field_name(field_name):
    return re.sub(r'[^a-zA-Z0-9]', '_', field_name).lower()

@app.route('/')
def index():
    return render_template("Personalized_stock_filter.html")

@app.route('/load_data', methods=['GET'])
def load_data():
    data = load_json_data()
    return jsonify(data)

@app.route('/download_csv', methods=['GET'])
def download_csv():
    data = load_json_data()
    if not data:
        return jsonify({"error": "No stock data available"}), 404
    df = pd.DataFrame(data)
    response = Response(df.to_csv(index=False), content_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=stock_data.csv"
    return response

@app.route('/filter', methods=['POST'])
def filter_data():
    """Applies filters based on user selection and returns the filtered data."""
    data = load_json_data()
    if not data:
        return jsonify({"error": "No stock data available"}), 404

    filters = request.json
    if not filters:
        return jsonify({"error": "No filters provided"}), 400

    df = pd.DataFrame(data)

    for field, condition in filters.items():
        # Normalize column names
        normalized_field = field.replace(" ", "_").lower()

        if normalized_field not in df.columns:
            continue  # Skip fields not in dataset

        value = condition.get("value")
        condition_type = condition.get("type")

        if value is None or condition_type is None:
            continue  # Skip incomplete filters

        try:
            # Ensure value is a float for comparison
            value = float(value)

            if condition_type == "greater_than":
                df = df[df[normalized_field].astype(float) > value]
            elif condition_type == "less_than":
                df = df[df[normalized_field].astype(float) < value]
            elif condition_type == "equal_to":
                df = df[df[normalized_field].astype(float) == value]
        except (ValueError, KeyError):
            continue  # Skip if conversion fails or key doesn't exist

    return jsonify(df.to_dict(orient="records"))

if __name__ == '__main__':
    app.run(debug=True)
