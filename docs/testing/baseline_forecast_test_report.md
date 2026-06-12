# 移动平均基线预测模型测试报告

## 基本信息

- 测试日期：2026-06-11
- 测试分支：`feature/baseline-forecast`
- 测试对象：算法A移动平均基线预测模型
- 相关模块：
  - `algorithm/baseline_model.py`
  - `backend/services/predict_service.py`
  - `tests/test_algorithm.py`

## 本地测试环境

- Python：`3.13.12`
- Python 解释器：`D:\Conda\python.exe`
- pytest：`9.0.3`
- pytest 安装方式：`python -m pip install pytest`
- pytest 安装位置：`D:\Conda\Lib\site-packages`

## 测试范围

本次测试重点覆盖算法A今日交付内容：

- 预测天数是否与输入参数一致
- 预测日期是否按天连续递增
- 预测销量是否保持非负
- 是否能按商品类别筛选历史销量
- 是否兼容原始订单列名：`Order_Date`、`Product_Category`、`Quantity`
- 是否正确保留 0 销量历史记录
- 是否将历史区间内缺失日期按 0 销量补齐后参与移动平均
- 是否能直接读取真实原始数据 `data/raw/global_ecommerce_sales.csv` 进行预测
- LightGBM 不存在时，后端预测服务是否能回退到移动平均基线模型
- 在无历史数据时，预测接口是否仍返回后端兼容结构：`{"dates": [...], "sales": [...]}`

## 执行命令与结果

### 1. pytest 安装确认

命令：

```powershell
python -m pip show pytest
```

结果：

```text
Name: pytest
Version: 9.0.3
Location: D:\Conda\Lib\site-packages
```

结论：本地环境已安装 pytest。

### 2. 语法编译检查

命令：

```powershell
python -m compileall -q algorithm backend tests
```

结果：命令退出码为 0，无编译错误输出。

结论：算法、后端服务和测试目录内的 Python 文件语法检查通过。

### 3. pytest 测试收集

命令：

```powershell
python -m pytest tests --collect-only -q
```

结果：

```text
tests/test_algorithm.py::BaselinePredictorTest::test_predict_dates_are_continuous
tests/test_algorithm.py::BaselinePredictorTest::test_predict_days_count
tests/test_algorithm.py::BaselinePredictorTest::test_predict_fills_missing_calendar_days_with_zero
tests/test_algorithm.py::BaselinePredictorTest::test_predict_filters_category
tests/test_algorithm.py::BaselinePredictorTest::test_predict_keeps_zero_sales_days
tests/test_algorithm.py::BaselinePredictorTest::test_predict_sales_are_non_negative
tests/test_algorithm.py::BaselinePredictorTest::test_predict_service_falls_back_to_baseline_when_lightgbm_missing
tests/test_algorithm.py::BaselinePredictorTest::test_predict_supports_raw_order_columns
tests/test_algorithm.py::BaselinePredictorTest::test_predict_with_real_raw_csv

9 tests collected in 0.09s
```

结论：pytest 能正常发现算法测试用例，共收集 9 项。

### 4. pytest 详细执行

命令：

```powershell
python -m pytest tests/test_algorithm.py -vv
```

结果：

```text
tests/test_algorithm.py::BaselinePredictorTest::test_predict_dates_are_continuous PASSED
tests/test_algorithm.py::BaselinePredictorTest::test_predict_days_count PASSED
tests/test_algorithm.py::BaselinePredictorTest::test_predict_fills_missing_calendar_days_with_zero PASSED
tests/test_algorithm.py::BaselinePredictorTest::test_predict_filters_category PASSED
tests/test_algorithm.py::BaselinePredictorTest::test_predict_keeps_zero_sales_days PASSED
tests/test_algorithm.py::BaselinePredictorTest::test_predict_sales_are_non_negative PASSED
tests/test_algorithm.py::BaselinePredictorTest::test_predict_service_falls_back_to_baseline_when_lightgbm_missing PASSED
tests/test_algorithm.py::BaselinePredictorTest::test_predict_supports_raw_order_columns PASSED
tests/test_algorithm.py::BaselinePredictorTest::test_predict_with_real_raw_csv PASSED

9 passed in 0.15s
```

结论：算法单元测试全部通过。

### 5. tests 目录级 pytest 执行

命令：

```powershell
python -m pytest tests -q
```

结果：

```text
.........                                                                [100%]
9 passed in 0.18s
```

结论：当前 tests 目录下可执行的 pytest 测试全部通过。

### 6. unittest 兼容验证

命令：

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

结果：

```text
Ran 9 tests in 0.034s

OK
```

结论：测试文件仍兼容 Python 标准库 unittest 运行方式。

### 7. 最小导入与预测调用

命令：

```powershell
python -c "from algorithm.baseline_model import BaselinePredictor; print(BaselinePredictor().predict('Technology', 7))"
```

结果：

```text
{'dates': ['2026-06-12', '2026-06-13', '2026-06-14', '2026-06-15', '2026-06-16', '2026-06-17', '2026-06-18'], 'sales': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}
```

结论：模型可被直接导入；无历史数据时仍能返回后端兼容的预测结果结构。

### 8. 真实原始数据预测验证

命令：

```powershell
python -c "from algorithm.baseline_model import BaselinePredictor; print(BaselinePredictor('data/raw/global_ecommerce_sales.csv').predict('Technology', 7))"
```

结果：

```text
{'dates': ['2026-01-01', '2026-01-02', '2026-01-03', '2026-01-04', '2026-01-05', '2026-01-06', '2026-01-07'], 'sales': [1.14, 1.14, 1.14, 1.14, 1.14, 1.14, 1.14]}
```

结论：移动平均模型可直接读取真实原始 CSV，按 `Technology` 类别生成未来 7 天预测；预测日期从真实数据最后日期 `2025-12-31` 的下一天 `2026-01-01` 开始，销量输出为非负浮点数。

### 9. 后端回退验证

验证内容：

- 当 `model_type="lightgbm"` 但 LightGBM 模块不存在时，`PredictService` 会回退到 `BaselinePredictor`。
- 返回结果仍包含 `dates` 和 `sales`，长度与请求天数一致。
- 预测销量保持非负。

结论：后端预测服务在复杂模型不可用时仍能稳定返回结果，符合算法A作为兜底模型的职责。

## 当前结论

算法A移动平均基线预测模型在当前本地环境下通过语法编译、pytest 收集、pytest 执行、unittest 兼容运行、最小导入调用、真实 CSV 预测和后端回退验证。当前测试能证明模型基础预测行为、筛选逻辑、日期连续性、缺失日期补 0、非负输出、原始订单格式兼容性和真实数据输入均符合本阶段交付要求。

## 注意事项

- 当前测试主要覆盖算法模块核心行为与后端预测服务轻量回退，尚未覆盖完整前后端 HTTP 联调流程。
- 本地 `tests/ffmpeg.zip` 与 `tests/ffmpeg_tmp/` 已加入 `.gitignore`，不会进入后续提交。
- 后续如数据负责人提供 `daily_sales_for_forecast.csv`，建议继续补充基于每日聚合表的集成测试。
