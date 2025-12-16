#!/bin/bash

# Start FastAPI development server with proper file watcher exclusions
# This prevents ENOSPC file watcher limit errors

cd "$(dirname "$0")"

source venv/bin/activate 2>/dev/null || echo "Note: Virtual environment not activated"

echo "Starting FastAPI development server..."
echo "Using file watcher exclusions to prevent ENOSPC errors..."
echo ""

uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --reload-exclude "profiles/*" \
  --reload-exclude "output/*" \
  --reload-exclude "logs/*" \
  --reload-exclude "images/*" \
  --reload-exclude "venv/*" \
  --reload-exclude "chromedata/*" \
  --reload-exclude "**/__pycache__/*"



