from flask import Flask, request, jsonify
import re
import os
import json

app = Flask(__name__)

# Path to the JSON file in your local Git repository
JSON_FILE = 'json/20_mc_de.json'

# Ensure the JSON file exists locally
if not os.path.exists(JSON_FILE):
    # If the file doesn't exist, create it with an empty structure
    with open(JSON_FILE, 'w') as file:
        json.dump({"emails": []}, file, indent=4)

# Email validation function
def is_valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email)

# Route to handle email subscription
@app.route('/subscribe-mc-20-de', methods=['POST'])
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

        # Save the updated list back to the file
        with open(JSON_FILE, 'w') as file:
            json.dump(email_data, file, indent=4)

        return jsonify({"message": "Subscription successful"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"message": "An error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=True)
