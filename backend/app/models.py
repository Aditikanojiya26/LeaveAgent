from app.db import get_conn


def create_tables():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    email TEXT UNIQUE,
                    password_hash TEXT
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INT NOT NULL,
                    thread_id TEXT NOT NULL UNIQUE,
                    title TEXT DEFAULT 'New Chat',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_user
                        FOREIGN KEY(user_id)
                        REFERENCES users(id)
                        ON DELETE CASCADE
                )
            """)

        

        conn.commit()