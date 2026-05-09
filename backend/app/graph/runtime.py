import os
from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver
from app.graph.builder import build_graph
from psycopg_pool import ConnectionPool

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

pool = ConnectionPool(
    conninfo=DATABASE_URL,
    kwargs={
        "autocommit": True,
        "prepare_threshold": 0,
    },
)

checkpointer = PostgresSaver(pool)
checkpointer.setup()

graph = build_graph(checkpointer)