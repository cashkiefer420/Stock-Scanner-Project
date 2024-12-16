from flask import Flask, request, jsonify
import os
import json
import re
import smtplib
from jinja2 import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import time
import threading

app = Flask(__name__)

# SMTP Configuration
SMTP_SERVER = 'smtp.ionos.com'
SMTP_PORT = 587
SENDER_EMAIL = 'noreply.rts@retailtradescanner.com'
SENDER_PASSWORD = 'pIqvin-persi2-pibsij'

# Paths to JSON files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, 'json', '20_price_in.json')
STOCK_INFO_FILE = os.path.join(BASE_DIR, 'json', 'Filtered_price_20_in.json')
USED_TICKERS_FILE = os.path.join(BASE_DIR, 'json', 'ut_price_20_in.json')

# Ensure JSON files exist
for file in [JSON_FILE, USED_TICKERS_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump({"emails": [], "used_tickers": []}, f, indent=4)

# Email validation
def is_valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email)

# Route to handle email subscription
@app.route('/subscribe-price-20-in', methods=['POST'])
def subscribe_email():
    try:
        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"message": "Email is required"}), 400
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
  
        return jsonify({"message": "An error occurred"}), 500

def send_stock_notifications():
    try:
        # Load email data
        with open(JSON_FILE, 'r') as f:
            email_data = json.load(f)

        # Load used tickers
        with open(USED_TICKERS_FILE, 'r') as f:
            used_tickers_data = json.load(f)

        # Load stock data
        with open(STOCK_INFO_FILE, 'r') as f:
            stock_data = json.load(f)

        # Email template
        html_template = """
        <html>
          <body>
            <h1>Stock <strong>{{ stock_symbol }}</strong> Incresase Twenty Percent Notification</h1>
            <p>Dear Investor,</p>
            <p>The stock <strong>{{ stock_symbol }}</strong> has experienced a price movement.</p>
            <p>Current Price: ${{ current_price }}</p>
            <p>Percentage Change: {{ percentage_change }}%</p>
            <p>Volume Today: {{ Volume_today }}</p>
            <p>Best Regards,<br>Retail Trade Scanner</p>
          </body>
        </html>
        """

        # Initialize SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        # Prepare template
        template = Template(html_template)

        for ticker_info in stock_data.get("stocks", []):
            ticker = ticker_info.get("ticker", "Unknown")

            # Skip if the ticker is already used
            if ticker in used_tickers_data["used_tickers"]:
                continue

            filled_html = template.render(
                stock_symbol=ticker,
                current_price=ticker_info.get("Current Price", "N/A"),
                percentage_change=ticker_info.get("percentage_change", "N/A"),
                Volume_today=ticker_info.get("Volume today", "N/A"),
            )

            for recipient in email_data["emails"]:
                msg = MIMEMultipart()
                msg['From'] = SENDER_EMAIL
                msg['To'] = recipient
                msg['Subject'] = f'Stock Movement Notification for {ticker}'

                msg.attach(MIMEText(filled_html, 'html'))
                server.sendmail(SENDER_EMAIL, recipient, msg.as_string())

            # Mark ticker as used
            used_tickers_data["used_tickers"].append(ticker)

        # Save updated used tickers
        with open(USED_TICKERS_FILE, 'w') as f:
            json.dump(used_tickers_data, f, indent=4)

        server.quit()
    except Exception as e:


def periodic_check():
    """Check every 5 minutes for new stock data and send notifications."""
    while True:
       
        send_stock_notifications()
        time.sleep(300)  # Wait for 5 minutes

def reset_used_tickers():
    """Reset the used tickers file at midnight."""
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            with open(USED_TICKERS_FILE, 'w') as f:
                json.dump({"used_tickers": []}, f, indent=4)
        
        time.sleep(60)  # Check the time every minute

# Start background threads
reset_thread = threading.Thread(target=reset_used_tickers, daemon=True)
reset_thread.start()

check_thread = threading.Thread(target=periodic_check, daemon=True)
check_thread.start()

if __name__ == '__main__':
    app.run(debug=True)
