from django.db import models

class StockAlert(models.Model):
    ticker = models.CharField(max_length=10)
    company_name = models.CharField(max_length=255, blank=True)  # <- New field
    current_price = models.FloatField()
    volume_today = models.BigIntegerField()
    avg_volume = models.BigIntegerField(null=True, blank=True)
    dvav = models.FloatField(null=True, blank=True)
    dvsa = models.FloatField(null=True, blank=True)
    pe_ratio = models.FloatField(null=True, blank=True)
    market_cap = models.BigIntegerField(null=True, blank=True)
    note = models.TextField(blank=True)
    last_update = models.DateTimeField()
    sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.ticker} - {self.note or 'No Note'}"
