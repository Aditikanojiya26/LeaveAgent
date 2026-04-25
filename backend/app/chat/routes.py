from fastapi import APIRouter, Request, Body


from app.auth.routes import get_current_user
from app.chat.service import (
    create_chat_session,
    list_chat_sessions,
    send_chat_message,
    list_chat_messages
)

router = APIRouter(prefix="/chats", tags=["Chats"])


@router.post("")
def create_chat(request: Request):
    user_id = get_current_user(request)
    return create_chat_session(user_id)


@router.get("")
def get_chats(request: Request):
    user_id = get_current_user(request)
    return list_chat_sessions(user_id)


@router.post("/{chat_id}/message")
def send_message(chat_id: int, request: Request, data: dict = Body(...)):
    user_id = get_current_user(request)
    return send_chat_message(user_id, chat_id, data["message"])

@router.get("/{chat_id}/messages")
def get_chat_messages(chat_id: int, request: Request):
    user_id = get_current_user(request)
    return list_chat_messages(user_id, chat_id)