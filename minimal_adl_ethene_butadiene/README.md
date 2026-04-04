# Minimal ADL (ANI)

工程目录：`minimal_adl_ethene_butadiene`  
模型类型：`ANI`  
环境名：`ADL_env`

当前默认流程已经切到 `TS seed + harmonic-quantum-boltzmann 初始条件 + 双向 MD 主动学习`，不再使用旧的静态 `400` 点几何池。

## 当前主线

1. `geometries/ture_seed/TS.log` 解析成标准化 TS seed
2. Round 0 从 TS seed 采样 `200` 个初始条件并完成 xTB / Gaussian 标注
3. 累计标注样本写入 `data/processed/cumulative_labeled_manifest.json`
4. 构建 delta 数据集并训练 ANI 主模型 / 辅助模型
5. 后续每轮从 TS seed 再采样 `100` 个初始条件，跑双向 `±150 fs` MD
6. 从 MD 轨迹帧里按 UQ + RMSD 去重选择下一轮样本

## 文档

- [环境配置](../docs/ani/环境配置.md)
- [训练流程](../docs/ani/训练流程.md)
- [结果说明](../docs/ani/结果说明.md)
- [数据分析 notebook](../docs/ani/数据分析.ipynb)
- [主目录总流程（新手详细版）](../训练总流程_新手详细版.md)
