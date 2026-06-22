# backend/api/inventory.py
from fastapi import APIRouter, HTTPException

import pandas as pd

from algorithm.inventory_warning import compute_inventory_warnings
from models.schemas import InventoryWarning
from services.data_service import data_service
from services.predict_service import DEFAULT_RAW_DATA_PATH, predict_service

router = APIRouter()


def _load_warning_data():
    """优先使用上传数据，未上传时回退数据库。"""
    if data_service.current_data is not None:
        return data_service.current_data

    try:
        from database import get_orders_df
        return get_orders_df()
    except Exception:
        if DEFAULT_RAW_DATA_PATH.exists():
            return pd.read_csv(DEFAULT_RAW_DATA_PATH)
        return None

@router.get("/inventory/warnings", response_model=list[InventoryWarning])
async def get_inventory_warnings():
    """获取库存预警信息（按产品类别）。"""
    try:
        data = _load_warning_data()
        if data is None:
            raise HTTPException(400, "请先上传数据文件，或确保默认 CSV 存在")

        def predict_fn(category: str, days: int):
            # LightGBM 失败时 PredictService 会自动回退移动平均
            return predict_service.predict(category, days, "lightgbm")

        raw_warnings = compute_inventory_warnings(data, predict_fn=predict_fn)
        return [InventoryWarning(**item) for item in raw_warnings]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"库存预警失败: {str(e)}")