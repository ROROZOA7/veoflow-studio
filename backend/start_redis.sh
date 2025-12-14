#!/bin/bash

# Start Redis for VeoFlow Studio

echo "Starting Redis..."

# Check if Redis is already running
if redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis is already running"
    exit 0
fi

# Try to start Redis using different methods
if command -v redis-server > /dev/null 2>&1; then
    echo "Starting Redis server..."
    redis-server --daemonize yes
    sleep 1
    if redis-cli ping > /dev/null 2>&1; then
        echo "✓ Redis started successfully"
    else
        echo "✗ Failed to start Redis"
        exit 1
    fi
elif command -v docker > /dev/null 2>&1; then
    echo "Starting Redis using Docker..."
    docker run -d --name veoflow-redis -p 6379:6379 redis:latest
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo "✓ Redis started in Docker"
    else
        echo "✗ Failed to start Redis in Docker"
        exit 1
    fi
else
    echo "✗ Redis not found. Please install Redis:"
    echo ""
    echo "Ubuntu/Debian:"
    echo "  sudo apt install redis-server"
    echo ""
    echo "Or use Docker:"
    echo "  docker run -d --name veoflow-redis -p 6379:6379 redis:latest"
    echo ""
    echo "Or install manually from: https://redis.io/download"
    exit 1
fi

