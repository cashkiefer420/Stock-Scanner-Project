import json

# Define the absolute path to the JSON file
json_file_path = "/home/ec2-user/Stock-Scanner-Project/json/Sample_tickers.json"

try:
    # Open and read the JSON file
    with open(json_file_path, "r") as file:
        data = json.load(file)  # Load existing data into a Python dictionary

    # Modify the JSON data (example: adding a new ticker)
    data["new_ticker"] = "XYZ"

    # Write the updated data back to the JSON file
    with open(json_file_path, "w") as file:
        json.dump(data, file, indent=4)

    print("JSON file updated successfully!")

except FileNotFoundError:
    print(f"Error: File not found at {json_file_path}")
except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

