from flask import Flask, request, jsonify, render_template, Response
import pandas as pd
import json
import os

app = Flask(__name__)

# Set base directory
base_dir = r"C:\Users\Carte\Documents\Stock-Scanner-Project-Windows"
FILE_PATH = os.path.join(base_dir, "json", "stock_data_export.json")

# Function to load JSON data
def load_json_data():
    if not os.path.exists(FILE_PATH):
        return []
    try:
        with open(FILE_PATH, 'r') as file:
            data = json.load(file)
            if isinstance(data, list):  # Ensure it's a list of dictionaries
                return data
            else:
                print("Error: JSON data is not a list")
                return []
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return []

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/load_data', methods=['GET'])
def load_data():
    """Loads the stock data and returns it as JSON."""
    data = load_json_data()
    return jsonify(data)

@app.route('/download_csv', methods=['GET'])
def download_csv():
    """Downloads the full stock dataset as CSV."""
    data = load_json_data()
    
    if not data:
        return jsonify({"error": "No stock data available"}), 404
    
    df = pd.DataFrame(data)
    
    # Convert DataFrame to CSV
    csv_data = df.to_csv(index=False)

    response = Response(csv_data, content_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=stock_data.csv"
    
    return response

@app.route('/filter', methods=['POST'])
def filter_data():
    """Applies filters based on user selection and returns the filtered data."""
    data = load_json_data()
    if not data:
        return jsonify([])

    filters = request.json
    df = pd.DataFrame(data)

    for field, condition in filters.items():
        if field not in df.columns:
            continue  # Skip fields not in the dataset

        value = condition["value"]
        condition_type = condition["type"]

        if condition_type == "greater_than":
            df = df[df[field] > value]
        elif condition_type == "less_than":
            df = df[df[field] < value]
        elif condition_type == "equal_to":
            df = df[df[field] == value]

    return jsonify(df.to_dict(orient="records"))

if __name__ == '__main__':
    app.run(debug=True)