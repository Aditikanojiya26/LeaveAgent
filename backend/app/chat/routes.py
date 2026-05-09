from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.auth.routes import get_current_user

from app.chat.service import (
    create_chat_session,
    list_chat_sessions,
    send_chat_message,
    list_chat_messages
)

from app.schemas.chat import ChatMessageRequest

router = APIRouter(prefix="/chats", tags=["Chats"])


@router.post("")
def create_chat(
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = get_current_user(request)
    return create_chat_session(db, user_id)


@router.get("")
def get_chats(
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = get_current_user(request)
    return list_chat_sessions(db, user_id)


@router.post("/{chat_id}/message")
def send_message(
    chat_id: int,
    data: ChatMessageRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = get_current_user(request)
    return send_chat_message(db, user_id, chat_id, data.message)


@router.get("/{chat_id}/messages")
def get_chat_messages(
    chat_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = get_current_user(request)
    return list_chat_messages(db, user_id, chat_id)