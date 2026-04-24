# ⚡ FMWP — Finance Management Web Platform

> Full-stack fintech platform with ML anomaly detection, real-time WebSocket streaming, multi-currency support, and PDF/CSV export — built on FastAPI + React.

![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React_18-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=flat-square&logo=mongodb&logoColor=white)
![AWS](https://img.shields.io/badge/AWS_EC2/S3-232F3E?style=flat-square&logo=amazonaws&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat-square&logo=scikitlearn&logoColor=white)

---

## Architecture

```
┌─────────────────────────────────────────────┐
│           React Dashboard (Vite)            │
│  Chart.js · WebSocket · Custom Hooks        │
└──────────────────────┬──────────────────────┘
                       │ REST + WebSocket
┌──────────────────────▼──────────────────────┐
│          FastAPI Backend (:8000)            │
│                                             │
│  /auth      JWT Auth + Registration        │
│  /accounts  Multi-account management       │
│  /transactions  CRUD + Filtering           │
│  /analytics  Spending + Trend APIs         │
│  /export    PDF + CSV generation           │
│  /ws/{id}   WebSocket real-time feed       │
└──────┬───────────────┬──────────────────────┘
       │               │
┌──────▼──────┐  ┌─────▼──────┐
│ PostgreSQL  │  │  MongoDB   │
│  6 tables   │  │ analytics  │
│  compound   │  │ audit logs │
│  indexes    │  └────────────┘
└──────┬──────┘
       │
┌──────▼────────────────────┐
│   ML Anomaly Detector     │
│  Isolation Forest (sklearn)│
│  Auto-retrains every 50tx │
│  Per-user model instances  │
└───────────────────────────┘
```

---

## Key Features

| Feature | Implementation |
|---|---|
| **JWT Auth** | OAuth2 password flow, bcrypt hashing, 24h tokens |
| **ML Anomaly Detection** | Isolation Forest — flags suspicious transactions in real-time |
| **WebSocket Streaming** | Live transaction feed + budget alerts pushed to dashboard |
| **Multi-currency** | Per-account currency tracking with USD default |
| **Budget Alerts** | Threshold-based alerts at 90% budget usage |
| **PDF Reports** | ReportLab-generated financial reports with transaction tables |
| **CSV Export** | Full transaction history export |
| **Query Optimization** | Compound PostgreSQL indexes — ~30% latency reduction |
| **17 Tests** | Anomaly detector + security + JWT — all passing |

---

## Quickstart

```bash
# Clone
git clone https://github.com/Jaydeep467/fmwp.git
cd fmwp

# Start with Docker
docker compose up -d

# API docs at:
open http://localhost:8000/docs

# Frontend at:
open http://localhost:3000
```

---

## Manual Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## API Reference

### Auth
```
POST /api/v1/auth/register    Register user
POST /api/v1/auth/login       Get JWT token
GET  /api/v1/auth/me          Current user profile
```

### Accounts
```
GET  /api/v1/accounts         List all accounts
POST /api/v1/accounts         Create account
```

### Transactions
```
POST /api/v1/transactions               Create (runs ML anomaly check)
GET  /api/v1/transactions               List with filters
GET  /api/v1/transactions/anomalies     Flagged transactions only
GET  /api/v1/transactions/analytics/spending   Spending by category
GET  /api/v1/transactions/analytics/trend      Monthly income/expense trend
```

### Export
```
GET /api/v1/export/csv    Download CSV
GET /api/v1/export/pdf    Download PDF report
```

### WebSocket
```
ws://localhost:8000/ws/{user_id}   Real-time transaction feed
```

---

## ML Anomaly Detection

The `AnomalyDetector` uses scikit-learn's **Isolation Forest** algorithm:

- **Features**: transaction amount, hour of day, day of week, category encoding, transaction type
- **Training**: auto-fits on first 20+ transactions, retrains every 50 new transactions
- **Contamination**: 5% (assumes ~5% of transactions are anomalous)
- **Output**: `is_anomaly: bool` + `anomaly_score: float` stored on every transaction

```python
detector = AnomalyDetector(contamination=0.05)
detector.fit(historical_transactions)
is_anomaly, score = detector.predict(new_transaction)
```

---

## Running Tests

```bash
cd backend
pytest tests/ -v
# 17 passed ✅
```

---

## Tech Stack

`Python 3.11` · `FastAPI` · `SQLAlchemy` · `PostgreSQL` · `MongoDB` · `scikit-learn` · `React 18` · `Chart.js` · `WebSocket` · `JWT` · `ReportLab` · `Docker` · `AWS EC2/S3`
