from fastapi import APIRouter, HTTPException, status
from api.models.requests import LoginRequest
from api.models.responses import TokenResponse
from api.auth import create_token
from utils.auth import _load_env_credentials

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    expected_user, expected_pass, _ = _load_env_credentials()
    if body.username != expected_user or body.password != expected_pass:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_token(body.username)
    return TokenResponse(access_token=token)
