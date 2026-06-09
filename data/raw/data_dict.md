# 数据字典：Global E-Commerce Sales Dataset

> 数据集名称：Global E-Commerce Sales Dataset  
> 数据集来源：[E-Commerce Sales Data Analysis](https://www.kaggle.com/datasets/bibirehana/global-e-commarce-sales-data-analysis)  
> 用途：电商销售分析与预测系统  
> 记录数：1 行表头，2,000 行交易记录  
> 时间范围：2023-01-02 至 2025-12-31  
> 覆盖范围：20 个国家，5 个全球区域，4 个产品类别，3 个客户细分，4 种支付方式

## 字段总览

| 字段名 | 数据类型 | 业务含义 | 示例值 |
|--------|----------|----------|--------|
| Order_ID | 字符串 | 订单唯一标识 | ORD-11121 |
| Order_Date | 日期 | 订单创建日期 | 2023-01-02 |
| Customer_Name | 字符串 | 客户姓名 | Karen Suzuki |
| Customer_Segment | 字符串 | 客户类型/细分 | Corporate, Consumer, Home Office |
| Country | 字符串 | 客户所在国家 | United States, Spain, Mexico |
| Region | 字符串 | 全球区域 | North America, Europe, Asia Pacific, Middle East & Africa, South America |
| Product_Category | 字符串 | 产品大类 | Technology, Furniture, Clothing & Accessories, Office Supplies |
| Product_Name | 字符串 | 具体产品名称 | Wireless Bluetooth Headphones |
| Quantity | 整数 | 购买数量 | 3 |
| Unit_Price | 浮点数 | 产品单价（美元） | 99.43 |
| Discount_Percent | 整数/浮点数 | 折扣百分比 | 0, 5, 10, 15, 20, 25, 30 |
| Total_Sales | 浮点数 | 销售额 = Quantity × Unit_Price × (1 - Discount_Percent/100) | 298.29 |
| Shipping_Cost | 浮点数 | 运费（美元） | 9.31 |
| Profit | 浮点数 | 利润（美元） | 124.92 |
| Payment_Method | 字符串 | 支付方式 | Cash on Delivery, Credit Card, PayPal, Bank Transfer |

---

## 字段详细说明

### 1. Order_ID
- **类型**：字符串
- **唯一性**：是，每个订单有唯一编号
- **格式**：`ORD-` + 5位数字，如 `ORD-11121`
- **用途**：订单主键，可用于关联（如有其他表）或去重

### 2. Order_Date
- **类型**：日期（YYYY-MM-DD）
- **范围**：2023-01-02 至 2025-12-31
- **用途**：时间序列分析、销售趋势、季节性分析、预测
- **注意事项**：数据未按日期严格排序，预处理时需排序

### 3. Customer_Name
- **类型**：字符串
- **格式**：名 + 姓，如 `Karen Suzuki`
- **用途**：客户识别

### 4. Customer_Segment
- **类型**：分类变量
- **取值**：
  - `Corporate` – 企业客户
  - `Consumer` – 个人消费者
  - `Home Office` – 家庭办公/小型办公
- **用途**：客户细分分析、购买力比较、营销策略模拟

### 5. Country
- **类型**：字符串
- **取值**：20 个国家，包括：
  - United States, Canada, Mexico
  - United Kingdom, Germany, France, Spain, Italy
  - China, Japan, South Korea, India, Australia
  - Saudi Arabia, UAE, South Africa, Nigeria
  - Brazil, Argentina, Colombia
- **用途**：国家级销售分析、地图可视化

### 6. Region
- **类型**：分类变量
- **取值**：
  - `North America` – 北美
  - `Europe` – 欧洲
  - `Asia Pacific` – 亚太
  - `Middle East & Africa` – 中东与非洲
  - `South America` – 南美
- **用途**：区域级销售分析、地区对比

### 7. Product_Category
- **类型**：分类变量
- **取值**：
  - `Technology` – 科技产品（耳机、键盘、鼠标等）
  - `Furniture` – 家具（桌椅、书柜等）
  - `Office Supplies` – 办公用品（文具、纸夹等）
  - `Clothing & Accessories` – 服装与配饰（衬衫、背包等）
- **用途**：产品大类分析、按类别预测销量

### 8. Product_Name
- **类型**：字符串
- **示例**：`Wireless Bluetooth Headphones`, `Mechanical Gaming Keyboard`, `Standing Desk Converter`
- **用途**：具体产品分析、热销单品排行
- **注意**：同一产品名称可能在不同订单中出现，可聚合统计

### 9. Quantity
- **类型**：整数
- **范围**：1 ～ 15（观察值，可能更大）
- **用途**：目标变量（销量预测）、销售分析
- **业务含义**：客户一次购买该产品的数量

### 10. Unit_Price
- **类型**：浮点数
- **单位**：美元（USD）
- **精度**：两位小数
- **用途**：价格分析、折扣计算
- **注意**：`Total_Sales` 已应用折扣，`Unit_Price` 为折扣前单价

### 11. Discount_Percent
- **类型**：整数（0, 5, 10, 15, 20, 25, 30）
- **含义**：促销折扣百分比
- **用途**：分析折扣对销量的影响、利润分析
- **公式**：`Total_Sales = Quantity × Unit_Price × (1 - Discount_Percent/100)`

### 12. Total_Sales
- **类型**：浮点数
- **单位**：美元
- **含义**：该订单的总销售额（已扣除折扣）
- **用途**：销售额分析、利润计算
- **公式**：`Total_Sales = Quantity × Unit_Price × (1 - Discount_Percent/100)`

### 13. Shipping_Cost
- **类型**：浮点数
- **单位**：美元
- **含义**：该订单的运费
- **用途**：成本分析、净利润计算
- **注意**：运费会从利润中扣除，影响净利润率

### 14. Profit
- **类型**：浮点数
- **单位**：美元
- **含义**：该订单的利润（已扣除产品成本、运费等）
- **用途**：盈利能力分析、高利润产品/客户识别
- **注意**：利润可能为负（亏损订单），可用于分析促销策略的有效性

### 15. Payment_Method
- **类型**：分类变量
- **取值**：
  - `Cash on Delivery` – 货到付款
  - `Credit Card` – 信用卡
  - `PayPal` – 贝宝支付
  - `Bank Transfer` – 银行转账
- **用途**：支付方式偏好分析、支付风险模拟

---

## 数据质量说明

- **缺失值**：未发现缺失值，所有字段均完整。
- **异常值**：`Profit` 字段存在负值（亏损订单），属于正常业务现象，无需剔除。
- **数据类型**：日期需转为 `datetime`；分类字段建议编码为数值（如 One-Hot 或 Label Encoding）。
- **排序**：数据未按 `Order_Date` 严格排序，预处理时必须排序。

---

## 数据使用建议

| 功能模块 | 使用字段 |
|----------|----------|
| 销售分析（趋势、排行） | `Order_Date`, `Product_Category`, `Product_Name`, `Region`, `Quantity`, `Total_Sales`, `Profit` |
| 销量预测 | `Order_Date`, `Product_Category` (聚合), `Quantity` (目标), `Discount_Percent`, `Shipping_Cost` (可选特征) |
| 客户细分分析（扩展） | `Customer_Segment`, `Total_Sales`, `Profit`, `Quantity` |
| 促销效果分析 | `Discount_Percent`, `Quantity`, `Total_Sales`, `Profit` |
| 支付方式分析 | `Payment_Method`, `Total_Sales`, `Quantity` |
| 可视化报表 | 所有字段均可用于图表展示 |