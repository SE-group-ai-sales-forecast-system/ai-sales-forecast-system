import sys
from pathlib import Path

# 添加项目根目录和 backend 目录到路径，兼容从项目根目录或 backend 目录启动。
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
for path in (PROJECT_ROOT, BACKEND_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.append(path_text)

DEFAULT_RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "global_ecommerce_sales.csv"


class PredictService:
    def __init__(self):
        """初始化预测服务，导入算法模块"""
        self.lightgbm = None
        self.baseline = None
        self.default_data_path = DEFAULT_RAW_DATA_PATH

        try:
            from algorithm.baseline_model import BaselinePredictor
            self.baseline = BaselinePredictor(self._default_data_source())
        except Exception as e:
            print(f"基线模型导入失败: {e}")

        try:
            from algorithm.lightgbm_model import LightGBMPredictor
            default_data = self._default_data_source()
            self.lightgbm = LightGBMPredictor(data=default_data)
        except Exception as e:
            print(f"LightGBM模型导入失败: {e}")
    
    def predict(self, product_id: str, days: int, model_type: str):
        """调用预测模型"""
        horizon = self._normalize_days(days)
        if model_type == "lightgbm" and self.lightgbm is not None:
            current_data = self._current_or_default_data()
            result = self._predict_with_lightgbm(product_id, horizon, current_data)
            if result is not None:
                return result

        return self._predict_with_baseline(product_id, horizon)

    def _predict_with_lightgbm(self, product_id: str, days: int, data):
        """LightGBM 不可用或预测失败时返回 None，由调用方回退基线模型。"""
        try:
            result = self.lightgbm.predict(product_id, days, data=data)
        except Exception as e:
            print(f"LightGBM预测失败，回退基线模型: {e}")
            return None

        if not self._is_valid_result(result, days):
            print("LightGBM预测结果格式异常，回退基线模型")
            return None

        return result

    def _predict_with_baseline(self, product_id: str, days: int):
        if self.baseline is not None:
            current_data = self._current_or_default_data()
            return self.baseline.predict(product_id, days, data=current_data)

        return self._empty_predict(days)

    def _is_valid_result(self, result, days: int) -> bool:
        if not isinstance(result, dict):
            return False
        dates = result.get("dates")
        sales = result.get("sales")
        expected_length = self._normalize_days(days)
        return (
            isinstance(dates, list)
            and isinstance(sales, list)
            and len(dates) == expected_length
            and len(sales) == expected_length
        )

    def _current_or_default_data(self):
        """优先使用上传数据，未上传时回退到仓库内真实原始 CSV。"""
        data_service = self._load_data_service()
        if data_service is not None and data_service.current_data is not None:
            return data_service.current_data
        return self._default_data_source()

    def _load_data_service(self):
        try:
            from backend.services.data_service import data_service
            return data_service
        except ImportError:
            pass

        try:
            from services.data_service import data_service
            return data_service
        except ImportError:
            return None

    def _default_data_source(self):
        if self.default_data_path.exists():
            return self.default_data_path
        return None

    def _normalize_days(self, days, default: int = 7) -> int:
        if isinstance(days, bool):
            return default
        if isinstance(days, int):
            parsed_days = days
        elif isinstance(days, str) and days.strip().isdigit():
            parsed_days = int(days)
        else:
            return default
        return parsed_days if parsed_days > 0 else default
    
    def _empty_predict(self, days: int):
        """稳定的空预测，避免在无模型时返回随机结果。"""
        from datetime import datetime, timedelta
        horizon = self._normalize_days(days)
        
        dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") 
                 for i in range(1, horizon + 1)]
        
        return {
            "dates": dates,
            "sales": [0.0 for _ in range(horizon)]
        }

predict_service = PredictService()
