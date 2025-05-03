import json
import os
import time
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from stocks.models import StockAlert
import yfinance as yf

class Command(BaseCommand):
    help = "Retry importing failed tickers from failed_tickers.json"

    def handle(self, *args, **options):
        failed_file = os.path.join(os.path.dirname(__file__), '../../../../../json/failed_tickers.json')

        if not os.path.exists(failed_file):
            self.stdout.write(self.style.WARNING("No failed_tickers.json file found."))
            return

        with open(failed_file, 'r') as f:
            failed_tickers = json.load(f)

        if not failed_tickers:
            self.stdout.write(self.style.SUCCESS("No failed tickers to retry."))
            return

        successful = []
        remaining = []

        for ticker in failed_tickers:
            try:
                ticker_obj = yf.Ticker(ticker)
                hist_data = ticker_obj.history(period="3mo")
                if hist_data.empty:
                    raise ValueError("No historical data")

                info = ticker_obj.fast_info or ticker_obj.info
                if not info:
                    raise ValueError("No info found")

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
                if dvsa and dvsa >= 1.0:
                    note_parts.append("dvsa volume 100")
                elif dvsa and dvsa >= 0.5:
                    note_parts.append("dvsa volume 50")

                if pe:
                    pe_val = float(pe)
                    if pe_val >= 30:
                        note_parts.append("pe increase 30")
                    elif pe_val >= 20:
                        note_parts.append("pe increase 20")
                    elif pe_val >= 10:
                        note_parts.append("pe increase 10")
                    elif pe_val <= 10:
                        note_parts.append("pe decrease 10")

                price_change = ((current_price - prev_price) / prev_price) * 100 if prev_price else 0
                if price_change <= -20:
                    note_parts.append("price drop 20")
                elif price_change <= -15:
                    note_parts.append("price drop 15")
                elif price_change <= -10:
                    note_parts.append("price drop 10")

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
                print(f"✅ Retried and saved {ticker}")
                successful.append(ticker)

                # Optional sleep to reduce risk of rate limits
                time.sleep(1)

            except Exception as e:
                print(f"❌ Still failed for {ticker}: {e}")
                remaining.append(ticker)

        # Overwrite the failed file with any tickers that still failed
        with open(failed_file, 'w') as f:
            json.dump(remaining, f, indent=2)

        print(f"🎯 Retry complete: {len(successful)} succeeded, {len(remaining)} still failed")
