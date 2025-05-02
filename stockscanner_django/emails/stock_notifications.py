from collections import defaultdict
from core.models import Subscription
from stocks.models import StockAlert
from emails.tasks import send_personalized_email
from emails.email_filter import EmailFilter

def send_stock_notifications():
    new_alerts = StockAlert.objects.filter(sent=False)

    if not new_alerts.exists():
        print("No new stocks to send.")
        return

    filter = EmailFilter()
    category_map = defaultdict(list)

    for alert in new_alerts:
        category = filter.filter_email(alert.note.lower())
        print(f"[DEBUG] Category result: '{category}' from note: '{alert.note}'")
        if category != "Uncategorized":
            category_map[category].append(alert)
            alert.sent = True
            alert.save()

    for category, alerts in category_map.items():
        subscribers = Subscription.objects.filter(category=category)
        if not subscribers.exists():
            print(f"No subscribers for category {category}")
            continue

        stock_list = [
            {
                "stock_symbol": alert.ticker,
                "PRICE": str(alert.current_price),
                "VOLUME": str(alert.volume_today),
                "DVAV": str(alert.dvav or 0),
                "DVSA": str(alert.dvsa or 0),
            } for alert in alerts
        ]

        for sub in subscribers:
            send_personalized_email.delay(
                user_email=sub.email,
                user_name=sub.email.split("@")[0],
                category=category,
                stock_list=stock_list
            )
            print(f"Queued {len(alerts)} alerts for {sub.email} in category {category}")
