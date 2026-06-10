import os

class Settings:
    # 项目根目录
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 数据目录
    DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
    DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
    
    # 允许上传的文件格式
    ALLOWED_EXTENSIONS = {".csv"}
    
    # 预测默认天数
    DEFAULT_PREDICT_DAYS = [7, 14, 30]
    
    # ========== JWT 认证配置 ==========
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS = 24
settings = Settings()