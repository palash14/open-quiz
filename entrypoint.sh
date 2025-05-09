#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting entrypoint script..."

# Run Alembic migrations
if [ "$ENVIRONMENT" = "dev" ]; then
    echo "Running database migrations..."
    alembic upgrade head

    # echo "Running database seeders..."
    python database/run_seeder.py
fi

# echo "Starting Uvicorn server..."
exec uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload