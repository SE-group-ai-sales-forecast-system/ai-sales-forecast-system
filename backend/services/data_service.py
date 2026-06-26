import pandas as pd
import os
from config import settings
from datetime import datetime
from database import import_csv_to_db, get_orders_df


class DataService:
    def __init__(self):
        os.makedirs(settings.DATA_RAW_DIR, exist_ok=True)
        os.makedirs(settings.DATA_PROCESSED_DIR, exist_ok=True)
        self.current_data = None
        self.data_filepath = None

    def save_upload_file(self, file_content: bytes, filename: str) -> str:
        os.makedirs(settings.DATA_RAW_DIR, exist_ok=True)
        filepath = os.path.join(settings.DATA_RAW_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(file_content)

        import_csv_to_db(filepath, table_name="orders")

        return filepath

    def load_data(self, filepath: str = None) -> pd.DataFrame:
        self.current_data = get_orders_df()
        self.data_filepath = filepath
        return self.current_data

    def get_file_info(self, df: pd.DataFrame = None) -> dict:
        if df is None:
            df = self.current_data
        if df is None:
            return {"rows": 0, "columns": [], "dtypes": {}, "missing_values": {}}
        return {
            "rows": len(df),
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict()
        }


data_service = DataService()