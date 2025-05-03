from django.core.management.base import BaseCommand
from core.models import Subscription

class Command(BaseCommand):
    help = 'Seed test subscriptions for all 18 alert categories.'

    def handle(self, *args, **kwargs):
        categories = [
            "DVSA 50", "DVSA 100", "DVSA 150",
            "MC 10 IN", "MC 20 IN", "MC 30 IN",
            "MC 10 DE", "MC 20 DE", "MC 30 DE",
            "PE 10 IN", "PE 20 IN", "PE 30 IN",
            "PE 10 DE", "PE 20 DE", "PE 30 DE",
            "PRICE 10 DE", "PRICE 15 DE", "PRICE 20 DE"
        ]

        email = "cash.kiefer2008@gmail.com"
        created_count = 0

        for category in categories:
            obj, created = Subscription.objects.get_or_create(email=email, category=category)
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Created {created_count} new subscriptions for {email}."))
