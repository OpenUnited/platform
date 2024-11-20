#!/bin/bash

# Start Django Q cluster in the background
python manage.py qcluster &
QCLUSTER_PID=$!

# Start Django development server
python manage.py runserver &
DJANGO_PID=$!

# Handle shutdown
trap "kill $QCLUSTER_PID $DJANGO_PID" EXIT

# Wait for both processes
wait
