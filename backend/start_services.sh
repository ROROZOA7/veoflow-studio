#!/bin/bash

# VeoFlow Studio - Start All Services Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}VeoFlow Studio - Starting Services${NC}"
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${YELLOW}Redis is not running.${NC}"
    echo "Please start Redis in another terminal:"
    echo "  redis-server"
    echo ""
    read -p "Press Enter to continue anyway (services may not work without Redis)..."
fi

# Check if database is initialized
if [ ! -f "veoflow.db" ] && [ ! -f "../.env" ]; then
    echo -e "${YELLOW}Initializing database...${NC}"
    python init_db.py
fi

echo ""
echo -e "${GREEN}Starting services...${NC}"
echo ""
echo "Services will start in separate processes."
echo "Press Ctrl+C to stop all services."
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping services...${NC}"
    kill $FASTAPI_PID $CELERY_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start FastAPI server
echo -e "${GREEN}[1/2] Starting FastAPI server on http://localhost:8000${NC}"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
FASTAPI_PID=$!

# Wait a bit for FastAPI to start
sleep 2

# Start Celery worker
echo -e "${GREEN}[2/2] Starting Celery worker${NC}"
celery -A app.workers.render_worker worker --loglevel=info &
CELERY_PID=$!

echo ""
echo -e "${GREEN}✓ All services started!${NC}"
echo ""
echo "FastAPI API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for processes
wait

