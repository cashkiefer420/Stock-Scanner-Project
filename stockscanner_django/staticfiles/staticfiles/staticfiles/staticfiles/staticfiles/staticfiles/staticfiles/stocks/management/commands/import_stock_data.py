import os
import json
import random
import signal
import logging
import time
from datetime import datetime, timedelta
import pytz
import pandas as pd
import yfinance as yf
import numpy as np

from django.core.management.base import BaseCommand
from stocks.models import StockAlert

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class TimeoutException(Exception): pass
def timeout_handler(signum, frame): raise TimeoutException()
signal.signal(signal.SIGALRM, timeout_handler)

def compute_note(pe, mc_change, dvsa, price_change):
    note_parts = []

    if dvsa:
        if dvsa >= 1.0:
            note_parts.append("dvsa volume 100")
        elif dvsa >= 0.5:
            note_parts.append("dvsa volume 50")

    if mc_change:
        if mc_change >= 0.30:
            note_parts.append("market cap increase 30")
        elif mc_change >= 0.20:
            note_parts.append("market cap increase 20")
        elif mc_change >= 0.10:
            note_parts.append("market cap increase 10")
        elif mc_change <= -0.30:
            note_parts.append("market cap decrease 30")
        elif mc_change <= -0.20:
            note_parts.append("market cap decrease 20")
        elif mc_change <= -0.10:
            note_parts.append("market cap decrease 10")

    if pe is not None:
        if pe >= 30:
            note_parts.append("pe increase 30")
        elif pe >= 20:
            note_parts.append("pe increase 20")
        elif pe >= 10:
            note_parts.append("pe increase 10")
        elif pe <= 10:
            note_parts.append("pe decrease 10")

    if price_change:
        if price_change <= -20:
            note_parts.append("price drop 20")
        elif price_change <= -15:
            note_parts.append("price drop 15")
        elif price_change <= -10:
            note_parts.append("price drop 10")

    return ", ".join(note_parts) if note_parts else "dvsa volume 50"

class Command(BaseCommand):
    help = "Fetch stock data and store it in the database"

    def handle(self, *args, **options):
        start_time = time.time()

        # Load ticker info
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        formatted_path = os.path.join(BASE_DIR, '../../../../../json/formatted_tickers.json')

        with open(formatted_path, 'r') as f:
            tickers_json = json.load(f)

        tickers_data = {
            entry["Ticker"]: {"name": entry.get("Company Name", "")}
            for entry in tickers_json.get("tickers", []) if "Ticker" in entry
        }

        if not tickers_data:
            print("🚫 No valid tickers found in formatted_tickers.json — exiting.")
            return

        print(f"🔍 Processing {len(tickers_data)} tickers...")

        for ticker in tickers_data:
            try:
                signal.alarm(10)
                ticker_obj = yf.Ticker(ticker)
                hist_data = ticker_obj.history(period="3mo")
                signal.alarm(0)

                if hist_data.empty:
                    continue

                info = ticker_obj.fast_info or ticker_obj.info
                if not info:
                    continue

                current_price = hist_data['Close'].iloc[-1]
                prev_price = hist_data['Close'].iloc[-2] if len(hist_data) >= 2 else current_price
                volume_today = hist_data['Volume'].iloc[-1]
                avg_volume = info.get('averageVolume', 0)
                shares = info.get('sharesOutstanding', 0)
                pe = info.get('trailingPE')
                mc = info.get('marketCap')

                dvav = round(volume_today / avg_volume, 4) if avg_volume else None
                dvsa = round(volume_today / shares, 4) if shares else None

                # Calculate price change today (as a %)
                price_change_today = ((current_price - prev_price) / prev_price) * 100 if prev_price else 0

                # Get historical market cap ~3 months ago (90 days)
                mc_3mo_ago = mc  # fallback
                try:
                    three_months_ago = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
                    hist_3mo = hist_data.loc[three_months_ago:]
                    if not hist_3mo.empty:
                        mc_3mo_ago = hist_3mo['Close'].iloc[0] * shares
                except:
                    pass

                mc_change = ((mc - mc_3mo_ago) / mc_3mo_ago) if mc_3mo_ago else 0

                StockAlert.objects.update_or_create(
                    ticker=ticker,
                    defaults={
                        'current_price': float(current_price),
                        'volume_today': int(volume_today),
                        'avg_volume': int(avg_volume) if avg_volume else None,
                        'dvav': dvav,
                        'dvsa': dvsa,
                        'pe_ratio': pe if isinstance(pe, (int, float)) else None,
                        'market_cap': mc if isinstance(mc, (int, float)) else None,
                        'note': compute_note(pe, mc_change, dvsa, price_change_today),
                        'last_update': datetime.now()
                    }
                )
                print(f"✅ Saved {ticker}")

            except TimeoutException:
                print(f"⏰ Timeout getting history for {ticker}")
            except Exception as e:
                print(f"❌ Error processing {ticker}: {e}")

        elapsed = time.time() - start_time
        print(f"⏱️ Completed in {int(elapsed//60)} min {int(elapsed%60)} sec.")
