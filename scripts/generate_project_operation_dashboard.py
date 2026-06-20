"""Generate a source-backed project operation dashboard.

The dashboard uses local Git history and the documented course schedule to
present the compressed "two-month" software engineering simulation without
rewriting commits or fabricating historical metadata.
"""

from __future__ import annotations

import html
import json
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "docs" / "operation"
HTML_OUTPUT = OUTPUT_DIR / "project_operation_dashboard_0620.html"
MD_OUTPUT = OUTPUT_DIR / "project_operation_dashboard_0620.md"
JSON_OUTPUT = OUTPUT_DIR / "project_operation_metrics_0620.json"

START_DATE = date(2026, 6, 9)
END_DATE = date(2026, 6, 20)

AUTHOR_ALIASES = {
    "16723149+zhang-hangchen464654@user.noreply.gitee.com": "张航晨 / dragon-zhang-woo（算法A）",
    "zhanghch66@mail2.sysu.edu.cn": "张航晨 / dragon-zhang-woo（算法A）",
    "jihx6@mail2.sysu.edu.cn": "AstonFrwine（项目管理）",
    "19867877751@163.com": "ljf / jfLuo33（算法B）",
    "2284599948@qq.com": "fuyw1（后端）",
}

SIMULATED_PHASES = [
    ("第1周", "立项与需求收敛", "项目初始化、README、需求与计划文档"),
    ("第2周", "架构与数据准备", "后端框架、系统架构、原始数据接入"),
    ("第3周", "算法A基线模型", "移动平均模型、真实数据验证、测试报告"),
    ("第4周", "预测接口与算法B接入", "预测服务、LightGBM、接口契约回退"),
    ("第5周", "评估与预警联调", "MAE评估、指数平滑、库存预警链路"),
    ("第6周", "测试与缺陷修复", "异常输入、LightGBM可选依赖、接口回归"),
    ("第7周", "演示材料与页面联调", "模型对比图、预测页、最终回归"),
    ("第8周", "答辩收口与交付", "讲稿、PPT大纲、贡献归属与最终包"),
]


@dataclass(frozen=True)
class Commit:
    sha: str
    commit_date: date
    author_name: str
    author_email: str
    subject: str

    @property
    def canonical_author(self) -> str:
        return AUTHOR_ALIASES.get(
            self.author_email,
            f"{self.author_name}（{self.author_email}）",
        )

    @property
    def is_merge_pr(self) -> bool:
        return self.subject.startswith("Merge pull request #")

    @property
    def pr_number(self) -> int | None:
        match = re.search(r"Merge pull request #(\d+)", self.subject)
        return int(match.group(1)) if match else None


def run_git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
    )
    return completed.stdout


def load_commits() -> list[Commit]:
    raw = run_git(
        [
            "log",
            "--all",
            "--date=short",
            "--format=%H%x1f%ad%x1f%an%x1f%ae%x1f%s",
        ]
    )
    commits: list[Commit] = []
    for line in raw.splitlines():
        sha, commit_date, author_name, author_email, subject = line.split("\x1f", 4)
        commits.append(
            Commit(
                sha=sha,
                commit_date=datetime.strptime(commit_date, "%Y-%m-%d").date(),
                author_name=author_name,
                author_email=author_email,
                subject=subject,
            )
        )
    return sorted(commits, key=lambda item: (item.commit_date, item.sha))


def phase_for_day(day: date) -> str:
    if day <= date(2026, 6, 9):
        return "第1周"
    if day == date(2026, 6, 10):
        return "第2周"
    if day <= date(2026, 6, 12):
        return "第3周"
    if day <= date(2026, 6, 14):
        return "第4周"
    if day == date(2026, 6, 15):
        return "第5周"
    if day <= date(2026, 6, 16):
        return "第6周"
    if day <= date(2026, 6, 18):
        return "第7周"
    return "第8周"


