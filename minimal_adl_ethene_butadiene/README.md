# 最小版 ADL 项目：Ethene + 1,3-Butadiene

这个子项目是当前仓库里真正推荐使用的主入口，目标不是完整复现整篇论文，而是把最小版 active delta-learning 第一轮流程在服务器上稳定跑通，并且让结果能直接进入分析与汇报。

当前默认设置：

- 体系：`ethene + 1,3-butadiene`
- `baseline`：`GFN2-xTB`
- `target`：Gaussian `wB97X-D/6-31G*`
- 主模型：`ANI`
- 默认训练设备：`cuda`
- 默认训练环境名：`ADL_env`
- 学习目标：
  - `delta_E = E_target - E_baseline`
  - `delta_F = F_target - F_baseline`

## 现在推荐的使用方式
与之前“逐条敲单阶段脚本”的方式相比，现在更推荐：

1. 先跑 `scripts/run_first_round_pipeline.py`
2. 跑完后直接打开 `../docs/数据分析.ipynb`

也就是说，主线已经从“只保证算得完”升级为“算完就能分析”。

## 目录结构

```text
minimal_adl_ethene_butadiene/
├── configs/
├── data/
│   ├── raw/
│   └── processed/
├── geometries/
│   └── seed/
├── labels/
│   ├── gaussian/
│   └── xtb/
├── logs/
├── models/
├── results/
├── scripts/
└── src/minimal_adl/
```

## 环境准备
当前默认训练环境名是 `ADL_env`。如果你的 PBS 训练环境不是这个名字，可以改 `configs/base.yaml` 中的 `cluster.conda_env`；如果你只是打开 notebook 做分析，可以继续使用单独的 `data_env`。

推荐的最小依赖栈包括：

- `numpy`
- `PyYAML`
- `matplotlib`
- `seaborn`
- `joblib`
- `scikit-learn`
- `mlatom`
- `torch`
- `torchani`
- `pyh5md`

如果你要补齐 notebook 绘图环境，建议在分析环境 `data_env` 中先补最常缺的绘图库：

```bash
conda activate data_env
python -m pip install "seaborn>=0.12"
```

如果 `data_env` 里还缺 `pandas`、`matplotlib` 或 `scikit-learn`，再按报错补装；不必为了分析 notebook 把整套训练依赖都装进 `data_env`。

## 先做环境自检
开始跑主线之前，建议先做两步：

```bash
conda activate ADL_env
python scripts/check_environment.py --config configs/base.yaml --strict
python scripts/check_environment.py --config configs/base.yaml --strict --test-mlatom-xtb
```

如果你已经在 GPU 节点内，也可以继续检查：

```bash
python scripts/check_environment.py --config configs/base.yaml --strict --expect-gpu
```

自检报告默认会写到：

- `results/check_environment_latest.json`

## 一键跑完整第一轮
最推荐的命令是：

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --submit-mode-labels pbs       --submit-mode-train pbs       --submit-mode-uq pbs
```

如果你第一次上服务器，想先插入一个小样本联通测试：

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --submit-mode-labels pbs       --submit-mode-train pbs       --submit-mode-uq pbs       --with-smoke-tests
```

主控脚本固定覆盖：

1. 环境自检
2. 几何池生成
3. 初始选点
4. baseline 标注
5. target 标注
6. delta 数据集构建
7. 主模型训练
8. 辅助模型训练
9. 训练诊断产物导出
10. UQ 评估
11. 第 1 轮选点

## 如何恢复或局部重跑
`run_first_round_pipeline.py` 默认 `resume=true`。也就是说，如果标准产物已经存在，它会自动跳过已经完成的阶段。

常用命令：

只从训练阶段开始往后重跑：

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --from-stage train_main_model       --submit-mode-train pbs       --submit-mode-uq pbs
```

强制重跑训练及后续阶段：

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --from-stage train_main_model       --force       --submit-mode-train pbs       --submit-mode-uq pbs
```

只想跑到训练诊断产物导出为止：

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --to-stage export_training_diagnostics       --submit-mode-labels pbs       --submit-mode-train pbs
```

## 训练后会自动生成哪些标准分析文件
升级后，训练结束后会自动补齐这些产物：

- `models/training_split.json`
- `models/train_main_predictions.csv`
- `models/train_aux_predictions.csv`
- `models/train_main_history.json`
- `models/train_aux_history.json`
- `models/training_diagnostics.json`

UQ 与主控流程产物则位于：

- `results/uncertainty_latest.json`
- `results/round_001_selection_summary.json`
- `results/pipeline_run_summary.json`

这些文件就是 `../docs/数据分析.ipynb` 的默认输入。

## 如何分析结果
训练和 UQ 跑完后，直接打开：

- [../docs/数据分析.ipynb](../docs/数据分析.ipynb)

标准路径下通常不需要先改 `CONFIG`；如果你切换到辅助模型分析，可以把 `MODEL_VIEW` 改成 `aux`。

notebook 默认回答四个问题：

1. 数据长什么样
2. 模型训练得顺不顺
3. 模型预测得准不准
4. 模型为什么这样预测

## PBS 任务分工
当前配置默认分流如下：

- `xTB` baseline 标注：CPU 队列
- Gaussian target 标注：CPU 队列
- 主模型训练：GPU 队列
- 辅助模型训练：GPU 队列
- 不确定性评估：GPU 队列

当前 `base.yaml` 里已经给四类任务都预留了：

- `cluster.resources_by_method.baseline.extra_pbs_lines`
- `cluster.resources_by_method.target.extra_pbs_lines`
- `cluster.resources_by_method.training.extra_pbs_lines`
- `cluster.resources_by_method.uncertainty.extra_pbs_lines`

如果你的机房要求额外资源语句，例如 `#PBS -l gpus=1`，就在对应的 `extra_pbs_lines` 里填写。

## 还想看更细的说明
建议继续读：

- [../docs/流程介绍.md](../docs/流程介绍.md)
- [../docs/AIQM_FIRST_ROUND_RUNBOOK.md](../docs/AIQM_FIRST_ROUND_RUNBOOK.md)
- [../docs/AIQM_FIRST_ROUND_RESULT_SUMMARY.md](../docs/AIQM_FIRST_ROUND_RESULT_SUMMARY.md)
