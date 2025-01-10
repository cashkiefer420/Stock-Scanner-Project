import json
import os 

current_dir = os.path.dirname(os.path.abspath(__file__))

while os.path.basename(current_dir) != "Stock-Scanner-Project":
    current_dir = os.path.dirname(current_dir)
    if current_dir == "/":
        raise FileNotFoundError("Base directory 'Stock-Scanner-Project' not found!")

base_dir = current_dir

# Define the absolute path to the JSON file
file_path = os.path.join(base_dir, "json", "Sample_ticker.json")

print("Base directory:", base_dir)

print("Full file path:", file_path)


