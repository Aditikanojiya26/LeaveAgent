from typing import TypedDict, Annotated, Literal, Optional,List
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from pydantic import BaseModel,Field
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from app.llm_config import build_fallback_llm
from app.leave.service import apply_leave_request
from app.models.leave import Task, ProjectDeadline,LeaveRequest
from datetime import datetime
from app.models.user import User
from concurrent.futures import ThreadPoolExecutor
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



from app.graph.leave_nodes import (
    ask_dates_node,
    extract_dates_node,
    route_dates,
    ask_leave_type_node,
    extract_leave_type_node,
    route_leave_type,
)

load_dotenv()

llm = build_fallback_llm()


class ChatState(TypedDict):
    messages: Annotated[list, add_messages]
 
    # Flow control
    step:   Optional[str]
    answer: Optional[str]
    error:  Optional[str]
 
    # Leave dates
    start_date:  Optional[str]
    end_date:    Optional[str]
    leave_days:  Optional[int]
    leave_type:  Optional[Literal["casual", "sick", "privilege"]]
 
    # Reason HITL
    reason_raw:      Optional[str]
    reason_polished: Optional[str]
    reason_approved: Optional[bool]
 
    # Confirmation
    confirm_intent: Optional[str]
 
    # ── Work recommendation (were missing before) ──────────────────────────
    work_recommendation: Optional[Literal["APPROVE", "REJECT", "NEEDS_REVIEW"]]
    work_risk:           Optional[Literal["LOW", "MEDIUM", "HIGH"]]
    work_reason:         Optional[str]
    work_blockers:       Optional[List[str]]
    work_suggestion:     Optional[str]
 
    # Shown to manager on the leave card
    manager_warning: Optional[str]
 


class ConfirmIntent(BaseModel):
    intent: Literal["confirm", "cancel", "unclear"]


confirm_llm = llm.with_structured_output(ConfirmIntent)




# ── Thresholds (tweak without touching logic) ─────────────────────────────────
HIGH_RISK_TEAM_LEAVE_COUNT = 2      # ≥ this many team members on leave → HIGH risk
MEDIUM_RISK_TEAM_LEAVE_COUNT = 1    # ≥ this → MEDIUM risk
HIGH_PROGRESS_THRESHOLD = 80        # task progress % considered "nearly done"
 
 
# ── Structured LLM output ─────────────────────────────────────────────────────
 
class WorkDecision(BaseModel):
    recommendation: Literal["APPROVE", "REJECT", "NEEDS_REVIEW"]
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    reason: str = Field(description="Plain-language explanation for the manager (2–3 sentences)")
    blocking_items: List[str] = Field(
        default_factory=list,
        description="Specific tasks or deadlines that block approval. Empty if none.",
    )
    suggestion: str = Field(
        default="",
        description="Actionable suggestion for the employee or manager (handover, delegation, rescheduling, etc.)",
    )
    


work_decision_llm = llm.with_structured_output(WorkDecision)




def get_last_user_message(state: ChatState) -> str:
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            return msg.content
    return ""

def _fetch_tasks(db, user_id, start_date, end_date):
    
    return (
        db.query(Task)
        .filter(
            Task.employee_id == user_id,
            Task.status.in_(["PENDING", "IN_PROGRESS"]),
            Task.deadline >= start_date,
            Task.deadline <= end_date,
        )
        .all()
    )


def _fetch_deadlines(db, user_id, start_date, end_date):
    
    return (
        db.query(ProjectDeadline)
        .filter(
            ProjectDeadline.employee_id == user_id,
            ProjectDeadline.deadline_date >= start_date,
            ProjectDeadline.deadline_date <= end_date,
        )
        .all()
    )


def _fetch_team_leaves(db, user_id, start_date, end_date):
    current_user = db.query(User).filter(User.id == user_id).first()
    manager_id = current_user.manager_id  # who manages this employee

    # Get all teammates = same manager, excluding self
    teammate_ids = (
            db.query(User.id)
            .filter(
                User.manager_id == manager_id,
                User.id != user_id,
            )
            .subquery()
        )

    return (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.employee_id.in_(teammate_ids),
            LeaveRequest.status == "APPROVED",
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
        )
        .all()
    )

def _run_queries(db, user_id, start_date, end_date):
    tasks = _fetch_tasks(db, user_id, start_date, end_date)
    deadlines = _fetch_deadlines(db, user_id, start_date, end_date)
    leaves = _fetch_team_leaves(db, user_id, start_date, end_date)

    return tasks, deadlines, leaves
 
