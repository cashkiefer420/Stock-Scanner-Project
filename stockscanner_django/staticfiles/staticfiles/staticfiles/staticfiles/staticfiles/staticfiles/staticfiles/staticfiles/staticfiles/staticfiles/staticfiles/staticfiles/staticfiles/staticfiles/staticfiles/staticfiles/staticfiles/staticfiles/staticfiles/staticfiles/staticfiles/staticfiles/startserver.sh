#!/bin/bash

PROJECT_NAME="stockscanner_django"
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
STATIC_DIR="$PROJECT_DIR/static"
MEDIA_DIR="$PROJECT_DIR/media"
CADDYFILE="$PROJECT_DIR/Caddyfile"

export STATIC_PATH="$STATIC_DIR"
export MEDIA_PATH="$MEDIA_DIR"

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Celery worker..."
celery -A $PROJECT_NAME worker --loglevel=info > celery.log 2>&1 &

echo "Starting Celery Beat..."
celery -A $PROJECT_NAME beat --loglevel=info > beat.log 2>&1 &

if [ "$1" == "dev" ]; then
    echo "Starting Django development server..."
    python manage.py runserver
else
    echo "Starting Gunicorn server on 127.0.0.1:8000..."
    gunicorn $PROJECT_NAME.wsgi:application --bind 127.0.0.1:8000 &

    echo "Starting Caddy reverse proxy..."
    caddy run --config "$CADDYFILE" --adapter caddyfile &

    echo "✅ Caddy + Gunicorn + Celery are all running!"
fi
