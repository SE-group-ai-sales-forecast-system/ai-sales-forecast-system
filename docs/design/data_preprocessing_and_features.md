# 数据集预处理与特征工程指南

> 适用于项目：基于 AI 智能的电商商品销售分析与预测系统  
> 数据集：E-Commerce Sales & Profit Analysis（3500 条订单记录）  
> 目标：支撑销售分析、销量预测、库存预警、可视化报表四大核心功能  

## 一、数据集快速回顾

| 字段名 | 类型 | 说明 |
|--------|------|------|
| Order Date | 日期 | 订单发生日期，格式 `YYYY-MM-DD`，范围 2022-01-01 ~ 2024-12-31 |
| Product Name | 字符串 | 具体商品名称，如 Printer, Mouse, Tablet 等 |
| Category | 字符串 | 商品大类：Office, Accessories, Electronics |
| Region | 字符串 | 销售地区：North, South, East, West |
| Quantity | 整数 | 该订单中购买的商品数量 |
| Sales | 浮点数 | 订单总销售额（美元） |
| Profit | 浮点数 | 订单总利润（美元） |

> ✅ 数据无缺失值，无需处理异常值。  
> ⚠️ 原始数据未按时间排序，需预处理。

---

## 二、数据预处理（负责人：2号 数据负责人）

### 2.1 基础清洗步骤

```python
import pandas as pd

# 读取数据
df = pd.read_csv('ecommerce_sales_data.csv')

# 转换日期类型
df['Order Date'] = pd.to_datetime(df['Order Date'])

# 按日期升序排序（关键！）
df = df.sort_values('Order Date').reset_index(drop=True)

# 检查日期范围
print(df['Order Date'].min(), df['Order Date'].max())
```

### 2.2 创建两种数据视图

为了同时满足 **销售分析**（需要明细订单）和 **销量预测**（需要时间序列），建议生成两张表：

#### 视图A：订单明细表（用于分析）
- 保留所有原始字段，不做聚合。
- 用途：销售趋势分析（按月/按类别）、热销商品排行、地区利润分布。

#### 视图B：每日销量聚合表（用于预测）
- 按 `Order Date` 和 `Category`（可选）分组，计算每日总销量。
- 也可按 `Product Name` 粒度预测，但会增加模型复杂度。**建议先按 Category 预测**。

```python
# 按日期+品类聚合
daily_category_sales = df.groupby(['Order Date', 'Category'])['Quantity'].sum().reset_index()
daily_category_sales.columns = ['ds', 'category', 'y']   # ds: 日期, y: 销量

# 检查是否每天每个品类都有记录（如果没有，补0）
all_dates = pd.date_range(df['Order Date'].min(), df['Order Date'].max(), freq='D')
full_index = pd.MultiIndex.from_product([all_dates, daily_category_sales['category'].unique()], names=['ds', 'category'])
daily_category_sales = daily_category_sales.set_index(['ds', 'category']).reindex(full_index, fill_value=0).reset_index()
```

> 保存视图B为 `daily_sales_for_forecast.csv`，供算法组使用。

### 2.3 数据划分（用于评估预测模型）

**绝对禁止随机打乱！** 必须按时间顺序划分。

```python
# 以最后 30 天作为测试集
split_date = df['Order Date'].max() - pd.Timedelta(days=30)
train = daily_category_sales[daily_category_sales['ds'] < split_date]
test = daily_category_sales[daily_category_sales['ds'] >= split_date]
```

---

## 三、特征工程（负责人：4号 算法负责人B）

> 目标：为 LightGBM 模型准备特征矩阵。  
> 以下特征均基于 `daily_category_sales` 表（每日每品类销量）。

### 3.1 时间特征（基础）

从 `ds` 列提取：

| 特征名 | 说明 | 示例值 |
|--------|------|--------|
| year | 年份 | 2022, 2023, 2024 |
| month | 月份 | 1 ~ 12 |
| day | 当月第几天 | 1 ~ 31 |
| dayofweek | 星期几（0=周一, 6=周日） | 0~6 |
| is_weekend | 是否周末 | 0 或 1 |
| quarter | 季度 | 1,2,3,4 |
| dayofyear | 年中的第几天 | 1~365 |

```python
def create_time_features(df):
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

利用过去几天的销量预测未来。**注意：** 对每个 `category` 单独计算。

| 特征名 | 含义 | 预测未来1天时使用 |
|--------|------|------------------|
| lag_1 | 前1天销量 | ✅ |
| lag_2 | 前2天销量 | ✅ |
| lag_3 | 前3天销量 | ✅ |
| lag_7 | 前7天销量（周同期） | ✅ |
| lag_14 | 前14天销量 | 可选 |
| lag_30 | 前30天销量 | 可选 |

```python
# 按品类分组计算滞后特征
for lag in [1,2,3,7,14,30]:
    df[f'lag_{lag}'] = df.groupby('category')['y'].shift(lag)
