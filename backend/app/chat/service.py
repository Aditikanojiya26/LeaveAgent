import uuid
from app.db import get_conn

from langgraph.checkpoint.postgres import PostgresSaver
from app.db import DATABASE_URL
from app.graph.builder import build_graph
from langsmith import traceable


def create_chat_session(user_id: int):
    thread_id = str(uuid.uuid4())
    title = "New Chat"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_sessions (user_id, thread_id, title)
                VALUES (%s, %s, %s)
                RETURNING id, title, thread_id, created_at
                """,
                (user_id, thread_id, title)
            )
            row = cur.fetchone()
        conn.commit()

    return {
        "chat_id": row[0],
        "title": row[1],
        "thread_id": row[2],
        "created_at": str(row[3]),
    }


def list_chat_sessions(user_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, thread_id, created_at
                FROM chat_sessions
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
            rows = cur.fetchall()

    return [
        {
            "chat_id": row[0],
            "title": row[1],
            "thread_id": row[2],
            "created_at": str(row[3]),
        }
        for row in rows
    ]


@traceable

def send_chat_message(user_id: int, chat_id: int, message: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT thread_id
                FROM chat_sessions
                WHERE id = %s AND user_id = %s
                """,
                (chat_id, user_id)
            )
            row = cur.fetchone()

            if not row:
                raise Exception("Chat not found")

            thread_id = str(row[0])

            cur.execute(
                """
                INSERT INTO chat_messages (chat_id, role, content)
                VALUES (%s, %s, %s)
                """,
                (chat_id, "user", message)
            )
            conn.commit()

    with PostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
        checkpointer.setup()
        graph = build_graph(checkpointer)

        result = graph.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config={"configurable": {"thread_id": thread_id}}
        )

    ai_msg = result["messages"][-1]
    assistant_text = ai_msg.content
    print(assistant_text)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_messages (chat_id, role, content)
                VALUES (%s, %s, %s)
                """,
                (chat_id, "assistant", assistant_text)
            )
            conn.commit()

    return {
        "chat_id": chat_id,
        "assistant_message": assistant_text
    }
def list_chat_messages(user_id: int, chat_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM chat_sessions
                WHERE id = %s AND user_id = %s
                """,
                (chat_id, user_id)
            )
            exists = cur.fetchone()

            if not exists:
                raise Exception("Chat not found")

            cur.execute(
                """
                SELECT id, role, content, created_at
                FROM chat_messages
                WHERE chat_id = %s
                ORDER BY created_at ASC, id ASC
                """,
                (chat_id,)
            )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "role": row[1],
            "content": row[2],
            "created_at": row[3].isoformat() if row[3] else None,
        }
        for row in rows
    ]