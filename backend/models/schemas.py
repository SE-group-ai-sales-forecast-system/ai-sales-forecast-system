from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date

class UploadResponse(BaseModel):
    """上传文件响应"""
    filename: str
    rows: int
    columns: List[str]
    message: str

class SalesAnalysisRequest(BaseModel):
    """销售分析请求"""
    dimension: str  # time, product, category, region
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    top_n: Optional[int] = 10

class SalesAnalysisResponse(BaseModel):
    """销售分析响应"""
    data: List[Dict[str, Any]]
    chart_type: str  # line, bar, pie

class PredictRequest(BaseModel):
    """预测请求"""
    product_id: str
    days: int = 7  # 7, 14, 30
    model_type: str = "lightgbm"  # lightgbm, baseline

class PredictResponse(BaseModel):
    """预测响应"""
    product_id: str
    predicted_dates: List[str]
    predicted_sales: List[float]
    confidence_interval: Optional[Dict[str, List[float]]] = None

class InventoryWarning(BaseModel):
    """库存预警"""
    product_id: str
    product_name: str
    current_stock: int
    predicted_demand: int
    status: str  # 库存不足/正常/过高
    suggested_order: int

class DashboardResponse(BaseModel):
    """看板汇总数据"""
    total_sales: float
    total_orders: int
    avg_daily_sales: float
    top_products: List[Dict]
    recent_trend: List[Dict]
    inventory_warnings: List[InventoryWarning]
    
# ========== 用户认证相关 ==========
class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str

class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str
    role: str  # admin 或 user

class User(BaseModel):
    """用户信息"""
    username: str
    role: str