def bar_rows(items: list[tuple[str, int]], maximum: int) -> str:
    rows = []
    for label, value in items:
        width = 0 if maximum == 0 else round(value / maximum * 100, 1)
        rows.append(
            "<div class=\"bar-row\">"
            f"<span>{html.escape(label)}</span>"
            "<div class=\"bar-track\">"
            f"<div class=\"bar-fill\" style=\"width: {width}%\"></div>"
            "</div>"
            f"<strong>{value}</strong>"
            "</div>"
        )
    return "\n".join(rows)


def build_metrics(commits: list[Commit]) -> dict[str, object]:
    window_commits = [item for item in commits if START_DATE <= item.commit_date <= END_DATE]
    non_merge_commits = [item for item in window_commits if not item.is_merge_pr]
    merge_commits = [item for item in window_commits if item.is_merge_pr]
    algorithm_a_commits = [
        item
        for item in window_commits
        if item.author_email
        in {
            "16723149+zhang-hangchen464654@user.noreply.gitee.com",
            "zhanghch66@mail2.sysu.edu.cn",
        }
    ]

    by_author = Counter(item.canonical_author for item in window_commits)
    by_day = Counter(item.commit_date.isoformat() for item in window_commits)
    by_phase = Counter(phase_for_day(item.commit_date) for item in window_commits)

    pr_numbers = sorted(number for item in merge_commits if (number := item.pr_number) is not None)
    algorithm_a_prs = [12, 13, 15, 16, 18, 21, 23, 24, 26, 29, 30]

    return {
        "source": "local git log --all + docs/management course schedule",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "actual_window": f"{START_DATE.isoformat()} to {END_DATE.isoformat()}",
        "simulated_cycle": "8-week / two-month software engineering lifecycle",
        "total_commits": len(window_commits),
        "non_merge_commits": len(non_merge_commits),
        "merged_pr_count": len(merge_commits),
        "merged_pr_numbers": pr_numbers,
        "algorithm_a_commits": len(algorithm_a_commits),
        "algorithm_a_pr_numbers": algorithm_a_prs,
        "author_counts": dict(by_author),
        "daily_counts": dict(sorted(by_day.items())),
        "phase_counts": dict(by_phase),
        "phases": SIMULATED_PHASES,
    }


