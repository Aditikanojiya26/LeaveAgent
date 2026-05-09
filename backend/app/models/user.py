from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)

    role = Column(String, default="EMPLOYEE")
    manager_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    manager = relationship("User", remote_side=[id])

    chat_sessions = relationship(
            "ChatSession",
            back_populates="user",
            cascade="all, delete-orphan"
        )