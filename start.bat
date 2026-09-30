@echo off
title AI RoadGuard - Starting...
color 0A

echo ============================================
echo    AI RoadGuard - One-Click Launcher
echo ============================================
echo.

:: Get the directory where this script lives
set "ROOT=%~dp0"

:: ---- Start Backend (FastAPI) ----
echo [1/3] Starting Backend Server...
start "RoadGuard Backend" cmd /k "cd /d "%ROOT%backend" && call venv\Scripts\activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: Give backend a moment to boot before frontend
timeout /t 3 /nobreak >nul

:: ---- Start Frontend (Vite) ----
echo [2/3] Starting Frontend Dev Server...
start "RoadGuard Frontend" cmd /k "cd /d "%ROOT%frontend" && npm run dev -- --port 5173"

:: Wait for Vite to be ready
timeout /t 5 /nobreak >nul

:: ---- Open Browser ----
echo [3/3] Opening browser...
start "" http://localhost:5173

echo.
echo ============================================
echo    App is running!
echo    Frontend : http://localhost:5173
echo    Backend  : http://localhost:8000
echo    API Docs : http://localhost:8000/docs
echo ============================================
echo.
echo Close this window anytime. The servers will
echo keep running in their own windows.
echo.
pause
