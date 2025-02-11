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
JSON_FILE = os.path.join(JSON_FOLDER, '10_price_de.json')
STOCK_INFO_FILE = os.path.join(JSON_FOLDER, 'Filtered_price_10_de.json')
USED_TICKERS_FILE = os.path.join(JSON_FOLDER, 'ut_price_10_de.json')

# Ensure JSON files exist
def ensure_json_file(filepath, default_data):
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump(default_data, f, indent=4)

ensure_json_file(JSON_FILE, {"emails": []})
ensure_json_file(USED_TICKERS_FILE, {"used_tickers": []})
ensure_json_file(STOCK_INFO_FILE, {"stocks": []})

def send_stock_notifications():
    try:
        with open(JSON_FILE, 'r') as f:
            email_data = json.load(f)
        with open(USED_TICKERS_FILE, 'r') as f:
            used_tickers_data = json.load(f)
        with open(STOCK_INFO_FILE, 'r') as f:
            stock_data = json.load(f)

        emails = email_data.get("emails", [])
        if not emails:
            print(f"[{datetime.now()}] No subscribers.")
            return

        new_stocks = []
        
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
        template = Template(html_template)

        for ticker_info in stock_data.get("stocks", []):
            ticker = ticker_info.get("Ticker", "Unknown")
            percentage_change = ticker_info.get("Price Change Today", 0)

            if ticker in used_tickers_data["used_tickers"] or percentage_change > -10:
                continue

            new_stocks.append(ticker)

        if not new_stocks:
            print(f"[{datetime.now()}] No new stock alerts.")
            return

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)

            for ticker in new_stocks:
                ticker_info = next((s for s in stock_data["stocks"] if s["Ticker"] == ticker), {})
                filled_html = template.render(
                    stock_symbol=ticker,
                    current_price=ticker_info.get("Current Price", "N/A"),
                    percentage_change=ticker_info.get("Price Change Today", "N/A"),
                    volume_today=ticker_info.get("Volume Today", "N/A"),
                )

                for recipient in emails:
                    msg = MIMEMultipart()
                    msg['From'] = SENDER_EMAIL
                    msg['To'] = recipient
                    msg['Subject'] = f'Stock Alert: {ticker} Down 10%+'
                    msg.attach(MIMEText(filled_html, 'html'))
                    server.sendmail(SENDER_EMAIL, recipient, msg.as_string())

                used_tickers_data["used_tickers"].append(ticker)

        with open(USED_TICKERS_FILE, 'w') as f:
            json.dump(used_tickers_data, f, indent=4)

        print(f"[{datetime.now()}] Sent notifications for: {', '.join(new_stocks)}")

    except Exception as e:
        print(f"[{datetime.now()}] Error sending notifications: {str(e)}")

# Periodic check function
def periodic_check():
    while True:
        try:
            send_stock_notifications()
        except Exception as e:
            print(f"[{datetime.now()}] Error in periodic check: {str(e)}")
        time.sleep(300)  # Wait 5 minutes

# Reset used tickers at midnight
def reset_used_tickers():
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            with open(USED_TICKERS_FILE, 'w') as f:
                json.dump({"used_tickers": []}, f, indent=4)
            print(f"[{datetime.now()}] Reset used tickers.")
        time.sleep(60)  # Check every minute

# Start background threads
import threading
reset_thread = threading.Thread(target=reset_used_tickers, daemon=True)
reset_thread.start()

check_thread = threading.Thread(target=periodic_check, daemon=True)
check_thread.start()

# Keep script running
while True:
    time.sleep(10)
