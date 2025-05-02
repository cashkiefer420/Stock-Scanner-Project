from django.core.management.base import BaseCommand
from emails.stock_notifications import send_stock_notifications

class Command(BaseCommand):
    help = 'Send personalized stock emails based on new stock alerts.'

    def handle(self, *args, **kwargs):
        send_stock_notifications()
