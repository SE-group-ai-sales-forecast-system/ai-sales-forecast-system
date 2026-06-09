# 数据集预处理与特征工程指南（基于 Global E-Commerce Sales Dataset）

> 适用项目：基于 AI 智能的电商商品销售分析与预测系统  
> 数据集：Global E-Commerce Sales Dataset（2000+ 订单，15 字段）  
> 目标：支撑销售分析、销量预测、库存预警、可视化报表  

## 一、数据集快速回顾

| 字段名 | 类型 | 说明 | 项目用途 |
|--------|------|------|----------|
| Order_Date | 日期 | 订单日期 | 时间序列分析、趋势图 |
| Product_Category | 分类 | 产品大类（4种） | 聚合预测、类别销售排行 |
| Product_Name | 分类 | 具体产品名 | 单品分析、热销排行 |
| Quantity | 数值 | 销售数量 | **预测目标** |
| Total_Sales | 数值 | 销售额 | 销售分析、盈利分析 |
| Profit | 数值 | 利润 | 利润分析 |
| Customer_Segment | 分类 | Consumer/Corporate/Home Office | 客户细分分析 |
| Region | 分类 | 5大全球区域 | 地理销售分析 |
| Country | 分类 | 20个国家 | 国家级别分析 |
| Discount_Percent | 数值 | 折扣率（0-30） | 促销效果分析 |
| Shipping_Cost | 数值 | 运费 | 成本分析 |
| Payment_Method | 分类 | 4种支付方式 | 支付偏好分析 |
| Unit_Price | 数值 | 单价 | 可衍生均价 |
| Order_ID | 标识 | 唯一订单号 | 主键 |
| Customer_Name | 文本 | 客户姓名 | 可选用户画像 |

## 二、数据预处理（由数据负责人负责）

### 2.1 基础清洗

```python
import pandas as pd

df = pd.read_csv('global_ecommerce_sales.csv')
df['Order_Date'] = pd.to_datetime(df['Order_Date'])
df = df.sort_values('Order_Date').reset_index(drop=True)

# 检查缺失值（应无缺失）
print(df.isnull().sum())
```

### 2.2 创建两张核心表

#### 表A：订单明细表（用于分析）
- 保留所有原始字段，不加聚合。
- 用途：销售趋势、热销排行、地区分布、客户细分、折扣分析等。
- 保存为：`sales_orders_cleaned.csv`

#### 表B：每日销量聚合表（用于预测）
- 按 `Order_Date` + `Product_Category` 分组，计算每日总销量。
- 补全缺失日期（每个类别每一天都有记录，销量填0）。
- 保存为：`daily_sales_for_forecast.csv`

```python
daily = df.groupby(['Order_Date', 'Product_Category'])['Quantity'].sum().reset_index()
daily.columns = ['ds', 'category', 'y']

# 补全日期
all_dates = pd.date_range(df['Order_Date'].min(), df['Order_Date'].max(), freq='D')
full_idx = pd.MultiIndex.from_product([all_dates, daily['category'].unique()], names=['ds', 'category'])
daily = daily.set_index(['ds', 'category']).reindex(full_idx, fill_value=0).reset_index()
```

### 2.3 可选：衍生每日外部特征（提升预测精度）

```python
# 每日平均折扣率
daily_discount = df.groupby('Order_Date')['Discount_Percent'].mean().rename('avg_discount')
# 每日平均运费
daily_shipping = df.groupby('Order_Date')['Shipping_Cost'].mean().rename('avg_shipping_cost')
# 合并到 daily 表中
daily = daily.merge(daily_discount, left_on='ds', right_index=True, how='left')
daily = daily.merge(daily_shipping, left_on='ds', right_index=True, how='left')
```

## 三、特征工程（由算法负责人B负责）

基于 `daily_sales_for_forecast.csv`（如包含额外特征则一并使用）。
B
### 3.1 时间特征

```python
def add_time_features(df):
    df = df.copy()
    df['year'] = df['ds'].dt.year
    df['month'] = df['ds'].dt.month
    df['day'] = df['ds'].dt.day
    df['dayofweek'] = df['ds'].dt.dayofweek
    df['is_weekend'] = (df['dayofweek'] >= 5).astype(int)
    df['quarter'] = df['ds'].dt.quarter
    df['dayofyear'] = df['ds'].dt.dayofyear
    return df
```

### 3.2 滞后特征（Lag Features）

按 `category` 分组计算：

```python
for lag in [1, 2, 3, 7, 14, 30]:
    df[f'lag_{lag}'] = df.groupby('category')['y'].shift(lag)
```

### 3.3 滚动统计特征

```python
df['rolling_mean_7'] = df.groupby('category')['y'].transform(lambda x: x.rolling(7, min_periods=1).mean())
df['rolling_std_7'] = df.groupby('category')['y'].transform(lambda x: x.rolling(7, min_periods=1).std())
df['rolling_mean_30'] = df.groupby('category')['y'].transform(lambda x: x.rolling(30, min_periods=1).mean())
```

### 3.4 数据划分（时间顺序）

```python
split_date = df['ds'].max() - pd.Timedelta(days=30)
train = df[df['ds'] < split_date]
test = df[df['ds'] >= split_date]
```

## 四、库存预警模拟方案（由算法负责人B负责）

由于数据无真实库存字段，采用以下模拟规则：

```python
def simulate_inventory_warnings(df_orders, forecast_7d_dict):
    # 计算每个类别过去30天的日均销量
    last_30 = df_orders[df_orders['Order_Date'] > df_orders['Order_Date'].max() - pd.Timedelta(days=30)]
    avg_daily = last_30.groupby('Product_Category')['Quantity'].mean()
    
    # 当前库存 = 日均销量 × 14（安全天数）
    current_stock = avg_daily * 14
    
    warnings = []
    for cat in current_stock.index:
        forecast_7d = forecast_7d_dict.get(cat, 0)
        safe_stock = forecast_7d * 1.2
        if current_stock[cat] < safe_stock:
            warnings.append({
                'category': cat,
                'current_stock': round(current_stock[cat], 2),
                'forecast_7d': forecast_7d,
                'safe_stock': round(safe_stock, 2),
                'suggested_order': round(safe_stock - current_stock[cat], 2)
            })
    return warnings
```

## 五、评估指标

- **MAE**（平均绝对误差）
- **RMSE**（均方根误差）
- **MAPE**（平均绝对百分比误差）

使用时间序列交叉验证（TimeSeriesSplit）进行评估。