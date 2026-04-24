from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
import io
from datetime import datetime

from app.core.config import settings
from app.models.database import create_tables, get_db, Transaction, User
from app.routers.auth import router as auth_router
from app.routers.transactions import router as tx_router, accounts_router
from app.routers.websocket import router as ws_router
from app.core.security import get_current_user
from app.services.export_service import generate_csv, generate_pdf_report
from sqlalchemy.orm import Session

app = FastAPI(
    title="FMWP - Finance Management Web Platform",
    description="Production-grade personal finance API with ML anomaly detection, real-time WebSocket streaming, and multi-currency support.",
    version="1.0.0",
    docs_url="/docs",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router,    prefix=settings.API_V1_PREFIX)
app.include_router(tx_router,      prefix=settings.API_V1_PREFIX)
app.include_router(accounts_router, prefix=settings.API_V1_PREFIX)
app.include_router(ws_router)


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    create_tables()


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "FMWP API", "timestamp": datetime.utcnow().isoformat()}


# ── Export endpoints ──────────────────────────────────────────────────────────
@app.get("/api/v1/export/csv")
def export_csv(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user["user_id"]
    ).order_by(Transaction.created_at.desc()).limit(1000).all()

    tx_list = [
        {
            "id": t.id, "created_at": str(t.created_at),
            "type": t.type.value, "category": t.category.value,
            "description": t.description, "merchant": t.merchant,
            "amount": t.amount, "currency": t.currency,
            "is_anomaly": t.is_anomaly,
        }
        for t in transactions
    ]

    csv_bytes = generate_csv(tx_list)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


@app.get("/api/v1/export/pdf")
def export_pdf(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user["user_id"]
    ).order_by(Transaction.created_at.desc()).limit(50).all()

    tx_list = [{"id": t.id, "created_at": str(t.created_at), "type": t.type.value,
                "category": t.category.value, "description": t.description,
                "amount": t.amount, "is_anomaly": t.is_anomaly} for t in transactions]

    income = sum(t.amount for t in transactions if t.type.value == "income")
    expenses = sum(t.amount for t in transactions if t.type.value == "expense")

    pdf_bytes = generate_pdf_report(
        user_name=user.full_name if user else "User",
        transactions=tx_list,
        summary={
            "income": income, "expenses": expenses,
            "net": income - expenses,
            "savings_rate": ((income - expenses) / income * 100) if income > 0 else 0,
            "anomaly_count": sum(1 for t in transactions if t.is_anomaly),
        },
        month=datetime.utcnow().strftime("%B %Y"),
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=financial_report.pdf"},
    )
