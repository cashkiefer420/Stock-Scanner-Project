import json
import os

# Define the target directory
json_folder = "json"

# Ensure the directory exists
if not os.path.exists(json_folder):
    os.makedirs(json_folder)

# Hardcoded list of JSON files to format
email_json_files = [
    "1.125_volume.json",
    "1.25_price_in.json",
    "1.5_volume.json",
    "1.75_volume.json",
    "10_de_pe_subs.json",
    "10_in_pe_subs.json",
    "10_mc_de.json",
    "10_mc_in.json",
    "10_price_de.json",
    "15_price_de.json",
    "2.5_volume.json",
    "20_de_pe_subs.json",
    "20_in_pe_subs.json",
    "20_mc_de.json",
    "20_mc_in.json",
    "20_price_de.json",
    "20_price_in.json",
    "2x_volume.json",
    "30_de_pe_subs.json",
    "30_in_pe_subs.json",
    "30_mc_de.json",
    "30_mc_in.json",
    "3x_volume.json",
    "50_price_in.json",
    "5x_volume.json"
]

# JSON structure
default_content = {
    "emails": []
}

# Create and format each JSON file
for filename in email_json_files:
    file_path = os.path.join(json_folder, filename)

    with open(file_path, "w") as json_file:
        json.dump(default_content, json_file, indent=4)

    print(f"Formatted: {filename}")

print("Selected JSON files have been formatted successfully.")
