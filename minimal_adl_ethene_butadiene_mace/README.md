# Minimal ADL（MACE）

工程目录：`minimal_adl_ethene_butadiene_mace`  
模型类型：`MACE`  
环境名：`ADL_MACE`

## 快速开始

推荐优先看：

- [环境配置](../docs/mace/环境配置.md)
- [训练流程](../docs/mace/训练流程.md)

仓库内已额外提供 CPU 默认版环境入口：

- [environment.cpu.yml](environment.cpu.yml)
- [requirements.txt](requirements.txt)
- [scripts/install_mace_deps_stepwise.sh](scripts/install_mace_deps_stepwise.sh)

推荐使用顺序：

1. 先用 `environment.cpu.yml` 建 conda 基础环境
2. 再运行 `scripts/install_mace_deps_stepwise.sh` 安装 pip 侧精确依赖
3. `requirements.txt` 作为 pip 版本清单和排错参考，不建议直接单独 `pip install -r`

说明：

- 当前机房默认推荐走 CPU 路线
- 一些关键包需要 `--no-deps` 才能稳定，因此分步安装脚本仍是权威路径
- 如果镜像、系统库或 MLatom 依赖链出现偏差，优先回退到分步安装脚本

## 文档

- [环境配置](../docs/mace/环境配置.md)
- [训练流程](../docs/mace/训练流程.md)
- [结果说明](../docs/mace/结果说明.md)
- [数据分析 notebook](../docs/mace/数据分析.ipynb)
- [主目录总流程（新手详细版）](../训练总流程_新手详细版.md)
