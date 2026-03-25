# 最小版 ADL 复现项目：ethene + 1,3-butadiene

这个子项目是当前仓库里真正推荐使用的入口，目标不是完整复现整篇论文，而是先把最小可运行的 active delta-learning 第一轮工作流在 AIQM 集群上跑通。

- 体系：`ethene + 1,3-butadiene`
- baseline：`GFN2-xTB`
- target：`wB97X-D/6-31G*`
- 默认训练后端：`ANI`
- 默认训练设备：`cuda`
- 推荐兼容栈：`PyTorch 1.12.0 + cudatoolkit 11.3 + TorchANI 2.2`
- 学习目标：
  - `delta_E = E_target - E_baseline`
  - `delta_F = F_target - F_baseline`

## 1. 当前子项目实现了什么

当前仓库的真实入口就是下面这些脚本：

1. `sample_initial_geometries.py`
   - 从种子结构生成初始几何池
   - 默认生成 400 个几何
2. `active_learning_loop.py`
   - 第 0 轮默认选择 250 个初始点
   - 后续每轮最多新增 100 个点
3. `run_xtb_labels.py`
   - 批量提交 `GFN2-xTB` baseline 标注
4. `run_target_labels.py`
   - 批量提交 Gaussian `wB97X-D/6-31G*` target 标注
5. `build_delta_dataset.py`
   - 汇总 baseline 和 target 结果，构建统一 delta 数据集
6. `train_main_model.py`
   - 主模型学习 `delta_E + delta_F`
   - 支持 `--submit-mode pbs`
7. `train_aux_model.py`
   - 辅助模型只学习 `delta_E`
   - 支持 `--submit-mode pbs`
8. `evaluate_uncertainty.py`
   - 用 `|pred_main_delta_E - pred_aux_delta_E|` 评估不确定性
   - 支持 `--submit-mode pbs`

### 当前默认值

- 几何池：400
- 初始选点：250
- 每轮新增上限：100
- 主模型：学习 `delta_E + delta_F`
- 辅助模型：学习 `delta_E`
- 不确定性：两模型 `delta_E` 预测差绝对值
- 收敛条件：高不确定性点比例 `< 5%`

## 2. 哪些地方忠于论文，哪些地方做了简化

### 论文一致

- 初始点数默认 250
- 每轮最多新增 100 个点
- 主模型学习 `delta_E + delta_F`
- 辅助模型只学习 `delta_E`
- 不确定性定义为两者的 `delta_E` 预测差绝对值
- 收敛判断采用高不确定性点比例 `< 5%`

### 工程简化

- 只保留 `ethene + 1,3-butadiene`
- 不做 `C60`
- 不做 `ANI-1ccx baseline`
- target 从论文中的 `B3LYP/6-31G*` 改成 `wB97X-D/6-31G*`
- 初始几何采样使用教学版随机微扰，而不是严格量子玻尔兹曼采样
- Gaussian 不再走旧的 `RunG16.sh`，而是走 `MLatom + PBS`

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

## 4. 环境准备

这份子项目 README 只保留和当前仓库一致的那套安装口径。推荐环境名是 `ADL_env`，并直接复用集群系统程序：

- `xtb`：`/share/apps/xtb-6.7.1/xtb-dist/bin/xtb`
- `g16`：`/share/apps/gaussian/g16/g16`

### 先确认你在“完整仓库 clone”里运行

如果你是在 PBS 集群上跑这个项目，推荐在登录节点保留完整 Git 仓库，而不是只复制
`minimal_adl_ethene_butadiene/` 子目录。正确做法是先在集群上：

```bash
cd /share/home/Chenlehui/work
git clone https://github.com/LehuiChen/test_ADL.git
cd test_ADL
git status
```

然后再进入这个子项目目录：

```bash
cd /share/home/Chenlehui/work/test_ADL/minimal_adl_ethene_butadiene
```

以后代码更新时，请回到仓库根目录执行：

```bash
cd /share/home/Chenlehui/work/test_ADL
git pull --ff-only
cd /share/home/Chenlehui/work/test_ADL/minimal_adl_ethene_butadiene
```

如果你只拷了子目录，没有上层 `.git`，那么 `git pull` 会失败，并提示
`Not a git repository`。

推荐兼容栈：

- `Python 3.10`
- `PyTorch 1.12.0`
- `torchvision 0.13.0`
- `torchaudio 0.12.0`
- `cudatoolkit 11.3`
- `TorchANI 2.2`

推荐安装顺序：

```bash
source ~/.bashrc
conda create -n ADL_env python=3.10 -y
conda activate ADL_env

conda install -y -n base conda-libmamba-solver
conda config --set solver libmamba
conda config --set channel_priority flexible

conda install -y -c conda-forge numpy scipy pyyaml matplotlib
conda install -y -c conda-forge joblib scikit-learn h5py statsmodels tqdm
python -m pip install pyh5md
conda install -y pytorch==1.12.0 torchvision==0.13.0 torchaudio==0.12.0 cudatoolkit=11.3 -c pytorch -c conda-forge -c defaults
conda install -y -c conda-forge pandas pyarrow rich typer ase zarr numcodecs fasteners huggingface_hub httpx ninja

python -m pip install --upgrade pip setuptools wheel
python -m pip install "torchani==2.2" --no-deps
python -m pip install mlatom --no-deps
```

> [!IMPORTANT]
> 当前推荐兼容栈是 `PyTorch 1.12.0 + cudatoolkit 11.3 + TorchANI 2.2`。如果 GPU 节点驱动较老，例如 `470.94`，优先保持这一套，不要直接改成 `pytorch-cuda=12.1`。

