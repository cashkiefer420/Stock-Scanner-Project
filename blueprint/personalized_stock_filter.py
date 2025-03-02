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

# Function to load CSV, convert it to JSON, and save
def convert_csv_to_json():
    csv_file = os.path.join(base_dir, 'filtered_stocks.csv')

    if not os.path.exists(csv_file):
        return None

    try:
        df = pd.read_csv(csv_file)
        df.replace("N/A", None, inplace=True)

        # Convert numeric columns
        for col in df.columns:
            if col not in ["Ticker", "Company Name"]:  # Preserve these columns
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Save as JSON
        df.to_json(FILE_PATH, orient="records", indent=4)
        return df.to_dict(orient="records")

    except Exception as e:
        print(f"Error converting CSV to JSON: {e}")
        return None

# Initial JSON conversion
stock_data = convert_csv_to_json() if os.path.exists(FILE_PATH) else []

@app.route('/load_csv', methods=['GET'])
def load_csv():
    data = convert_csv_to_json()
    
    if data is None:
        return jsonify({"error": "No filtered data available"}), 404
    
    return jsonify(data)

@app.route('/filter', methods=['POST'])
def filter_data():
    if not stock_data:
        return jsonify({"error": "Stock data not available"}), 500

    try:
        filters = request.json
        if not filters:
            return jsonify({"error": "No filters provided"}), 400

        filtered_df = pd.DataFrame(stock_data)

        # Apply filters
        for key, condition in filters.items():
            if key in filtered_df:
                value = safe_float(condition.get('value', 0))

                # Ignore filter if value is 0 (include all)
                if value is None or value == 0:
                    continue  

                if condition['type'] == 'greater_than':
                    filtered_df = filtered_df[filtered_df[key] >= value]
                elif condition['type'] == 'less_than':
                    filtered_df = filtered_df[filtered_df[key] <= value]
                elif condition['type'] == 'equal_to':
                    filtered_df = filtered_df[filtered_df[key] == value]

        if filtered_df.empty:
            return jsonify({"message": "No stocks match the filters."}), 200

        return jsonify(filtered_df.to_dict(orient='records'))

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    if not stock_data:
        return jsonify({"error": "Stock data not available"}), 500

    try:
        filters = request.json
        filtered_df = pd.DataFrame(stock_data)

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

        # Drop "Bid Ask Spread" & "Days Range" before exporting
        filtered_df = filtered_df.drop(columns=["Bid Ask Spread", "Days Range"], errors="ignore")

        file_path = os.path.join(base_dir, 'filtered_stocks.csv')
        filtered_df.to_csv(file_path, index=False)
        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/table', methods=['GET'])
def table():
    if not stock_data:
        return jsonify({"error": "Stock data not available"}), 500

    sorted_column = request.args.get('sort_by', 'Current Price')
    ascending = request.args.get('order', 'asc') == 'asc'

    df = pd.DataFrame(stock_data)

    if sorted_column not in df.columns:
        return jsonify({"error": f"Invalid column: {sorted_column}"}), 400

    sorted_df = df.sort_values(by=sorted_column, ascending=ascending)

    return jsonify(sorted_df.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)
