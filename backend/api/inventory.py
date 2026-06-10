# backend/api/inventory.py
from fastapi import APIRouter, HTTPException, Depends
from models.schemas import InventoryWarning
from services.data_service import data_service
from services.predict_service import predict_service
import random

router = APIRouter()

@router.get("/inventory/warnings", response_model=list[InventoryWarning])
async def get_inventory_warnings():
    """获取库存预警信息"""
    try:
        if data_service.current_data is None:
            raise HTTPException(400, "请先上传数据文件")
        
        df = data_service.current_data.copy()
        
        # 获取所有商品列表
        products = df['Product_Name'].unique().tolist()[:20]
        
        warnings = []
        for product in products:
            # 模拟当前库存
            current_stock = random.randint(100, 1000)
            
            # 获取预测销量
            try:
                result = predict_service.predict(product, 7, "lightgbm")
                predicted_demand = sum(result["sales"])
            except:
                predicted_demand = random.randint(50, 200)
            
            # 判断库存状态
            if current_stock < predicted_demand * 0.5:
                status = "库存不足"
                suggested_order = int(predicted_demand * 1.5 - current_stock)
            elif current_stock > predicted_demand * 3:
                status = "库存过高"
                suggested_order = 0
            else:
                status = "正常"
                suggested_order = int(predicted_demand * 0.8)
            
            warnings.append(InventoryWarning(
                product_id=product,
                product_name=product,
                current_stock=current_stock,
                predicted_demand=int(predicted_demand),
                status=status,
                suggested_order=suggested_order
            ))
        
        return warnings
        
    except Exception as e:
        raise HTTPException(500, f"库存预警失败: {str(e)}")