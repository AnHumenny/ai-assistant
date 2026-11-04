from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from backend.app.core.db.base import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str] = mapped_column(
        String(64), nullable=False, default="general"
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_with: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(384), nullable=True
    )
