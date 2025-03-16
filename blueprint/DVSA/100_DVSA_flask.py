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
    return render_template('Index-DVSA-100.html')

# Paths to JSON files
BASE_DIR = r"/home/ec2-user/Stock-Scanner-Project/"
JSON_FOLDER = os.path.join(BASE_DIR, 'json')
JSON_FILE = os.path.join(JSON_FOLDER, '100_dvsa.json')

# Ensure JSON folder exists
if not os.path.exists(JSON_FOLDER):
    os.makedirs(JSON_FOLDER)

# Ensure JSON file exists with the correct structure
def ensure_json_file(filepath, default_data):
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump(default_data, f, indent=4)

# Ensuring that the "emails" key is in the right format when file is created
ensure_json_file(JSON_FILE, {"emails": []})

# Email validation function using regex
def is_valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email)

@app.route('/subscribe-DVSA-100', methods=['POST'])
def subscribe_email():
    try:
        data = request.get_json()
        
        # Check if the request contains an email field
        if not data or "email" not in data:
            return jsonify({"message": "Invalid request format"}), 400

        email = data["email"]
        
        # Validate email format
        if not is_valid_email(email):
            return jsonify({"message": "Invalid email format"}), 400

        # Load the existing email data
        with open(JSON_FILE, 'r') as file:
            email_data = json.load(file)

        # Prevent duplicate subscriptions
        if email in email_data["emails"]:
            return jsonify({"message": "Email already subscribed"}), 400

        # Add the new email to the list
        email_data["emails"].append(email)

        # Save the updated email data back to the file
        with open(JSON_FILE, 'w') as file:
            json.dump(email_data, file, indent=4)

        return jsonify({"message": "Subscription successful"}), 200

    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001)
