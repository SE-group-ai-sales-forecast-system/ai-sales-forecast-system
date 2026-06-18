from __future__ import annotations

import json
from pathlib import Path
from urllib import error, request

import pandas as pd
import streamlit as st

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

    model_columns = st.columns(2)
    lightgbm_clicked = model_columns[0].button(
        "使用 LightGBM 预测",
        use_container_width=True,
        type="primary",
    )
    baseline_clicked = model_columns[1].button(
        "使用 Baseline 预测",
        use_container_width=True,
    )

    if not lightgbm_clicked and not baseline_clicked:
        st.write("选择品类和预测天数后生成预测。")
        return

    model_type = "baseline" if baseline_clicked else "lightgbm"

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

    st.success(f"{product_id} 未来 {days} 天预测已生成。")
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


def main() -> None:
    st.set_page_config(page_title="销售预测", layout="wide")

    st.session_state.setdefault("backend_url", API_BASE_URL)
    st.sidebar.title("AI 销售预测系统")
    st.sidebar.text_input("后端地址", key="backend_url")
    st.sidebar.divider()

    render_login()
    render_prediction_page()


if __name__ == "__main__":
    main()
