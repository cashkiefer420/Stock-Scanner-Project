import os
import json
import smtplib
import time
from jinja2 import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# SMTP Configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = 'noreply.retailtradescanner@gmail.com'
SENDER_PASSWORD = 'sufvpztttmjjivprp'

# Paths to JSON files
BASE_DIR = r"/home/ec2-user/Stock-Scanner-Project/"
JSON_FOLDER = os.path.join(BASE_DIR, 'json')
EMAILS_FILE = os.path.join(JSON_FOLDER, '10_price_de.json')
STOCKS_FILE = os.path.join(JSON_FOLDER, 'Filtered_price_10_de.json')
USED_TICKERS_FILE = os.path.join(JSON_FOLDER, 'ut_price_10_de.json')

# Ensure JSON files exist
def ensure_json_file(filepath, default_data):
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump(default_data, f, indent=4)

ensure_json_file(EMAILS_FILE, {"emails": []})
ensure_json_file(STOCKS_FILE, {"stocks": []})
ensure_json_file(USED_TICKERS_FILE, {"used_tickers": []})

# Email template
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

# Function to send stock notifications
def send_stock_notifications():
    try:
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
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        template = Template(html_template)

        for stock in new_stocks:
            ticker = stock["Ticker"]
            percentage_change = stock["Price Change Today"]

            # Render email content
            filled_html = template.render(
                stock_symbol=ticker,
                current_price=stock.get("Current Price", "N/A"),
                percentage_change=percentage_change,
                volume_today=stock.get("Volume Today", "N/A"),
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

        # Update used tickers file
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
            with open(USED_TICKERS_FILE, 'w') as f:
                json.dump({"used_tickers": []}, f, indent=4)
            print("Reset used tickers at midnight.")
        time.sleep(60)  # Check every minute

# Start background threads
import threading

reset_thread = threading.Thread(target=reset_used_tickers, daemon=True)
reset_thread.start()

check_thread = threading.Thread(target=periodic_check, daemon=True)
check_thread.start()

if __name__ == '__main__':
    send_stock_notifications()  # Run once at startup