from django.contrib import admin
from .models import Subscription

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'category', 'subscribed_at')
    list_filter = ('category', 'subscribed_at')
    search_fields = ('email', 'category')
    ordering = ('-subscribed_at',)

    # Optionally add this to a custom management command or startup file
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
import json

# Crontab: 9:00 AM daily
schedule, created = CrontabSchedule.objects.get_or_create(
    minute='0',
    hour='9',
    day_of_week='*',
    day_of_month='*',
    month_of_year='*',
)

#PeriodicTask.objects.create(
    #crontab=schedule,
    #name='Send MC 10 IN Emails',
    #task='emails.tasks.send_mc_10_in_email',
    #kwargs=json.dumps({}),
#)
