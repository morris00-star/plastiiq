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
python manage.py seed_cutout_geometries
python manage.py seed_bulk_products

echo "=== Build completed successfully! ==="