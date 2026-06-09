import pandas as pd
import os
from config import settings
from datetime import datetime

class DataService:
    def __init__(self):
        # 确保目录存在
        os.makedirs(settings.DATA_RAW_DIR, exist_ok=True)
        os.makedirs(settings.DATA_PROCESSED_DIR, exist_ok=True)
        
        # 添加状态属性
        self.current_data = None      # 存储当前加载的 DataFrame
        self.data_filepath = None     # 存储当前数据文件路径
    
    def save_upload_file(self, file_content: bytes, filename: str) -> str:
        """保存上传的文件"""
        os.makedirs(settings.DATA_RAW_DIR, exist_ok=True)
        filepath = os.path.join(settings.DATA_RAW_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(file_content)
        return filepath
    
    def load_data(self, filepath: str) -> pd.DataFrame:
        """加载数据并保存到 current_data"""
        self.current_data = pd.read_csv(filepath)
        self.data_filepath = filepath
        return self.current_data
    
    def get_file_info(self, df: pd.DataFrame) -> dict:
        """获取文件基本信息"""
        return {
            "rows": len(df),
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict()
        }

# 创建全局实例
data_service = DataService()