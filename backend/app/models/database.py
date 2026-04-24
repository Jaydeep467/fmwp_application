from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import enum
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class TransactionCategory(str, enum.Enum):
    FOOD = "food"
    TRANSPORT = "transport"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    HEALTHCARE = "healthcare"
    SHOPPING = "shopping"
    SALARY = "salary"
    INVESTMENT = "investment"
    OTHER = "other"


class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name       = Column(String)
    currency        = Column(String(3), default="USD")
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    accounts        = relationship("Account", back_populates="owner")
    budgets         = relationship("Budget", back_populates="owner")


class Account(Base):
    __tablename__ = "accounts"
    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    name         = Column(String, nullable=False)
    account_type = Column(String, default="checking")
    balance      = Column(Float, default=0.0)
    currency     = Column(String(3), default="USD")
    created_at   = Column(DateTime, default=datetime.utcnow)
    owner        = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"
    id            = Column(Integer, primary_key=True, index=True)
    account_id    = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount        = Column(Float, nullable=False)
    currency      = Column(String(3), default="USD")
    type          = Column(Enum(TransactionType), nullable=False)
    category      = Column(Enum(TransactionCategory), default=TransactionCategory.OTHER)
    description   = Column(String)
    merchant      = Column(String)
    is_anomaly    = Column(Boolean, default=False)
    anomaly_score = Column(Float, default=0.0)
    extra_data    = Column(JSONB, default={})
    created_at    = Column(DateTime, default=datetime.utcnow, index=True)
    account       = relationship("Account", back_populates="transactions")


class Budget(Base):
    __tablename__ = "budgets"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    category   = Column(Enum(TransactionCategory), nullable=False)
    limit      = Column(Float, nullable=False)
    spent      = Column(Float, default=0.0)
    month      = Column(Integer, nullable=False)
    year       = Column(Integer, nullable=False)
    alert_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner      = relationship("User", back_populates="budgets")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)