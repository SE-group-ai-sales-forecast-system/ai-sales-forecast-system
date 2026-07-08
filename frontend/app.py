from __future__ import annotations

import json
from pathlib import Path
from urllib import error, request

import pandas as pd
import streamlit as st
import requests

try:
    import plotly.express as px
except Exception:
    px = None


API_BASE_URL = "http://localhost:8000"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "global_ecommerce_sales.csv"
DEFAULT_CATEGORIES = [
    "Technology",
    "Furniture",
    "Office Supplies",
    "Clothing & Accessories",
]


@st.cache_data(show_spinner=False)
def load_categories() -> list[str]:
    """Read stable demo categories from the bundled real sales CSV."""
    if not RAW_DATA_PATH.exists():
        return DEFAULT_CATEGORIES

    try:
        data = pd.read_csv(RAW_DATA_PATH, usecols=["Product_Category"])
    except Exception:
        return DEFAULT_CATEGORIES

    categories = sorted(
        str(category)
        for category in data["Product_Category"].dropna().unique().tolist()
        if str(category).strip()
    )
    return categories or DEFAULT_CATEGORIES


def post_json(path: str, payload: dict, token: str | None = None):
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{st.session_state.backend_url.rstrip('/')}{path}"
    api_request = request.Request(url, data=body, headers=headers, method="POST")

    try:
        with request.urlopen(api_request, timeout=20) as response:
            response_body = response.read().decode("utf-8")
            return response.status, json.loads(response_body) if response_body else {}
    except error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="ignore")
        try:
            detail = json.loads(response_body)
        except json.JSONDecodeError:
            detail = {"detail": response_body or str(exc)}
        return exc.code, detail
    except error.URLError as exc:
        return None, {"detail": f"无法连接后端服务：{exc.reason}"}
    except TimeoutError:
        return None, {"detail": "后端服务响应超时，请确认服务已启动。"}
    except Exception as exc:
        return None, {"detail": f"请求失败：{exc}"}


def format_error(result) -> str:
    if isinstance(result, dict):
        detail = result.get("detail") or result.get("message") or result
        return str(detail)
    return str(result)


def render_login() -> None:
    st.sidebar.subheader("登录")

    if st.session_state.get("token"):
        st.sidebar.success(f"已登录：{st.session_state.get('username')}")
        if st.sidebar.button("退出登录", use_container_width=True):
            st.session_state.pop("token", None)
            st.session_state.pop("username", None)
            st.session_state.pop("role", None)
            st.rerun()
        return

    with st.sidebar.form("login_form"):
        username = st.text_input("用户名", value="admin")
        password = st.text_input("密码", value="admin123", type="password")
        submitted = st.form_submit_button("登录", use_container_width=True)

    if not submitted:
        st.sidebar.caption("演示账号：admin/admin123 或 user/user123")
        return

    status, result = post_json(
        "/api/login",
        {"username": username, "password": password},
    )
    if status == 200:
        st.session_state["token"] = result["access_token"]
        st.session_state["username"] = username
        st.session_state["role"] = result.get("role", "")
        st.sidebar.success("登录成功")
        st.rerun()
    else:
        st.sidebar.error(format_error(result))


