import sqlite3
import pandas as pd
from pathlib import Path
from config import settings

DB_PATH = Path(settings.BASE_DIR) / "data" / "sales.db"


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            order_date DATE,
            customer_name TEXT,
            customer_segment TEXT,
            country TEXT,
            region TEXT,
            product_category TEXT,
            product_name TEXT,
            quantity INTEGER,
            unit_price REAL,
            discount_percent REAL,
            total_sales REAL,
            shipping_cost REAL,
            profit REAL,
            payment_method TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_sales (
            date DATE,
            category TEXT,
            quantity INTEGER,
            PRIMARY KEY (date, category)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forecast_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            forecast_date DATE,
            category TEXT,
            horizon INTEGER,
            predicted_quantity REAL,
            model_version TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            current_stock REAL,
            forecast_7d REAL,
            safe_stock REAL,
            suggested_order REAL,
            warning_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print(f"数据库初始化完成: {DB_PATH}")


def import_csv_to_db(csv_path: str, table_name: str = "orders"):
    df = pd.read_csv(csv_path)

    column_mapping = {
        "Order_ID": "order_id",
        "Order_Date": "order_date",
        "Customer_Name": "customer_name",
        "Customer_Segment": "customer_segment",
        "Country": "country",
        "Region": "region",
        "Product_Category": "product_category",
        "Product_Name": "product_name",
        "Quantity": "quantity",
        "Unit_Price": "unit_price",
        "Discount_Percent": "discount_percent",
        "Total_Sales": "total_sales",
        "Shipping_Cost": "shipping_cost",
        "Profit": "profit",
        "Payment_Method": "payment_method",
    }

    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df.rename(columns={old_col: new_col}, inplace=True)

    conn = get_connection()
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()

    _build_daily_sales()

    print(f"导入完成: {len(df)} 行数据 -> {table_name}")


def _build_daily_sales():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT order_date AS date, product_category AS category, SUM(quantity) AS quantity
        FROM orders
        GROUP BY order_date, product_category
        ORDER BY order_date
    """, conn)

    df.to_sql("daily_sales", conn, if_exists="replace", index=False)
    conn.close()
    print(f"daily_sales 聚合表已生成: {len(df)} 行")


def query_to_df(sql: str, params=None) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def get_orders_df(category: str = None, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    sql = "SELECT * FROM orders WHERE 1=1"
    params = []

    if category:
        sql += " AND product_category = ?"
        params.append(category)
    if start_date:
        sql += " AND order_date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND order_date <= ?"
        params.append(end_date)

    return query_to_df(sql, params)


def get_daily_sales_df(category: str = None) -> pd.DataFrame:
    if category:
        return query_to_df(
            "SELECT * FROM daily_sales WHERE category = ? ORDER BY date",
            [category]
        )
    return query_to_df("SELECT * FROM daily_sales ORDER BY date")


def save_forecast_results(results: list[dict]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM forecast_results")
    cursor.executemany(
        "INSERT INTO forecast_results (forecast_date, category, horizon, predicted_quantity, model_version) "
        "VALUES (:forecast_date, :category, :horizon, :predicted_quantity, :model_version)",
        results
    )
    conn.commit()
    conn.close()


def save_inventory_warnings(warnings: list[dict]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory_warnings")
    cursor.executemany(
        "INSERT INTO inventory_warnings (category, current_stock, forecast_7d, safe_stock, suggested_order, warning_date) "
        "VALUES (:category, :current_stock, :forecast_7d, :safe_stock, :suggested_order, :warning_date)",
        warnings
    )
    conn.commit()
    conn.close()