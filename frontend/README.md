# AI RoadGuard — Frontend

React 19 + Vite frontend for the **Pothole & Road Damage Detection** system. Provides an interactive dashboard to upload road images/videos, view AI-annotated results, browse inspection history, and download engineering PDF reports.

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10 or later |
| Node.js | 18 or later |
| npm | 9 or later |

---

## Quick Start — Run the Full App

Open **two terminals** from the repository root (`road-damage-detection/`):

### Terminal 1 — Backend (FastAPI)

```bash
cd backend

# Create and activate virtual environment (first time only)
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS / Linux

# Install Python dependencies (first time only)
pip install -r requirements.txt

# Start the API server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend API: **http://127.0.0.1:8000**
Swagger docs: **http://127.0.0.1:8000/docs**

### Terminal 2 — Frontend (React + Vite)

```bash
cd frontend

# Install Node dependencies (first time only)
npm install

# Start the dev server
npm run dev
```

Frontend app: **http://localhost:5173**

> **Important:** The backend must be running before using the frontend. Analysis, dashboard, history, and report features all call the backend API at `http://127.0.0.1:8000`.

---

## Backend API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/analysis/image` | Upload an image for road damage analysis |
| `POST` | `/api/analysis/video` | Upload a video for frame-by-frame analysis |
| `GET` | `/api/dashboard/stats` | Aggregate analytics (totals, distributions) |
| `GET` | `/api/dashboard/history` | List past inspection records |
| `GET` | `/api/analysis/{id}/report` | Download PDF inspection report |

---

## Frontend Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start local dev server with Hot Module Replacement (HMR) |
| `npm run build` | Build optimised production bundle to `dist/` |
| `npm run preview` | Locally preview the production build |
| `npm run lint` | Run Oxlint static analysis |

---

## Running Tests

```bash
cd backend
python -m pytest
```

All 14 tests cover API routes, detector service, report generation, and video processing.

---

## Production Build

```bash
cd frontend
npm run build
```

Output is placed in `frontend/dist/`. Preview it locally:

```bash
npm run preview
```

---

## Tech Stack

### Backend
- **FastAPI** — async REST API framework
- **Ultralytics YOLO** — real-time object detection (PyTorch)
- **OpenCV** — image/video annotation rendering
- **SQLAlchemy** — ORM with SQLite database
- **ReportLab** — PDF report generation
- **Pydantic V2** — request/response validation

### Frontend
- **React 19** — UI framework
- **Vite 5** — Build tool & dev server
- **React Router v7** — Client-side routing
- **Recharts** — Interactive data visualisations on the Analytics Dashboard
- **Axios** — HTTP client for backend API calls
- **Lucide React** — Icon library
- **Tailwind CSS v4** — Utility-first styling
- **Oxlint** — Fast JavaScript/TypeScript linter

---

## Project Structure

```
road-damage-detection/
├── backend/
│   ├── app/
│   │   ├── api/             # API routes (health, analysis, dashboard)
│   │   ├── core/            # App settings and environment config
│   │   ├── database/        # SQLAlchemy session & ORM models
│   │   ├── models/          # Pydantic request/response schemas
│   │   ├── services/        # detector, video_processor, report_generator
│   │   └── utils/           # File validation & storage helpers
│   ├── outputs/             # Annotated images, videos, and PDFs
│   ├── tests/               # 14 pytest unit & integration tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # Shared layout & navigation components
│   │   ├── pages/
│   │   │   ├── HomePage.jsx
│   │   │   ├── AnalyzePage.jsx
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── HistoryPage.jsx
│   │   │   └── AnalysisDetailPage.jsx
│   │   ├── services/
│   │   │   └── api.js       # Axios API wrapper
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css        # Custom CSS design system
│   ├── package.json
│   └── vite.config.js
├── ml/
│   ├── configs/             # YOLO dataset & training configs
│   ├── train.py             # Model training pipeline
│   ├── evaluate.py          # Validation metrics reporting
│   └── prepare_dataset.py   # Dataset extraction & split script
├── README.md
└── progress.md
```

---

For the full project overview and ML training instructions, see the [root README](../README.md).
