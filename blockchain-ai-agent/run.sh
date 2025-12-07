#!/bin/bash
# Uvicorn startup script for Sui Blockchain AI Agent

echo "Starting Sui Blockchain AI Agent with Uvicorn..."

# Run from the project directory
cd "$(dirname "$0")"

# Start uvicorn
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --log-level info
