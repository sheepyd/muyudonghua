#!/bin/bash

# MuYuDonghua One-Click Dev Launcher

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo ">>> Stopping servers..."
    # Kill background jobs started by this script
    kill $(jobs -p) 2>/dev/null
    exit
}
trap cleanup EXIT INT TERM

echo "🚀 MuYuDonghua Dev Launcher starting..."

# 0. Check for .env file
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "   Please copy .env.example to .env and fill in your keys."
    echo "   Command: cp .env.example .env"
    exit 1
fi

# 1. Setup Backend
echo ">>> Setting up Backend..."
cd backend

# Check for venv
if [ ! -d "venv" ]; then
    echo "Creating virtual environment (first time setup)..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to create venv. Is python3-venv installed?"
        exit 1
    fi
    echo "Installing backend dependencies..."
    ./venv/bin/pip install -r requirements.txt
fi

# Start Backend
echo "Starting Backend on Port 8800..."
./venv/bin/python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
sleep 2

# 2. Setup Frontend
echo ">>> Setting up Frontend..."
cd frontend

# Ensure deps are installed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies (this may take a minute)..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Error: npm install failed. Is Node.js and npm installed?"
        exit 1
    fi
fi

# Start Frontend
echo "Starting Frontend on Port 3000..."
npm run dev