def build_html(metrics: dict[str, object]) -> str:
    author_items = sorted(metrics["author_counts"].items(), key=lambda item: item[1], reverse=True)
    day_items = list(metrics["daily_counts"].items())
    phase_counts = metrics["phase_counts"]
    phase_items = [(phase, phase_counts.get(phase, 0)) for phase, _, _ in SIMULATED_PHASES]

    max_author = max([value for _, value in author_items] or [0])
    max_day = max([value for _, value in day_items] or [0])
    max_phase = max([value for _, value in phase_items] or [0])

    phases_html = "\n".join(
        "<tr>"
        f"<td>{phase}</td>"
        f"<td>{html.escape(title)}</td>"
        f"<td>{html.escape(deliverable)}</td>"
        f"<td>{phase_counts.get(phase, 0)}</td>"
        "</tr>"
        for phase, title, deliverable in SIMULATED_PHASES
    )

    pr_text = ", ".join(f"#{number}" for number in metrics["merged_pr_numbers"])
    algorithm_a_pr_text = ", ".join(f"#{number}" for number in metrics["algorithm_a_pr_numbers"])

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI Sales Forecast System 项目操作数据看板</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f7fb;
      --panel: #ffffff;
      --ink: #172033;
      --muted: #627085;
      --line: #dbe3ee;
      --blue: #2563eb;
      --green: #138a5b;
      --amber: #b7791f;
      --red: #b42318;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, "Microsoft YaHei", sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.5;
    }}
    header {{
      padding: 28px 36px 18px;
      background: #ffffff;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{ margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }}
    h2 {{ margin: 0 0 14px; font-size: 18px; }}
    p {{ margin: 0; color: var(--muted); }}
    main {{ padding: 24px 36px 36px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    .metric-label {{ color: var(--muted); font-size: 13px; }}
    .metric-value {{ display: block; margin-top: 6px; font-size: 30px; font-weight: 700; }}
    .metric-note {{ margin-top: 4px; color: var(--muted); font-size: 12px; }}
    .layout {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 18px;
      margin-bottom: 18px;
    }}
    .bar-row {{
      display: grid;
      grid-template-columns: minmax(180px, 1fr) 2fr 48px;
      align-items: center;
      gap: 10px;
      margin: 10px 0;
      font-size: 13px;
    }}
    .bar-track {{
      height: 14px;
      border-radius: 4px;
      background: #eef2f7;
      overflow: hidden;
    }}
    .bar-fill {{ height: 100%; background: var(--blue); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      padding: 10px 8px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}
    th {{ color: var(--muted); font-weight: 600; }}
    .badge {{
      display: inline-block;
      margin: 4px 6px 0 0;
      padding: 4px 8px;
      border-radius: 6px;
      background: #e8f0ff;
      color: #174ea6;
      font-size: 12px;
      font-weight: 600;
    }}
    .warning {{
      border-left: 4px solid var(--amber);
    }}
    .ok {{
      border-left: 4px solid var(--green);
    }}
    footer {{
      padding: 0 36px 28px;
      color: var(--muted);
      font-size: 12px;
    }}
    @media (max-width: 900px) {{
      header, main, footer {{ padding-left: 18px; padding-right: 18px; }}
      .grid, .layout {{ grid-template-columns: 1fr; }}
      .bar-row {{ grid-template-columns: 1fr; gap: 4px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>AI Sales Forecast System 项目操作数据看板</h1>
    <p>数据来源：本地 Git 历史、PR 合并记录与 docs/management 排期。实际开发窗口 {metrics["actual_window"]}，对应课程要求的两个月软件工程开发模拟。</p>
  </header>

  <main>
    <section class="grid">
      <div class="card">
        <span class="metric-label">实际开发窗口提交</span>
        <span class="metric-value">{metrics["total_commits"]}</span>
        <div class="metric-note">含 merge commit，覆盖 6 人协作痕迹</div>
      </div>
      <div class="card">
        <span class="metric-label">非合并开发提交</span>
        <span class="metric-value">{metrics["non_merge_commits"]}</span>
        <div class="metric-note">代码、文档、测试与数据相关操作</div>
      </div>
      <div class="card">
        <span class="metric-label">已合入 PR</span>
        <span class="metric-value">{metrics["merged_pr_count"]}</span>
        <div class="metric-note">PR：{html.escape(pr_text)}</div>
      </div>
      <div class="card ok">
        <span class="metric-label">算法A可追踪提交</span>
        <span class="metric-value">{metrics["algorithm_a_commits"]}</span>
        <div class="metric-note">含旧 Gitee noreply 与新 GitHub 邮箱身份</div>
      </div>
    </section>

    <section class="layout">
      <div class="card">
        <h2>贡献者操作分布</h2>
        {bar_rows(author_items, max_author)}
      </div>
      <div class="card">
        <h2>每日提交节奏</h2>
        {bar_rows(day_items, max_day)}
      </div>
    </section>

    <section class="layout">
      <div class="card">
        <h2>两个月模拟周期映射</h2>
        {bar_rows(phase_items, max_phase)}
      </div>
      <div class="card warning">
        <h2>贡献归属说明</h2>
        <p>算法A早期提交作者为 <strong>张航晨 &lt;16723149+zhang-hangchen464654@user.noreply.gitee.com&gt;</strong>。该邮箱是 Gitee noreply，GitHub 贡献者组件可能无法自动归属到 dragon-zhang-woo，但 Git 历史、PR 与文档均可追踪。</p>
        <p style="margin-top: 10px;">6/20 后续提交已切换为 <strong>dragon-zhang-woo &lt;zhanghch66@mail2.sysu.edu.cn&gt;</strong>。</p>
      </div>
    </section>

    <section class="card">
      <h2>模拟两个月开发排期与交付证据</h2>
      <table>
        <thead>
          <tr>
            <th>模拟周</th>
            <th>阶段</th>
            <th>关键交付</th>
            <th>提交数</th>
          </tr>
        </thead>
        <tbody>
          {phases_html}
        </tbody>
      </table>
    </section>

    <section class="card" style="margin-top: 18px;">
      <h2>算法A交付摘要</h2>
      <div>
        <span class="badge">移动平均基线</span>
        <span class="badge">指数平滑备选</span>
        <span class="badge">LightGBM 回退</span>
        <span class="badge">/api/predict 契约稳定</span>
        <span class="badge">MAE 评估</span>
        <span class="badge">库存预警联调</span>
        <span class="badge">预测页回归</span>
        <span class="badge">答辩图表</span>
      </div>
      <p style="margin-top: 12px;">算法A相关 PR 证据：{html.escape(algorithm_a_pr_text)}。该看板不重写提交历史，不伪造日期；它把课程压缩开发周期、真实 Git 操作记录和答辩交付物放在同一张可展示页面中。</p>
    </section>
  </main>

  <footer>
    Generated at {metrics["generated_at"]}. Reproduce with: python scripts/generate_project_operation_dashboard.py
  </footer>
</body>
</html>
"""


def build_markdown(metrics: dict[str, object]) -> str:
    author_lines = "\n".join(
        f"- {author}: {count} commits"
        for author, count in sorted(
            metrics["author_counts"].items(), key=lambda item: item[1], reverse=True
        )
    )
    phase_lines = "\n".join(
        f"| {phase} | {title} | {deliverable} | {metrics['phase_counts'].get(phase, 0)} |"
        for phase, title, deliverable in SIMULATED_PHASES
    )

    return f"""# 项目操作数据看板说明

- 生成时间：{metrics["generated_at"]}
- 数据来源：本地 `git log --all`、PR merge commit、`docs/management` 排期。
- 实际开发窗口：{metrics["actual_window"]}
- 课程表达：两周压缩模拟两个月软件工程开发周期。
- HTML 看板：[project_operation_dashboard_0620.html](project_operation_dashboard_0620.html)
- JSON 指标：[project_operation_metrics_0620.json](project_operation_metrics_0620.json)

## 核心指标

- 实际窗口提交数：{metrics["total_commits"]}
- 非合并开发提交数：{metrics["non_merge_commits"]}
- 已合入 PR 数：{metrics["merged_pr_count"]}
- 算法A可追踪提交数：{metrics["algorithm_a_commits"]}

## 贡献者操作分布

{author_lines}

## 两个月模拟周期映射

| 模拟周 | 阶段 | 关键交付 | 提交数 |
| --- | --- | --- | --- |
{phase_lines}

## 算法A贡献归属说明

算法A早期提交作者为 `张航晨 <16723149+zhang-hangchen464654@user.noreply.gitee.com>`。
该邮箱是 Gitee noreply，GitHub 贡献者组件可能无法自动归属到 `dragon-zhang-woo`。
但 Git 历史、PR 合并记录、测试报告和记忆文件均能证明算法A工作可追踪。

6/20 后续提交已切换为 `dragon-zhang-woo <zhanghch66@mail2.sysu.edu.cn>`。
"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    commits = load_commits()
    metrics = build_metrics(commits)
    JSON_OUTPUT.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    HTML_OUTPUT.write_text(build_html(metrics), encoding="utf-8")
    MD_OUTPUT.write_text(build_markdown(metrics), encoding="utf-8")
    print(f"Generated {HTML_OUTPUT}")
    print(f"Generated {MD_OUTPUT}")
    print(f"Generated {JSON_OUTPUT}")


if __name__ == "__main__":
    main()
