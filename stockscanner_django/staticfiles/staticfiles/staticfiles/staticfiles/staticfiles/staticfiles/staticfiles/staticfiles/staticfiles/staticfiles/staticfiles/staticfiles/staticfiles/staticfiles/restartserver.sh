#!/bin/bash

echo "Stopping Gunicorn, Celery, and Caddy..."
pkill -f "celery -A stockscanner_django"
pkill -f "gunicorn stockscanner_django.wsgi"
pkill -f "caddy run"

sleep 2

echo "Restarting server..."
./startserver.sh
