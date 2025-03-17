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
celery -A app.worker worker --loglevel=WARNING --without-heartbeat --without-gossip --without-mingle --concurrency=2 --max-memory-per-child=50000 &
CELERY_WORKER_PID=$!

# Start Celery beat in the background (only if you need scheduling)
echo "Starting Celery beat scheduler..."
celery -A app.worker beat --loglevel=WARNING --max-interval=3600 &
CELERY_BEAT_PID=$!

# Add memory monitoring to log when system is running low on memory
echo "Setting up memory monitoring..."
(
  while true; do
    # Get free memory in KB
    free_mem=$(free -m | awk 'NR==2{print $4}')
    if [ $free_mem -lt 100 ]; then
      echo "WARNING: Low memory - only ${free_mem}MB free"
    fi
    sleep 60
  done
) &
MEMORY_MONITOR_PID=$!

# Start FastAPI server
echo "Starting FastAPI server on port $PORT..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --limit-concurrency 20 --timeout-keep-alive 30 &
API_PID=$!

# Handle shutdown signals
function handle_sigterm() {
  echo "Received shutdown signal, stopping all processes..."
  kill $CELERY_WORKER_PID $CELERY_BEAT_PID $API_PID $MEMORY_MONITOR_PID 2>/dev/null || true
  wait
  echo "All processes stopped"
  exit 0
}

# Add a function to check if processes are still running
function check_processes() {
  if ! kill -0 $CELERY_WORKER_PID 2>/dev/null; then
    echo "Celery worker process died, restarting..."
    celery -A app.worker worker --loglevel=WARNING --without-heartbeat --without-gossip --without-mingle --concurrency=2 --max-memory-per-child=50000 &
    CELERY_WORKER_PID=$!
  fi
  
  if ! kill -0 $CELERY_BEAT_PID 2>/dev/null; then
    echo "Celery beat process died, restarting..."
    celery -A app.worker beat --loglevel=WARNING --max-interval=3600 &
    CELERY_BEAT_PID=$!
  fi
  
  if ! kill -0 $API_PID 2>/dev/null; then
    echo "API process died, restarting..."
    uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --limit-concurrency 20 --timeout-keep-alive 30 &
    API_PID=$!
  fi
}

trap handle_sigterm SIGINT SIGTERM

# Keep the script running and check processes every minute
echo "All services started - backend is ready"
while true; do
  check_processes
  sleep 60
done 