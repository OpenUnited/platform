#!/bin/bash

# Apply database migrations (only for main platform)
if [ "$SERVICE_TYPE" != "worker" ]; then
    echo "Apply database migrations"
    echo "----------------------------------------------------------"
    python manage.py migrate --run-syncdb

    # Prepare static files
    echo "Preparing static files"
    echo "----------------------------------------------------------"
    python manage.py collectstatic --no-input
fi

# Start appropriate service
if [ "$SERVICE_TYPE" = "worker" ]; then
    echo "Starting Django Q worker"
    echo "----------------------------------------------------------"
    python manage.py qcluster
else
    echo "Starting server"
    echo "----------------------------------------------------------"
    python manage.py runserver 0.0.0.0:80
fi
