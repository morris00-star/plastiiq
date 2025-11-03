#!/usr/bin/env bash
# build.sh

set -o errexit

echo "=== Setting up Python environment ==="
python --version
pip --version

echo "=== Installing dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Running migrations ==="
python manage.py migrate

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --clear

echo "=== Loading initial data ==="
python manage.py load_initial_data

echo "=== Build completed successfully! ==="