def _build_tasks_context(tasks) -> list[dict]:
    return [
        {
            "title":    t.title,
            "priority": t.priority,          # HIGH / MEDIUM / LOW
            "deadline": str(t.deadline),
            "status":   t.status,
            "progress": f"{t.progress}%",    # ← was missing before
            "nearly_done": t.progress >= HIGH_PROGRESS_THRESHOLD,
        }
        for t in tasks
    ]
 
 
def _build_deadlines_context(deadlines) -> list[dict]:
    return [
        {
            "title":       p.title,
            "deadline":    str(p.deadline_date),
            "description": p.description or "N/A",
        }
        for p in deadlines
    ]
 
 
def _build_team_leaves_context(team_leaves) -> list[dict]:
    return [
        {
            "employee_id": l.employee_id,
            "from":        str(l.start_date),
            "to":          str(l.end_date),
        }
        for l in team_leaves
    ]

def _build_prompt(state, tasks_data, deadlines_data, team_leaves_data) -> str:
    return f"""
You are an enterprise HR leave approval assistant.

Analyze the leave request and return a professional decision.

DECISION RULES:
- REJECT:
  * Any HIGH priority task with progress < 80%
  * Any critical project deadline during leave period

- NEEDS_REVIEW:
  * MEDIUM priority tasks with approaching deadlines
  * {HIGH_RISK_TEAM_LEAVE_COUNT}+ teammates already on leave
  * HIGH priority tasks nearly completed but still active

- APPROVE:
  * No operational conflicts
  * Only LOW priority tasks affected

LEAVE REQUEST:
- Start Date: {state.get("start_date")}
- End Date: {state.get("end_date")}
- Total Days: {state.get("leave_days")}
- Leave Type: {state.get("leave_type")}
- Reason: {state.get("reason_polished")}

EMPLOYEE TASKS:
{tasks_data or "No active tasks"}

PROJECT DEADLINES:
{deadlines_data or "No overlapping deadlines"}

TEAM AVAILABILITY:
{len(team_leaves_data)} teammate(s) on leave
{team_leaves_data or "No overlapping team leaves"}

IMPORTANT:
Return ALL fields.

Required Output Format:
{{
  "recommendation": "APPROVE | REJECT | NEEDS_REVIEW",
  "risk_level": "LOW | MEDIUM | HIGH",
  "reason": "Detailed professional explanation",
  "blocking_items": ["exact task/deadline names"],
  "suggestion": "Specific actionable recommendation"
}}

RULES:
- blocking_items must contain exact titles only
- suggestion must be concise and actionable
- response must be valid JSON only
"""
 
# ── Manager warning formatter ─────────────────────────────────────────────────
 
def _format_manager_warning(decision: WorkDecision, state) -> str:
    risk_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(decision.risk_level, "⚪")
    rec_emoji  = {"APPROVE": "✅", "NEEDS_REVIEW": "⚠️", "REJECT": "❌"}.get(decision.recommendation, "❓")

    blockers = (
        "\n".join(f"  • {b}" for b in decision.blocking_items)
        if decision.blocking_items else "  None"
    )

    lines = [
        f"{rec_emoji} AI Recommendation: {decision.recommendation}",
        f"{risk_emoji} Risk Level: {decision.risk_level}",
        "",
        f"Analysis: {decision.reason}",
        "",
        f"Blocking items:\n{blockers}",
    ]
    if decision.suggestion:
        lines += ["", f"Suggestion: {decision.suggestion}"]

    print(lines)

    return "\n".join(lines)
 
 
# ── The node ──────────────────────────────────────────────────────────────────
 
