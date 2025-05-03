# emails/models.py
from django.db import models

class StockAlert(models.Model):
    ticker = models.CharField(max_length=10)
    note = models.CharField(max_length=255)  # Used by EmailFilter
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume_today = models.BigIntegerField()
    dvav = models.DecimalField(max_digits=10, decimal_places=2)
    dvsa = models.DecimalField(max_digits=10, decimal_places=2)
    sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.ticker} - {self.note}"
