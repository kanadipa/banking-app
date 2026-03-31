from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, UniqueConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, func, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.account import Account


class TransferType(StrEnum):
    transfer = "transfer"
    deposit = "deposit"


class TransferStatus(StrEnum):
    completed = "completed"
    failed = "failed"


class Transfer(Base):
    __tablename__ = "transfers"
    __table_args__ = (
        UniqueConstraint(
            "from_account_id",
            "to_account_id",
            "reference",
            "amount",
            name="uq_transfer_from_account_reference"),
        CheckConstraint("amount > 0", name="transfers_amount_positive"),
        Index(
            "transfers_reference_unique",
            "reference",
            unique=True,
            postgresql_where=text("reference IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=True, index=True)
    to_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    type: Mapped[TransferType] = mapped_column(SAEnum(TransferType, name="transfer_type"), nullable=False)
    status: Mapped[TransferStatus] = mapped_column(SAEnum(TransferStatus, name="transfer_status"), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    requested_by: Mapped[str] = mapped_column(String(100), nullable=False)
    balance_after: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    from_account: Mapped[Account] = relationship(foreign_keys=[from_account_id], back_populates="outgoing_transfers")
    to_account: Mapped[Account] = relationship(foreign_keys=[to_account_id], back_populates="incoming_transfers")
