#!/bin/bash

# Reset existing database
echo "Reset existing database"
echo "----------------------------------------------------------"
nohup python reset_database.py

# Create database migrations
echo "Create database migrations"
echo "----------------------------------------------------------"
nohup python manage.py makemigrations

# Apply database migrations
echo "Apply database migrations"
echo "----------------------------------------------------------"
nohup python manage.py migrate --run-syncdb

# Load Sample Data
echo "Load Sample Data"
echo "----------------------------------------------------------"
echo "Y" | python load_sample_data.py

# Start server
echo "Starting server"
echo "----------------------------------------------------------"
python manage.py runserver 0.0.0.0:80
