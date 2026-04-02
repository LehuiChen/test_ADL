# AIQM 集群第一轮结果摘要

这份摘要对应当前最小版 ADL 第一轮主线在 `ethene + 1,3-butadiene` 体系上的真实跑通结果。

## 一句话结论
当前第一轮已经完成“几何池生成、初始选点、双层标注、delta 数据集构建、主辅模型训练、不确定性评估、第 1 轮选点和收敛判断”的完整闭环，并且满足当前默认收敛条件。

## 关键数字

- `pool = 400`
- `initial = 250`
- `uncertainty on 400 samples`
- `round 1 selected = 5`
- `uncertain ratio = 3.33%`
- `converged = true`

这意味着：

- 一开始共准备了 `400` 个候选几何
- 第 0 轮先用 `250` 个样本构造训练集
- 训练后对 `400` 个样本都做了 UQ 评估
- 只有 `5` 个样本高于阈值，值得优先补标
- 高不确定性比例 `3.33%` 低于默认 `5%`
- 因此当前可以判定第一轮闭环已经跑通并达到当前收敛条件

## 现在新增的标准分析产物
为了让结果能直接进入 notebook 分析，当前主线还会统一输出：

- `models/training_split.json`
- `models/train_main_predictions.csv`
- `models/train_aux_predictions.csv`
- `models/train_main_history.json`
- `models/train_aux_history.json`
- `models/training_diagnostics.json`
- `results/pipeline_run_summary.json`

其中：

- `train_main_predictions.csv` 负责逐样本误差分析
- `train_main_history.json` 负责训练曲线输入
- `training_diagnostics.json` 负责告诉 notebook 默认应该读哪些文件
- `pipeline_run_summary.json` 负责保留整条主控流程的阶段记录

## 对汇报最有用的表达方式
如果你要在组会或实验汇报里用一句话概括，可以直接说：

当前最小版 ADL 第一轮已经完成从几何生成、初始选点、双层标注、delta 数据集构建、主辅模型训练、不确定性评估到第 1 轮选点和收敛判断的完整闭环；本轮高不确定性比例仅 `3.33%`，低于默认 `5%` 阈值，因此可判定当前流程已经跑通并满足第一轮收敛条件。

## 下一步建议

- 如果只想做结果汇报，直接打开 `docs/数据分析.ipynb`
- 如果想继续第 2 轮，可以优先补标这 `5` 个样本
- 如果中间某阶段失败，现在优先使用 `scripts/run_first_round_pipeline.py` 的 `resume` 或 `--from-stage` 机制重跑
