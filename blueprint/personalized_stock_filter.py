from flask import Flask, request, jsonify, render_template, send_file
import pandas as pd
import json
import os

app = Flask(__name__)

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/')
def index():
    return render_template("Personalized_Stock_filter.html")

# Set base directory
base_dir = r"C:\Users\Carte\Documents\Stock-Scanner-Project-Windows"
FILE_PATH = os.path.join(base_dir, "json", "stock_data_export.json")

# Function to safely convert values to float
def safe_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

# Load JSON data into a DataFrame
try:
    with open(FILE_PATH, 'r') as f:
        stock_data = json.load(f)
    
    df = pd.DataFrame(stock_data)
    df.replace("N/A", None, inplace=True)

    # Convert only numeric columns to numbers, keeping Ticker & Company Name as is
    for col in df.columns:
        if col not in ["Ticker", "Company Name"]:  # Preserve these columns
            df[col] = pd.to_numeric(df[col], errors='coerce')

except Exception as e:
    print(f"Error loading data: {e}")
    df = pd.DataFrame()  # Empty DataFrame if loading fails

@app.route('/filter', methods=['POST'])
def filter_data():
    if df.empty:
        return jsonify({"error": "Stock data not available"}), 500

    try:
        filters = request.json
        if not filters:
            return jsonify({"error": "No filters provided"}), 400

        filtered_df = df.copy()

        # Apply filters
        for key, condition in filters.items():
            if key in filtered_df:
                value = safe_float(condition.get('value', 0))

                # Ignore this filter if value is 0 (user wants to include all)
                if value is None or value == 0:
                    continue  

                if condition['type'] == 'greater_than':
                    filtered_df = filtered_df[filtered_df[key] > value]
                elif condition['type'] == 'less_than':
                    filtered_df = filtered_df[filtered_df[key] < value]
                elif condition['type'] == 'equal_to':
                    filtered_df = filtered_df[filtered_df[key] == value]

        if filtered_df.empty:
            return jsonify({"message": "No stocks match the filters."}), 200

        return jsonify(filtered_df.to_dict(orient='records'))

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    if df.empty:
        return jsonify({"error": "Stock data not available"}), 500

    try:
        filters = request.json
        filtered_df = df.copy()

        # Apply filters
        for key, condition in filters.items():
            if key in filtered_df:
                value = safe_float(condition.get('value', 0))

                # Ignore this filter if value is 0 (user wants to include all)
                if value is None or value == 0:
                    continue  

                if condition['type'] == 'greater_than':
                    filtered_df = filtered_df[filtered_df[key] > value]
                elif condition['type'] == 'less_than':
                    filtered_df = filtered_df[filtered_df[key] < value]
                elif condition['type'] == 'equal_to':
                    filtered_df = filtered_df[filtered_df[key] == value]

        if filtered_df.empty:
            return jsonify({"message": "No stocks match the filters."}), 200

        file_path = os.path.join(base_dir, 'filtered_stocks.csv')
        filtered_df.to_csv(file_path, index=False)
        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/table', methods=['GET'])
def table():
    if df.empty:
        return jsonify({"error": "Stock data not available"}), 500

    sorted_column = request.args.get('sort_by', 'Current Price')
    ascending = request.args.get('order', 'asc') == 'asc'

    if sorted_column not in df.columns:
        return jsonify({"error": f"Invalid column: {sorted_column}"}), 400

    sorted_df = df.sort_values(by=sorted_column, ascending=ascending)

    return jsonify(sorted_df.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)