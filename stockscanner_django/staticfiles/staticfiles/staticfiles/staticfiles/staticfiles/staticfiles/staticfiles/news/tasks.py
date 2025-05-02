from celery import shared_task
from . import scraper  # assuming `news.py` is in /blueprint

@shared_task
def update_news_feed():
    print("📡 Running hourly news scrape...")
    scraper.main()
    print("✅ News feed updated.")
