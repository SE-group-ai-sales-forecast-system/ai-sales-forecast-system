# backend/api/auth.py
from fastapi import APIRouter, HTTPException
from models.schemas import LoginRequest, LoginResponse
from db.users import get_user
from utils.auth import verify_password, create_access_token

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """用户登录"""
    # 1. 查找用户
    user = get_user(request.username)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 2. 验证密码
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 3. 生成 token
    token = create_access_token(request.username, user["role"])
    
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        role=user["role"]
    )