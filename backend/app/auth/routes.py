from fastapi import APIRouter, Response, HTTPException, Request
from app.db import get_conn
from app.auth.utils import hash_password, verify_password, create_token
from jose import jwt, JWTError
import os

router = APIRouter(prefix="/auth", tags=["Auth"])

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


@router.post("/register")
def register(data: dict):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
                (data["name"], data["email"], hash_password(data["password"]))
            )
        conn.commit()

    return {"msg": "User created"}


@router.post("/login")
def login(data: dict, response: Response):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, password_hash FROM users WHERE email = %s",
                (data["email"],)
            )
            user = cur.fetchone()

    if not user or not verify_password(data["password"], user[3]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"user_id": user[0]})

    response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,
    secure=False,   # local dev
    samesite="lax"
)

    return {
        "msg": "Logged in",
        "user": {
            "id": user[0],
            "name": user[1],
            "email": user[2]
        }
    }


def get_current_user(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not logged in")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["user_id"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/me")
def me(request: Request):
    user_id = get_current_user(request)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email FROM users WHERE id = %s",
                (user_id,)
            )
            user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user[0],
        "name": user[1],
        "email": user[2]
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"msg": "Logged out"}