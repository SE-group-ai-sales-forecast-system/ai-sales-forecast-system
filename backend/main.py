import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parent
backend_root_text = str(backend_root)
if backend_root_text not in sys.path:
    sys.path.append(backend_root_text)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import upload, analysis, predict, inventory, auth
from contextlib import asynccontextmanager
from database import init_db, import_csv_to_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    default_csv = Path(__file__).resolve().parents[1] / "data" / "raw" / "global_ecommerce_sales.csv"
    if default_csv.exists():
        try:
            import_csv_to_db(str(default_csv), table_name="orders")
        except Exception as e:
            print(f"默认数据导入失败: {e}")

    yield

app = FastAPI(
    title="AI销售预测系统API",
    description="电商销售数据分析与预测后端接口",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS，允许前端调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api", tags=["用户认证"])
app.include_router(upload.router, prefix="/api", tags=["数据上传"])
app.include_router(analysis.router, prefix="/api", tags=["数据分析"])
app.include_router(inventory.router, prefix="/api", tags=["库存预警"])
app.include_router(predict.router, prefix="/api", tags=["销量预测"])

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "后端服务运行正常"}

@app.get("/")
async def root():
    return {
        "message": "AI销售预测系统API",
        "docs_url": "/docs",
        "version": "1.0.0"
    }
