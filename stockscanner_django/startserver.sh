#!/bin/bash

# If "dev" is passed, use Django's dev server
if [ "$1" == "dev" ]; then
    echo "Starting Django development server..."
    python manage.py runserver
else
    echo "Starting Gunicorn server..."
    gunicorn stockscanner_django.wsgi:application --bind 0.0.0.0:8000
fi