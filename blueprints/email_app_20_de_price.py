from flask import Flask, request, jsonify
import re
import os
import json

app = Flask(__name__)

# Path to the JSON file
JSON_FILE = 'https://raw.githubusercontent.com/Toasterfire-come/Stock-Scanner-Project/refs/heads/main/json/10_de_pe_subs.json?token=GHSAT0AAAAAAC3JEC3P5WTROS37K44QZMZKZ2WI3YQ'

response =  requests.get(JSON_FILE)
if response.status_code == 200:
    email_data  =  json.loads(response.text)
    print(email_data)
else:
    print(f"Failed to fetch the file: {response.status_code}")

# Ensure the JSON file exists
if not os.path.exists(JSON_FILE):
    with open(JSON_FILE, 'w') as file:
        json.dump({"emails": []}, file, indent=4)

# Email validation function
def is_valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email)

# Route to handle email subscription
@app.route('/subscribe-price-20-de', methods=['POST'])
def subscribe_email():
    try:
        # Get email from the request
        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"message": "Email is required"}), 400

        # Validate email format
        if not is_valid_email(email):
            return jsonify({"message": "Invalid email format"}), 400

        # Load existing emails
        with open(JSON_FILE, 'r') as file:
            email_data = json.load(file)

        # Check if email already exists
        if email in email_data["emails"]:
            return jsonify({"message": "Email already subscribed"}), 400

        # Add email to the list
        email_data["emails"].append(email)

        # Save the updated email list
        with open(JSON_FILE, 'w') as file:
            json.dump(email_data, file, indent=4)

        return jsonify({"message": "Subscription successful!"}), 200

    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)

