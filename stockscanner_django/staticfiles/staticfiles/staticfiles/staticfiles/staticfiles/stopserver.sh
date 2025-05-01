#!/bin/bash

echo "Stopping Gunicorn..."
pkill -f "gunicorn stockscanner_django.wsgi"

echo "Stopping Celery worker..."
pkill -f "celery -A stockscanner_django worker"

echo "Stopping Celery Beat..."
pkill -f "celery -A stockscanner_django beat"

echo "Stopping Caddy..."
pkill -f "caddy run"

echo "✅ All server processes have been stopped."
