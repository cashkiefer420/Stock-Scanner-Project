import yfinance as yf
import json
import logging
import boto3
from datetime import datetime, timedelta

# Logging setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# S3 setup
s3 = boto3.client("s3")
BUCKET_NAME = "exportbucket--use2-az1--x-s3"
EXPORT_FILE_KEY = "stock_data_export.json"
PE_FILE_KEY = "PE_num.json"
MC_FILE_KEY = "MC_num.json"

def read_s3_json(key):
    """Reads JSON data from an S3 bucket."""
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
        return json.loads(response['Body'].read().decode('utf-8'))
    except s3.exceptions.NoSuchKey:
        logger.error(f"File {key} not found in S3 bucket.")
        return {}
    except Exception as e:
        logger.error(f"Error reading {key} from S3: {e}")
        return {}

def write_s3_json(key, data):
    """Writes JSON data to an S3 bucket."""
    try:
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=json.dumps(data, indent=4).encode('utf-8'))
    except Exception as e:
        logger.error(f"Error writing {key} to S3: {e}")

def calculate_percent_change(new, old):
    """Calculates the percentage change between two values."""
    try:
        if old == 0 or old == 'N/A':
            return 'N/A'
        return round(((new - old) / old) * 100, 2)
    except Exception as e:
        logger.error(f"Error calculating percent change: {e}")
        return 'N/A'

def update_daily_value(data, ticker, value, today):
    """Updates daily value for a ticker in the data."""
    if ticker not in data or today not in data[ticker]:
        if ticker not in data:
            data[ticker] = {}
        data[ticker][today] = value
    return data[ticker][today]

def get_historical_value(data, ticker, days_ago):
    """Gets the historical value of a ticker from a specified number of days ago."""
    target_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    return data.get(ticker, {}).get(target_date, 'N/A')

def fetch_price(ticker, pe_data, mc_data, export_data, today):
    """Fetches the latest price and other information for a given ticker."""
    try:
        stock = yf.Ticker(ticker)
        hist_data = stock.history(period="3mo")
        if hist_data.empty:
            return None

        info = stock.info
        current_price = hist_data['Close'].iloc[-1]
        prev_price = hist_data['Close'].iloc[-2]
        volume_today = hist_data['Volume'].iloc[-1]
        avg_volume = info.get('averageVolume', 'N/A')

        export_entry = next((item for item in export_data if item['Ticker'] == ticker), {})
        last_update = export_entry.get("Last Update", "")[:10]

        # Preserve existing values for specific fields
        shares = export_entry.get('Shares Available', 'N/A')
        dividend_yield = export_entry.get('Dividend Yield', 'N/A')
        one_year_target = export_entry.get('One Year Target', 'N/A')

        # Update only if the last update is not today
        if today != last_update:
            shares = info.get('sharesOutstanding', 'N/A')
            dividend_yield = info.get('dividendYield', 'N/A')
            one_year_target = info.get('targetMeanPrice', 'N/A')

        company_name = export_entry.get('Company Name', 'N/A')  # Preserve the existing company name

        pe = update_daily_value(pe_data, ticker, info.get('trailingPE', 'N/A'), today)
        mc = update_daily_value(mc_data, ticker, info.get('marketCap', 'N/A'), today)

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

        return {
            'Ticker': ticker,
            'Company Name': company_name,  # Preserve the existing company name
            'Current Price': round(current_price, 2),
            'Price Change Today': calculate_percent_change(current_price, prev_price),
            'Price Change Week': week_change,
            'Price Change Month': calculate_percent_change(current_price, hist_data['Close'].iloc[0]),
            'Price Change Year': year_change,
            'Bid Ask Spread': bid_ask,
            'Days Range': day_range,
            'Volume Today': volume_today,
            'Avg Volume (3 mon)': avg_volume,
            'DVAV (Day Volume Over Average Volume)': dvav,
            'P/E Ratio': pe,
            'P/E Change (3 Mon)': pe_change,
            'Shares Available': shares,  # Updated once a day
            'Market Cap': mc,
            'Market Cap Change (3 Mon)': mc_change,
            'Dividend Yield': dividend_yield,  # Updated once a day
            'One Year Target': one_year_target,  # Updated once a day
            'DVSA (Volume Today Over Shares Available)': dvsa,
            'Last Update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        logger.exception(f"Error processing {ticker}")
        return None

def lambda_handler(event, context):
    """AWS Lambda entry point."""
    today = datetime.now().strftime("%Y-%m-%d")

    # Read data from the stock_data_export.json file in S3
    export_data = read_s3_json(EXPORT_FILE_KEY)
    tickers = [entry['Ticker'] for entry in export_data if 'Ticker' in entry]  # Extract tickers from export data

    # Read additional data files
    pe_data = read_s3_json(PE_FILE_KEY)
    mc_data = read_s3_json(MC_FILE_KEY)

    results = []
    for ticker in tickers:
        data = fetch_price(ticker, pe_data, mc_data, export_data, today)
        if data:
            results.append(data)

    # Write updated data back to S3
    write_s3_json(EXPORT_FILE_KEY, results)
    write_s3_json(PE_FILE_KEY, pe_data)
    write_s3_json(MC_FILE_KEY, mc_data)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f"Updated {len(results)} tickers.",
            'timestamp': datetime.now().isoformat()
        })
    }
