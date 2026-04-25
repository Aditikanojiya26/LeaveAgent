from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models import create_tables
from app.auth.routes import router as auth_router
from app.chat.routes import router as chat_router
from dotenv import load_dotenv
load_dotenv(override=True) 

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


create_tables()

app.include_router(auth_router)
app.include_router(chat_router)

@app.get("/")
def root():
    return {"message": "API is working"}