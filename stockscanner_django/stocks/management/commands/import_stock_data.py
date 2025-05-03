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
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.core.management.base import BaseCommand
from django.utils.timezone import now, make_aware
from stocks.models import StockAlert

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class TimeoutException(Exception): pass
def timeout_handler(signum, frame): raise TimeoutException()
signal.signal(signal.SIGALRM, timeout_handler)


class Command(BaseCommand):
    help = "Fetch stock data and store it in the database"

    def handle(self, *args, **options):
        start_time = time.time()

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

        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = {executor.submit(self.process_ticker, ticker): ticker for ticker in tickers_data}
            for future in as_completed(futures):
                ticker = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"❌ Error processing {ticker}: {e}")

        elapsed = time.time() - start_time
        print(f"⏱️ Completed in {int(elapsed//60)} min {int(elapsed%60)} sec.")

    def process_ticker(self, ticker):
        retries = 0
        max_retries = 4
        base_delay = 2

        while retries <= max_retries:
            try:
                time.sleep(random.uniform(0.5, 2.5))  # Add delay to avoid rate limiting
                signal.alarm(10)
                ticker_obj = yf.Ticker(ticker)
                hist_data = ticker_obj.history(period="3mo")
                signal.alarm(0)

                if hist_data.empty:
                    return

                info = ticker_obj.fast_info or ticker_obj.info
                if not info:
                    return

                current_price = hist_data['Close'].iloc[-1]
                prev_price = hist_data['Close'].iloc[-2] if len(hist_data) >= 2 else current_price
                volume_today = hist_data['Volume'].iloc[-1]
                avg_volume = info.get('averageVolume', 0)
                shares = info.get('sharesOutstanding', 0)
                pe = info.get('trailingPE')
                mc = info.get('marketCap')

                dvav = round(volume_today / avg_volume, 4) if avg_volume else None
                dvsa = round(volume_today / shares, 4) if shares else None

                note_parts = []
                try:
                    if dvsa and dvsa >= 1.0:
                        note_parts.append("dvsa volume 100")
                    elif dvsa and dvsa >= 0.5:
                        note_parts.append("dvsa volume 50")
                except Exception: pass

                try:
                    if mc and isinstance(mc, (int, float)):
                        mc_change = 0  # Placeholder
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
                except Exception: pass

                try:
                    pe_val = float(pe)
                    if pe_val >= 30:
                        note_parts.append("pe increase 30")
                    elif pe_val >= 20:
                        note_parts.append("pe increase 20")
                    elif pe_val >= 10:
                        note_parts.append("pe increase 10")
                    elif pe_val <= 10:
                        note_parts.append("pe decrease 10")
                except Exception: pass

                try:
                    price_change = ((current_price - prev_price) / prev_price) * 100 if prev_price else 0
                    if price_change <= -20:
                        note_parts.append("price drop 20")
                    elif price_change <= -15:
                        note_parts.append("price drop 15")
                    elif price_change <= -10:
                        note_parts.append("price drop 10")
                except Exception: pass

                note = ", ".join(note_parts) if note_parts else "dvsa volume 50"

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
                        'note': note,
                        'last_update': make_aware(datetime.utcnow())
                    }
                )
                print(f"✅ Saved {ticker}")
                return

            except TimeoutException:
                print(f"⏰ Timeout getting history for {ticker}")
                break
            except Exception as e:
                retries += 1
                if "Too Many Requests" in str(e):
                    wait = base_delay * (2 ** retries)
                    print(f"🔁 {ticker}: Rate limited, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    break

        print(f"❌ Giving up on {ticker}")
