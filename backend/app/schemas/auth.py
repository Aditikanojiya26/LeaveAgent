from pydantic import BaseModel, EmailStr
from typing import Optional, Literal

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "employee"
    manager_id: Optional[int] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str