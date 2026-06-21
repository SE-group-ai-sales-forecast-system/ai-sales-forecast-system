# 基于 AI 智能的电商商品销售分析与预测系统

> 软件工程课程实践项目 —— 企业商业智能（BI）分析系统 / 电商销售预测系统，**6月22日**（第 17 周）小组演示。

## 📖 项目简介

本项目面向电商运营人员，提供**销售数据分析**、**销量预测**、**库存预警**和**可视化报表**等功能。系统通过移动平均基线模型与 LightGBM 增强模型对历史销售数据进行预测，支持未来 7/14/30 天销量预测，并结合模拟库存自动判断库存风险，辅助运营决策。

项目采用前后端分离架构，后端提供 RESTful API，前端实现交互看板，算法模块独立封装。整个开发过程遵循软件工程规范，包含完整的需求、设计、测试和项目管理文档。

## 🎯 核心功能

- **数据导入与清洗**：支持 CSV 上传，自动处理缺失值、重复值和日期格式。
- **销售数据分析**：按时间、商品、品类、地区等多维度统计销售额与销量，展示趋势与排行。
- **销量预测**：选择商品或品类，预测未来销量并绘制曲线（支持 7/14/30 天）。
- **库存预警**：模拟库存，结合当前预测销量，判断“库存不足/正常/过高”，给出建议补货量。
- **可视化报表**：销售趋势图、热销商品排行、地区分布图、预测对比曲线、预警表格。
- **用户登录与权限**（基础）：简单登录页，区分普通用户与管理员（可选扩展）。

## 🛠 技术栈

| 层次         | 技术选型                                                     |
| ------------ | ------------------------------------------------------------ |
| **前端**     | Streamlit（快速原型） / Vue3 + ECharts（可换）                |
| **后端**     | Python 3.13.12 + FastAPI + Uvicorn                              |
| **算法**     | Pandas, NumPy, Scikit-learn, LightGBM；默认稳定基线为 7 日移动平均，指数平滑为备选 |
| **数据库**   | SQLite（开发）/ MySQL（可选）                                |
| **可视化**   | Plotly, Matplotlib, ECharts                                  |
| **测试**     | Pytest                                                        |
| **版本控制** | Git + GitHub（私有仓库）                                     |

## 📁 目录结构（预测）

```
ai-sales-forecast-system/
│
├── .gitignore
├── README.md
├── requirements.txt
│
├── data/                     # 数据目录
│   ├── raw/                  # 原始数据（不提交git）
│   ├── processed/            # 清洗后数据（示例数据可提交）
│   └── data_dict.md          # 字段说明
│
├── backend/                  # FastAPI后端
│   ├── __init__.py
│   ├── main.py               # 入口文件
│   ├── api/                  # 路由
│   ├── models/               # 数据模型
│   ├── services/             # 业务逻辑
│   └── config.py
│
├── frontend/                 # 前端应用
│   ├── app.py                # Streamlit主程序
│   ├── pages/                # 多页面（登录、数据管理、分析、预测、预警）
│   └── assets/
│
├── algorithm/                # 算法模块
│   ├── data_cleaning.py
│   ├── feature_engineering.py
│   ├── baseline_model.py
│   ├── lightgbm_model.py
│   ├── inventory_warning.py
│   └── evaluation.py
│
├── tests/                    # 测试用例
│   ├── test_backend.py
│   ├── test_algorithm.py
│   └── test_cases.md
│
├── docs/                     # 文档
│   ├── requirements/         # 需求分析文档
│   ├── design/               # 软件设计文档
│   ├── management/           # 项目管理文档（分工、甘特图）
│   └── presentation/         # PPT、视频素材
│
└── scripts/                  # 辅助脚本
    └── run.sh / run.bat
```

## 🚀 用户快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/SE-group-ai-sales-forecast-system/ai-sales-forecast-system.git
cd ai-sales-forecast-system
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
# 或
venv\Scripts\activate         # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 准备数据

- 将电商销售数据（CSV格式）放入 `data/raw/` 目录。
- 示例数据格式请参考 `data/data_dict.md`（至少包含：日期、商品ID、销量、销售额、地区、库存量）。

### 5. 启动后端服务

```bash
cd backend
uvicorn main:app --reload --port 8000
```

