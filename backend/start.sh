#!/bin/bash
# start.sh - Combined startup script for FastAPI and Celery
set -e

# Load environment variables
source ./.env 2>/dev/null || true

# Create credentials directory and extract Firebase credentials
if [ -n "$FIREBASE_CREDENTIALS_BASE64" ]; then
  echo "Setting up Firebase credentials from base64 environment variable"
  mkdir -p ./credentials
  echo $FIREBASE_CREDENTIALS_BASE64 | base64 --decode > ./credentials/firebase-credentials.json
  export FIREBASE_CREDENTIALS_PATH="./credentials/firebase-credentials.json"
  echo "Firebase credentials saved to $FIREBASE_CREDENTIALS_PATH"
fi

# Determine the port - use $PORT for Render or default to 8000
PORT=${PORT:-8000}

# Start Celery worker in the background
echo "Starting Celery worker..."
celery -A app.worker worker --loglevel=WARNING &
CELERY_WORKER_PID=$!

# Start Celery beat in the background (only if you need scheduling)
echo "Starting Celery beat scheduler..."
celery -A app.worker beat --loglevel=WARNING &
CELERY_BEAT_PID=$!

# Start FastAPI server
echo "Starting FastAPI server on port $PORT..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT &
API_PID=$!

# Handle shutdown signals
function handle_sigterm() {
  echo "Received shutdown signal, stopping all processes..."
  kill $CELERY_WORKER_PID $CELERY_BEAT_PID $API_PID 2>/dev/null || true
  wait
  echo "All processes stopped"
  exit 0
}

trap handle_sigterm SIGINT SIGTERM

# Keep the script running
echo "All services started - backend is ready"
wait 