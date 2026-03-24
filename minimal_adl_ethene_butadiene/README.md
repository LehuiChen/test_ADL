# 最小版 ADL 复现项目：ethene + 1,3-butadiene

这个子项目是基于原论文仓库重新整理的“教学式最小实现”。目标不是完整复现整篇论文，而是先把最小可运行的 active delta-learning 工作流打通：

- 体系：`ethene + 1,3-butadiene`
- baseline：`GFN2-xTB`
- target：`wB97X-D/6-31G*`
- 默认模型后端：`MLatom KREG`
- 学习目标：
  - `delta_E = E_target - E_baseline`
  - `delta_F = F_target - F_baseline`

## 1. 这个子项目做了什么

本项目拆成了几条初学者更容易理解的链路：

1. `sample_initial_geometries.py`
   - 从一个种子几何生成一批初始几何。
   - 这是工程简化版采样，不是论文中的严格 harmonic quantum Boltzmann 采样。
2. `run_xtb_labels.py`
   - 为每个几何提交 baseline 标注任务。
   - 底层通过 MLatom 调用 `GFN2-xTB`。
3. `run_target_labels.py`
   - 为每个几何提交 target 标注任务。
   - 底层通过 MLatom 调用 Gaussian 的 `wB97X-D/6-31G*` 单点能和力计算。
4. `build_delta_dataset.py`
   - 读取 baseline 和 target 结果，构建统一的 `npz + metadata.json` 数据集。
5. `train_main_model.py`
   - 训练主模型，学习 `delta_E + delta_F`。
6. `train_aux_model.py`
   - 训练辅助模型，只学习 `delta_E`。
7. `evaluate_uncertainty.py`
   - 用主模型和辅助模型预测未标注几何，计算不确定性：
   - `|pred_main_delta_E - pred_aux_delta_E|`
8. `active_learning_loop.py`
   - 初始选择 250 个点。
   - 每轮最多新增 100 个高不确定性点。
   - 高不确定性点比例低于 5% 时视为收敛。

## 2. 哪些地方忠于论文，哪些地方做了简化

### 论文一致

- 初始点数默认 250。
- 每轮最多新增 100 个点。
- 主模型学习 `delta_E + delta_F`。
- 辅助模型只学习 `delta_E`。
- 不确定性定义为两者的 `delta_E` 预测差绝对值。
- 收敛判断采用“高不确定性点比例 < 5%”。

### 工程简化

- 只保留 `ethene + 1,3-butadiene` 体系。
- 不做 C60，不做 ANI-1ccx baseline，不做完整论文中的所有实验。
- target 从论文中的 `B3LYP/6-31G*` 改成了 `wB97X-D/6-31G*`。
- 初始几何采样默认使用“随机微扰种子结构”的教学版方法，而不是严格的量子玻尔兹曼采样。
- 主动学习外层循环写成了更容易读的 Python 脚本，而不是完全依赖 MLatom 的黑箱式高层接口。
- 为了降低第一次跑通的门槛，训练默认使用 `KREG`；如果你想更贴近原论文的神经网络风格，可以把 `configs/base.yaml` 里的 `ml_model_type` 改成 `ANI`。

## 3. 目录说明

```text
minimal_adl_ethene_butadiene/
├─ configs/
├─ data/
│  ├─ raw/
│  └─ processed/
├─ geometries/
│  └─ seed/
├─ labels/
│  ├─ gaussian/
│  └─ xtb/
├─ logs/
├─ models/
├─ results/
├─ scripts/
└─ src/minimal_adl/
```

## 4. 运行前准备

建议在你的 PBS 集群环境中准备：

- conda 环境：`aiqm`
- Python 包：
  - `numpy`
  - `PyYAML`
  - `MLatom`
  - `matplotlib`（可选，仅用于后续扩展画图）
- 外部程序：
  - `xtb`
  - `g16` 或集群上可调用的 Gaussian 命令

## 5. 推荐执行顺序

下面是假设你已经进入本项目目录后的最小顺序：

```bash
python scripts/sample_initial_geometries.py --config configs/base.yaml
python scripts/active_learning_loop.py --config configs/base.yaml --manifest data/raw/geometry_pool_manifest.json
python scripts/run_xtb_labels.py --config configs/base.yaml --manifest data/raw/initial_selection_manifest.json
python scripts/run_target_labels.py --config configs/base.yaml --manifest data/raw/initial_selection_manifest.json
python scripts/build_delta_dataset.py --config configs/base.yaml --manifest data/raw/initial_selection_manifest.json
python scripts/train_main_model.py --config configs/base.yaml
python scripts/train_aux_model.py --config configs/base.yaml
python scripts/evaluate_uncertainty.py --config configs/base.yaml --manifest data/raw/geometry_pool_manifest.json
python scripts/active_learning_loop.py --config configs/base.yaml --manifest data/raw/geometry_pool_manifest.json --round-index 1
```

## 6. 关于 PBS 作业

这个项目默认支持 PBS 提交：

- 每个样本会生成独立作业目录。
- 每个作业目录至少包含：
  - `job.pbs`
  - `status.json`
  - `label.json`（成功时）
  - `stdout.log`
  - `stderr.log`

如果你只是想先在登录节点或调试节点上验证代码逻辑，也可以把脚本参数改为 `--submit-mode local`。

## 7. 重要提醒

- 这个项目的中文注释是按“本科生能跟着看懂”的标准写的，所以更偏重可读性，而不是最短代码。
- 当前仓库外层的原始 `adl/` 与 `static/` 目录没有被改动，这个子项目是独立的干净实现。
