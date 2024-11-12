from datetime import datetime

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from app.schemas import Tags

class Base(DeclarativeBase):
    pass

class Todo(Base):
    """Todo model
    """
    __tablename__ = 'todos'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(nullable=False)
    details: Mapped[str] = mapped_column(nullable=False)
    completed: Mapped[bool] = mapped_column(default=False, nullable=False)
    tag: Mapped[str] = mapped_column(default=Tags.plans, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f'<Todo {self.id}>'
