from flask import Flask, request, jsonify
import os
import json
import re
import smtplib
from jinja2 import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import timeimport os
import json
import smtplib
import time
from jinja2 import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import threading

# SMTP Configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = 'noreply.retailtradescanner@gmail.com'
APP_PASSWORD = 'mzqmvhsjqeqrjmjv'  # Use App Password for security

# Paths to JSON files
BASE_DIR = r"/home/ec2-user/Stock-Scanner-Project/"
JSON_FOLDER = os.path.join(BASE_DIR, 'json')

# Ensure the JSON directory exists
os.makedirs(JSON_FOLDER, exist_ok=True)

# Files and their expected default structures
JSON_FILES = {
    "20_de_pe_subs.json": {"emails": []},
    "Filtered_pe_20_de.json": {"stocks": []},
    "ut_20_pe_de.json": {"used_tickers": []}
}

# Function to ensure files exist with the correct format
def ensure_json_files():
    for filename, default_data in JSON_FILES.items():
        file_path = os.path.join(JSON_FOLDER, filename)
        if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
            with open(file_path, 'w') as f:
                json.dump(default_data, f, indent=4)

# Call the function to check and create missing files
ensure_json_files()

# File paths
EMAILS_FILE = os.path.join(JSON_FOLDER, "20_de_pe_subs.json")
STOCKS_FILE = os.path.join(JSON_FOLDER, "Filtered_pe_20_de.json")
USED_TICKERS_FILE = os.path.join(JSON_FOLDER, "ut_20_pe_de.json")

# Improved HTML Email Template
html_template = """
<html>
  <head>
    <style>
      body {
        font-family: Arial, sans-serif;
        background-color: #f4f4f4;
        margin: 0;
        padding: 0;
      }
      .email-container {
        max-width: 600px;
        margin: 20px auto;
        background: #ffffff;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
      }
      .header {
        background: #004085;
        color: #ffffff;
        text-align: center;
        padding: 15px;
        font-size: 20px;
        font-weight: bold;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
      }
      .content {
        padding: 20px;
        font-size: 16px;
        color: #333333;
      }
      .highlight {
        font-weight: bold;
        color: #d9534f;
      }
      .footer {
        margin-top: 20px;
        text-align: center;
        font-size: 14px;
        color: #777777;
      }
    </style>
  </head>
  <body>
    <div class="email-container">
      <div class="header">
        Stock Alert: {{ stock_symbol }} Down 10%
      </div>
      <div class="content">
        <p>Dear Investor,</p>
        <p>The stock <strong>{{ stock_symbol }}</strong> has had a P/E change today.</p>
        <p>
          <strong>Current Price:</strong> <span class="highlight">${{ current_price }}</span><br>
          <strong>P/E Percentage Change:</strong> <span class="highlight">{{ pe_change }}%</span><br>
          <strong>P/E Ratio:</strong> {{ pe_ratio }}
        </p>
        <p>Stay informed and make strategic decisions.</p>
      </div>
      <div class="footer">
        &copy; 2025 Retail Trade Scanner | This is an automated notification.
      </div>
    </div>
  </body>
</html>
"""

# Function to send stock notifications
def send_stock_notifications():
    try:
        ensure_json_files()  # Ensure files exist before reading

        # Load JSON data
        with open(EMAILS_FILE, 'r') as f:
            email_data = json.load(f)
        with open(STOCKS_FILE, 'r') as f:
            stock_data = json.load(f)
        with open(USED_TICKERS_FILE, 'r') as f:
            used_tickers_data = json.load(f)

        used_tickers = set(used_tickers_data["used_tickers"])
        new_stocks = [s for s in stock_data["stocks"] if s["Ticker"] not in used_tickers]

        if not new_stocks:
            print("No new stocks to send.")
            return

        # Initialize SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)

        template = Template(html_template)

        for stock in new_stocks:
            ticker = stock["Ticker"]
            percentage_change = stock["Price Change Today"]

            # Render email content
            filled_html = template.render(
                stock_symbol=ticker,
                current_price=ticker_info.get("Current Price", "N/A"),
                pe_ratio=ticker_info.get("P/E Ratio", "N/A"),
                pe_change=ticker_info.get("P/E Change (3 Mon)", "N/A"),
            )

            for recipient in email_data["emails"]:
                msg = MIMEMultipart()
                msg['From'] = SENDER_EMAIL
                msg['To'] = recipient
                msg['Subject'] = f'Stock Movement Notification for {ticker}'

                msg.attach(MIMEText(filled_html, 'html'))
                server.sendmail(SENDER_EMAIL, recipient, msg.as_string())

            # Move stock to used tickers list
            used_tickers.add(ticker)

            print(f"Sent email for {ticker}")

        # Update used tickers file with correct format
        with open(USED_TICKERS_FILE, 'w') as f:
            json.dump({"used_tickers": list(used_tickers)}, f, indent=4)

        server.quit()

    except Exception as e:
        print(f"Error sending notifications: {str(e)}")

# Periodic function to check every 5 minutes
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
            # Reset used tickers list at midnight
            with open(USED_TICKERS_FILE, 'w') as f:
                json.dump({"used_tickers": []}, f, indent=4)
            print("Reset used tickers at midnight.")
        time.sleep(60)  # Check every minute

# Start background threads for periodic checks and resetting used tickers
reset_thread = threading.Thread(target=reset_used_tickers, daemon=True)
reset_thread.start()

check_thread = threading.Thread(target=periodic_check, daemon=True)
check_thread.start()

if __name__ == '__main__':
    send_stock_notifications()  # Run once at startup
import threading

app = Flask(__name__)

# SMTP Configuration
SMTP_SERVER = 'smtp.ionos.com'
SMTP_PORT = 587
SENDER_EMAIL = 'noreply.rts@retailtradescanner.com'
SENDER_PASSWORD = 'pIqvin-persi2-pibsij'

# Paths to JSON files
BASE_DIR = r"/home/ec2-user/Stock-Scanner-Project/"
JSON_FILE = os.path.join(BASE_DIR, 'json', '20_pe_de.json')
STOCK_INFO_FILE = os.path.join(BASE_DIR, 'json', 'Filtered_pe_20_de.json')
USED_TICKERS_FILE = os.path.join(BASE_DIR, 'json', 'ut_pe_2o_de.json')

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
@app.route('/subscribe-pe-20-de', methods=['POST'])
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
            <h1>Stock <strong>{{ stock_symbol }}</strong> P/E Decrease Twenty Percent Notification</h1>
            <p>Dear Investor,</p>
            <p>The stock <strong>{{ stock_symbol }}</strong> has experienced a P/E movement.</p>
            <p>Current Price: ${{ current_price }}</p>
            <p>P/E Change: {{ pe_change }}%</p>
            <p>P/E Ratio: {{ pe }}%</p>
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
                pe=ticker_info.get("P/E Ratio", "N/A"),
                pe_change=ticker_info.get("P/E Change (3 Mon)", "N/A"),
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
