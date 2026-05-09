
from datetime import date, datetime
from app.models.leave import LeaveBalance
from app.models.leave import LeaveRequest
from datetime import datetime


def get_or_create_balance(db, employee_id: int):
    current_year = date.today().year

    balance = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == employee_id,
        LeaveBalance.year == current_year
    ).first()

    if not balance:
        balance = LeaveBalance(
            employee_id=employee_id,
            year=current_year,
            casual=8,
            sick=10,
            privilege=12,
        )
        db.add(balance)
        db.commit()
        db.refresh(balance)

    return balance


def get_leave_balance(db, employee_id: int, leave_type: str):
    balance = get_or_create_balance(db, employee_id)
    return getattr(balance, leave_type, 0)


def calculate_leave_days(start: str, end: str):
    start_dt = datetime.strptime(start, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end, "%Y-%m-%d").date()
    return (end_dt - start_dt).days + 1


def apply_leave_request(
    db,
    user_id,
    chat_id,   # ✅ add this
    leave_type,
    start_date,
    end_date,
    reason,
    ai_recommendation=None,
    ai_risk=None,
    ai_reason=None,
    ai_blockers=None,
    ai_suggestion=None,
    manager_warning=None,
):
    leave = LeaveRequest(
        employee_id=user_id,
        chat_id=chat_id,   # ✅ now available
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        status="PENDING",

        ai_recommendation=ai_recommendation,
        ai_risk=ai_risk,
        ai_reason=ai_reason,
        ai_blockers=ai_blockers or [],
        ai_suggestion=ai_suggestion,
        manager_warning=manager_warning,
    )

    db.add(leave)
    db.commit()
    db.refresh(leave)

    return leave