```

### 3.3 滚动统计特征（Rolling Window）

捕捉近期趋势和波动。

| 特征名 | 计算方式 | 窗口 |
|--------|----------|------|
| rolling_mean_7 | 过去7天平均销量 | 7 |
| rolling_std_7 | 过去7天销量标准差 | 7 |
| rolling_mean_30 | 过去30天平均销量 | 30 |

```python
df['rolling_mean_7'] = df.groupby('category')['y'].transform(lambda x: x.rolling(7, min_periods=1).mean())
df['rolling_std_7'] = df.groupby('category')['y'].transform(lambda x: x.rolling(7, min_periods=1).std())
df['rolling_mean_30'] = df.groupby('category')['y'].transform(lambda x: x.rolling(30, min_periods=1).mean())
```

### 3.4 其他可选特征（提升精度）

- **月份正弦/余弦编码**：捕捉季节性循环  
  ```python
  df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
  df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
  ```
- **节假日标记**：可根据实际国家节假日（如圣诞节、新年、黑五）手工添加。由于数据集无此信息，可忽略或简单标记“12月为促销月”。

---

## 四、目标变量定义

对于 **销量预测** 模块：

- **目标变量**：`y` = 每日每个品类的总销量（来自视图B）。
- 如果最终系统允许按“商品名称”预测，则聚合粒度改为 `Product Name`，但数据量会增大，特征工程类似。

---

## 五、库存预警模拟方案（负责人：4号）

由于原数据没有库存字段，采用以下**模拟策略**：

### 5.1 为每个产品设定“当前库存”

规则：当前库存 = 该产品过去30天的日均销量 × 安全天数（如14天）。

```python
# 计算每个产品最近30天的日均销量
recent = df[df['Order Date'] > df['Order Date'].max() - pd.Timedelta(days=30)]
avg_daily_sales = recent.groupby('Product Name')['Quantity'].mean()
# 设定当前库存 = 日均销量 × 14
current_stock = avg_daily_sales * 14
```

### 5.2 预警逻辑

- **安全库存** = 预测的未来7天总销量 × 1.2（冗余系数）
- **预警条件**：`当前库存 < 安全库存`
- **建议补货量** = `安全库存 - 当前库存`

前端预警页展示：商品名称、当前库存、预测未来7天销量、安全库存、建议补货量。

---

## 六、预测评估方法（负责人：3号、4号）

### 6.1 评估指标（回归任务）

- **MAE**（平均绝对误差）：`mean(|真实值 - 预测值|)`
- **RMSE**（均方根误差）：`sqrt(mean((真实值-预测值)^2))`
- **MAPE**（平均绝对百分比误差）：适合解释业务意义

### 6.2 时间序列交叉验证

不建议使用普通 KFold，应使用 **TimeSeriesSplit**：

```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
for train_idx, test_idx in tscv.split(daily_sales):
    train = daily_sales.iloc[train_idx]
    test = daily_sales.iloc[test_idx]
    # 训练与评估
```

### 6.3 基线模型对比

- **Naive 方法**：预测值 = 前一天销量
- **移动平均（窗口7）**
- **Prophet**（可选）
- **LightGBM**（主模型）

必须输出对比表格（在项目文档中展示模型优越性）。

---

## 七、给小组的工作任务清单

| 角色 | 基于本数据集的子任务 |
|------|----------------------|
| 2号（数据负责人） | 完成 2.1~2.3 预处理，生成视图B，划分训练/测试集，提交 cleaned_data.csv 和 daily_sales.csv |
| 3号（算法A） | 实现 Prophet 或移动平均基线模型，输出预测结果并计算误差，提供预测曲线绘图函数 |
| 4号（算法B） | 完成特征工程（第三部分），训练 LightGBM 模型，实现库存预警模拟规则，输出模型评估报告 |
| 5号（后端） | 将预处理和特征工程代码封装为 API 可调用的函数（如 `/forecast` 接收品类，返回预测值） |
| 6号（前端/测试） | 设计预测页面（品类选择、预测天数）、预警页面（表格展示），调用后端接口 |
| 1号（组长） | 协调以上步骤，确保数据流畅通，并更新项目文档中的数据描述部分 |

---

## 八、常见问题与注意事项

- **日期排序**：绝对不要遗忘，否则滞后特征会错乱。
- **类别一致性**：视图B中的 `category` 列必须与原始数据完全一致（Accessories, Electronics, Office）。
- **预测粒度选择**：初期建议按 Category 预测，简化模型；后期可扩展至 Product Name。
- **缺失值处理**：滚动统计前几个窗口会得到 NaN，可用 `fillna(0)` 或向前填充。
- **库存字段**：仅用于演示预警逻辑，不要求真实数据，但需在文档中说明“模拟假设”。

---

**文档版本**：v1.0  
**最后更新**：2026-06-09  
**维护者**：项目组全体  