def work_recommendation_node(state, config: RunnableConfig):
    from app.llm_config import build_fallback_llm
 
    db      = config["configurable"]["db"]
    user_id = config["configurable"]["user_id"]
 
    start_date = datetime.fromisoformat(state["start_date"]).date()
    end_date   = datetime.fromisoformat(state["end_date"]).date()
 
    # ── 1. Fetch data (parallel) ───────────────────────────────────────────
    try:
        tasks, deadlines, team_leaves = _run_queries(
            db, user_id, start_date, end_date
        )
    except Exception as exc:
        logger.error("DB fetch failed in work_recommendation_node: %s", exc)
        # Fallback: sequential
        tasks      = _fetch_tasks(db, user_id, start_date, end_date)
        deadlines  = _fetch_deadlines(db, user_id, start_date, end_date)
        team_leaves = _fetch_team_leaves(db, user_id, start_date, end_date)
 
    # ── 2. Build structured context ────────────────────────────────────────
    tasks_data     = _build_tasks_context(tasks)
    deadlines_data = _build_deadlines_context(deadlines)
    team_leaves_data = _build_team_leaves_context(team_leaves)
 
    # ── 3. Build prompt & call LLM ─────────────────────────────────────────
    prompt = _build_prompt(state, tasks_data, deadlines_data, team_leaves_data)
 
    llm = build_fallback_llm()
    work_decision_llm = llm.with_structured_output(WorkDecision)
 
    
    decision: WorkDecision = work_decision_llm.invoke(prompt)
    
        
    
 
    # ── 4. Format manager warning ──────────────────────────────────────────
    manager_warning = _format_manager_warning(decision, state)
 
    return {
        # Declared in ChatState (add these if missing):
        "work_recommendation": decision.recommendation,
        "work_risk":           decision.risk_level,
        "work_reason":         decision.reason,
        "work_blockers":       decision.blocking_items,
        "work_suggestion":     decision.suggestion,
        "manager_warning":     manager_warning,
    }
 
# ---------------- Reason HITL ----------------

def ask_reason_node(state: ChatState):
    msg = "📝 Why are you taking leave? Write your reason and I will refine it professionally."

    return {
        "step": "awaiting_reason",
        "answer": msg,
        "messages": [AIMessage(content=msg)],
    }


def refine_reason_node(state: ChatState):
    user_text = get_last_user_message(state).strip()

    approved_words = {
        "yes", "ok", "okay", "approve", "approved",
        "fine", "looks good", "use it"
    }

    if state.get("reason_polished") and user_text.lower() in approved_words:
        return {
            "reason_approved": True,
            "step": "ready_for_preview",
        }

    response = llm.invoke(
    f"""
You are an HR assistant rewriting employee leave reasons professionally.

TASK:
Rewrite the employee's leave reason into a concise, formal, workplace-appropriate sentence suitable for a leave request system.

STRICT RULES:
- Return ONLY the rewritten reason.
- Do NOT include introductions, explanations, labels, or bullet points.
- Do NOT provide multiple versions.
- Do NOT mention these instructions.
- Keep the meaning unchanged.
- Keep it concise and professional.
- Maximum 2-4 sentence.
- Preserve important details from the original reason.

Employee Leave Reason:
{user_text}
"""
)

    polished = response.content.strip()

    # safety cleanup
    polished = polished.replace("Here are a few options,", "").strip()
    polished = polished.replace("Here are a few options:", "").strip()

    msg = (
        f"Refined reason:\n\n"
        f"{polished}\n\n"
        f"Reply yes to use this reason, or type a better reason."
    )

    return {
        "reason_raw": user_text,
        "reason_polished": polished,
        "reason_approved": False,
        "step": "awaiting_reason",
        "answer": msg,
        "messages": [AIMessage(content=msg)],
    }
def route_after_refine_reason(state: ChatState):
    if state.get("reason_approved"):
        return "work_recommendation"
    return END

# ---------------- Final Preview ----------------

def final_preview_node(state: ChatState):
    blockers = state.get("work_blockers") or []
    blocker_text = "\n".join([f"- {b}" for b in blockers]) if blockers else "None"

    suggestion = state.get("work_suggestion") or "No suggestion"

    msg = f"""
LEAVE REQUEST SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━

Leave Dates    : {state.get('start_date')} → {state.get('end_date')}
Total Days     : {state.get('leave_days')}
Leave Type     : {state.get('leave_type')}
Reason         : {state.get('reason_polished')}

━━━━━━━━━━━━━━━━━━━━━━━━━━
WORK IMPACT ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━

Recommendation : {state.get('work_recommendation')}
Risk Level     : {state.get('work_risk')}

Analysis:
{state.get('work_reason')}

Blocking Items:
{blocker_text}

Suggested Actions:
{suggestion}

━━━━━━━━━━━━━━━━━━━━━━━━━━

Type 'confirm' to submit the request.
Type 'cancel' to discard the request.
"""
    return {
        "step": "awaiting_final_confirmation",
        "answer": msg,
        "messages": [AIMessage(content=msg)],
    }

def process_final_confirmation_node(state: ChatState):
    user_text = get_last_user_message(state)

    result = confirm_llm.invoke(
        f"Classify this reply as confirm, cancel, or unclear: {user_text}"
    )

    return {
        "confirm_intent": result.intent
    }


