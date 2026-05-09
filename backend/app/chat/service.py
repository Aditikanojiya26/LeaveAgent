from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver
from sqlalchemy.orm import joinedload

from app.graph.runtime import graph

import uuid
import os 
from dotenv import load_dotenv
load_dotenv() 
DATABASE_URL = os.getenv("DATABASE_URL")
from app.graph.builder import build_graph

import uuid

def create_chat_session(db: Session, user_id: int):
    thread_id = str(uuid.uuid4())

    chat = ChatSession(
        user_id=user_id,
        thread_id=thread_id,
        title="New Chat"
    )

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return {
        "chat_id": chat.id,
        "title": chat.title,
        "thread_id": chat.thread_id,
        "created_at": str(chat.created_at),
    }

def list_chat_sessions(db: Session, user_id: int):
    chats = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )

    return [
        {
            "chat_id": chat.id,
            "title": chat.title,
            "thread_id": chat.thread_id,
            "created_at": str(chat.created_at),
        }
        for chat in chats
    ]


def send_chat_message(
    db: Session,
    user_id: int,
    chat_id: int,
    message: str
):
    chat = (
    db.query(ChatSession)
    .options(joinedload(ChatSession.user))
    .filter(ChatSession.id == chat_id, ChatSession.user_id == user_id)
    .first()
    )
    user = chat.user

    # 2️⃣ Save user message
    user_msg = ChatMessage(
        chat_id=chat_id,
        role="user",
        content=message
    )
    db.add(user_msg)
    db.commit()  
    result = graph.invoke(
            {
                "messages": [HumanMessage(content=message)],
                # ❌ REMOVE these — not serializable, move to configurable
                # "user_id": user.id,
                # "db": db,

                # ✅ KEEP only serializable state fields
                "intent": None,
                "answer": None,
                "role": user.role,   # only if role is a plain string
            },
            config={
                "configurable": {
                    "thread_id": str(chat.thread_id),
                    # ✅ ADD these here instead
                    "user_id": user.id,
                    "chat_id": chat.id,
                    "db": db,
                }
            }
        )

# Because our new graph returns:
#return {
#     "answer": answer,                  # ✅ immediate response
#     "messages": [AIMessage(content=answer)],  # ✅ memory append
# }
    # 4️⃣ Extract response
    assistant_text = result.get("answer")

    if not assistant_text and result.get("messages"):
        assistant_text = result["messages"][-1].content

    if not assistant_text:
        assistant_text = "Sorry, something went wrong."

    # 5️⃣ Save assistant message
    ai_msg = ChatMessage(
        chat_id=chat_id,
        role="assistant",
        content=assistant_text
    )

    db.add(ai_msg)
    db.commit()

    return {
        "chat_id": chat_id,
        "assistant_message": assistant_text
    }

def list_chat_messages(db: Session, user_id: int, chat_id: int):
    chat = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == chat_id,
            ChatSession.user_id == user_id
        )
        .first()
    )

    if not chat:
        raise Exception("Chat not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        .all()
    )

    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        }
        for msg in messages
    ]