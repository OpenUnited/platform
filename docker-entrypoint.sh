#!/bin/bash

# Apply database migrations
echo "Apply database migrations"
echo "----------------------------------------------------------"
nohup python manage.py migrate --run-syncdb

# Prepare static files
echo "Preparing static files"
echo "----------------------------------------------------------"
nohup python manage.py collectstatic --no-input

# Start Django Q worker in background
echo "Starting Django Q worker"
echo "----------------------------------------------------------"
python manage.py qcluster &

# Start server
echo "Starting server"
echo "----------------------------------------------------------"
python manage.py runserver 0.0.0.0:80
