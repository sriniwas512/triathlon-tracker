# 🏊 🚴 🏃 Triathlon Competition Tracker — March 2026

[![Run Tests](https://github.com/sriniwas512/triathlon-tracker/actions/workflows/test.yml/badge.svg)](https://github.com/sriniwas512/triathlon-tracker/actions/workflows/test.yml)

A head-to-head triathlon challenge tracker for March 2026. Athletes connect their Strava accounts; the app tracks Cycling, Running, and Swimming activities across 5 weekend blocks, scores them by calories, and displays a live dashboard with projections.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python FastAPI |
| Database | Firebase Firestore |
| Frontend | React + Chart.js (Vite) |
| Auth | Strava OAuth 2.0 |
| Backend Hosting | Railway |
| Frontend Hosting | Firebase Hosting |
| CI/CD | GitHub Actions |

## Quick Start

### 1. Register a Strava App

1. Go to [strava.com/settings/api](https://www.strava.com/settings/api)
2. Create a new application
3. Set **Authorization Callback Domain** to your backend URL (e.g. `localhost` for development, or your Railway production domain)
4. Note the **Client ID** and **Client Secret**

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your Strava credentials and Firebase service account:

```env
STRAVA_CLIENT_ID=your_id
STRAVA_CLIENT_SECRET=your_secret
FIREBASE_SERVICE_ACCOUNT_JSON=path/to/service-account.json
# PLAYER names are now synchronized from Strava automatically
TIMEZONE_DISPLAY=Asia/Singapore
FRONTEND_URL=http://localhost:5173
API_BASE_URL=http://localhost:8000
```

### 3. Run Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The backend seeds player slots and block definitions on startup.

### 4. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

### 5. Connect Athletes

1. Navigate to `/login`
2. Click "Connect with Strava" for each player
3. Complete OAuth authorization on Strava
4. Once both players are connected, enter the dashboard

### 6. Sync & Score

- Click **🔄 Sync Strava** in the header to pull latest activities
- Scores are automatically calculated every Monday 12:00 UTC via `POST /api/scores/calculate-job`
- Manually trigger scoring: `POST /api/scores/calculate/{block_id}`

## Running Tests

```bash
pip install -r backend/requirements.txt
python -m pytest backend/tests/ -v
```

## Seed Test Data

```bash
python scripts/seed_test_data.py
```

This creates mock activities across all 5 blocks demonstrating: clean sweeps, ties, missing sports, and the Block 1 edge case.

## Deployment

### Backend → Railway

Push to `main` triggers `.github/workflows/deploy-backend.yml`:
- Installs Railway CLI
- Deploys the service to Railway using your `RAILWAY_TOKEN`

### Frontend → Firebase Hosting

Push to `main` triggers `.github/workflows/deploy-frontend.yml`:
- Builds React app with Vite
- Deploys to Firebase Hosting

### Required GitHub Secrets

| Secret | Description |
|---|---|
| `RAILWAY_TOKEN` | Railway project CI/CD token |
| `STRAVA_CLIENT_ID` | Strava app client ID |
| `STRAVA_CLIENT_SECRET` | Strava app client secret |
| `FRONTEND_URL` | Deployed frontend URL |
| `FIREBASE_SERVICE_ACCOUNT` | Firebase service account for hosting |
| `FIREBASE_PROJECT_ID` | Firebase project ID |
| `API_BASE_URL` | Backend API URL for frontend build |
| `TIMEZONE_DISPLAY` | `Asia/Singapore` or `Europe/Munich` |

## Competition Rules

- **5 weekend blocks** in March 2026
- **3 sports**: Cycling, Running, Swimming (Block 1: Swimming only)
- **Scoring**: Higher calories = 2pts, tie = 1pt each, solo = 2pts
- **Clean Sweep Bonus**: Win all 3 sports when both log all 3 → +1 bonus point
- **Maximum**: 31 points (3 + 4×7)

## Project Structure

```
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py             # Block definitions, sport mapping
│   ├── firebase_client.py    # Firestore singleton
│   ├── routers/              # API route handlers
│   ├── services/             # Business logic
│   ├── tests/                # Unit tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/            # LoginPage, DashboardPage
│   │   ├── components/       # Dashboard panels
│   │   ├── api.js            # API client
│   │   └── index.css         # Design system
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── scripts/
│   └── seed_test_data.py
├── .github/workflows/        # CI/CD
├── .env.example
└── README.md
```
