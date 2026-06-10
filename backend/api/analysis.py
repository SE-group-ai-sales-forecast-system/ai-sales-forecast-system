from fastapi import APIRouter, HTTPException, Depends
from models.schemas import SalesAnalysisRequest, SalesAnalysisResponse
from services.data_service import data_service
from dependencies.auth import get_current_user 
import pandas as pd

router = APIRouter()

@router.post("/analysis", response_model=SalesAnalysisResponse)
async def get_sales_analysis(
    request: SalesAnalysisRequest,
    current_user: dict = Depends(get_current_user) 
):
    """获取销售分析数据 - 从已上传的 CSV 读取"""
    try:
        if data_service.current_data is None:
            raise HTTPException(400, "请先上传数据文件")
        
        df = data_service.current_data.copy()
        
        # 映射列名（适配你的 CSV）
        date_col = "Order_Date"           # 订单日期
        product_col = "Product_Name"      # 商品名称
        sales_col = "Quantity"            # 销量（数量）
        revenue_col = "Total_Sales"       # 销售额
        region_col = "Region"             # 地区
        category_col = "Product_Category" # 商品品类
        profit_col = "Profit"             # 利润
        
        # 日期过滤
        if request.start_date and request.end_date and date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col])
            mask = (df[date_col] >= request.start_date) & (df[date_col] <= request.end_date)
            df = df[mask]
        
        top_n = request.top_n if request.top_n else 10
        
        if request.dimension == "product":
            # 按商品聚合销量
            grouped = df.groupby(product_col)[sales_col].sum().sort_values(ascending=False).head(top_n)
            data = [{"name": str(idx), "value": float(val)} for idx, val in grouped.items()]
            chart_type = "bar"
            
        elif request.dimension == "time":
            # 按时间聚合销量
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col])
                grouped = df.groupby(df[date_col].dt.date)[sales_col].sum().sort_index()
                data = [{"date": str(idx), "sales": float(val)} for idx, val in grouped.items()]
                chart_type = "line"
            else:
                data = []
                chart_type = "line"
                
        elif request.dimension == "revenue":
            # 按销售额聚合销量
            grouped = df.groupby(revenue_col)[sales_col].sum().sort_values(ascending=False)
            data = [{"name": str(idx), "value": float(val)} for idx, val in grouped.items()]
            chart_type = "pie"
            
        elif request.dimension == "category":
            # 按品类聚合销量
            grouped = df.groupby(category_col)[sales_col].sum().sort_values(ascending=False).head(top_n)
            data = [{"name": str(idx), "value": float(val)} for idx, val in grouped.items()]
            chart_type = "pie"
            
        elif request.dimension == "region":
            # 按地区聚合销量
            grouped = df.groupby(region_col)[sales_col].sum().sort_values(ascending=False)
            data = [{"name": str(idx), "value": float(val)} for idx, val in grouped.items()]
            chart_type = "pie"
            
        elif request.dimension == "profit":
            # 按利润聚合销量
            grouped = df.groupby(profit_col)[sales_col].sum().sort_values(ascending=False)
            data = [{"name": str(idx), "value": float(val)} for idx, val in grouped.items()]
            chart_type = "pie"
            
        else:
            raise HTTPException(400, f"不支持的维度: {request.dimension}")
        
        return SalesAnalysisResponse(data=data, chart_type=chart_type)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"分析失败: {str(e)}")