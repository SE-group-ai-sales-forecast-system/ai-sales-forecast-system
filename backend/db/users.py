from utils.auth import hash_password

# 模拟用户数据库
# 密码：admin123 / user123
_users_db = {
    "admin": {
        "password_hash": hash_password("admin123"),
        "role": "admin"
    },
    "user": {
        "password_hash": hash_password("user123"),
        "role": "user"
    }
}

def get_user(username: str):
    """根据用户名获取用户"""
    user = _users_db.get(username)
    if user:
        return {"username": username, **user}
    return None

def user_exists(username: str) -> bool:
    """检查用户是否存在"""
    return username in _users_db