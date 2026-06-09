from fastapi import APIRouter, HTTPException
from models.schemas import PredictRequest, PredictResponse
from services.predict_service import predict_service

router = APIRouter()

@router.post("/predict", response_model=PredictResponse)
async def get_predict(request: PredictRequest):
    """获取销量预测"""
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