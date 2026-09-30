# AI RoadGuard — Frontend

React 19 + Vite frontend for the **Pothole & Road Damage Detection** system. Provides an interactive dashboard to upload road images/videos, view AI-annotated results, browse inspection history, and download engineering PDF reports.

---

## Prerequisites

| Tool | Version |
|------|---------|
| Node.js | 18 or later |
| npm | 9 or later |

---

## Getting Started

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start the Development Server

```bash
npm run dev
```

The app will be available at **http://localhost:5173**

> **Note:** The backend API must be running at `http://127.0.0.1:8000` for analysis, dashboard, and report features to work. See the [backend README](../backend/) or the [root README](../README.md) for setup instructions.

---

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start local dev server with Hot Module Replacement (HMR) |
| `npm run build` | Build optimised production bundle to `dist/` |
| `npm run preview` | Locally preview the production build |
| `npm run lint` | Run Oxlint static analysis |

---

## Running Against the Backend

1. Start the FastAPI backend first:

   ```bash
   # From the repository root
   cd backend
   python -m venv venv
   venv\Scripts\activate        # Windows
   # source venv/bin/activate   # macOS / Linux
   pip install -r requirements.txt
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

2. Then start the frontend:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Open **http://localhost:5173** in your browser.

---

## Production Build

```bash
npm run build
```

Output is placed in `frontend/dist/`. You can serve it with any static host or preview it locally:

```bash
npm run preview
```

---

## Tech Stack

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
frontend/
├── public/
├── src/
│   ├── components/          # Shared layout & navigation components
│   ├── pages/
│   │   ├── HomePage.jsx         # Landing page
│   │   ├── AnalyzePage.jsx      # Image / video upload & results
│   │   ├── DashboardPage.jsx    # Aggregate analytics
│   │   ├── HistoryPage.jsx      # Past inspections list
│   │   └── AnalysisDetailPage.jsx  # Individual result view
│   ├── services/
│   │   └── api.js           # Axios API wrapper (base URL, helpers)
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css            # Custom CSS design system
├── package.json
├── vite.config.js
└── README.md
```

---

For full project documentation including ML training and backend API reference, see the [root README](../README.md).