def route_final_confirmation(state: ChatState):
    intent = state.get("confirm_intent")

    if intent == "confirm":
        return "submit_leave"

    if intent == "cancel":
        return "cancel_leave"

    return "unclear_confirmation"


# ---------------- Submit / Cancel ----------------

def submit_leave_node(state: ChatState, config: RunnableConfig):
    db = config["configurable"]["db"]
    user_id = config["configurable"]["user_id"]
    chat_id = config["configurable"]["chat_id"]

    apply_leave_request(
    db=db,
    user_id=user_id,
    chat_id=chat_id,
    leave_type=state["leave_type"],
    start_date=state["start_date"],
    end_date=state["end_date"],
    reason=state["reason_polished"],

    ai_recommendation=state.get("work_recommendation"),
    ai_risk=state.get("work_risk"),
    ai_reason=state.get("work_reason"),
    ai_blockers=state.get("work_blockers") or [],
    ai_suggestion=state.get("work_suggestion"),
    manager_warning=state.get("manager_warning"),
    )

    msg = "🎉 Leave request sent successfully. Your manager will review it with any work-impact warnings."

    return {
        "step": "done",
        "answer": msg,
        "messages": [AIMessage(content=msg)],
    }

def cancel_leave_node(state: ChatState):
    msg = "❌ Leave request cancelled."

    return {
        "step": "cancelled",
        "answer": msg,
        "messages": [AIMessage(content=msg)],
    }


def unclear_confirmation_node(state: ChatState):
    msg = "Please reply **confirm** to send the request to HR or **cancel** to discard."

    return {
        "step": "awaiting_final_confirmation",
        "answer": msg,
        "messages": [AIMessage(content=msg)],
    }


# ---------------- Entry Router ----------------

def route_entry(state: ChatState):
    step = state.get("step")

    if step == "awaiting_dates":
        return "extract_dates"

    if step == "awaiting_leave_type":
        return "extract_leave_type"

    if step == "awaiting_reason":
        return "refine_reason"

    if step == "awaiting_final_confirmation":
        return "process_final_confirmation"

    return "ask_dates"


# ---------------- Build Graph ----------------

def build_graph(checkpointer=None):
    builder = StateGraph(ChatState)

    builder.add_node("ask_dates", ask_dates_node)
    builder.add_node("extract_dates", extract_dates_node)

    builder.add_node("ask_leave_type", ask_leave_type_node)
    builder.add_node("extract_leave_type", extract_leave_type_node)

    builder.add_node("ask_reason", ask_reason_node)
    builder.add_node("refine_reason", refine_reason_node)

    builder.add_node("final_preview", final_preview_node)
    builder.add_node("process_final_confirmation", process_final_confirmation_node)

    builder.add_node("submit_leave", submit_leave_node)
    builder.add_node("cancel_leave", cancel_leave_node)
    builder.add_node("unclear_confirmation", unclear_confirmation_node)
    builder.add_node("work_recommendation", work_recommendation_node)

    builder.add_conditional_edges(
        START,
        route_entry,
        {
            "ask_dates": "ask_dates",
            "extract_dates": "extract_dates",
            "extract_leave_type": "extract_leave_type",
            "refine_reason": "refine_reason",
            "process_final_confirmation": "process_final_confirmation",
        },
    )

    builder.add_edge("ask_dates", END)

    builder.add_conditional_edges(
        "extract_dates",
        route_dates,
        {
            "ask_dates": "ask_dates",
            "ask_leave_type": "ask_leave_type",
        },
    )

    builder.add_edge("ask_leave_type", END)

    builder.add_conditional_edges(
        "extract_leave_type",
        route_leave_type,
        {
            "ask_leave_type": "ask_leave_type",
            "ask_reason": "ask_reason",
        },
    )

    builder.add_edge("ask_reason", END)

    builder.add_conditional_edges(
    "refine_reason",
    route_after_refine_reason,
    {
        "work_recommendation": "work_recommendation",
        END: END,
    },
)
    builder.add_edge("work_recommendation", "final_preview")

    builder.add_edge("final_preview", END)

    builder.add_conditional_edges(
        "process_final_confirmation",
        route_final_confirmation,
        {
            "submit_leave": "submit_leave",
            "cancel_leave": "cancel_leave",
            "unclear_confirmation": "unclear_confirmation",
        },
    )

    builder.add_edge("submit_leave", END)
    builder.add_edge("cancel_leave", END)
    builder.add_edge("unclear_confirmation", END)

    return builder.compile(checkpointer=checkpointer)