from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models.database import TransactionType, TransactionCategory


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    currency: str = "USD"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


class AccountCreate(BaseModel):
    name: str
    account_type: str = "checking"
    balance: float = 0.0
    currency: str = "USD"


class AccountResponse(BaseModel):
    id: int
    name: str
    account_type: str
    balance: float
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    account_id: int
    amount: float
    currency: str = "USD"
    type: TransactionType
    category: TransactionCategory = TransactionCategory.OTHER
    description: Optional[str] = None
    merchant: Optional[str] = None


class TransactionResponse(BaseModel):
    id: int
    account_id: int
    amount: float
    currency: str
    type: TransactionType
    category: TransactionCategory
    description: Optional[str]
    merchant: Optional[str]
    is_anomaly: bool
    anomaly_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionFilter(BaseModel):
    type: Optional[TransactionType] = None
    category: Optional[TransactionCategory] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_anomaly: Optional[bool] = None


class BudgetCreate(BaseModel):
    category: TransactionCategory
    limit: float
    month: int
    year: int


class BudgetResponse(BaseModel):
    id: int
    category: TransactionCategory
    limit: float
    spent: float
    month: int
    year: int
    percentage_used: float = 0.0

    class Config:
        from_attributes = True


class SpendingByCategory(BaseModel):
    category: str
    total: float
    count: int
    percentage: float


class MonthlyTrend(BaseModel):
    month: str
    income: float
    expenses: float
    net: float


class DashboardSummary(BaseModel):
    total_balance: float
    monthly_income: float
    monthly_expenses: float
    savings_rate: float
    anomaly_count: int
    top_categories: List[SpendingByCategory]
    monthly_trend: List[MonthlyTrend]