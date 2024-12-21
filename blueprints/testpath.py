import json
from pathlib import path

base_dir = Path(__file__).resolve()
while base_dir.name != "Stock-Scanner-Project"  and base_dir.parent !=base_dir:
    base_dir = base_dir.parent

if base_dir.name != "Stock-Scanner-Project":
    raise FileNotFoundError("Base directory 'Stock-Scanner-Project' not found!")

# Define the absolute path to the JSON file
json_file_path = base_dir / "json" / "Sample_ticker.json"

print(json_file_path)

print("JSON file Found successfully!")

except FileNotFoundError:
    print(f"Error: File not found at {json_file_path}")
except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

