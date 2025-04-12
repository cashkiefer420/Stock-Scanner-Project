import yfinance as yf
import json
import logging
import boto3
import os
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Config
S3_BUCKET = "your-stock-bucket"
TICKER_FILE = "formatted_tickers.json"
EXPORT_FILE = "stock_data_export.json"
PE_FILE = "PE_num.json"
MC_FILE = "MC_num.json"
SHARES_FILE = "shares_num.json"
COMPANY_FILE = "company_names.json"

s3 = boto3.client('s3')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def s3_load_json(key):
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=key)
        return json.loads(response['Body'].read())
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return {}
        raise

def s3_save_json(key, data):
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=json.dumps(data, indent=4).encode('utf-8'))

def calculate_percent_change(new, old):
    try:
        if old == 0 or old == 'N/A':
            return 'N/A'
        return round(((new - old) / old) * 100, 2)
    except:
        return 'N/A'

def update_daily_value(data, ticker, value):
    today = datetime.now().strftime("%Y-%m-%d")
    if ticker not in data:
        data[ticker] = {}
    if today not in data[ticker]:
        data[ticker][today] = value
    return data[ticker][today]

def get_today_value(data, ticker):
    today = datetime.now().strftime("%Y-%m-%d")
    return data.get(ticker, {}).get(today, 'N/A')

def get_historical_value(data, ticker, days_ago):
    target_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    return data.get(ticker, {}).get(target_date, 'N/A')

def fetch_price(ticker, pe_data, mc_data, shares_data, company_data):
    try:
        stock = yf.Ticker(ticker)
        hist_data = stock.history(period="3mo")
        if hist_data.empty:
            return {'Ticker': ticker, 'Current Price': 'N/A'}

        info = stock.info

        pe = update_daily_value(pe_data, ticker, info.get('trailingPE', 'N/A'))
        mc = update_daily_value(mc_data, ticker, info.get('marketCap', 'N/A'))
        shares = update_daily_value(shares_data, ticker, info.get('sharesOutstanding', 'N/A'))

        if ticker not in company_data:
            company_data[ticker] = info.get('longName', 'N/A')

        current_price = hist_data['Close'].iloc[-1]
        prev_price = hist_data['Close'].iloc[-2]
        volume_today = hist_data['Volume'].iloc[-1]
        avg_volume = info.get('averageVolume', 'N/A')

        bid_ask = f"{info.get('bid', 'N/A')} - {info.get('ask', 'N/A')}"
        day_range = f"{info.get('dayLow', 'N/A')} - {info.get('dayHigh', 'N/A')}"
        dvav = round(volume_today / avg_volume, 4) if avg_volume not in [0, 'N/A'] else 'N/A'
        dvsa = round(volume_today / shares, 4) if shares not in [0, 'N/A'] else 'N/A'
        pe_change = calculate_percent_change(pe, get_historical_value(pe_data, ticker, 90))
        mc_change = calculate_percent_change(mc, current_price * shares if current_price != 'N/A' and shares != 'N/A' else 'N/A')

        week_data = stock.history(start=datetime.today() - timedelta(days=7))
        week_change = calculate_percent_change(current_price, week_data['Close'].iloc[0]) if not week_data.empty else 'N/A'

        year_data = stock.history(start=datetime(datetime.now().year, 1, 1))
        year_change = calculate_percent_change(current_price, year_data['Close'].iloc[0]) if not year_data.empty else 'N/A'

        result = {
            'Ticker': ticker,
            'Company Name': company_data[ticker],
            'Current Price': round(current_price, 2),
            'Price Change Today': calculate_percent_change(current_price, prev_price),
            'Price Change Week': week_change,
            'Price Change Month': calculate_percent_change(current_price, hist_data['Close'].iloc[0]),
            'Price Change Year': year_change,
            'Bid Ask Spread': bid_ask,
            'Days Range': day_range,
            'Volume Today': volume_today,
            'Avg Volume (3 mon)': avg_volume,
            'DVAV (Day Volume Over Avg Volume)': dvav,
            'P/E Ratio': pe,
            'P/E Change (3 Mon)': pe_change,
            'Shares Available': shares,
            'Market Cap': mc,
            'Market Cap Change (3 Mon)': mc_change,
            'Dividend Yield': info.get('dividendYield', 'N/A'),
            'One Year Target': info.get('targetMeanPrice', 'N/A'),
            'DVSA (Vol Today / Shares)': dvsa,
            'Last Update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        return result

    except Exception as e:
        logging.exception(f"Error processing ticker {ticker}")
        return {'Ticker': ticker, 'Current Price': 'N/A'}

def lambda_handler(event, context):
    tickers = s3_load_json(TICKER_FILE).get("tickers", [])
    if not tickers:
        return {"message": "No tickers found."}

    pe_data = s3_load_json(PE_FILE)
    mc_data = s3_load_json(MC_FILE)
    shares_data = s3_load_json(SHARES_FILE)
    company_data = s3_load_json(COMPANY_FILE)

    results = [fetch_price(t, pe_data, mc_data, shares_data, company_data) for t in tickers]

    # Save everything back to S3
    s3_save_json(PE_FILE, pe_data)
    s3_save_json(MC_FILE, mc_data)
    s3_save_json(SHARES_FILE, shares_data)
    s3_save_json(COMPANY_FILE, company_data)
    s3_save_json(EXPORT_FILE, results)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Successfully updated {len(results)} tickers.',
            'timestamp': datetime.now().isoformat()
        })
    }