后端 API 文档地址：
http://localhost:8000/docs
### 6. 启动前端看板

打开另一个终端，在项目根目录执行：

```bash
streamlit run frontend/app.py
```

浏览器自动打开 `http://localhost:8501` 即可访问系统。

### 7. 一键启动(适配Windows和Linux/macOS)

```bash
python scripts/start.py
```

## 🧪 测试

运行所有测试：

```bash
pytest tests/
```

或单独测试某个模块：

```bash
pytest tests/test_algorithm.py
```

最终回归建议命令：

```bash
python -m compileall -q algorithm backend frontend tests
python -m algorithm.evaluation
python -m algorithm.lightgbm_evaluation
python -m pytest tests -q
python -m unittest discover -s tests -p "test_*.py" -v
```

说明：`lightgbm` 是可选增强依赖；本地未安装时，LightGBM 专项评估会输出跳过信息，预测接口仍可通过移动平均基线稳定返回结果。

## 👥 小组分工

| 成员 | 角色         | 主要任务                                                         | 个人产出                                 |
| ---- | ------------ | ---------------------------------------------------------------- | ---------------------------------------- |
| [1号](https://github.com/AstonFrwine)  | 项目经理    | 需求收敛、任务分配、进度管理、文档汇总、PPT与汇报组织            | 项目管理文档、甘特图、分工说明、答辩串词 |
| [2号](https://github.com/ClaytonWs)  | 数据负责人   | 整理电商销售数据、数据清洗、字段字典、数据质量检查               | 数据集、数据说明、清洗代码、质量报告     |
| [3号](https://github.com/dragon-zhang-woo)  | 算法负责人A  | 移动平均基线模型、指数平滑备选、回测与误差分析、预测兜底链路             | 基线模型代码、回测结果、误差图           |
| [4号](https://github.com/jfLuo33)  | 算法负责人B  | LightGBM主模型、特征工程、误差评价、库存预警规则                 | 主模型代码、特征工程代码、预测结果表     |
| [5号](https://github.com/fuyw1)  | 后端负责人   | FastAPI接口、模型调用、数据读取、接口文档与后端联调              | 后端代码、接口文档、运行说明             |
| [6号](https://github.com/Traveler-BS)  | 前端/测试负责人 | 页面实现、图表交互、测试用例设计、系统截图与录屏                 | 前端页面、测试报告、截图、演示视频素材   |

## 📄 主要文档

- [分支协作规范](BRANCH_STRATEGY.md)
- [需求分析文档](docs/requirements/requirements.md)
- [数据字典文档](data/data_dict.md)
- [最小可行产品（MVP）功能文档](docs/requirements/mvp_scope.md)
- [项目计划与推进方案](docs/management/project_plan.md)
- [项目操作数据看板](docs/operation/project_operation_dashboard_0620.md)
- [项目贡献说明](CONTRIBUTORS.md)
- [用例](docs/design/use_case.md)
- [‼️ 极限冲刺时间表](docs/management/detailed_assignment.md)
- [算法A模型答辩讲稿](docs/presentation/algorithm_a_model_defense_0619.md)
- [算法A答辩PPT页级大纲](docs/presentation/algorithm_a_ppt_outline_0619.md)

## 📌 版本规划

- **v0.1**：完成数据清洗、销售分析基础可视化、基线模型。
- **v0.2**：完成LightGBM预测、库存预警、前后端联调、完整页面。
- **v1.0**：系统测试、文档完善、答辩准备。

## 🤝 贡献指南

1. 创建个人功能分支：`git checkout -b feature/模块名`
2. 提交代码：`git commit -m "[模块] 简要描述"`
3. 推送到远程：`git push origin feature/模块名`
4. 在 GitHub 上创建 Pull Request，由组长或模块负责人 Review 后合并至 `main` 分支。

## 📜 免责声明

本项目为课程实践作品，部分或全部数据为模拟或公开数据集，仅用于教学展示。使用者应遵守相应 LICENSE 并对生成内容负责，开发者概不承担由此产生的任何责任。

当前预测模型适合课程演示、趋势参考和原型联调，不应直接作为真实生产采购或库存自动决策依据；实际上线前需要接入持续更新的业务数据、外部影响因素、模型监控和人工审批。
