#!/usr/bin/env bash
# build.sh

set -o errexit

# cd plastic_qc_calculator

# Install dependencies
pip install --upgrade pip

pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate

# Load initial data
python manage.py load_initial_data