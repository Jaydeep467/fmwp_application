from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.database import get_db, Account
from app.schemas.schemas import (
    TransactionCreate, TransactionResponse, TransactionFilter,
    AccountCreate, AccountResponse
)
from app.core.security import get_current_user
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])
accounts_router = APIRouter(prefix="/accounts", tags=["Accounts"])


@accounts_router.post("", response_model=AccountResponse, status_code=201)
def create_account(data: AccountCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    account = Account(user_id=current_user["user_id"], **data.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@accounts_router.get("", response_model=List[AccountResponse])
def get_accounts(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Account).filter(Account.user_id == current_user["user_id"]).all()


@router.post("", response_model=TransactionResponse, status_code=201)
def create_transaction(data: TransactionCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return TransactionService.create_transaction(db, current_user["user_id"], data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("", response_model=List[TransactionResponse])
def get_transactions(
    type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    is_anomaly: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filters = TransactionFilter(
        type=type, category=category,
        min_amount=min_amount, max_amount=max_amount,
        is_anomaly=is_anomaly,
    )
    return TransactionService.get_transactions(db, current_user["user_id"], filters, skip, limit)


@router.get("/anomalies", response_model=List[TransactionResponse])
def get_anomalies(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    filters = TransactionFilter(is_anomaly=True)
    return TransactionService.get_transactions(db, current_user["user_id"], filters)


@router.get("/analytics/spending")
def get_spending(
    month: int = Query(datetime.utcnow().month),
    year: int = Query(datetime.utcnow().year),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService.get_spending_by_category(db, current_user["user_id"], month, year)


@router.get("/analytics/trend")
def get_trend(
    months: int = Query(6, le=24),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TransactionService.get_monthly_trend(db, current_user["user_id"], months)