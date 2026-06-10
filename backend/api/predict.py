from fastapi import APIRouter, HTTPException, Depends
from models.schemas import PredictRequest, PredictResponse
from services.predict_service import predict_service
from dependencies.auth import get_current_user

router = APIRouter()

@router.post("/predict", response_model=PredictResponse)
async def get_predict(
    request: PredictRequest,
    current_user: dict = Depends(get_current_user)                      
):
    """获取销量预测"""
    print(f"用户 {current_user['username']} 调用了预测接口")
    try:
        result = predict_service.predict(
            request.product_id,
            request.days,
            request.model_type
        )
        
        return PredictResponse(
            product_id=request.product_id,
            predicted_dates=result["dates"],
            predicted_sales=result["sales"],
            confidence_interval=None
        )
    except Exception as e:
        raise HTTPException(500, f"预测失败: {str(e)}")