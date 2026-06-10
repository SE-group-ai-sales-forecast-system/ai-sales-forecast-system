from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import upload, analysis, predict, inventory, auth

app = FastAPI(
    title="AI销售预测系统API",
    description="电商销售数据分析与预测后端接口",
    version="1.0.0"
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