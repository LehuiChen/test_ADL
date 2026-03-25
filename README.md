# Minimal Active Delta-Learning for Ethene + 1,3-Butadiene

这是一个面向教学和第一次上手集群复现实验的最小版仓库，用来整理论文
*Active delta-learning for fast construction of interatomic potentials and stable molecular dynamics simulations*
在 `ethene + 1,3-butadiene` 体系上的可运行流程。

本仓库不追求完整复现整篇论文，只保留最小主动学习闭环：

- 体系：`ethene + 1,3-butadiene`
- baseline：`GFN2-xTB`
- target：`wB97X-D/6-31G*`
- 主模型：`ANI`
- 训练设备：`cuda`
- 学习目标：
  - `delta_E = E_target - E_baseline`
  - `delta_F = F_target - F_baseline`

## 最推荐的入口

如果你现在要真正跑通第一轮，请按下面顺序看：

1. [minimal_adl_ethene_butadiene/README.md](./minimal_adl_ethene_butadiene/README.md)
2. [docs/AIQM_FIRST_ROUND_RUNBOOK.md](./docs/AIQM_FIRST_ROUND_RUNBOOK.md)
3. [minimal_adl_ethene_butadiene/configs/base.yaml](./minimal_adl_ethene_butadiene/configs/base.yaml)

其中：

- 子项目 README 负责解释当前仓库到底实现了什么、环境如何准备、PBS 如何适配
- 第一轮运行指南负责给出按步骤执行的命令清单
- `configs/base.yaml` 是所有默认值和队列配置的单一来源

## 当前仓库里有什么

### 1. 最小可运行项目

核心实现位于 [minimal_adl_ethene_butadiene/README.md](./minimal_adl_ethene_butadiene/README.md) 对应的子项目中，特点是：

- 目录结构清晰
- 脚本职责单一
- 配置集中在 `configs/base.yaml`
- 默认支持 `PBS + ADL_env`
- 复用系统安装的 `xtb` 和 `g16`
- 提供环境自检脚本 `scripts/check_environment.py`
- 优先保证“先跑通，再放大规模”

### 2. 原论文参考目录

仓库中保留了原始参考内容，但默认不作为新手入口：

- `adl/`
- `static/`

这些目录更适合对照论文思路，不建议第一次复现时直接在里面继续开发。

## 当前最小工作流

在 `minimal_adl_ethene_butadiene/` 中，当前已经实现了以下主线：

1. `sample_initial_geometries.py`
   - 从种子结构生成初始几何池
   - 默认生成 400 个几何
2. `active_learning_loop.py`
   - 第 0 轮按默认值选出 250 个初始样本
   - 后续每轮最多新增 100 个样本
3. `run_xtb_labels.py`
   - 提交 `GFN2-xTB` baseline 标注
4. `run_target_labels.py`
   - 提交 Gaussian `wB97X-D/6-31G*` target 标注
5. `build_delta_dataset.py`
   - 构建统一的 `delta_E + delta_F` 数据集
6. `train_main_model.py`
   - 主模型学习 `delta_E + delta_F`
7. `train_aux_model.py`
   - 辅助模型只学习 `delta_E`
8. `evaluate_uncertainty.py`
   - 使用 `|pred_main_delta_E - pred_aux_delta_E|` 作为不确定性

### 与论文保持一致

- 初始样本数默认 250
- 每轮最多新增 100 个点
- 主模型学习 `delta_E + delta_F`
- 辅助模型只学习 `delta_E`
- 不确定性定义为两模型 `delta_E` 预测差绝对值
- 高不确定性点比例 `< 5%` 视为收敛

### 为了最小可运行做的简化

- 只保留 `ethene + 1,3-butadiene`
- 不做 `C60`
- 不做 `ANI-1ccx baseline`
- target 从论文中的 `B3LYP/6-31G*` 改为 `wB97X-D/6-31G*`
- 初始几何池使用教学版随机微扰生成

## AIQM 集群环境摘要

当前仓库默认按 AIQM 集群的 `ADL_env` 工作流组织，推荐兼容栈是：

- `Python 3.10`
- `PyTorch 1.12.0`
- `torchvision 0.13.0`
- `torchaudio 0.12.0`
- `cudatoolkit 11.3`
- `TorchANI 2.2`

安装顺序建议固定为：

1. 用 `conda` 安装基础科学计算依赖
2. `python -m pip install pyh5md`
3. 固定 `PyTorch 1.12.0 + cudatoolkit 11.3`
4. `python -m pip install "torchani==2.2" --no-deps`
5. `python -m pip install mlatom --no-deps`

> [!WARNING]
> 不要在已经固定好 `torch==1.12.0` 的环境里直接执行：
>
> ```bash
> python -m pip install mlatom
> ```
>
> 这可能会让 `pip` 自动升级 `torch`，破坏复现实验环境。

> [!NOTE]
> 在登录节点上执行 `python -c "import torch; print(torch.cuda.is_available())"` 返回 `False` 是正常现象。
> CUDA 是否真正可用，请在 PBS 申请到的 GPU 节点内检查。

当前这版集群适配默认按下面方式分流：

- `xtb` 标注：CPU 队列
- Gaussian `wB97X-D/6-31G*` 标注：CPU 队列
- `ANI` 训练与不确定性评估：GPU 队列 `GPU`

如果你的机房除了 `queue: GPU` 之外还要求额外资源字段，例如 `gpus=1` 或 `ngpus=1`，请在
`configs/base.yaml` 的 `cluster.resources_by_method.*.extra_pbs_lines` 中填写；当前仓库已经为这些字段预留了配置入口。

## 第一轮推荐顺序

如果你只想先跑通第一轮，推荐顺序是：

1. 环境安装与版本检查
2. GPU 节点 CUDA 检查
3. `scripts/check_environment.py`
4. 几何池生成
5. 第 0 轮初始选点
6. `mlatom + xtb` 最小联通检查
7. 小样本 `xtb` 冒烟测试
8. 小样本 Gaussian 冒烟测试
9. 完整批次标注
10. 构建 delta 数据集
11. 主模型训练
12. 辅助模型训练
13. 不确定性评估
14. 第 1 轮选点

详细命令请直接看 [docs/AIQM_FIRST_ROUND_RUNBOOK.md](./docs/AIQM_FIRST_ROUND_RUNBOOK.md)。

## Git 版本管理说明

如果你需要提交、回退或打版本标签，可以看：

- [docs/GIT_VERSIONING_GUIDE.md](./docs/GIT_VERSIONING_GUIDE.md)

## 论文来源

- Yaohuang Huang, Yi-Fan Hou, Pavlo O. Dral. *Active delta-learning for fast construction of interatomic potentials and stable molecular dynamics simulations*. Mach. Learn.: Sci. Technol. 2025.
- ChemRxiv 预印本：[10.26434/chemrxiv-2024-fb02r](https://doi.org/10.26434/chemrxiv-2024-fb02r)
- MLatom 官方仓库：[dralgroup/mlatom](https://github.com/dralgroup/mlatom)
