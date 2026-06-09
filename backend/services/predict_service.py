import sys
import os
from pathlib import Path

# 添加algorithm模块到路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

class PredictService:
    def __init__(self):
        """初始化预测服务，导入算法模块"""
        try:
            # 导入算法模块
            from algorithm.lightgbm_model import LightGBMPredictor
            from algorithm.baseline_model import BaselinePredictor
            self.lightgbm = LightGBMPredictor()
            self.baseline = BaselinePredictor()
            self.models_ready = True
        except ImportError as e:
            print(f"算法模块导入失败: {e}")
            self.models_ready = False
    
    def predict(self, product_id: str, days: int, model_type: str):
        """调用预测模型"""
        if not self.models_ready:
            # 返回模拟数据用于测试
            return self._mock_predict(product_id, days)
        
        # 实际调用算法模块
        if model_type == "lightgbm":
            return self.lightgbm.predict(product_id, days)
        else:
            return self.baseline.predict(product_id, days)
    
    def _mock_predict(self, product_id: str, days: int):
        """模拟预测数据（用于前期测试）"""
        import random
        from datetime import datetime, timedelta
        
        dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") 
                 for i in range(1, days+1)]
        sales = [random.randint(50, 200) for _ in range(days)]
        
        return {
            "dates": dates,
            "sales": sales
        }

predict_service = PredictService()