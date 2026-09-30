#!/usr/bin/env bash
# build.sh — Render build script
# Installs backend deps + builds the React frontend into backend-servable static files.

set -o errexit  # Exit on error

echo "=== Installing Backend Dependencies ==="
cd backend
pip install -r requirements.txt
cd ..

echo "=== Building Frontend ==="
cd frontend
npm install
npm run build
cd ..

echo "=== Build Complete ==="
echo "Frontend built to frontend/dist/"
