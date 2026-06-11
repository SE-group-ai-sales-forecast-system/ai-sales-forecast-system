import sys
from pathlib import Path

# 添加algorithm模块到路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

class PredictService:
    def __init__(self):
        """初始化预测服务，导入算法模块"""
        self.lightgbm = None
        self.baseline = None

        try:
            from algorithm.baseline_model import BaselinePredictor
            self.baseline = BaselinePredictor()
        except ImportError as e:
            print(f"基线模型导入失败: {e}")

        try:
            from algorithm.lightgbm_model import LightGBMPredictor
            self.lightgbm = LightGBMPredictor()
        except ImportError as e:
            print(f"LightGBM模型导入失败: {e}")
    
    def predict(self, product_id: str, days: int, model_type: str):
        """调用预测模型"""
        if model_type == "lightgbm" and self.lightgbm is not None:
            return self.lightgbm.predict(product_id, days)

        if self.baseline is not None:
            try:
                from services.data_service import data_service
                current_data = data_service.current_data
            except ImportError:
                current_data = None
            return self.baseline.predict(product_id, days, data=current_data)

        return self._empty_predict(days)
    
    def _empty_predict(self, days: int):
        """稳定的空预测，避免在无模型时返回随机结果。"""
        from datetime import datetime, timedelta
        
        dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") 
                 for i in range(1, days+1)]
        
        return {
            "dates": dates,
            "sales": [0.0 for _ in range(days)]
        }

predict_service = PredictService()
