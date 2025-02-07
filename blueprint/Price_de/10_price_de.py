from flask import Flask, request, jsonify, render_template
import os
import json
import re
import smtplib
import requests  # Added requests module
from jinja2 import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import time
import threading

app = Flask(__name__, static_folder=r"/home/ec2-user/Stock-Scanner-Project/static")

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/')
def index():
    return render_template('Index-Price-Decrease-10.html')

# SMTP Configuration
SMTP_SERVER = 'smtp.ionos.com'
SMTP_PORT = 587
SENDER_EMAIL = 'noreply.rts@retailtradescanner.com'
SENDER_PASSWORD = 'pIqvin-persi2-pibsij'

# Paths to JSON files
BASE_DIR = r"/home/ec2-user/Stock-Scanner-Project/"
JSON_FOLDER = os.path.join(BASE_DIR, 'json')
JSON_FILE = os.path.join(JSON_FOLDER, '10_price_de.json')
STOCK_INFO_FILE = os.path.join(JSON_FOLDER, 'Filtered_price_10_de.json')
USED_TICKERS_FILE = os.path.join(JSON_FOLDER, 'ut_price_10_de.json')

# Ensure the JSON folder exists
if not os.path.exists(JSON_FOLDER):
    os.makedirs(JSON_FOLDER)

# Ensure JSON files exist with correct initial structure
def ensure_json_file(filepath, default_data):
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump(default_data, f, indent=4)

ensure_json_file(JSON_FILE, {"emails": []})
ensure_json_file(USED_TICKERS_FILE, {"used_tickers": []})
ensure_json_file(STOCK_INFO_FILE, {"stocks": []})

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

        with open(JSON_FILE, 'r') as file:
            email_data = json.load(file)

        if email in email_data["emails"]:
            return jsonify({"message": "Email already subscribed"}), 400

        email_data["emails"].append(email)
        with open(JSON_FILE, 'w') as file:
            json.dump(email_data, file, indent=4)

        return jsonify({"message": "Subscription successful"}), 200

    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

# Function to send stock notifications
def send_stock_notifications():
    try:
        ensure_json_file(JSON_FILE, {"emails": []})
        ensure_json_file(USED_TICKERS_FILE, {"used_tickers": []})
        ensure_json_file(STOCK_INFO_FILE, {"stocks": []})

        with open(JSON_FILE, 'r') as f:
            email_data = json.load(f)
        with open(USED_TICKERS_FILE, 'r') as f:
            used_tickers_data = json.load(f)
        with open(STOCK_INFO_FILE, 'r') as f:
            stock_data = json.load(f)

        html_template = """
        <html>
          <body>
            <h1>Stock <strong>{{ stock_symbol }}</strong> Down Ten Percent Notification</h1>
            <p>Dear Investor,</p>
            <p>The stock <strong>{{ stock_symbol }}</strong> has dropped significantly.</p>
            <p><strong>Current Price:</strong> ${{ current_price }}</p>
            <p><strong>Percentage Change:</strong> {{ percentage_change }}%</p>
            <p><strong>Volume Today:</strong> {{ volume_today }}</p>
            <p>Best Regards,<br>Retail Trade Scanner</p>
          </body>
        </html>
        """

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        template = Template(html_template)

        for ticker_info in stock_data.get("stocks", []):
            ticker = ticker_info.get("Ticker", "Unknown")
            percentage_change = ticker_info.get("Price Change Today", 0)

            if ticker in used_tickers_data["used_tickers"] or percentage_change < -10:
                continue

            filled_html = template.render(
                stock_symbol=ticker,
                current_price=ticker_info.get("Current Price", "N/A"),
                percentage_change=percentage_change,
                volume_today=ticker_info.get("Volume Today", "N/A"),
            )

            for recipient in email_data["emails"]:
                msg = MIMEMultipart()
                msg['From'] = SENDER_EMAIL
                msg['To'] = recipient
                msg['Subject'] = f'Stock Movement Notification for {ticker}'

                msg.attach(MIMEText(filled_html, 'html'))
                server.sendmail(SENDER_EMAIL, recipient, msg.as_string())

            used_tickers_data["used_tickers"].append(ticker)

        with open(USED_TICKERS_FILE, 'w') as f:
            json.dump(used_tickers_data, f, indent=4)

        server.quit()
    except Exception as e:
        print(f"Error sending notifications: {str(e)}")

# Periodic function to check and send notifications every 5 minutes
def periodic_check():
    while True:
        try:
            send_stock_notifications()
        except Exception as e:
            print(f"Error in periodic check: {str(e)}")
        time.sleep(300)  # Wait for 5 minutes

# Reset used tickers at midnight
def reset_used_tickers():
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            with open(USED_TICKERS_FILE, 'w') as f:
                json.dump({"used_tickers": []}, f, indent=4)
        time.sleep(60)  # Check the time every minute

# Function to subscribe test email programmatically
def test_email_subscription():
    try:
        url = "http://127.0.0.1:5000"
        email_data = {"email": "Carter.kiefer2010@outlook.com"}

        response = requests.post(url, json=email_data)

        if response.status_code == 200:
            print("Test email successfully subscribed!")
        else:
            print(f"Failed to subscribe test email: {response.json()}")
    except Exception as e:
        print(f"Error during test email subscription: {str(e)}")

# Start background threads
reset_thread = threading.Thread(target=reset_used_tickers, daemon=True)
reset_thread.start()

check_thread = threading.Thread(target=periodic_check, daemon=True)
check_thread.start()

# Run Flask app and subscribe test email
if __name__ == '__main__':
    test_email_subscription()  # Subscribe test email at startup
    app.run(debug=True)