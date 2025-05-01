from celery import shared_task
from django.core.mail import send_mail
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stockscanner_django.settings")
from django.conf import settings
from core.models import Subscription


@shared_task
def send_dvsa_50_email():
    subject = "DVSA 50%"
    message = "This is your alert for: DVSA 50%"
    recipients = Subscription.objects.filter(category="DVSA-50").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )


@shared_task
def send_dvsa_100_email():
    subject = "DVSA 100% Alert"
    message = "This is your alert for: DVSA 100% Alert"
    recipients = Subscription.objects.filter(category="DVSA-100").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )


@shared_task
def send_dvsa_150_email():
    subject = "DVSA 150% Alert"
    message = "This is your alert for: DVSA 150% Alert"
    recipients = Subscription.objects.filter(category="DVSA-150").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )


@shared_task
def send_mc_10_in_email():
    subject = "Market Cap +10%"
    message = "This is your alert for: Market Cap +10%"
    recipients = Subscription.objects.filter(category="mc-10-in").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )


@shared_task
def send_mc_20_in_email():
    subject = "Market Cap +20%"
    message = "This is your alert for: Market Cap +20%"
    recipients = Subscription.objects.filter(category="mc-20-in").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )


@shared_task
def send_mc_30_in_email():
    subject = "Market Cap +30%"
    message = "This is your alert for: Market Cap +30%"
    recipients = Subscription.objects.filter(category="mc-30-in").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )


@shared_task
def send_mc_10_de_email():
    subject = "Market Cap -10%"
    message = "This is your alert for: Market Cap -10%"
    recipients = Subscription.objects.filter(category="mc-10-de").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )


@shared_task
def send_mc_20_de_email():
    subject = "Market Cap -20%"
    message = "This is your alert for: Market Cap -20%"
    recipients = Subscription.objects.filter(category="mc-20-de").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )


@shared_task
def send_mc_30_de_email():
    subject = "Market Cap -30%"
    message = "This is your alert for: Market Cap -30%"
    recipients = Subscription.objects.filter(category="mc-30-de").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )


@shared_task
def send_pe_10_in_email():
    subject = "P/E +10%"
    message = "This is your alert for: P/E +10%"
    recipients = Subscription.objects.filter(category="pe-10-in").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )


@shared_task
def send_pe_20_in_email():
    subject = "P/E +20%"
    message = "This is your alert for: P/E +20%"
    recipients = Subscription.objects.filter(category="pe-20-in").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )


@shared_task
def send_pe_30_in_email():
    subject = "P/E +30%"
    message = "This is your alert for: P/E +30%"
    recipients = Subscription.objects.filter(category="pe-30-in").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )


@shared_task
def send_pe_10_de_email():
    subject = "P/E -10%"
    message = "This is your alert for: P/E -10%"
    recipients = Subscription.objects.filter(category="pe-10-de").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )


@shared_task
def send_pe_20_de_email():
    subject = "P/E -20%"
    message = "This is your alert for: P/E -20%"
    recipients = Subscription.objects.filter(category="pe-20-de").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )


@shared_task
def send_pe_30_de_email():
    subject = "P/E -30%"
    message = "This is your alert for: P/E -30%"
    recipients = Subscription.objects.filter(category="pe-30-de").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )


@shared_task
def send_price_10_de_email():
    subject = "Price Drop -10%"
    message = "This is your alert for: Price Drop -10%"
    recipients = Subscription.objects.filter(category="price-10-de").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )


@shared_task
def send_price_15_de_email():
    subject = "Price Drop -15%"
    message = "This is your alert for: Price Drop -15%"
    recipients = Subscription.objects.filter(category="price-15-de").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )


@shared_task
def send_price_20_de_email():
    subject = "Price Drop -20%"
    message = "This is your alert for: Price Drop -20%"
    recipients = Subscription.objects.filter(category="price-20-de").values_list('email', flat=True)
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        list(recipients),
        fail_silently=False,
    )
