
import os
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
    "30_mc_de.json": {"emails": []},
    "Filtered_market_cap_30_de.json": {"stocks": []},
    "ut_30_mc_de.json": {"used_tickers": []}
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
EMAILS_FILE = os.path.join(JSON_FOLDER, "30_mc_de.json")
STOCKS_FILE = os.path.join(JSON_FOLDER, "Filtered_market_cap_30_de.json")
USED_TICKERS_FILE = os.path.join(JSON_FOLDER, "ut_30_mc_de.json")

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
        Stock Alert: {{ stock_symbol }} Market Cap Decrease 20%
      </div>
      <div class="content">
        <p>Dear Investor,</p>
        <p>The stock <strong>{{ stock_symbol }}</strong> has had a Market Cap change today.</p>
        <p>
          <strong>Current Price:</strong> <span class="highlight">${{ current_price }}</span><br>
          <strong>Market Cap Percentage Change:</strong> <span class="highlight">{{ mc_change }}%</span><br>
          <strong>Market Cap:</strong> {{ mc }}
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
                current_price=ticker_defo.get("Current Price", "N/A"),
                mc=ticker_defo.get("Market Cap", "N/A"),
                mc_change=ticker_defo.get("Market Cap Change (3 Mon)", "N/A"),
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
