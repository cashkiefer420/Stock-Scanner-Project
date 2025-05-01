from celery import shared_task
from blueprint import news  # assuming `news.py` is in /blueprint

@shared_task
def update_news_feed():
    print("📡 Running hourly news scrape...")
    news.main()
    print("✅ News feed updated.")
