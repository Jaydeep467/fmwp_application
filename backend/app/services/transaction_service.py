from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import datetime
import logging

from app.models.database import Transaction, Account, Budget, TransactionType, TransactionCategory
from app.schemas.schemas import TransactionCreate, TransactionFilter, SpendingByCategory, MonthlyTrend
from app.ml.anomaly_detector import get_detector, retrain_detector

logger = logging.getLogger(__name__)


class TransactionService:

    @staticmethod
    def create_transaction(db: Session, user_id: int, data: TransactionCreate) -> Transaction:
        # Verify account belongs to user
        account = db.query(Account).filter(
            Account.id == data.account_id,
            Account.user_id == user_id
        ).first()
        if not account:
            raise ValueError("Account not found")

        # Run anomaly detection
        tx_dict = {
            "amount": data.amount,
            "type": data.type.value,
            "category": data.category.value,
            "created_at": datetime.utcnow().isoformat(),
        }
        detector = get_detector(user_id)
        is_anomaly, anomaly_score = detector.predict(tx_dict)

        # Create transaction
        transaction = Transaction(
            account_id=data.account_id,
            user_id=user_id,
            amount=data.amount,
            currency=data.currency,
            type=data.type,
            category=data.category,
            description=data.description,
            merchant=data.merchant,
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
        )
        db.add(transaction)

        # Update account balance
        if data.type == TransactionType.INCOME:
            account.balance += data.amount
        elif data.type == TransactionType.EXPENSE:
            account.balance -= data.amount

        # Update budget spending
        TransactionService._update_budget(db, user_id, data)

        db.commit()
        db.refresh(transaction)

        # Retrain anomaly detector periodically
        tx_count = db.query(Transaction).filter(Transaction.user_id == user_id).count()
        if tx_count % 50 == 0:  # Retrain every 50 transactions
            TransactionService._retrain_detector(db, user_id)

        if is_anomaly:
            logger.warning(
                f"Anomaly detected for user {user_id}: "
                f"amount={data.amount}, score={anomaly_score}"
            )

        return transaction

    @staticmethod
    def get_transactions(
        db: Session,
        user_id: int,
        filters: Optional[TransactionFilter] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Transaction]:
        query = db.query(Transaction).filter(Transaction.user_id == user_id)

        if filters:
            if filters.type:
                query = query.filter(Transaction.type == filters.type)
            if filters.category:
                query = query.filter(Transaction.category == filters.category)
            if filters.min_amount:
                query = query.filter(Transaction.amount >= filters.min_amount)
            if filters.max_amount:
                query = query.filter(Transaction.amount <= filters.max_amount)
            if filters.start_date:
                query = query.filter(Transaction.created_at >= filters.start_date)
            if filters.end_date:
                query = query.filter(Transaction.created_at <= filters.end_date)
            if filters.is_anomaly is not None:
                query = query.filter(Transaction.is_anomaly == filters.is_anomaly)

        return query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_spending_by_category(db: Session, user_id: int, month: int, year: int) -> List[SpendingByCategory]:
        results = db.query(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
        ).filter(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            func.extract("month", Transaction.created_at) == month,
            func.extract("year", Transaction.created_at) == year,
        ).group_by(Transaction.category).all()

        total_spending = sum(r.total for r in results) or 1

        return [
            SpendingByCategory(
                category=r.category.value,
                total=round(r.total, 2),
                count=r.count,
                percentage=round((r.total / total_spending) * 100, 1),
            )
            for r in results
        ]

    @staticmethod
    def get_monthly_trend(db: Session, user_id: int, months: int = 6) -> List[MonthlyTrend]:
        results = db.query(
            func.extract("year", Transaction.created_at).label("year"),
            func.extract("month", Transaction.created_at).label("month"),
            Transaction.type,
            func.sum(Transaction.amount).label("total"),
        ).filter(
            Transaction.user_id == user_id
        ).group_by("year", "month", Transaction.type).all()

        trend_map = {}
        for r in results:
            key = f"{int(r.year)}-{int(r.month):02d}"
            if key not in trend_map:
                trend_map[key] = {"income": 0, "expenses": 0}
            if r.type == TransactionType.INCOME:
                trend_map[key]["income"] += r.total
            elif r.type == TransactionType.EXPENSE:
                trend_map[key]["expenses"] += r.total

        return [
            MonthlyTrend(
                month=k,
                income=round(v["income"], 2),
                expenses=round(v["expenses"], 2),
                net=round(v["income"] - v["expenses"], 2),
            )
            for k, v in sorted(trend_map.items())[-months:]
        ]

    @staticmethod
    def _update_budget(db: Session, user_id: int, data: TransactionCreate):
        if data.type != TransactionType.EXPENSE:
            return
        now = datetime.utcnow()
        budget = db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.category == data.category,
            Budget.month == now.month,
            Budget.year == now.year,
        ).first()
        if budget:
            budget.spent += data.amount
            if budget.spent >= budget.limit * 0.9 and not budget.alert_sent:
                budget.alert_sent = True
                logger.warning(
                    f"Budget alert: user {user_id} has used "
                    f"{budget.spent:.2f}/{budget.limit:.2f} for {data.category.value}"
                )

    @staticmethod
    def _retrain_detector(db: Session, user_id: int):
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(Transaction.created_at.desc()).limit(500).all()

        tx_list = [
            {
                "amount": t.amount,
                "type": t.type.value,
                "category": t.category.value,
                "created_at": t.created_at.isoformat(),
            }
            for t in transactions
        ]
        retrain_detector(user_id, tx_list)
