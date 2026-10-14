from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, Boolean, DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.transaction import Transaction

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    categories: Mapped[list["Category"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    __table_args__ = (
        Index(
            "uq_users_email_lower",
            func.lower(email),
            unique=True,
        ),
    )