# 算法A协作开发记忆文件

## 1. 项目协作背景

- 项目名称：AI 智能电商商品销售分析与预测系统。
- 远程仓库：`SE-group-ai-sales-forecast-system/ai-sales-forecast-system`。
- 协作模式：六人小组在两周内模拟两个月的软件工程协作开发流程。
- 项目性质：软件工程期末实践项目，重点不仅是代码实现，也包括需求、设计、分工、分支协作、测试验证、PR 审查和答辩追踪。
- 当前主要开发分支：`develop`。
- 稳定发布分支：`main`，不直接在 `main` 上开发。

## 2. 我的角色与职责

- 我的协作角色：算法A。
- 当前主线任务：实现销售预测的移动平均基线模型。
- 算法A定位：
  - 为系统提供可稳定调用的基础预测能力。
  - 在更复杂模型不可用或依赖未安装时，作为后端预测服务的可靠兜底方案。
  - 优先保证接口稳定、输出格式统一、测试可验证。

## 3. 仓库整体结构与当前状态

### 主要目录

- `algorithm/`：算法模块目录，当前已新增移动平均基线模型 `baseline_model.py`。
- `backend/`：后端服务目录，包含预测服务等业务逻辑。
- `frontend/`：前端目录，早期检查时前端实现仍较薄弱。
- `data/`：数据目录，用于存放原始数据、处理后数据或示例数据。
- `docs/`：项目文档目录。
  - `docs/requirements/`：需求与 MVP 范围文档。
  - `docs/design/`：架构设计、用例图等设计文档。
  - `docs/management/`：项目计划、详细分工等管理文档。
  - `docs/testing/`：测试报告与验证记录。
  - `docs/memory/`：面向后续协作恢复上下文的记忆文件。
- `tests/`：测试目录，当前已包含算法A相关单元测试 `test_algorithm.py`。

### 当前已完成的算法A工作

- 已从 `develop` 创建功能分支：`feature/baseline-forecast`。
- 已实现 `algorithm/baseline_model.py`：
  - `BaselinePredictor` 移动平均预测器。
  - 默认窗口为 7 天。
  - 返回结构兼容后端预测服务：`{"dates": [...], "sales": [...]}`。
  - 支持按商品类别或商品名筛选历史销量。
  - 支持列表、字典、CSV 路径和类 DataFrame 输入。
  - 数据不足或无数据时返回稳定兜底结果，避免接口崩溃。
- 已更新 `backend/services/predict_service.py`：
  - 优先调用 LightGBM。
  - LightGBM 不可用时回退到移动平均基线模型。
  - 避免继续使用随机模拟数据作为主要兜底。
- 已新增 `tests/test_algorithm.py`：
  - 覆盖预测天数、日期连续、销量非负、类别筛选、原始订单列名兼容、0 销量保留等行为。
- 已新增测试报告：
  - `docs/testing/baseline_forecast_test_report.md`
- 已更新 `.gitignore`：
  - 忽略本地 `tests/ffmpeg.zip`
  - 忽略本地 `tests/ffmpeg_tmp/`
- 已从最新 `develop` 新建后续稳固分支：`feature/algorithm-a-real-data-validation`。
- 已补强真实原始订单数据场景：
  - 按日期聚合后补齐类别历史区间内缺失日期为 0 销量。
  - 让 7 日移动平均按连续日历天计算，而不是只按有订单的日期计算。
- 已补充真实数据验证：
  - 直接读取 `data/raw/global_ecommerce_sales.csv`。
  - 验证 `Technology` 类别预测从 `2026-01-01` 开始。
  - 验证 LightGBM 不存在时后端预测服务可回退到基线模型。
- 已完成 6/13 预测接口联调稳固：
  - PR #15 `test(算法): 补充真实数据预测验证` 已合入 `develop`。
  - 从最新 `develop` 新建 `feature/algorithm-a-predict-api-integration`。
  - 后端预测服务在未上传数据时默认读取 `data/raw/global_ecommerce_sales.csv`。
  - 从项目根目录或 `backend/` 目录调用预测服务时，都能返回真实数据驱动的预测结果。
  - 已补充 `/api/predict` TestClient 轻量联调测试。
