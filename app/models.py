from sqlalchemy import Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base

class Callback(Base):
    __tablename__ = "callbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String, index=True)
    ip: Mapped[str] = mapped_column(String)
    method: Mapped[str] = mapped_column(String)
    headers: Mapped[str] = mapped_column(Text)
    query: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)