# 项目贡献说明

本文件用于期末考核和答辩时说明小组成员分工、Git 操作记录与模块交付关系。GitHub 自动贡献者统计可能受到提交邮箱归属影响，因此最终贡献以 Git 历史、PR 合并记录、管理文档、测试报告和本说明共同为准。

## 核心成员与职责

| 成员 | GitHub | 角色 | 主要交付 |
| --- | --- | --- | --- |
| 1号 | [AstonFrwine](https://github.com/AstonFrwine) | 项目经理 | 需求收敛、任务分配、文档汇总、PR 合并、答辩组织 |
| 2号 | [ClaytonWs](https://github.com/ClaytonWs) | 数据负责人 | 数据整理、字段字典、数据质量说明 |
| 3号 | [dragon-zhang-woo](https://github.com/dragon-zhang-woo) | 算法负责人A | 移动平均基线、指数平滑备选、预测接口回退、MAE 评估、模型对比图、预测页回归协助 |
| 4号 | [jfLuo33](https://github.com/jfLuo33) | 算法负责人B | LightGBM、特征工程、库存预警规则、模型评估 |
| 5号 | [fuyw1](https://github.com/fuyw1) | 后端负责人 | FastAPI 接口、登录、启动脚本、后端联调 |
| 6号 | [Traveler-BS](https://github.com/Traveler-BS) | 前端/测试负责人 | Streamlit 页面、测试用例、演示视频素材 |

## 算法A贡献归属说明

算法A早期提交使用的作者邮箱为：

```text
张航晨 <16723149+zhang-hangchen464654@user.noreply.gitee.com>
```

该邮箱是 Gitee noreply 邮箱，GitHub 贡献者组件可能无法自动归属到 `dragon-zhang-woo`。但这些提交仍然保留在 Git 历史中，并可通过 `git shortlog -sne --all`、PR 合并记录、测试报告和算法A记忆文件追踪。

6/20 后续提交已切换为：

```text
dragon-zhang-woo <zhanghch66@mail2.sysu.edu.cn>
```

## 算法A主要交付证据

- PR #12/#13：移动平均基线预测模型与测试报告。
- PR #15/#16：真实数据预测验证与预测服务默认真实数据源。
- PR #18：预测接口契约稳固和 LightGBM 异常回退。
- PR #21：预测误差评估与指数平滑备选。
- PR #23：预测链路测试、异常输入修复和模型评估记录。
- PR #24：移动平均 vs 实际销量答辩图表。
- PR #26：最终回归与预测页交互修复。
- PR #29：模型答辩材料与完成度盘点。

## 操作数据看板

- Markdown 摘要：`docs/operation/project_operation_dashboard_0620.md`
- HTML 看板：`docs/operation/project_operation_dashboard_0620.html`
- 可复现脚本：`scripts/generate_project_operation_dashboard.py`

看板使用真实 Git 历史与管理排期生成，说明实际 6/9-6/20 开发窗口如何对应课程要求中的两个月软件工程开发模拟。
