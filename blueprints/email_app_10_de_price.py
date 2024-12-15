from flask import Flask, request, jsonify
import re
import os
import json
import smtplib
from jinja2 import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

# Path to the JSON file in your local Git repository
JSON_FILE = 'json/10_price_de.json'

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
@app.route('/subscribe-price-10-de', methods=['POST'])
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

# Load the stock information data
with open('json/Filtered_price_10_de.json') as f:
    stock_info = json.load(f)

# Load the email list data
with open('json/10_price_de.json') as f:
    email_data = json.load(f)

# HTML email template for stock movement
html_template = """
<html>
  <body>
    <h1>Stock <strong>{{ stock_symbol }}</strong> Down Ten Percent Notification</h1>
    <p>Dear Investor,</p>
    <p>The stock <strong>{{ stock_symbol }}</strong> has experienced a price movement.</p>
    <p>Current Price: ${{ current_price }}</p>
    <p>Percentage Change: {{ percentage_change }}%</p>
    <p>Volume Today: {{ Volume_today }}%</p>
    <p>Best Regards,<br>Retail Trade Scanner</p>
  </body>
</html>
"""

# SMTP server configuration (example with Gmail)
SMTP_SERVER = 'smtp.ionos.com'
SMTP_PORT = 587
SENDER_EMAIL = 'noreply.rts@retailtradescanner.com'
SENDER_PASSWORD = 'pIqvin-persi2-pibsij'

# Initialize the SMTP server
server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
server.starttls()
server.login(SENDER_EMAIL, SENDER_PASSWORD)

# Prepare the template
template = Template(html_template)

# Loop through each email address
for recipient in email_data["emails"]:
    # Fill in the template with stock movement data
    filled_html = template.render(
        stock_symbol=stock_info["ticker"],
        current_price=stock_info["Current Price"],
        percentage_change=stock_info["percentage_change"]
        Volume_Today=stock_info["Volume today"],
    )

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient
    msg['Subject'] = f'Stock Movement Notification for {stock_info["stock_symbol"]}'

    # Attach the HTML content to the email
    msg.attach(MIMEText(filled_html, 'html'))

    # Send the email
    server.sendmail(SENDER_EMAIL, recipient, msg.as_string())

# Close the SMTP server connection
server.quit()


if __name__ == '__main__':
    app.run(debug=True)
