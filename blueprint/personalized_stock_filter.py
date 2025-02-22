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
    return render_template("Personalized_Stock_filter.html")  # Use just the filename

base_dir = r"C:\Users\Carte\Documents\Stock-Scanner-Project-Windows"
FILE_PATH = os.path.join(base_dir, "json", "stock_data_export.json")

# Load your JSON data
with open(FILE_PATH, 'r') as f:
    stock_data = json.load(f)

# Normalize the data and handle N/A values
df = pd.DataFrame(stock_data)
df.replace("N/A", None, inplace=True)

# Convert numeric columns safely
for col in df.columns:
    try:
        df[col] = pd.to_numeric(df[col])
    except (ValueError, TypeError):
        pass  # Ignore conversion errors and keep the original value

@app.route('/filter', methods=['POST'])
def filter_data():
    filters = request.json
    filtered_df = df.copy()

    # Apply filters from the request
    for key, condition in filters.items():
        if key in filtered_df:
            value = condition['value']
            if value != 0:  # Ignore 0 values
                if condition['type'] == 'greater_than':
                    filtered_df = filtered_df[filtered_df[key] > value]
                elif condition['type'] == 'less_than':
                    filtered_df = filtered_df[filtered_df[key] < value]
                elif condition['type'] == 'equal_to':
                    filtered_df = filtered_df[filtered_df[key] == value]

    # Return filtered data
    filtered_data = filtered_df.to_dict(orient='records')
    return jsonify(filtered_data)

@app.route('/download', methods=['POST'])
def download():
    filters = request.json
    filtered_df = df.copy()

    # Apply filters from the request
    for key, condition in filters.items():
        if key in filtered_df:
            value = condition['value']
            if value != 0:  # Ignore 0 values
                if condition['type'] == 'greater_than':
                    filtered_df = filtered_df[filtered_df[key] > value]
                elif condition['type'] == 'less_than':
                    filtered_df = filtered_df[filtered_df[key] < value]
                elif condition['type'] == 'equal_to':
                    filtered_df = filtered_df[filtered_df[key] == value]

    # Save filtered data to CSV
    file_path = 'filtered_stocks.csv'
    filtered_df.to_csv(file_path, index=False)
    return send_file(file_path, as_attachment=True)

@app.route('/table', methods=['GET'])
def table():
    sorted_column = request.args.get('sort_by', 'Current Price')
    ascending = request.args.get('order', 'asc') == 'asc'

    # Sort the DataFrame
    sorted_df = df.sort_values(by=sorted_column, ascending=ascending)

    # Return sorted data
    return jsonify(sorted_df.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)