- 已完成 6/14 预测接口契约稳固：
  - PR #16 `fix(算法): 完善预测服务默认真实数据源` 已合入 `develop`。
  - PR #18 `fix(算法): 稳固预测接口模型回退逻辑` 已合入 `develop`。
  - 从最新 `develop` 新建 `feature/algorithm-a-0614-predict-contract-validation`。
  - 在算法B LightGBM 合入后，加固 `PredictService` 的 LightGBM 调用路径。
  - 当 LightGBM 不可导入、预测抛错或返回异常结构时，预测服务会回退到算法A移动平均基线模型。
  - `/api/predict` 已覆盖默认 `model_type`、显式 `baseline` 和显式 `lightgbm` 请求。
  - 已验证 7、14、30 天预测长度和未知类别兼容结构。
- 已完成 6/15 预测误差评估与指数平滑备选：
  - 从最新 `develop` 新建 `feature/algorithm-a-0615-forecast-evaluation-smoothing`。
  - `BaselinePredictor` 默认仍保持 `moving_average`，新增显式 `strategy="exponential_smoothing"` 备选。
  - 新增 `algorithm/evaluation.py`，可基于真实 CSV 输出各品类移动平均与简单指数平滑的一步预测 MAE。
  - 真实 CSV 评估结果显示 `Office Supplies` 和 `Technology` 上指数平滑略优，另外两个品类移动平均略优。
  - 已补充算法B库存预警引擎通过 `PredictService` 调用算法A预测结果的最小联调测试。
- 已完成 6/16 测试与 Bug 修复收口：
  - PR #21 `feat(算法): 增加预测误差评估与指数平滑备选` 已合入 `develop`。
  - 从最新 `develop` 新建 `feature/algorithm-a-0616-testing-bugfix-evaluation-report`。
  - `PredictService` 直接调用遇到 `days=0`、负数、非整数、非数字或空值时，会稳定回落到 7 天默认预测。
  - 本地未安装 `lightgbm` 时，算法B LightGBM 专项测试跳过，算法A预测、回退、接口和库存预警测试仍能正常收集执行。
  - `/api/predict` 公共请求/响应契约保持不变。
- 已完成 6/17 答辩模型对比图准备：
  - PR #23 `test(算法): 补充预测链路测试与模型评估记录` 已合入 `develop`。
  - 从最新 `develop` 新建 `feature/algorithm-a-0617-model-comparison-chart`。
  - 新增 `algorithm/forecast_visualization.py`，可基于真实 CSV 生成最近 60 天实际销量 vs 7 日移动平均一步预测对比图。
  - 默认图表输出为 `docs/testing/images/moving_average_vs_actual_0617.png`，覆盖 4 个真实品类。
  - `/api/predict` 公共请求/响应契约保持不变，本轮只新增答辩图表材料和可复现脚本。

### 当前分支与 PR 状态

- 基线模型功能分支 `feature/baseline-forecast` 已通过 PR 合入 `develop`。
- 真实数据验证分支 `feature/algorithm-a-real-data-validation` 已通过 PR #15 合入 `develop`。
- 预测接口默认真实数据源分支 `feature/algorithm-a-predict-api-integration` 已通过 PR #16 合入 `develop`。
- 预测接口契约稳固分支 `feature/algorithm-a-0614-predict-contract-validation` 已通过 PR #18 合入 `develop`。
- 预测误差评估与指数平滑分支 `feature/algorithm-a-0615-forecast-evaluation-smoothing` 已通过 PR #21 合入 `develop`。
- 预测链路测试与 Bug 修复分支 `feature/algorithm-a-0616-testing-bugfix-evaluation-report` 已通过 PR #23 合入 `develop`。
- 当前开发分支：`feature/algorithm-a-0617-model-comparison-chart`。
- 当前开发 PR：#24 `feat(算法): 增加移动平均对比图生成能力`，目标分支为 `develop`。
- 当前开发任务：6/17 答辩模型对比图生成、测试报告补充和记忆文件更新。
- 目标合并分支：`develop`。

## 4. 具体开发计划

### 已完成计划

