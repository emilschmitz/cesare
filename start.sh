#!/usr/bin/env bash

# Usage: ./start.sh [dev|prod]
# Default is dev mode.

MODE=${1:-dev}

if [ "$MODE" = "dev" ]; then
  # Start Flask API in a new terminal window
  gnome-terminal -- bash -c "cd cesare-api && python app.py; exec bash" &
  # Start React app in a new terminal window
  gnome-terminal -- bash -c "cd cesare-web && npm start; exec bash" &
  echo "Started API and web app in development mode."
  echo "Check the new terminal windows for logs."
else
  # Production mode
  echo "Building React app..."
  cd cesare-web && npm run build && cd ..
  echo "Starting Flask API with gunicorn..."
  cd cesare-api && uv pip install gunicorn && uvx gunicorn -w 4 -b 0.0.0.0:5000 app:app &
  echo "Production servers started."
  echo "React build is in cesare-web/build. Serve it with your preferred static file server."
fi 