from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.routes import router as auth_router
from app.chat.routes import router as chat_router
from app.crud.routes import router as user_router
from dotenv import load_dotenv

load_dotenv()

from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.models.leave import LeaveRequest, ProjectDeadline, Task,LeaveApproval, LeaveBalance
from app.db import Base, engine
from app.manager.routes import router as manager_router


def create_tables():
    Base.metadata.create_all(bind=engine)
    


create_tables()   


app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(user_router)
app.include_router(manager_router)


@app.get("/")
def root():
    return {"message": "API is working"}