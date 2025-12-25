#!/bin/bash

# Function to handle cleanup on exit
cleanup() {
    echo "Stopping servers..."
    kill $(jobs -p) 2>/dev/null
}
trap cleanup EXIT

# 1. Start Backend
echo ">>> Starting Backend (Port 8800)..."
cd backend
# Check if venv exists, if not create it (optional, skipping for simplicity, using system/user python)
# Ensure deps are installed
pip install -r requirements.txt > /dev/null 2>&1
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready (simple sleep)
sleep 2

# 2. Start Frontend
echo ">>> Starting Frontend (Port 3000)..."
cd frontend
# Ensure deps are installed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies (this may take a minute)..."
    npm install
fi
npm run dev
