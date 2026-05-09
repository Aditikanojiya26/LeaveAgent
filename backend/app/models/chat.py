from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    thread_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    title = Column(
        String,
        default="New Chat"
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    # 🔥 Relationships
    user = relationship(
        "User",
        back_populates="chat_sessions"
    )

    messages = relationship(
        "ChatMessage",
        back_populates="chat_session",
        cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)

    chat_id = Column(
        Integer,
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False
    )

    role = Column(
        String,
        nullable=False
    )  # "user" or "assistant"

    content = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    # 🔥 Relationship
    chat_session = relationship(
        "ChatSession",
        back_populates="messages"
    )