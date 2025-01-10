import json

# Path to the input JSON file
input_file_path = r"C:\Users\Carter\Downloads\Stock-Scanner-Project-main\Stock-Scanner-Project-main\json\Sample_tickers.json"

# Path to save the new JSON file
output_file_path = r"C:\Users\Carter\Downloads\Stock-Scanner-Project-main\Stock-Scanner-Project-main\json\processed_tickers.json"

# Read the tickers from the input JSON file
with open(input_file_path, "r") as input_file:
    tickers = json.load(input_file)

# Reformat the tickers into the desired structure
formatted_json = {"tickers": tickers}

# Write the new JSON to the output file in one line
with open(output_file_path, "w") as output_file:
    json.dump(formatted_json, output_file, separators=(',', ':'))

print(f"Reformatted JSON saved to: {output_file_path}")
