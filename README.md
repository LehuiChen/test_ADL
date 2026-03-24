# Minimal Active Delta-Learning for Ethene + 1,3-Butadiene

这是一个面向本科生的最小复现仓库，用来实现论文 *Active delta-learning for fast construction of interatomic potentials and stable molecular dynamics simulations* 的教学版工作流。

本仓库不追求完整复现整篇论文，只保留最简单的 Diels-Alder 反应体系：

- 体系：`ethene + 1,3-butadiene`
- baseline：`GFN2-xTB`
- target：`wB97X-D/6-31G*`
- 学习目标：
  - `delta_E = E_target - E_baseline`
  - `delta_F = F_target - F_baseline`

## 这个仓库现在包含什么

### 1. 最推荐使用的最小版项目

请优先看：

- [minimal_adl_ethene_butadiene/README.md](./minimal_adl_ethene_butadiene/README.md)

这个子项目是专门整理出来的“教学式最小实现”，特点是：

- 目录结构清晰
- 所有脚本职责单一
- 配置集中在 `configs/base.yaml`
- 默认支持 `PBS + ADL_env` 环境
- 复用系统安装的 `xtb` 和 `g16`
- 中文注释较完整
- 优先保证“能跑通”而不是“一步做到最复杂”

### 2. 原论文参考目录

仓库里还保留了原始论文参考内容，但默认不作为日常开发入口：

- `adl/`
  - 原始主动学习脚本
- `static/`
  - 原始静态计算结果、几何优化、单点计算等参考数据

这些目录适合对照论文思路，但不适合初学者直接在里面继续开发。

## 当前最小工作流

在 `minimal_adl_ethene_butadiene/` 中，当前已经实现了下面这条主线：

1. 生成初始几何池
2. 对每个几何分别提交：
   - `GFN2-xTB` baseline 标注
   - Gaussian `wB97X-D/6-31G*` target 标注
3. 构建统一 delta 数据集：
   - `delta_E`
   - `delta_F`
4. 训练：
   - 主模型：学习 `delta_E + delta_F`
   - 辅助模型：只学习 `delta_E`
   - 默认后端：`ANI`
   - 默认设备：`cuda`
   - 推荐兼容栈：`PyTorch 1.12.0 + cudatoolkit 11.3 + TorchANI 2.2`
5. 评估不确定性：
   - `|pred_main_delta_E - pred_aux_delta_E|`
6. 进行最小主动学习选点：
   - 初始 250 点
   - 每轮最多新增 100 点
   - 高不确定性点比例 `< 5%` 视为收敛

## 哪些地方忠于论文，哪些地方做了简化

### 与论文保持一致

- 初始样本数默认 250
- 每轮最多新增 100 个点
- 主模型学习 `delta_E + delta_F`
- 辅助模型只学习 `delta_E`
- 不确定性使用两模型 `delta_E` 预测差
- 收敛条件使用高不确定性样本比例 `< 5%`

### 为了最小可运行而做的工程简化

- 只保留 `ethene + 1,3-butadiene`
- 不做 `C60`
- 不做 `ANI-1ccx baseline`
- 不做整篇论文全部实验与分析图
- target 从论文中的 `B3LYP/6-31G*` 改为 `wB97X-D/6-31G*`
- 初始采样使用更容易理解和调试的教学版实现
- 默认训练后端已经切为 `ANI + cuda`
- 如果 GPU 驱动较老，推荐使用 README 中的老版本 ANI 兼容栈
- 如果 GPU 暂时不可用，也可以手动切回 `KREG` 或 `cpu`

## 快速开始

进入最小项目目录后，推荐按这个顺序运行：

