#!/bin/bash

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo ">>> Stopping servers..."
    kill $(jobs -p) 2>/dev/null
}
trap cleanup EXIT

# 0. Check Environment
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found! Please create it based on .env.example"
fi

# 1. Start Backend
echo ">>> Starting Backend (Port 8800)..."
cd backend
if [ -f "venv/bin/python" ]; then
    echo "Using virtual environment..."
    ./venv/bin/python main.py &
else
    echo "!!! Warning: venv not found. Using system python3..."
    echo "Tip: Run 'python3 -m venv venv && ./venv/bin/pip install -r requirements.txt' in backend/"
    python3 main.py &
fi
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