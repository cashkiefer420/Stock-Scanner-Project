import os
import json
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

# Define the path to the JSON file
base_dir = r"C:\Users\Carter\Downloads\Stock-Scanner-Project-main"
json_filepath = os.path.join(base_dir, "json", "stock_data_export.json")

# Function to load JSON data
def load_json_data():
    if not os.path.exists(json_filepath):
        return []
    try:
        with open(json_filepath, 'r', encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return []

@app.route('/')
def home():
    return render_template('Look.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query', '').strip().lower().replace('.', '')
    data = load_json_data()
    result = next((item for item in data if item['Ticker'].lower() == query or item['Company Name'].lower().replace('.', '') == query), None)
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "Company or ticker not found."}), 404

if __name__ == '__main__':
    app.run(debug=True)
