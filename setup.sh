#!/bin/bash

# This is the simplest version of this script.
# I pushed this to collect ideas and implement
# these ideas on top of it.


python reset_database.py

python manage.py makemigrations

python manage.py migrate

echo "Y" | python load_sample_data.py

tailwindcss -o ./static/styles/tailwind.css --minify