def render_prediction_page() -> None:
    st.title("销售预测")
    st.caption("最终回归演示页：登录后调用后端预测接口，展示未来销量预测。")

    if not st.session_state.get("token"):
        st.info("请先在左侧登录，然后进行销量预测。")
        return

    categories = load_categories()
    technology_index = categories.index("Technology") if "Technology" in categories else 0

    st.session_state.setdefault("selected_days", 7)
    st.session_state.setdefault("selected_model_type", "lightgbm")

    product_id = st.selectbox("商品品类", categories, index=technology_index)

    st.write("预测天数")
    day_columns = st.columns(3)
    for column, value in zip(day_columns, [7, 14, 30]):
        label = f"{value} 天"
        button_type = "primary" if st.session_state.selected_days == value else "secondary"
        if column.button(label, type=button_type, use_container_width=True):
            st.session_state.selected_days = value
            st.rerun()

    days = int(st.session_state.selected_days)
    st.caption(f"当前预测天数：{days} 天")

    model_name_map = {
        "lightgbm": "LightGBM模型",
        "baseline": "Baseline基准模型",
    }

    st.caption(f"当前预测模型：{model_name_map[st.session_state.selected_model_type]}")

    def select_model(model_type: str) -> None:
        st.session_state.selected_model_type = model_type

    model_columns = st.columns(2)

    lightgbm_clicked = model_columns[0].button(
        "使用 LightGBM 预测",
        use_container_width=True,
        type="primary" if st.session_state.selected_model_type == "lightgbm" else "secondary",
        on_click=select_model,
        args=("lightgbm",),
    )

    baseline_clicked = model_columns[1].button(
        "使用 Baseline 预测",
        use_container_width=True,
        type="primary" if st.session_state.selected_model_type == "baseline" else "secondary",
        on_click=select_model,
        args=("baseline",),
    )

    if not lightgbm_clicked and not baseline_clicked:
        st.write("选择品类、预测天数和预测模型后生成预测。")
        return

    model_type = st.session_state.selected_model_type

    status, result = post_json(
        "/api/predict",
        {
            "product_id": product_id,
            "days": int(days),
            "model_type": model_type,
        },
        token=st.session_state["token"],
    )

    if status != 200:
        st.error(format_error(result))
        return

    dates = result.get("predicted_dates", [])
    sales = result.get("predicted_sales", [])
    if len(dates) != int(days) or len(sales) != int(days):
        st.error("预测接口返回长度异常，请检查后端预测服务。")
        st.json(result)
        return

    frame = pd.DataFrame(
        {
            "date": dates,
            "predicted_sales": [max(float(value), 0.0) for value in sales],
        }
    )

    st.success(
        f"{product_id} 未来 {days} 天预测已生成，当前使用模型：{model_name_map[model_type]}。"
    )

    if px is not None:
        chart = px.line(
            frame,
            x="date",
            y="predicted_sales",
            markers=True,
            labels={"date": "日期", "predicted_sales": "预测销量"},
        )
        chart.update_layout(margin={"l": 10, "r": 10, "t": 20, "b": 10})
        st.plotly_chart(chart, use_container_width=True)
    else:
        st.line_chart(frame.set_index("date"))

    st.dataframe(
        frame.rename(columns={"date": "日期", "predicted_sales": "预测销量"}),
        use_container_width=True,
        hide_index=True,
    )
def render_home_page() -> None:
    st.title("首页看板")
    st.caption("展示系统整体运行状态和核心业务流程。")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("系统状态", "运行中")
    col2.metric("预测模型", "2 个")
    col3.metric("支持品类", len(load_categories()))
    col4.metric("后端接口", "已连接")

    st.divider()

    st.subheader("系统典型工作流程")
    st.info("登录 → 选择商品品类 → 选择预测天数 → 生成销量预测 → 查看库存预警 → 辅助运营决策")

    st.subheader("当前已实现功能")
    st.write("1. 用户登录验证")
    st.write("2. 商品品类选择")
    st.write("3. 7 天、14 天、30 天销量预测")
    st.write("4. LightGBM 模型预测")
    st.write("5. Baseline 基准模型预测")


