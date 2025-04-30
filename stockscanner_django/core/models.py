from django.db import models

class Subscription(models.Model):
    email = models.EmailField()
    category = models.CharField(max_length=100)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} -> {self.category}"