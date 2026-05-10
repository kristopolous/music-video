#!/bin/bash

# Navigate to the project directory
# cd "$(dirname "$0")"

# Activate the virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment (.venv) not found. Please run 'uv venv' first."
    exit 1
fi

echo "Starting Music Video Automator Server..."
echo "Access the UI at: http://127.0.0.1:8000/static/index.html"

# Start the FastAPI server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