```bash
python scripts/sample_initial_geometries.py --config configs/base.yaml
python scripts/active_learning_loop.py --config configs/base.yaml --manifest data/raw/geometry_pool_manifest.json
python scripts/run_xtb_labels.py --config configs/base.yaml --manifest data/raw/initial_selection_manifest.json
python scripts/run_target_labels.py --config configs/base.yaml --manifest data/raw/initial_selection_manifest.json
python scripts/build_delta_dataset.py --config configs/base.yaml --manifest data/raw/initial_selection_manifest.json
python scripts/train_main_model.py --config configs/base.yaml --submit-mode pbs
python scripts/train_aux_model.py --config configs/base.yaml --submit-mode pbs
python scripts/evaluate_uncertainty.py --config configs/base.yaml --manifest data/raw/geometry_pool_manifest.json --submit-mode pbs
python scripts/active_learning_loop.py --config configs/base.yaml --manifest data/raw/geometry_pool_manifest.json --round-index 1
```

当前这版集群适配默认按下面方式分流：

- `xtb` 标注：CPU 队列
- Gaussian `wB97X-D/6-31G*` 标注：CPU 队列
- `ANI` 训练与不确定性评估：GPU 队列 `GPU`

Gaussian 继续通过 `MLatom` 直接调用，但 PBS 模板已经内置了你集群上需要的环境前置，例如 `g16-env.sh`、`ips2018u1.env`、`ADL_env`、系统 `xtb` 路径、`dftd4bin` 和 `GAUSS_SCRDIR`。

当前推荐的新环境是 `ADL_env`：

- Python 包放在 `ADL_env`
- `xtb` 直接复用系统路径 `/share/apps/xtb-6.7.1/xtb-dist/bin/xtb`
- Gaussian 继续复用系统安装 `/share/apps/gaussian/g16/g16`
- 对于驱动 `470.94` 这类老 GPU 节点，推荐使用 `PyTorch 1.12.0 + cudatoolkit 11.3 + TorchANI 2.2`

更详细的说明请看：

- [minimal_adl_ethene_butadiene/README.md](./minimal_adl_ethene_butadiene/README.md)
- [docs/AIQM_FIRST_ROUND_RUNBOOK.md](./docs/AIQM_FIRST_ROUND_RUNBOOK.md)

## Git 版本管理说明

为了方便版本控制、回退和打标签，我另外整理了一份中文说明：

- [docs/GIT_VERSIONING_GUIDE.md](./docs/GIT_VERSIONING_GUIDE.md)

里面包括：

- 日常 `add / commit / push`
- 如何安全回退
- 什么时候用 `revert`
- 什么时候不要乱用 `reset --hard`
- 如何打版本标签
- 如何在 GitHub 上基于 tag 发 release

## 论文来源

- Yaohuang Huang, Yi-Fan Hou, Pavlo O. Dral. *Active delta-learning for fast construction of interatomic potentials and stable molecular dynamics simulations*. Mach. Learn.: Sci. Technol. 2025.
- ChemRxiv 预印本：[10.26434/chemrxiv-2024-fb02r](https://doi.org/10.26434/chemrxiv-2024-fb02r)
- MLatom 官方仓库：[dralgroup/mlatom](https://github.com/dralgroup/mlatom)

## 你现在最应该看哪里

如果你是第一次打开这个仓库，建议按这个顺序看：

1. [minimal_adl_ethene_butadiene/README.md](./minimal_adl_ethene_butadiene/README.md)
2. [minimal_adl_ethene_butadiene/configs/base.yaml](./minimal_adl_ethene_butadiene/configs/base.yaml)
3. [minimal_adl_ethene_butadiene/scripts/sample_initial_geometries.py](./minimal_adl_ethene_butadiene/scripts/sample_initial_geometries.py)
4. [minimal_adl_ethene_butadiene/scripts/run_xtb_labels.py](./minimal_adl_ethene_butadiene/scripts/run_xtb_labels.py)
5. [minimal_adl_ethene_butadiene/scripts/run_target_labels.py](./minimal_adl_ethene_butadiene/scripts/run_target_labels.py)
6. [docs/GIT_VERSIONING_GUIDE.md](./docs/GIT_VERSIONING_GUIDE.md)
