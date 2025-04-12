import yfinance as yf
import json
import logging
import os
from datetime import datetime, timedelta

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Lambda can only write to /tmp
BASE_DIR         = "/tmp"
TICKER_FILE      = os.path.join(BASE_DIR, "formatted_tickers.json")
EXPORT_FILE      = os.path.join(BASE_DIR, "stock_data_export.json")
PE_FILE          = os.path.join(BASE_DIR, "PE_num.json")
MC_FILE          = os.path.join(BASE_DIR, "MC_num.json")

def load_json(path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def pct_change(new, old):
    try:
        if old in (0, 'N/A'):
            return 'N/A'
        return round(((new - old) / old) * 100, 2)
    except:
        return 'N/A'

def update_daily_record(path, ticker, record_dict):
    """
    In path (PE_FILE or MC_FILE), under data[ticker][today] store record_dict.
    record_dict can contain multiple keys: e.g. {'P/E':..., 'Shares Available':..., 'Company Name':...}
    """
    data  = load_json(path)
    today = datetime.now().strftime("%Y-%m-%d")
    if ticker not in data:
        data[ticker] = {}
    # only write once per day
    if today not in data[ticker]:
        data[ticker][today] = record_dict
        save_json(path, data)
    return data[ticker][today]

def get_historical(path, ticker, days_ago, key):
    data = load_json(path).get(ticker, {})
    target = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    # if exact date missing, pick closest earlier date
    dates = sorted(d for d in data.keys() if d <= target)
    if not dates:
        return 'N/A'
    return data[dates[-1]].get(key, 'N/A')

def fetch_price(ticker):
    try:
        stock     = yf.Ticker(ticker)
        hist      = stock.history(period="3mo")
        if hist.empty:
            return {'Ticker': ticker, 'Current Price': 'N/A', 'Last Update': datetime.utcnow().isoformat()}

        info          = stock.info
        company_name  = info.get('longName', 'N/A')
        pe_val        = info.get('trailingPE', 'N/A')
        mc_val        = info.get('marketCap', 'N/A')
        shares_avail  = info.get('sharesOutstanding', 'N/A')

        # 1) Update PE record (once/day), storing company & shares alongside
        pe_record = update_daily_record(
            PE_FILE, ticker,
            {
                'P/E': pe_val,
                'Shares Available': shares_avail,
                'Company Name': company_name
            }
        )
        # 2) Update MC record (once/day), storing company & shares alongside
        mc_record = update_daily_record(
            MC_FILE, ticker,
            {
                'Market Cap': mc_val,
                'Shares Available': shares_avail,
                'Company Name': company_name
            }
        )

        # pull reused values out of those records
        pe_today      = pe_record.get('P/E', 'N/A')
        mc_today      = mc_record.get('Market Cap', 'N/A')
        shares_today  = pe_record.get('Shares Available', 'N/A')
        name_today    = pe_record.get('Company Name', 'N/A')

        # price & volume
        price_now     = hist['Close'].iloc[-1]
        price_prev    = hist['Close'].iloc[-2]
        vol_today     = hist['Volume'].iloc[-1]
        avg_vol       = info.get('averageVolume', 'N/A')

        # bid/ask & day range
        bid_ask       = f"{info.get('bid','N/A')} - {info.get('ask','N/A')}"
        day_rng       = f"{info.get('dayLow','N/A')} - {info.get('dayHigh','N/A')}"

        # percent changes
        pct_today     = pct_change(price_now, price_prev)
        pct_week      = pct_change(price_now, hist['Close'].iloc[-5])
        pct_month     = pct_change(price_now, hist['Close'].iloc[0])
        start_year    = datetime(datetime.now().year,1,1)
        yr_hist       = stock.history(start=start_year)
        pct_year      = pct_change(price_now, yr_hist['Close'].iloc[0]) if not yr_hist.empty else 'N/A'

        # volume ratios
        dvav          = round(vol_today/avg_vol,4) if avg_vol not in [0,'N/A'] else 'N/A'
        dvsa          = round(vol_today/shares_today,4) if shares_today not in [0,'N/A'] else 'N/A'

        # 3‑month changes for PE & MC
        pe_3mo_ago   = get_historical(PE_FILE, ticker, 90, 'P/E')
        mc_3mo_ago   = get_historical(MC_FILE, ticker, 90, 'Market Cap')
        pe_change_3m = pct_change(pe_today, pe_3mo_ago)
        mc_change_3m = pct_change(mc_today, mc_3mo_ago)

        return {
            'Ticker': ticker,
            'Company Name': name_today,
            'Current Price': round(price_now,2),
            'Price Change Today': pct_today,
            'Price Change Week': pct_week,
            'Price Change Month': pct_month,
            'Price Change Year': pct_year,
            'Bid Ask Spread': bid_ask,
            'Days Range': day_rng,
            'Volume Today': vol_today,
            'Avg Volume (3 mon)': avg_vol,
            'DVAV (Day Volume Over Average Volume)': dvav,
            'P/E Ratio': pe_today,
            'P/E Change (3 Mon)': pe_change_3m,
            'Shares Available': shares_today,
            'Market Cap': mc_today,
            'Market Cap Change (3 Mon)': mc_change_3m,
            'Dividend Yield': info.get('dividendYield','N/A'),
            'One Year Target': info.get('targetMeanPrice','N/A'),
            'DVSA (Volume Today Over Shares Available)': dvsa,
            'Last Update': datetime.utcnow().isoformat()
        }

    except Exception:
        logging.exception(f"Error processing {ticker}")
        return {'Ticker': ticker, 'Current Price': 'N/A'}

def load_tickers():
    try:
        with open(TICKER_FILE, 'r') as f:
            return json.load(f).get('tickers', [])
    except:
        logging.error("Unable to load tickers.")
        return []

def lambda_handler(event, context):
    tickers = load_tickers()
    if not tickers:
        return {'statusCode': 400, 'body': 'No tickers found.'}

    results = [fetch_price(t) for t in tickers]
    save_json(EXPORT_FILE, results)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Updated {len(results)} tickers',
            'timestamp': datetime.utcnow().isoformat()
        })
    }