from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime,Text
from sqlalchemy.sql import func
from app.db import Base


from sqlalchemy import JSON

class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    leave_type = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String, nullable=False)

    chat_id = Column(Integer, ForeignKey("chat_sessions.id"))  # ✅ add this
    status = Column(String, default="PENDING")

    # 🔥 AI Fields (IMPORTANT)
    ai_recommendation = Column(String)   # APPROVE / REJECT / NEEDS_REVIEW
    ai_risk = Column(String)             # LOW / MEDIUM / HIGH
    ai_reason = Column(Text)
    ai_blockers = Column(JSON)           # array (tasks/deadlines)
    ai_suggestion = Column(Text)

    # UI summary
    manager_warning = Column(Text)

    created_at = Column(DateTime, server_default=func.now())


class LeaveApproval(Base):
    __tablename__ = "leave_approvals"

    id = Column(Integer, primary_key=True, index=True)

    leave_request_id = Column(
        Integer,
        ForeignKey("leave_requests.id", ondelete="CASCADE"),
        nullable=False
    )

    decided_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    decision = Column(String, nullable=False)  # APPROVED / REJECTED
    reason = Column(String)

    decided_at = Column(DateTime, server_default=func.now())


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    year = Column(Integer, nullable=False)

    casual = Column(Integer, default=8)
    sick = Column(Integer, default=10)
    privilege = Column(Integer, default=12)


class ProjectDeadline(Base):
    __tablename__ = "project_deadlines"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)
    description = Column(String)

    manager_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    deadline_date = Column(Date, nullable=False)

    created_at = Column(DateTime, server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_deadline_id = Column(Integer, ForeignKey("project_deadlines.id"))

    title = Column(String, nullable=False)

    priority = Column(String, nullable=False)  # HIGH / MEDIUM / LOW
    deadline = Column(Date, nullable=False)

    progress = Column(Integer, default=0)  # 0 to 100

    status = Column(String, default="PENDING")  # PENDING / IN_PROGRESS / COMPLETED

    created_at = Column(DateTime, server_default=func.now())