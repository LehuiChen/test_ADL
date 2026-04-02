# 文档总入口（ANI / MACE / NequIP）

本目录已按模型拆分，并保留旧路径兼容页。

## 1. 快速入口

- ANI（可运行主线）：[docs/ani/README.md](./ani/README.md)
- MACE（并列可运行）：[docs/mace/README.md](./mace/README.md)
- NequIP（预留占位）：[docs/nequip/README.md](./nequip/README.md)
- 环境总说明（重点）：[docs/common/环境配置.md](./common/环境配置.md)

## 2. 目录结构

- `docs/ani/`：ANI 运行手册、流程图、结果摘要、分析 notebook
- `docs/mace/`：MACE 运行手册与说明
- `docs/nequip/`：NequIP 运行手册与占位说明
- `docs/common/`：跨模型公共文档（环境、版本管理等）
- `docs/legacy/`：历史命名文档归档

## 3. 兼容说明

- 根目录下旧文档文件名（如 `RUNBOOK_ANI_FIRST_ROUND.md`）已改为兼容跳转页。
- 若你在服务器有旧收藏链接，仍可打开并跳转到新路径。

## 4. 关于 tmp

`tmp/` 是临时工作目录（例如调试脚本、一次性中间文件），不是正式交付产物目录。
仓库已在 `.gitignore` 中忽略 `/tmp/`，不建议把正式结果放在该目录。
