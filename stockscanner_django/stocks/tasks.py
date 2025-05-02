from celery import shared_task
from django.core.management import call_command

@shared_task
def run_stock_import():
    call_command('import_stock_data')
