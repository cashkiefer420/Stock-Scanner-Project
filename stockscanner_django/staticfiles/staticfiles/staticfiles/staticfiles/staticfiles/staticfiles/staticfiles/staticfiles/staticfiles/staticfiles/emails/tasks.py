from celery import shared_task
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.conf import settings
from emails.email_filter import EmailFilter

CATEGORY_TEMPLATE_MAP = {
    "DVSA 50": "emails/dvsa_50.html",
    "DVSA 100": "emails/dvsa_100.html",
    "DVSA 150": "emails/dvsa_150.html",
    "MC 10 IN": "emails/mc_10_in.html",
    "MC 20 IN": "emails/mc_20_in.html",
    "MC 30 IN": "emails/mc_30_in.html",
    "MC 10 DE": "emails/mc_10_de.html",
    "MC 20 DE": "emails/mc_20_de.html",
    "MC 30 DE": "emails/mc_30_de.html",
    "PE 10 IN": "emails/pe_10_in.html",
    "PE 20 IN": "emails/pe_20_in.html",
    "PE 30 IN": "emails/pe_30_in.html",
    "PE 10 DE": "emails/pe_10_de.html",
    "PE 20 DE": "emails/pe_20_de.html",
    "PE 30 DE": "emails/pe_30_de.html",
    "PRICE 10 DE": "emails/price_10_de.html",
    "PRICE 15 DE": "emails/price_15_de.html",
    "PRICE 20 DE": "emails/price_20_de.html",
}

@shared_task
def send_personalized_email(user_email, user_name, category, stock_list):
    if category not in CATEGORY_TEMPLATE_MAP:
        print(f"[INFO] Skipping email: No template for category '{category}'")
        return

    template_path = CATEGORY_TEMPLATE_MAP[category]
    subject = f"Stock Alerts for {category} ({len(stock_list)} stocks)"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [user_email]

    html_content = render_to_string(template_path, {
        "user_name": user_name,
        "category": category,
        "stocks": stock_list,
    })

    try:
        with get_connection() as connection:
            email = EmailMultiAlternatives(
                subject, "", from_email, to, connection=connection
            )
            email.attach_alternative(html_content, "text/html")
            print(f"[DEBUG] Sending summary email to: {user_email}, category: {category}, count: {len(stock_list)}")
            email.send()
    except Exception as e:
        print(f"[ERROR] Failed to send email to {user_email}: {e}")
