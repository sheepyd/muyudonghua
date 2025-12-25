#!/bin/bash

# MuYuDonghua Ultra-Robust One-Click Dev Launcher

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo ">>> Stopping servers..."
    kill $(jobs -p) 2>/dev/null
    exit
}
trap cleanup EXIT INT TERM

echo "🚀 MuYuDonghua Dev Launcher starting..."

# 0. Check for .env file
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "   Command: cp .env.example .env && nano .env"
    exit 1
fi

# 1. Setup Backend
echo ">>> [1/2] Setting up Backend..."
cd backend

# Ensure venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv || { echo "❌ Error: python3-venv missing. Install it with: apt install python3-venv"; exit 1; }
fi

# ALWAYS ensure dependencies are installed (pip will skip if already there)
echo "Ensuring backend dependencies are up to date..."
./venv/bin/pip install --upgrade pip > /dev/null
./venv/bin/pip install -r requirements.txt || { echo "❌ Error: Failed to install backend dependencies."; exit 1; }

# Start Backend
echo "Starting Backend on Port 8800..."
./venv/bin/python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend
sleep 2

# 2. Setup Frontend
echo ">>> [2/2] Setting up Frontend..."
cd frontend

# Ensure node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies (first time setup)..."
    npm install || { echo "❌ Error: npm install failed. Is Node.js installed?"; exit 1; }
fi

# Start Frontend
echo "Starting Frontend on Port 3000..."
npm run dev