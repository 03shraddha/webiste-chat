#!/usr/bin/env bash
# Start both the backend and frontend dev servers.
# Usage: bash start.sh

set -e

# 1. Check for .env
if [ ! -f backend/.env ]; then
  echo "ERROR: backend/.env not found. Copy backend/.env.example to backend/.env and add your ANTHROPIC_API_KEY."
  exit 1
fi

echo "Starting backend on http://localhost:8000 ..."
cd backend
python run.py &
BACKEND_PID=$!
cd ..

echo "Starting frontend on http://localhost:5173 ..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "Website Chat is running!"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

# Wait and handle shutdown
cleanup() {
  echo "Shutting down..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
}
trap cleanup INT TERM
wait
