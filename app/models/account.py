from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.transfer import Transfer


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"), server_default=text("0"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR", server_default=text("'EUR'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    customer: Mapped[Customer] = relationship(back_populates="accounts")
    outgoing_transfers: Mapped[list[Transfer]] = relationship(foreign_keys="Transfer.from_account_id", back_populates="from_account")
    incoming_transfers: Mapped[list[Transfer]] = relationship(foreign_keys="Transfer.to_account_id", back_populates="to_account")
