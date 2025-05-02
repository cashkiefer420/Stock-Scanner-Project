import json
from django.utils.dateparse import parse_datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from stocks.models import StockAlert
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware



def safe_float(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class Command(BaseCommand):
    help = 'Import stock alerts from stock_data_export.json into the StockAlert model.'

    def handle(self, *args, **kwargs):
        # Clear out old stock alerts before import
        StockAlert.objects.all().delete()
        path = Path("stock_data_export.json")

        if not path.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {path}"))
            return

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        count = 0
        for entry in data:
            ticker = entry.get("Ticker")
            if not ticker:
                continue

            try:
                price_change = entry.get("Price Change Today") or 0
                pe_ratio = entry.get("P/E Ratio")
                mc_change = entry.get("Market Cap Change (3 Mon)") or 0
                dvsa = entry.get("DVSA (Volume/Share)") or 0

                note_parts = []

                # DVSA thresholds
                try:
                    if float(dvsa) >= 1.0:
                        note_parts.append("dvsa volume 100")
                    elif float(dvsa) >= 0.5:
                        note_parts.append("dvsa volume 50")
                except Exception:
                    pass

                # Market cap change
                try:
                    mc_change = float(mc_change)
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
                except Exception:
                    pass

                # PE ratio
                try:
                    pe = float(pe_ratio)
                    if pe >= 30:
                        note_parts.append("pe increase 30")
                    elif pe >= 20:
                        note_parts.append("pe increase 20")
                    elif pe >= 10:
                        note_parts.append("pe increase 10")
                    elif pe <= 10:
                        note_parts.append("pe decrease 10")
                except Exception:
                    pass

                # Price drop
                try:
                    price_drop = float(price_change)
                    if price_drop <= -20:
                        note_parts.append("price drop 20")
                    elif price_drop <= -15:
                        note_parts.append("price drop 15")
                    elif price_drop <= -10:
                        note_parts.append("price drop 10")
                except Exception:
                    pass

                computed_note = ", ".join(note_parts) if note_parts else "dvsa volume 50"

                StockAlert.objects.create(
                    ticker=ticker,
                    current_price=entry.get("Current Price") or 0,
                    volume_today=entry.get("Volume Today") or 0,
                    avg_volume=entry.get("Avg Volume (3 mon)") or 0,
                    dvav=safe_float(entry.get("DVAV (Day Volume Over Avg Volume)")),
                    dvsa=safe_float(dvsa),
                    pe_ratio=safe_float(pe_ratio),
                    market_cap=entry.get("Market Cap") or 0,
                    note=computed_note,
                    last_update=make_aware(parse_datetime(entry.get("Last Update")))
                )
                count += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Failed to import {ticker}: {e}"))
        self.stdout.write(self.style.SUCCESS(f"Successfully imported {count} stock alerts."))

