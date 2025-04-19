import orjson
import yfinance as yf
import numpy as np
import boto3
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tenacity import retry, stop_after_attempt, wait_fixed
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# S3 setup
S3_BUCKET = "exportbucket--use2-az1--x-s3"
REGION = "us-east-2"
s3_client = boto3.client("s3", region_name=REGION)

# S3 keys (root level, no 'json/' prefix)
FORMATTED_TICKERS_KEY = "formatted_tickers.json"
PE_KEY = "PE_num.json"
MARKETCAP_KEY = "MC_num.json"
EXPORT_KEY = "stock_data_export.json"
TICKERS_NAMES_KEY = "Tickers&Names.json"

# JSON helpers
def read_json_file_s3(key):
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
        return orjson.loads(response["Body"].read())
    except ClientError as e:
        logger.error(f"S3 read error for {key}: {e}")
        return {}

def write_json_file_s3(key, data):
    try:
        def convert_numpy(obj):
            if isinstance(obj, (np.integer, int)): return int(obj)
            elif isinstance(obj, (np.floating, float)): return float(obj)
            elif isinstance(obj, np.ndarray): return obj.tolist()
            raise TypeError(f"Type {type(obj)} not serializable")

        content = orjson.dumps(data, default=convert_numpy, option=orjson.OPT_INDENT_2)
        s3_client.put_object(Bucket=S3_BUCKET, Key=key, Body=content)
    except Exception as e:
        logger.error(f"S3 write error for {key}: {e}")

# Ticker update function
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def update_stock_data(ticker, pe_data, mc_data, existing_data_map):
    try:
        t = yf.Ticker(ticker)
        info = t.info

        # Remove if delisted or invalid
        if not info or 'regularMarketPrice' not in info:
            logger.warning(f"Skipping {ticker} - no valid info")
            return None

        # Daily price changes
        today_price = info.get("regularMarketPrice")
        yesterday_price = info.get("previousClose")
        if not today_price or not yesterday_price:
            logger.warning(f"Skipping {ticker} - insufficient price data")
            return None

        daily_change = (today_price - yesterday_price) / yesterday_price * 100

        # Historical prices
        hist = t.history(period="5d")
        if hist.empty or "Close" not in hist:
            logger.warning(f"Skipping {ticker} - no historical data")
            return None

        hist_close = hist["Close"]
        pct_changes = hist_close.pct_change().dropna() * 100
        avg_pct_change = pct_changes.mean()
        min_pct_change = pct_changes.min()
        max_pct_change = pct_changes.max()

        # Volume analysis
        volumes = hist["Volume"]
        dvsa = (volumes.diff().dropna() / volumes.shift(1).dropna()).mean() * 100
        dvav = volumes.mean()

        # Use existing company name
        existing_entry = existing_data_map.get(ticker, {})
        company_name = existing_entry.get("Company Name", "")
        is_etf = existing_entry.get("Is ETF", False)

        # Cache PE, MC, Shares
        pe = pe_data.get(ticker)
        if pe is None:
            pe = info.get("trailingPE")
            if pe is not None:
                pe_data[ticker] = pe

        mc = mc_data.get(ticker)
        if mc is None:
            mc = info.get("marketCap")
            if mc is not None:
                mc_data[ticker] = mc

        shares_outstanding = info.get("sharesOutstanding")

        return {
            "Ticker": ticker,
            "Company Name": company_name,
            "Is ETF": is_etf,
            "PE": pe,
            "Market Cap": mc,
            "Shares Outstanding": shares_outstanding,
            "Price Change % (1D)": round(daily_change, 2),
            "Price Change % (Avg 5D)": round(avg_pct_change, 2),
            "Price Change % (Max 5D)": round(max_pct_change, 2),
            "Price Change % (Min 5D)": round(min_pct_change, 2),
            "DVSA (Δ Volume % Avg)": round(dvsa, 2),
            "DVAV (Daily Avg Volume)": int(dvav),
            "Last Update": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        }
    except Exception as e:
        logger.error(f"Error processing {ticker}: {e}")
        return None

def sync_tickers_and_names():
    tickers_names = read_json_file_s3(TICKERS_NAMES_KEY)
    formatted_tickers = read_json_file_s3(FORMATTED_TICKERS_KEY)

    names_dict = {item["Ticker"]: item["Company Name"] for item in tickers_names}
    tickers_list = formatted_tickers.get("tickers", [])
    updated_tickers = []

    for t in tickers_list:
        ticker_symbol = t.get("Ticker") if isinstance(t, dict) else t
        updated_tickers.append({
            "Ticker": ticker_symbol,
            "Company Name": names_dict.get(ticker_symbol, "")
        })

    write_json_file_s3(FORMATTED_TICKERS_KEY, {"tickers": updated_tickers})

def main():
    sync_tickers_and_names()

    tickers = read_json_file_s3(FORMATTED_TICKERS_KEY).get("tickers", [])
    tickers = [t.get("Ticker") if isinstance(t, dict) else t for t in tickers]

    pe_data = read_json_file_s3(PE_KEY)
    mc_data = read_json_file_s3(MARKETCAP_KEY)
    export_data = read_json_file_s3(EXPORT_KEY)

    existing_data_map = {entry["Ticker"]: entry for entry in export_data}

    updated_data = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(update_stock_data, ticker, pe_data, mc_data, existing_data_map): ticker for ticker in tickers}
        for future in as_completed(futures):
            result = future.result()
            if result:
                updated_data.append(result)

    for entry in updated_data:
        existing_data_map[entry["Ticker"]] = entry

    write_json_file_s3(EXPORT_KEY, list(existing_data_map.values()))
    write_json_file_s3(PE_KEY, pe_data)
    write_json_file_s3(MARKETCAP_KEY, mc_data)

if __name__ == "__main__":
    main()