# 分支协作规范

## 核心原则
- `main` 分支：只存放稳定版本，**仅在最终交付时由 `develop` 合并一次**。
- `develop` 分支：日常开发主干，所有功能分支都从这里切出，并合并回这里。

## 开发流程
1. 每次开发新功能或修复 Bug，从 `develop` 切出分支：
   - 功能分支：`feature/功能名`
   - 修复分支：`fix/问题描述`
   - 以此类推。

2. 本地开发完成后，推送到远程，发起 Pull Request，目标分支选择 `develop`。

3. PR 标题格式：`类型(模块): 简短描述`
   - 例如：`feat(forecast): 添加销量预测接口`
   - 类型：feat / fix / docs / refactor / test

4. `main` 分支由项目经理在最终交付时，从 `develop` 发起唯一一次 PR 并合并。