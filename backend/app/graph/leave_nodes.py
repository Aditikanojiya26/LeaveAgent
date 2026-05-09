from typing import Optional, Literal
from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime, date, timedelta
from dateutil import parser
from pydantic import BaseModel
from langchain_core.runnables import RunnableConfig
from sqlalchemy.orm import Session
from app.models.leave import LeaveRequest
from app.llm_config import build_fallback_llm
from app.leave.service import get_or_create_balance
from app.models.leave import LeaveRequest, ProjectDeadline, Task



# Import ChatState from builder to share a single state definition.
# Use TYPE_CHECKING to avoid circular imports at runtime.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.graph.builder import ChatState


llm = build_fallback_llm()


# ── Structured output models ──────────────────────────────────────────────────

class DateExtraction(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class LeaveTypeExtraction(BaseModel):
    leave_type: Optional[Literal["casual", "sick", "privilege"]] = None


date_llm = llm.with_structured_output(DateExtraction)
leave_type_llm = llm.with_structured_output(LeaveTypeExtraction)


# ── Helpers ───────────────────────────────────────────────────────────────────
def check_existing_leave(db, user_id, start_date, end_date):
    return (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.employee_id == user_id,
            LeaveRequest.status.in_(["PENDING", "APPROVED"]),
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
        )
        .first()
    )

def check_project_deadline(db, user_id, start_date, end_date):
    return (
        db.query(ProjectDeadline)
        .filter(
            ProjectDeadline.employee_id == user_id,
            ProjectDeadline.deadline_date >= start_date,
            ProjectDeadline.deadline_date <= end_date,
        )
        .first()
    )

def check_pending_task(db, user_id, start_date, end_date):
    return (
        db.query(Task)
        .filter(
            Task.employee_id == user_id,
            Task.status.in_(["PENDING", "IN_PROGRESS"]),
            Task.deadline >= start_date,
            Task.deadline <= end_date,
        )
        .first()
    )

def last_user_msg(state) -> str:
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            return msg.content
    return ""


def normalize_date(text: str) -> Optional[str]:
    if not text:
        return None

    t = text.strip().lower()
    today = date.today()

    if t == "today":
        return today.strftime("%Y-%m-%d")

    if t == "tomorrow":
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        return parser.parse(t, dayfirst=True).strftime("%Y-%m-%d")
    except Exception:
        return None


def working_days(start: str, end: str) -> int:
    s = datetime.strptime(start, "%Y-%m-%d").date()
    e = datetime.strptime(end, "%Y-%m-%d").date()

    count = 0
    cur = s

    while cur <= e:
        if cur.weekday() < 5:   # Mon–Fri
            count += 1
        cur += timedelta(days=1)

    return count


def _reply(msg: str, step: str, extra: dict = None) -> dict:
    return {
        "step": step,
        "answer": msg,
        "error": None,
        "messages": [AIMessage(content=msg)],
        **(extra or {}),
    }


# ── Date nodes ────────────────────────────────────────────────────────────────

def ask_dates_node(state) -> dict:
    error = state.get("error")

    if error:
        msg = f"⚠️ {error}\n\nPlease try again — what are your start and end dates?"
    else:
        msg = (
            "📅 Let's start with your leave dates.\n"
            "When would you like to take leave?\n\n"
            "Example: from 5th May to 8th May"
        )

    return _reply(msg, "awaiting_dates")


def extract_dates_node(state, config: RunnableConfig) -> dict:
    user_text = last_user_msg(state)

    result = date_llm.invoke(
        f"Extract start_date and end_date from this message. "
        f"Return dates exactly as the user wrote them. Do not convert.\n\n"
        f"Message: {user_text}"
    )

    start = normalize_date(result.start_date)
    end = normalize_date(result.end_date)
    today = date.today()

    errors = []

    if not start:
        errors.append("I couldn't understand the start date.")

    if not end:
        errors.append("I couldn't understand the end date.")

    if start and end:
        s = datetime.strptime(start, "%Y-%m-%d").date()
        e = datetime.strptime(end, "%Y-%m-%d").date()

        if s < today:
            errors.append("Start date can't be in the past.")

        if s > e:
            errors.append("End date can't be before start date.")

    if errors:
        return {"error": " ".join(errors)}

    db = config["configurable"]["db"]
    user_id = config["configurable"]["user_id"]

    # hard block: same employee already applied leave
    existing_leave = check_existing_leave(db, user_id, s, e)

    if existing_leave:
        return {
            "error": (
                f"You already have a leave request from "
                f"{existing_leave.start_date} to {existing_leave.end_date} "
                f"with status {existing_leave.status}. "
                f"Please choose different dates."
            )
        }

    
    days = working_days(start, end)

    return {
        "start_date": start,
        "end_date": end,
        "leave_days": days,
        "manager_warning": None,
        "error": None,
    }

def route_dates(state) -> str:
    if state.get("error"):
        return "ask_dates"
    return "ask_leave_type"


# ── Leave-type nodes ──────────────────────────────────────────────────────────

def ask_leave_type_node(state, config: RunnableConfig) -> dict:
    error = state.get("error")
    db = config["configurable"]["db"]
    user_id = config["configurable"]["user_id"]

    balance = get_or_create_balance(db, user_id)

    balance_lines = (
        f"- Casual — {balance.casual} day(s) left\n"
        f"- Sick — {balance.sick} day(s) left\n"
        f"- Privilege — {balance.privilege} day(s) left"
    )

    if error:
        msg = f"⚠️ {error}\n\nPlease choose a leave type:\n{balance_lines}"
    else:
        start = state.get("start_date")
        end = state.get("end_date")
        days = state.get("leave_days", 0)
        msg = (
            f"✅ Got it! {start} to {end} ({days} working day(s)).\n\n"
            f"What type of leave would you like?\n{balance_lines}"
        )

    return _reply(msg, "awaiting_leave_type")


def extract_leave_type_node(state, config: RunnableConfig) -> dict:
    user_text = last_user_msg(state)

    result = leave_type_llm.invoke(
        f"Extract leave type only. Allowed values: casual, sick, privilege.\n"
        f"Message: {user_text}"
    )

    if not result.leave_type:
        return {"error": "Please say casual, sick, or privilege."}

    db = config["configurable"]["db"]
    user_id = config["configurable"]["user_id"]

    balance = get_or_create_balance(db, user_id)
    available = getattr(balance, result.leave_type, 0)
    leave_days = state.get("leave_days", 0)

    if leave_days > available:
        return {
            "error": (
                f"You need {leave_days} day(s) of {result.leave_type} leave "
                f"but only have {available}. Please choose another type."
            ),
            "leave_type": None,
        }

    msg = f"✅ Got it — {result.leave_type} leave selected."

    return {
        "leave_type": result.leave_type,
        "error": None,
        "step": "ask_reason",      # signals builder what comes next
        "answer": msg,
        "messages": [AIMessage(content=msg)],
    }


def route_leave_type(state) -> str:
    if state.get("error"):
        return "ask_leave_type"
    return "ask_reason"            # was "done" — fixed to match graph node name