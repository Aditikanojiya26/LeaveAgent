from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.user import User
from app.models.leave import LeaveRequest,LeaveApproval
from app.auth.routes import get_current_user
from app.leave.service import get_or_create_balance
from sqlalchemy import select
from fastapi import HTTPException
from app.models.chat import ChatMessage

router = APIRouter(prefix="/manager")


@router.get("/leave-requests")
def get_team_leave_requests(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    employee_ids = select(User.id).where(User.manager_id == current_user_id)

    requests = (
    db.query(LeaveRequest, User.name)
    .join(User, LeaveRequest.employee_id == User.id)
    .filter(
        LeaveRequest.employee_id.in_(employee_ids),
        LeaveRequest.status == "PENDING",
    )
    .all()
)

    result = []

    for leave, employee_name in requests:
        result.append({
            "id": leave.id,
            "employee_id": leave.employee_id,
            "employee_name": employee_name,

            "leave_type": leave.leave_type,
            "start_date": leave.start_date,
            "end_date": leave.end_date,
            "reason": leave.reason,
            "status": leave.status,

            "ai_recommendation": leave.ai_recommendation,
            "ai_risk": leave.ai_risk,
            "ai_reason": leave.ai_reason,
            "ai_blockers": leave.ai_blockers,
            "ai_suggestion": leave.ai_suggestion,
        })

    return result


@router.patch("/leave-requests/{request_id}/decision")
def manager_leave_decision(
    request_id: int,
    decision: str,  # "APPROVED" or "REJECTED"
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user)
):
    leave = (
        db.query(LeaveRequest)
        .join(User, LeaveRequest.employee_id == User.id)    
        .filter(
            LeaveRequest.id == request_id,
            User.manager_id == current_user_id,
            LeaveRequest.status == "PENDING"
        )
        .first()
    )

    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if decision not in ["APPROVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Invalid decision")

    leave.status = decision

    if decision == "APPROVED":
        content = (
            f"Your leave request from {leave.start_date} to {leave.end_date} "
            f"has been approved by your manager."
        )
    else:
        content = (
            f"Your leave request from {leave.start_date} to {leave.end_date} "
            f"has been rejected by your manager."
        )

    chat_msg = ChatMessage(
        chat_id=leave.chat_id,
        role="assistant",
        content=content
    )

    db.add(chat_msg)
    db.commit()

    return {
        "message": f"Leave request {decision.lower()} successfully",
        "status": decision
    }