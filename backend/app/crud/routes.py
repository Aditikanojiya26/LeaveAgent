from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.user import User
from app.models.leave import LeaveRequest,LeaveApproval
from app.auth.routes import get_current_user
from app.leave.service import get_or_create_balance

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/managers")
def get_managers(db: Session = Depends(get_db)):
    managers = db.query(User).filter(User.role == "manager").all()

    return [
        {
            "id": m.id,
            "name": m.name
        }
        for m in managers
    ]


# GET /manager/leave-requests
@router.get("/manager/leave-requests")
def get_team_leave_requests(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # Get all employees under this manager
    employee_ids = (
        db.query(User.id)
        .filter(User.manager_id == current_user.id)
        .subquery()
    )

    requests = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.employee_id.in_(employee_ids),
            LeaveRequest.status == "PENDING",
        )
        .order_by(LeaveRequest.created_at.desc())
        .all()
    )
    return requests


# PATCH /manager/leave-requests/{id}/decision
@router.patch("/manager/leave-requests/{leave_id}/decision")
def decide_leave(
    leave_id: int,
    decision: str,
    reason: str = "",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()

    if not leave:
        return {"error": "Leave request not found"}

    decision = decision.upper()
    leave.status = decision

    approval = LeaveApproval(
        leave_request_id=leave_id,
        decided_by=current_user.id,
        decision=decision,
        reason=reason,
    )
    db.add(approval)

    leave_days = (leave.end_date - leave.start_date).days + 1

    if decision == "APPROVED":
        balance = get_or_create_balance(db, leave.employee_id)

        leave_type = leave.leave_type.lower()  # CASUAL -> casual

        current_balance = getattr(balance, leave_type)

        if current_balance < leave_days:
            return {"error": "Insufficient leave balance"}

        setattr(balance, leave_type, current_balance - leave_days)

    db.commit()
    return {"status": "ok"}