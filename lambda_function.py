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
TICKER_FILE_KEY = "formatted_tickers.json"
EXPORT_FILE_KEY = "stock_data_export.json"
PE_FILE_KEY = "PE_num.json"
MC_FILE_KEY = "MC_num.json"

def read_s3_json(key):
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
        return json.loads(response['Body'].read().decode('utf-8'))
    except s3.exceptions.NoSuchKey:
        return {}
    except Exception as e:
        logger.error(f"Error reading {key} from S3: {e}")
        return {}

def write_s3_json(key, data):
    try:
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=json.dumps(data, indent=4).encode('utf-8'))
    except Exception as e:
        logger.error(f"Error writing {key} to S3: {e}")

def calculate_percent_change(new, old):
    try:
        if old == 0 or old == 'N/A':
            return 'N/A'
        return round(((new - old) / old) * 100, 2)
    except:
        return 'N/A'

def update_daily_value(data, ticker, value, today):
    if ticker not in data or today not in data[ticker]:
        if ticker not in data:
            data[ticker] = {}
        data[ticker][today] = value
    return data[ticker][today]

def get_historical_value(data, ticker, days_ago):
    target_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    return data.get(ticker, {}).get(target_date, 'N/A')

def fetch_price(ticker, pe_data, mc_data, export_data, today):
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

        shares = export_entry.get('Shares Available')
        company_name = export_entry.get('Company Name')

        if today != last_update:
            shares = info.get('sharesOutstanding', 'N/A')
            company_name = company_name or info.get('longName', 'N/A')

        # Handle P/E Ratio
        trailing_pe = info.get('trailingPE')
        pe = None
        if trailing_pe not in [None, 'N/A']:
            pe = update_daily_value(pe_data, ticker, trailing_pe, today)

        # Handle Market Cap
        market_cap = info.get('marketCap')
        mc = None
        if market_cap not in [None, 'N/A']:
            mc = update_daily_value(mc_data, ticker, market_cap, today)

        # Handle Shares Available
        if shares in [None, 'N/A']:
            shares = None

        bid_ask = f"{info.get('bid', 'N/A')} - {info.get('ask', 'N/A')}"
        day_range = f"{info.get('dayLow', 'N/A')} - {info.get('dayHigh', 'N/A')}"
        dvav = round(volume_today / avg_volume, 4) if avg_volume not in [0, 'N/A'] else 'N/A'
        dvsa = round(volume_today / shares, 4) if shares not in [0, 'N/A'] else 'N/A'
        pe_change = calculate_percent_change(pe, get_historical_value(pe_data, ticker, 90)) if pe else 'N/A'
        mc_change = calculate_percent_change(mc, current_price * shares if current_price not in [None, 'N/A'] and shares not in [None, 'N/A'] else 'N/A') if mc else 'N/A'

        week_data = stock.history(start=datetime.today() - timedelta(days=7))
        week_change = calculate_percent_change(current_price, week_data['Close'].iloc[0]) if not week_data.empty else 'N/A'

        year_data = stock.history(start=datetime(datetime.now().year, 1, 1))
        year_change = calculate_percent_change(current_price, year_data['Close'].iloc[0]) if not year_data.empty else 'N/A'

        # Build the result dictionary, skipping invalid fields
        result = {
            'Ticker': ticker,
            'Company Name': company_name,
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
            'DVSA (Volume Today Over Shares Available)': dvsa,
            'Last Update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Conditionally add optional fields
        if pe is not None:
            result['P/E Ratio'] = pe
            result['P/E Change (3 Mon)'] = pe_change
        if mc is not None:
            result['Market Cap'] = mc
            result['Market Cap Change (3 Mon)'] = mc_change
        if shares is not None:
            result['Shares Available'] = shares
        if info.get('dividendYield') is not None:
            result['Dividend Yield'] = info.get('dividendYield')
        if info.get('targetMeanPrice') is not None:
            result['One Year Target'] = info.get('targetMeanPrice')

        return result

    except Exception as e:
        logger.exception(f"Error processing {ticker}")
        return None

def lambda_handler(event, context):
    today = datetime.now().strftime("%Y-%m-%d")

    tickers_data = read_s3_json(TICKER_FILE_KEY)
    tickers = tickers_data.get("tickers", [])

    export_data = read_s3_json(EXPORT_FILE_KEY)
    pe_data = read_s3_json(PE_FILE_KEY)
    mc_data = read_s3_json(MC_FILE_KEY)

    results = []
    for ticker in tickers:
        data = fetch_price(ticker, pe_data, mc_data, export_data, today)
        if data:
            results.append(data)

    # Clean up today's invalid entries in pe_data and mc_data
    for data_dict in [pe_data, mc_data]:
        for ticker, dates in list(data_dict.items()):
            if today in dates and dates[today] in [None, 'N/A']:
                del dates[today]  # Remove today's invalid entry

    # Write the filtered data back to S3
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
