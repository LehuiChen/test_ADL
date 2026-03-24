# 最小版 ADL 复现项目：ethene + 1,3-butadiene

这个子项目是基于原论文仓库重新整理的“教学式最小实现”。目标不是完整复现整篇论文，而是先把最小可运行的 active delta-learning 工作流打通：

- 体系：`ethene + 1,3-butadiene`
- baseline：`GFN2-xTB`
- target：`wB97X-D/6-31G*`
- 默认训练后端：`MLatom ANI`
- 默认训练设备：`cuda`
- 推荐 GPU 兼容栈：`PyTorch 1.12.0 + cudatoolkit 11.3 + TorchANI 2.2`
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
   - 支持 `--submit-mode pbs`，会按配置提交到 `GPU` 队列。
6. `train_aux_model.py`
   - 训练辅助模型，只学习 `delta_E`。
   - 支持 `--submit-mode pbs`，会按配置提交到 `GPU` 队列。
7. `evaluate_uncertainty.py`
   - 用主模型和辅助模型预测未标注几何，计算不确定性：
   - `|pred_main_delta_E - pred_aux_delta_E|`
   - 支持 `--submit-mode pbs`，会按配置提交到 `GPU` 队列。
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
- Gaussian 不走旧的 `RunG16.sh` 入口，而是继续走 `MLatom + PBS`，只是把你集群上实际需要的环境前置块吸收到 PBS 模板里。
- 如果 GPU 临时不可用，也可以把 `configs/base.yaml` 里的 `training.device` 改成 `cpu`，或者把 `training.ml_model_type` 改成 `KREG` 作为更保守的备用方案。

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

- conda 环境：`ADL_env`
- Python 包：
  - `numpy`
  - `PyYAML`
  - `mlatom`
  - `matplotlib`（可选，仅用于后续扩展画图）
  - `torch`
  - `torchani`
  - `joblib`
  - `scikit-learn`
- 外部程序：
  - 系统 `xtb`
  - Gaussian `g16`

当前配置默认假定你的集群环境满足下面这些命令或路径：

- `source /share/apps/gaussian/g16-env.sh`
- `source /share/env/ips2018u1.env`
- `source ~/.bashrc`
- `conda activate ADL_env`
- `export PATH=/share/apps/gaussian/g16:/share/pubbin:/share/home/Chenlehui/bin:/share/apps/xtb-6.7.1/xtb-dist/bin:$PATH`
- `export dftd4bin=/share/apps/dftd4-3.5.0/bin/dftd4`
- `export GAUSS_SCRDIR=/tmp/$USER/$PBS_JOBID`

推荐的新环境安装命令是：

```bash
conda create -n ADL_env python=3.10 -y
conda activate ADL_env
conda install -y -n base conda-libmamba-solver
conda config --set solver libmamba

conda install -y -c conda-forge numpy scipy pyyaml matplotlib
conda install -y -c conda-forge joblib scikit-learn h5py pyh5md statsmodels tqdm
conda install -y -c pytorch pytorch==1.12.0 torchvision==0.13.0 torchaudio==0.12.0 cudatoolkit=11.3
conda install -y -c conda-forge pandas pyarrow rich typer ase zarr numcodecs fasteners huggingface_hub httpx ninja

python -m pip install --upgrade pip setuptools wheel
python -m pip install mlatom
python -m pip install "torchani==2.2" --no-deps
```

注意：

- `xtb` 不通过 conda 安装，直接复用系统路径 `/share/apps/xtb-6.7.1/xtb-dist/bin/xtb`
- Python 里导入 MLatom 的正确写法是 `import mlatom as ml`
- 在你的集群环境里，`pip install mlatom torchani` 可能会触发 `h5py` 和 `pyarrow` 源码编译；因此推荐先用 `conda-forge` 装好这些二进制依赖，再用 `pip` 安装 `mlatom` 和 `torchani`
- `conda` 如果长时间卡在 `Solving environment`，优先启用 `libmamba`，并按上面这种“小批量分阶段安装”的顺序来
- 如果你的 GPU 节点驱动和你提供的一样是 `470.94`，优先使用上面这套老版本 GPU 兼容栈，不要直接装 `pytorch-cuda=12.1`
- 在登录节点上 `torch.cuda.is_available()` 返回 `False` 是正常的，请在 `gpu1` 这类 GPU 节点上验证 CUDA

安装完成后，建议先运行环境自检脚本：

```bash
python scripts/check_environment.py --expect-gpu
python scripts/check_environment.py --expect-gpu --test-mlatom-xtb
```

## 5. CPU / GPU 任务分工

这版配置已经按你的集群环境做了任务分流：

- `xtb` baseline 标注：CPU 队列 `default`
- Gaussian target 标注：CPU 队列 `default`
- `ANI` 主模型训练：GPU 队列 `GPU`
- `ANI` 辅助模型训练：GPU 队列 `GPU`
- 不确定性评估：GPU 队列 `GPU`

也就是说，Gaussian 不占用 RTX3080；RTX3080 主要用于 `ANI` 训练和预测。

如果你的 GPU 驱动版本较老，又想优先跑通工作流，也可以把 `configs/base.yaml` 里的 `training.ml_model_type` 改成 `KREG`，并把 `training.device` 改成 `cpu`。

## 6. 推荐执行顺序

下面是假设你已经进入本项目目录后的最小顺序：

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

如果你只是想先在登录节点或调试节点上验证代码逻辑，也可以把上面三个训练相关脚本改成 `--submit-mode local`。

## 7. 关于 PBS 作业

这个项目默认支持 PBS 提交：

- 每个标注样本会生成独立作业目录。
- 每个作业目录至少包含：
  - `job.pbs`
  - `status.json`
  - `label.json`（成功时）
  - `stdout.log`
  - `stderr.log`
- 训练和不确定性评估也会生成自己的 PBS 作业目录与状态文件。

其中：

- `run_xtb_labels.py` 和 `run_target_labels.py` 默认就是 `--submit-mode pbs`
- `train_main_model.py`、`train_aux_model.py`、`evaluate_uncertainty.py` 新增了 `--submit-mode {local,pbs}`
- 当训练和不确定性脚本使用 `--submit-mode pbs` 时，会自动走 `cluster.resources_by_method.training` 或 `cluster.resources_by_method.uncertainty` 的配置
- 初次配环境时，强烈建议先跑 `scripts/check_environment.py`，再进入大规模标注或训练

## 8. 重要提醒

- 这个项目的中文注释是按“本科生能跟着看懂”的标准写的，所以更偏重可读性，而不是最短代码。
- 当前仓库外层的原始 `adl/` 与 `static/` 目录没有被改动，这个子项目是独立的干净实现。
- 我本地这台机器没有 `PyYAML / mlatom / xtb / Gaussian`，所以这里做的是“代码结构 + PBS 接口”层面的实现；真正跑作业时，请在你的 `ADL_env` 环境中执行。

如果你想直接按命令一步步跑第一轮，可以看：

- [docs/AIQM_FIRST_ROUND_RUNBOOK.md](/D:/#sustech_work/work/adl25-main/docs/AIQM_FIRST_ROUND_RUNBOOK.md)
