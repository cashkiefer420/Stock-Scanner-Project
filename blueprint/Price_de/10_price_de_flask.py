from flask import Flask, request, jsonify, render_template
import os
import json
import re

app = Flask(__name__, static_folder=r"/home/ec2-user/Stock-Scanner-Project/static")

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/')
def index():
    return render_template('Index-Price-Decrease-10.html')

# Paths to JSON files
BASE_DIR = r"/home/ec2-user/Stock-Scanner-Project/"
JSON_FOLDER = os.path.join(BASE_DIR, 'json')
JSON_FILE = os.path.join(JSON_FOLDER, '10_price_de.json')

# Ensure JSON folder exists
if not os.path.exists(JSON_FOLDER):
    os.makedirs(JSON_FOLDER)

# Ensure JSON file exists with correct structure
def ensure_json_file(filepath, default_data):
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump(default_data, f, indent=4)

ensure_json_file(JSON_FILE, {"emails": []})

# Email validation function
def is_valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email)

@app.route('/subscribe-price-10-de', methods=['POST'])
def subscribe_email():
    try:
        data = request.get_json()
        if not data or "email" not in data:
            return jsonify({"message": "Invalid request format"}), 400

        email = data["email"]
        if not is_valid_email(email):
            return jsonify({"message": "Invalid email format"}), 400

        # Load email data
        with open(JSON_FILE, 'r') as file:
            email_data = json.load(file)

        # Prevent duplicate emails
        if email in email_data["emails"]:
            return jsonify({"message": "Email already subscribed"}), 400

        # Add email and save
        email_data["emails"].append(email)
        with open(JSON_FILE, 'w') as file:
            json.dump(email_data, file, indent=4)

        return jsonify({"message": "Subscription successful"}), 200

    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