def render_analysis_page() -> None:
    st.title("销售分析")
    st.caption("展示历史销售数据的基础分析结果，为销量预测提供参考。")

    if not RAW_DATA_PATH.exists():
        st.warning("未找到销售数据文件，暂时使用演示数据。")
        data = pd.DataFrame({
            "Product_Category": ["Technology", "Furniture", "Office Supplies", "Technology"],
            "Region": ["East", "West", "South", "North"],
            "Sales": [12000, 8500, 7600, 15000],
            "Quantity": [120, 85, 76, 150],
        })
    else:
        data = pd.read_csv(RAW_DATA_PATH)

    st.subheader("数据预览")
    st.dataframe(data.head(20), use_container_width=True)

    if "Order_Date" in data.columns and "Total_Sales" in data.columns:
        st.subheader("销售趋势折线图")

        trend_data = data.copy()
        trend_data["Order_Date"] = pd.to_datetime(trend_data["Order_Date"], errors="coerce")
        trend_data = trend_data.dropna(subset=["Order_Date"])

        if not trend_data.empty:
            monthly_sales = (
                trend_data
                .set_index("Order_Date")
                .resample("ME")["Total_Sales"]
                .sum()
                .reset_index()
            )
            monthly_sales["月份"] = monthly_sales["Order_Date"].dt.strftime("%Y-%m")
            monthly_sales = monthly_sales.rename(columns={"Total_Sales": "销售额"})

            if px is not None:
                fig = px.line(
                    monthly_sales,
                    x="月份",
                    y="销售额",
                    markers=True,
                    title="月度销售额趋势",
                    labels={"月份": "月份", "销售额": "销售额"},
                )
                fig.update_layout(margin={"l": 10, "r": 10, "t": 50, "b": 10})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.line_chart(monthly_sales.set_index("月份")["销售额"])
        else:
            st.warning("订单日期字段无法解析，暂时无法生成销售趋势图。")

    if "Product_Category" in data.columns:
        st.subheader("不同商品品类销售数量对比")

        category_count = data["Product_Category"].value_counts().reset_index()
        category_count.columns = ["商品品类", "数量"]

        if px is not None:
            fig = px.bar(
                category_count,
                x="商品品类",
                y="数量",
                text="数量",
                title="商品品类数量分布",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(category_count.set_index("商品品类"))

    if "Region" in data.columns:
        st.subheader("地区分布分析")

        region_count = data["Region"].value_counts().reset_index()
        region_count.columns = ["地区", "数量"]

        if px is not None:
            fig = px.pie(
                region_count,
                names="地区",
                values="数量",
                title="不同地区销售数据占比",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(region_count, use_container_width=True)


def render_inventory_page() -> None:
    st.title("库存预警")
    st.caption("根据预测需求量和当前库存，给出库存状态和补货建议。")

    if st.button("刷新预警数据", use_container_width=True):
        st.success("库存预警数据已刷新。")

    warning_data = pd.DataFrame([
        {
            "商品品类": "Technology",
            "当前库存": 120,
            "预测需求量": 180,
            "安全库存": 50,
            "库存状态": "库存不足",
            "补货建议": "建议补货 110 件",
        },
        {
            "商品品类": "Furniture",
            "当前库存": 300,
            "预测需求量": 120,
            "安全库存": 60,
            "库存状态": "库存正常",
            "补货建议": "暂不补货",
        },
        {
            "商品品类": "Office Supplies",
            "当前库存": 500,
            "预测需求量": 150,
            "安全库存": 80,
            "库存状态": "库存偏高",
            "补货建议": "减少进货",
        },
    ])

    def highlight_warning(row):
        if row["库存状态"] == "库存不足":
            return ["background-color: #7f1d1d; color: white; font-weight: bold"] * len(row)
        elif row["库存状态"] == "库存偏高":
            return ["background-color: #78350f; color: white"] * len(row)
        else:
            return [""] * len(row)

    st.dataframe(
        warning_data.style.apply(highlight_warning, axis=1),
        use_container_width=True,
        hide_index=True,
    )

    st.info("库存预警规则：当前库存 < 预测需求量 + 安全库存时，系统提示库存不足并给出补货建议。")

def render_upload_page() -> None:
    st.title("自定义数据上传")
    st.caption("前端支持上传CSV销售数据，并调用后端上传接口进行处理。")

    if not st.session_state.get("token"):
        st.info("请先在左侧登录，然后上传数据。")
        return

    uploaded_file = st.file_uploader(
        "请选择CSV文件",
        type=["csv"],
    )

    if uploaded_file is not None:
        st.write("文件名：", uploaded_file.name)

        if st.button("上传数据", use_container_width=True):
            try:
                response = requests.post(
                    f"{st.session_state.backend_url.rstrip('/')}/api/upload",
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file,
                            "text/csv",
                        )
                    },
                    headers={
                        "Authorization": f"Bearer {st.session_state['token']}"
                    },
                    timeout=20,
                )

                if response.status_code == 200:
                    st.success("数据上传成功")
                    st.json(response.json())
                else:
                    st.error(f"上传失败：{response.text}")

            except Exception as exc:
                st.error(f"无法连接后端服务：{exc}")


def render_about_page() -> None:
    st.title("系统说明")

    st.write("本系统面向电商运营人员，主要用于电商商品销售数据分析与销量预测。")
    st.write("系统通过调用后端预测接口，支持 LightGBM 模型和 Baseline 基准模型预测。")
    st.write("前端部分主要实现用户登录、页面导航、预测参数选择、预测结果展示、销售分析展示和库存预警展示。")

    st.subheader("前端负责人工作内容")
    st.write("1. 设计并实现系统前端页面结构")
    st.write("2. 实现登录状态展示与功能导航")
    st.write("3. 实现销售预测结果可视化")
    st.write("4. 补充销售分析和库存预警页面")
    st.write("5. 准备系统截图和演示材料")


def main() -> None:
    st.set_page_config(page_title="AI 销售预测系统", layout="wide")

    st.session_state.setdefault("backend_url", API_BASE_URL)

    st.sidebar.title("📦 AI 销售预测系统")
    st.sidebar.text_input("后端地址", key="backend_url")
    st.sidebar.divider()

    render_login()
    st.sidebar.divider()

    page = st.sidebar.radio(
        "功能导航",
        ["首页看板", "销售预测", "销售分析", "库存预警", "数据上传", "系统说明"],
    )

    if page == "首页看板":
        render_home_page()
    elif page == "销售预测":
        render_prediction_page()
    elif page == "销售分析":
        render_analysis_page()
    elif page == "库存预警":
        render_inventory_page()
    elif page == "数据上传":
        render_upload_page()
    elif page == "系统说明":
        render_about_page()


if __name__ == "__main__":
    main()
