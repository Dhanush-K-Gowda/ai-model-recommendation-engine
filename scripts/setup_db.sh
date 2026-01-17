#!/bin/bash
# Setup database: run migrations and import model data

set -e

cd "$(dirname "$0")"

echo "Running migrations..."
uv run python manage.py migrate

echo ""
echo "Importing model data..."
uv run python manage.py import_models --clear

echo ""
echo "Done!"
