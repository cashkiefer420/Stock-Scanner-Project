from flask import Flask, request, jsonify, render_template, send_file
import pandas as pd
import json
import os

app = Flask(__name__, template_folder='templates')

# Load JSON data
with open('stocks.json') as f:
    stock_data = json.load(f)

# Normalize data and handle N/A values
df = pd.DataFrame(stock_data)
df.replace("N/A", None, inplace=True)

# Convert numeric columns safely
for col in df.columns:
    try:
        df[col] = pd.to_numeric(df[col])
    except ValueError:
        pass  # Ignore columns that can't be converted

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/filter', methods=['POST'])
def filter_data():
    filters = request.json
    filtered_df = df.copy()

    # Apply filters
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
    
    return jsonify(filtered_df.to_dict(orient='records'))

@app.route('/download', methods=['POST'])
def download():
    filters = request.json
    filtered_df = df.copy()

    # Apply filters
    for key, condition in filters.items():
        if key in filtered_df:
            value = condition['value']
            if value != 0:
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
    return jsonify(sorted_df.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)