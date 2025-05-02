# projectname/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stockscanner_django.settings")

app = Celery("stockscanner_django")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(['emails', 'news', 'stocks',])
app.conf.beat_scheduler = 'django_celery_beat.schedulers.DatabaseScheduler'