1. 从 `develop` 新建 `feature/baseline-forecast` 分支。
2. 实现移动平均基线预测模型。
3. 将基线模型接入后端预测服务兜底逻辑。
4. 编写算法A单元测试。
5. 安装并使用 pytest 做更详细测试。
6. 编写测试报告并提交到 `docs/testing/`。
7. 忽略本地测试产物，避免误提交无关大文件。
8. 推送功能分支并创建指向 `develop` 的 PR。
9. 基于真实原始数据补充预测冒烟测试。
10. 补强缺失日期按 0 销量参与移动平均的逻辑。
11. 补充后端预测服务回退到基线模型的轻量验证。
12. 完成后端预测服务默认真实 CSV 数据源回退。
13. 补充 `/api/predict` 轻量联调测试。
14. 记录 6/13 预测接口联调验证结果。
15. 从最新 `develop` 新建 `feature/algorithm-a-0614-predict-contract-validation` 分支。
16. 加固 LightGBM 预测调用，异常或返回结构错误时回退到移动平均基线模型。
17. 补充默认模型、显式 LightGBM、显式 baseline、7/14/30 天和未知类别测试。
18. 记录 6/14 预测接口契约稳固验证结果。
19. 从最新 `develop` 新建 `feature/algorithm-a-0615-forecast-evaluation-smoothing` 分支。
20. 为 `BaselinePredictor` 增加简单指数平滑备选策略，并保持移动平均为默认策略。
21. 新增真实 CSV 预测误差评估模块，输出移动平均与指数平滑 MAE 对比表。
22. 补充库存预警引擎接入算法A预测结果的最小联调测试。
23. 记录 6/15 预测评估与指数平滑验证结果。
24. 从最新 `develop` 新建 `feature/algorithm-a-0616-testing-bugfix-evaluation-report` 分支。
25. 修复 `PredictService` 直接调用异常 `days` 输入可能导致 LightGBM 校验或空预测路径崩溃的问题。
26. 调整 LightGBM 专项测试，使本地未安装可选依赖时跳过，不阻断算法A测试收集。
27. 记录 6/16 测试与 Bug 修复、模型评估和手工预测验证结果。
28. 从最新 `develop` 新建 `feature/algorithm-a-0617-model-comparison-chart` 分支。
29. 新增移动平均 vs 实际销量对比图生成脚本，并生成答辩用 PNG 图表。
30. 补充图表数据连续性、非负销量和 PNG 文件生成测试。
31. 记录 6/17 答辩模型对比图验证结果。

### 后续建议计划

1. 等待 6/17 答辩模型对比图 PR 审查，并根据 review comments 修改。
2. 与组长确认 `docs/testing/images/moving_average_vs_actual_0617.png` 是否可直接放入答辩 PPT。
3. 与后端和前端成员确认 `/api/predict` 字段不再变更，便于预测页和库存预警页调用。
4. 若数据负责人提供新的每日聚合表，补充基于该数据源的集成测试。
5. 若时间允许，再与复杂模型成员协作比较 LightGBM、Prophet、SARIMAX 等模型效果。

## 5. 必须严格遵守的协作规范

- 所有功能开发必须从 `develop` 分支切出功能分支。
- 功能分支命名应清晰表达任务，例如 `feature/baseline-forecast`。
- 不直接向 `main` 提交代码。
- 不直接把未审查代码合并到 `develop`。
- 合并应通过 PR，目标分支为 `develop`。
- 提交信息使用中文，便于课程项目记录和答辩追踪。
- 每次提交前必须检查：
  - 当前所在分支是否正确。
  - `git status` 是否只包含本任务相关文件。
  - 是否误加入临时文件、大文件、缓存文件或本地环境文件。
- 修改代码后必须尽量运行相关测试，并在 PR 或测试报告中说明测试结果。
- 不随意回滚或覆盖队友改动。
- 发现远端 `develop` 更新后，应及时同步并处理冲突。
- 文档、测试和代码实现应一起维护，避免只有代码没有说明。

## 6. 当前可复用命令

```powershell
git checkout develop
git pull --ff-only origin develop
git checkout feature/algorithm-a-0617-model-comparison-chart
git status --short --branch
```

```powershell
python -m compileall -q algorithm backend tests
python -m algorithm.evaluation
python -m algorithm.forecast_visualization
python -m pytest tests -q
python -m unittest discover -s tests -p "test_*.py" -v
```

```powershell
python -c "from backend.services.predict_service import PredictService; print(PredictService().predict('Technology', 7, 'baseline'))"
```

## 7. 后续继续工作时的优先级

1. 优先保证当前 6/17 PR 与 `develop` 不冲突。
2. 优先响应 PR 审查意见。
3. 优先确认答辩图表和模型选择理由能被 PPT 复用，而不是提前实现复杂模型。
4. 优先保持算法A接口稳定，避免影响后端和前端协作。
5. 优先记录关键测试结果和设计理由，方便最终答辩。
