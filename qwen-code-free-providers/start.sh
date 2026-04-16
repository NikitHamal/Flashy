#!/bin/bash
# Start the Qwen Code Free Providers Bridge Server

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -q -r requirements.txt

# Start the server
echo "Starting Free Providers Bridge Server..."
python bridge_server.py "$@"
