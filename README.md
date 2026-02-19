# RWA with UI - Local Setup Guide

This project has two apps:

- **Backend**: FastAPI service (default: `http://127.0.0.1:8000`)
- **Frontend**: Angular UI (default: `http://localhost:4200`)

The frontend calls the backend at `http://<host>:8000`.

## Prerequisites

- **Python 3.13+** (as declared in `Backend/pyproject.toml`)
- **Node.js 18+** and npm
- Git (optional)

## 1) Backend setup (first time)

Open a terminal in `Backend`:

```bash
cd Backend
```

Create and activate a virtual environment (Windows CMD):

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Environment variables

Create `Backend/.env` and add required keys:

```env
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
LANGSMITH_API_KEY=your_key_here
```

## 2) Run backend

From `Backend` (with virtual environment activated):

```bash
python webapp_api.py
```

Health check:

- `http://127.0.0.1:8000/health`

---

## 3) Frontend setup (first time)

Open a second terminal in `Frontend`:

```bash
cd Frontend
npm install
```

## 4) Run frontend

From `Frontend`:

```bash
ng serve
```

Open:

- `http://localhost:4200`

---
