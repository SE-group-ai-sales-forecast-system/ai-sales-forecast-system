import jwt
import hashlib
from datetime import datetime, timedelta
from config import settings
from datetime import timezone

def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return hash_password(password) == hashed

def create_access_token(username: str, role: str) -> str:
    """创建 JWT token"""
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict:
    """解析 token"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return {"valid": True, "payload": payload}
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token已过期"}
    except jwt.InvalidTokenError:
        return {"valid": False, "error": "无效的Token"}