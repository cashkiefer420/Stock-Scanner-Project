import os
import json

# Define JSON output directory
JSON_DIR = "json"
os.makedirs(JSON_DIR, exist_ok=True)  # Ensure the JSON directory exists

# Hardcoded file mapping based on your structure
FILES_MAPPING = {
    "DVSA": {
        "100_DVSA.py": "ut-100-dvsa.json",
        "150_DVSA.py": "ut-150-dvsa.json",
        "50_DVSA.py": "ut-50-dvsa.json"
    },
    "MC_Change": {
        "10_mc_de.py": "ut-10-mc-de.json",
        "10_mc_in.py": "ut-10-mc-in.json",
        "20_mc_de.py": "ut-20-mc-de.json",
        "20_mc_in.py": "ut-20-mc-in.json",
        "30_mc_de.py": "ut-30-mc-de.json",
        "30_mc_in.py": "ut-30-mc-in.json"
    },
    "PE_Change": {
        "10_pe_de.py": "ut-10-pe-de.json",
        "10_pe_in.py": "ut-10-pe-in.json",
        "20_pe_de.py": "ut-20-pe-de.json",
        "20_pe_in.py": "ut-20-pe-in.json",
        "30_pe_de.py": "ut-30-pe-de.json",
        "30_pe_in.py": "ut-30-pe-in.json"
    },
    "Price_de": {
        "10_price_de_email.py": "ut-10-price-de.json",
        "10_price_de_flask.py": "ut-10-price-de.json",
        "15_Price_de.py": "ut-15-price-de.json",
        "20_price_de.py": "ut-20-price-de.json"
    },
    "Price_in": {
        "20_price_in.py": "ut-20-price-in.json",
        "50_price_in.py": "ut-50-price-in.json",
        "75_price_in.py": "ut-75-price-in.json"
    },
    "Volume": {
        "1.125_volume.py": "ut-1.125-volume.json",
        "1.25_volume.py": "ut-1.25-volume.json",
        "1.5_volume.py": "ut-1.5-volume.json",
        "1.75_volume.py": "ut-1.75-volume.json",
        "2.5_volume.py": "ut-2.5-volume.json",
        "5x_volume.py": "ut-5x-volume.json",
        "email_app_threetimes_volume.py": "ut-3x-volume.json",
        "email_app_twotimes_volume.py": "ut-2x-volume.json"
    }
}

def create_used_tickers_file(json_path):
    """Create a JSON file with the proper format."""
    if not os.path.exists(json_path):
        with open(json_path, "w") as f:
            json.dump({"used_tickers": []}, f, indent=4)
        print(f"Created {json_path}")
    else:
        print(f"{json_path} already exists.")

def generate_json_files():
    """Loop through the hardcoded mapping and generate JSON files."""
    for category, files in FILES_MAPPING.items():
        for script_name, json_filename in files.items():
            json_path = os.path.join(JSON_DIR, json_filename)
            create_used_tickers_file(json_path)

if __name__ == "__main__":
    generate_json_files()
