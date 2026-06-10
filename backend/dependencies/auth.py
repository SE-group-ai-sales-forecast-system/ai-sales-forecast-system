# backend/dependencies/auth.py
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.auth import decode_token

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前登录用户（用于接口依赖）"""
    token = credentials.credentials
    result = decode_token(token)
    
    if not result["valid"]:
        raise HTTPException(status_code=401, detail=result["error"])
    
    payload = result["payload"]
    return {
        "username": payload.get("sub"),
        "role": payload.get("role")
    }