> [!WARNING]
> 不要在已经固定好 `torch==1.12.0` 的环境里直接执行：
>
> ```bash
> python -m pip install mlatom
> ```
>
> 正确做法是：
>
> ```bash
> python -m pip install mlatom --no-deps
> ```
>
> 否则 `pip` 可能会把 `torch` 升级到 2.x，破坏复现环境。

> [!NOTE]
> 在登录节点上执行 `python -c "import torch; print(torch.cuda.is_available())"` 返回 `False` 是正常现象。请先进入 PBS 申请到的 GPU 节点，再判断 CUDA 是否可用。

### 加载系统程序路径

```bash
source /share/apps/gaussian/g16-env.sh
source /share/env/ips2018u1.env
source ~/.bashrc
conda activate ADL_env
export PATH=/share/apps/gaussian/g16:/share/pubbin:/share/home/Chenlehui/bin:/share/apps/xtb-6.7.1/xtb-dist/bin:$PATH
export dftd4bin=/share/apps/dftd4-3.5.0/bin/dftd4
```

建议先做基础检查：

```bash
which python
python --version
python -c "import yaml; print('PyYAML OK')"
python -c "import mlatom as ml; print('mlatom OK')"
python -c "import torchani; print('torchani OK')"
python - <<'PY'
import torch
print("torch =", torch.__version__)
print("torch cuda =", torch.version.cuda)
print("cuda available =", torch.cuda.is_available())
PY
which xtb
xtb --version
which g16
```

安装完成后，先运行：

```bash
python scripts/check_environment.py
python scripts/check_environment.py --test-mlatom-xtb
```

如果 `--test-mlatom-xtb` 报 `No module named 'pyscf'`，通常不是环境少装了 xTB，而是 MLatom 的通用方法分发提前导入了 PySCF 接口。当前仓库已经优先改为 xTB 专用接口，不需要额外安装 PySCF 才能跑 baseline。

如果你已经进入 GPU 节点，再运行：

```bash
python scripts/check_environment.py --expect-gpu
python scripts/check_environment.py --expect-gpu --test-mlatom-xtb
```

## 5. CPU / GPU 任务分工

当前配置默认这样分流：

- `xtb` baseline 标注：CPU 队列 `default`
- Gaussian target 标注：CPU 队列 `default`
- 主模型训练：GPU 队列 `GPU`
- 辅助模型训练：GPU 队列 `GPU`
- 不确定性评估：GPU 队列 `GPU`

也就是说，Gaussian 默认走 CPU 队列；GPU 主要留给 `ANI` 训练和预测。

### 关于 PBS 的 `extra_pbs_lines`

当前 `configs/base.yaml` 已经为四类任务都预留了：

- `cluster.resources_by_method.baseline.extra_pbs_lines`
- `cluster.resources_by_method.target.extra_pbs_lines`
- `cluster.resources_by_method.training.extra_pbs_lines`
- `cluster.resources_by_method.uncertainty.extra_pbs_lines`

默认这些字段是空列表，表示“只写队列、节点数、ppn、walltime”。
如果你的机房对 GPU 作业还要求额外资源行，例如：

```text
#PBS -l gpus=1
```

或：

```text
#PBS -l ngpus=1
```

请把对应语法填进 `training` 和 `uncertainty` 的 `extra_pbs_lines`。

## 6. 推荐的第一轮执行顺序

如果你是第一次跑，推荐顺序是：

1. 环境安装
2. 版本检查
3. GPU 节点 CUDA 检查
4. `scripts/check_environment.py`
5. 几何池生成
6. 第 0 轮选点
7. `mlatom + xtb` 最小联通检查
8. 小样本 `xtb` 冒烟测试
9. 小样本 Gaussian 冒烟测试
10. 完整批次标注
11. 构建数据集
12. 主模型训练
13. 辅助模型训练
14. 不确定性评估
15. 第 1 轮选点

> [!IMPORTANT]
> 第一次上集群时，不建议一开始就直接提交完整的 250 个 Gaussian 任务。先做小样本联通测试，更容易排查 PBS 环境变量、`xtb`/`g16` 路径、scratch 权限和 MLatom 调用链问题。

具体命令请看：

- [../docs/AIQM_FIRST_ROUND_RUNBOOK.md](../docs/AIQM_FIRST_ROUND_RUNBOOK.md)

## 7. 关于 PBS 作业

这个项目默认支持 PBS 提交：

- `run_xtb_labels.py` 和 `run_target_labels.py` 默认是 `--submit-mode pbs`
- `train_main_model.py`、`train_aux_model.py`、`evaluate_uncertainty.py` 支持 `--submit-mode {local,pbs}`
- 训练和不确定性任务使用 `pbs` 模式时，会自动读取 `cluster.resources_by_method.training` 或 `cluster.resources_by_method.uncertainty`

每个作业目录通常会包含：

- `job.pbs`
- `status.json`
- `stdout.log`
- `stderr.log`
- `label.json` 或阶段输出 JSON

## 8. 重要提醒

- 这个子项目按“先跑通第一轮”的目标组织，不追求第一次就扩展到全部体系和全部实验。
- 如果 GPU 临时不可用，也可以把 `training.device` 改成 `cpu`，或者把 `training.ml_model_type` 切成 `KREG` 作为更保守的备用方案。
- 当前仓库外层的 `adl/` 与 `static/` 没有被改动；这个子项目是独立的干净实现。
