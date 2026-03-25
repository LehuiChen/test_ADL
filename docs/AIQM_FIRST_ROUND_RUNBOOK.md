# AIQM 集群第一轮运行指南（ADL_env 版）

本指南对应当前仓库中的最小版项目 [../minimal_adl_ethene_butadiene/](../minimal_adl_ethene_butadiene/) ，面向
`ethene + 1,3-butadiene` 体系，采用：

- baseline：`GFN2-xTB`
- target：`wB97X-D/6-31G*`
- 主模型：`ANI`
- 训练设备：`cuda`
- 推荐兼容栈：`PyTorch 1.12.0 + cudatoolkit 11.3 + TorchANI 2.2`

本指南默认你是在 AIQM 集群的 Linux shell 中操作，而不是在本地 Windows 环境中操作。

---

## 快速开始摘要

如果你只想先快速跑通第一轮，建议按下面顺序执行：

1. 创建并激活 `ADL_env`
2. 安装固定兼容栈：`PyTorch 1.12.0 + cudatoolkit 11.3 + TorchANI 2.2`
3. 用 `--no-deps` 安装 `mlatom`，避免把 PyTorch 升级掉
4. 加载 `xtb`、`g16` 等系统程序路径
5. 跑 `scripts/check_environment.py`
6. 生成几何池
7. 进行第 0 轮初始选点
8. 先做一个小样本 `xtb + gaussian` 冒烟测试
9. 构建 delta 数据集
10. 提交主模型训练、辅助模型训练和不确定性评估
11. 生成下一轮样本清单

> [!IMPORTANT]
> 本 README 推荐的兼容栈是：
>
> - `Python 3.10`
> - `PyTorch 1.12.0`
> - `torchvision 0.13.0`
> - `torchaudio 0.12.0`
> - `cudatoolkit 11.3`
> - `TorchANI 2.2`

> [!WARNING]
> 不要在已经固定好 `torch==1.12.0` 的环境里直接执行：
>
> ```bash
> python -m pip install mlatom
> ```
>
> 否则 `pip` 可能会自动升级 `torch`，破坏复现环境。
> 正确做法是：
>
> ```bash
> python -m pip install mlatom --no-deps
> ```

> [!NOTE]
> 在登录节点上执行：
>
> ```bash
> python -c "import torch; print(torch.cuda.is_available())"
> ```
>
> 返回 `False` 是正常现象。请先进入 GPU 节点，再判断 CUDA 是否可用。

---

## 项目概览

- 项目目录：`minimal_adl_ethene_butadiene/`
- 体系：`ethene + 1,3-butadiene`
- baseline：`GFN2-xTB`
- target：`wB97X-D/6-31G*`
- 主模型：`ANI`
- 默认训练设备：`cuda`
- 默认几何池：400
- 第 0 轮初始点：250
- 每轮最多新增：100
- UQ：`|pred_main_delta_E - pred_aux_delta_E|`

集群上直接复用系统程序路径：

- `xtb`：`/share/apps/xtb-6.7.1/xtb-dist/bin/xtb`
- `g16`：`/share/apps/gaussian/g16/g16`

## 目录结构

当前最小版项目的典型目录结构如下：

```text
minimal_adl_ethene_butadiene/
├── configs/
│   └── base.yaml
├── data/
│   ├── raw/
│   │   ├── geometries/
│   │   ├── geometry_pool_manifest.json
│   │   └── initial_selection_manifest.json
│   └── processed/
│       ├── delta_dataset.npz
│       └── delta_dataset_metadata.json
├── geometries/
│   └── seed/
│       └── da_eqmol_seed.xyz
├── labels/
│   ├── xtb/
│   └── gaussian/
├── models/
│   ├── jobs/
│   ├── train_main_status.json
│   └── train_aux_status.json
├── results/
│   ├── jobs/
│   ├── uncertainty_status.json
│   ├── uncertainty_latest.json
│   ├── round_001_selection_summary.json
│   └── round_001_selected_manifest.json
├── scripts/
│   ├── check_environment.py
│   ├── sample_initial_geometries.py
│   ├── active_learning_loop.py
│   ├── run_xtb_labels.py
│   ├── run_target_labels.py
│   ├── build_delta_dataset.py
│   ├── train_main_model.py
│   ├── train_aux_model.py
│   └── evaluate_uncertainty.py
└── src/minimal_adl/
```

## 0. 进入项目目录

如果你的仓库放在别的位置，只改第一行：

```bash
export PROJECT_DIR=/share/home/Chenlehui/test_ADL
cd "$PROJECT_DIR/minimal_adl_ethene_butadiene"
pwd
```

## 1. 创建并激活 ADL_env

先确保 shell 里的 conda 初始化正常：

```bash
source ~/.bashrc
```

创建并激活环境：

```bash
conda create -n ADL_env python=3.10 -y
conda activate ADL_env
```

启用 `libmamba` 求解器，并放宽 `channel_priority`：

```bash
conda install -y -n base conda-libmamba-solver
conda config --set solver libmamba
conda config --set channel_priority flexible
```

分阶段安装基础科学计算依赖：

```bash
conda install -y -c conda-forge numpy scipy pyyaml matplotlib
conda install -y -c conda-forge joblib scikit-learn h5py statsmodels tqdm
python -m pip install pyh5md
conda install -y pytorch==1.12.0 torchvision==0.13.0 torchaudio==0.12.0 cudatoolkit=11.3 -c pytorch -c conda-forge -c defaults
conda install -y -c conda-forge pandas pyarrow rich typer ase zarr numcodecs fasteners huggingface_hub httpx ninja
```

升级打包工具，并按固定顺序安装 `torchani` 和 `mlatom`：

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install "torchani==2.2" --no-deps
python -m pip install mlatom --no-deps
```

安装顺序说明：

- `h5py`、`pandas`、`pyarrow` 这类重依赖优先交给 `conda`
- `pyh5md` 通过 `pip` 安装
- 先固定 `PyTorch 1.12.0 + cudatoolkit 11.3`
- 再安装 `torchani`
- 最后安装 `mlatom`，并禁止它重新解析依赖

## 2. 加载系统程序路径并检查依赖

建议按下面顺序加载环境：

```bash
source /share/apps/gaussian/g16-env.sh
source /share/env/ips2018u1.env
source ~/.bashrc
conda activate ADL_env
export PATH=/share/apps/gaussian/g16:/share/pubbin:/share/home/Chenlehui/bin:/share/apps/xtb-6.7.1/xtb-dist/bin:$PATH
export dftd4bin=/share/apps/dftd4-3.5.0/bin/dftd4
```

如果你在 PBS 子作业日志里看到 `PERLLIB: unbound variable`，通常不是 Gaussian 没装好，而是 `g16-env.sh` 和严格模式 `set -u` 的兼容问题。当前仓库已经在 target PBS 环境块中做了兼容处理，并限制了 `GAUSS_SCRDIR` 的清理范围，避免误删 `/tmp`。

基础检查：

```bash
which python
python --version

python -c "import yaml; print('PyYAML OK')"
python -c "import mlatom as ml; print('mlatom OK')"
python -c "import pyh5md; print('pyh5md OK')"
python -c "import torchani; print('torchani OK')"

which xtb
xtb --version

which Gau_Mlatom.py
which g16
ls /share/apps/gaussian/g16/g16
```

重点检查 PyTorch 版本是否仍然正确：

```bash
python - <<'PY'
import torch
print("torch =", torch.__version__)
print("torch cuda =", torch.version.cuda)
print("cuda available =", torch.cuda.is_available())
PY
```

期望结果应接近：

```text
torch = 1.12.0
torch cuda = 11.3
cuda available = False
```

其中 `cuda available = False` 在登录节点上是正常现象。

## 2.1 在 GPU 节点上检查 CUDA

当前集群是 PBS 系统。请先申请一个 GPU 交互节点，再检查 GPU 是否可见。

不同集群的 PBS 资源写法可能不同，下面只是示例，请以本机房实际写法为准：

```bash
qsub -I -q GPU -l nodes=1:ppn=4:gpus=1
```

进入 GPU 节点后，重新加载环境并检查：

```bash
source /share/apps/gaussian/g16-env.sh
source /share/env/ips2018u1.env
source ~/.bashrc
conda activate ADL_env
nvidia-smi
python - <<'PY'
import torch
print("torch =", torch.__version__)
print("torch cuda =", torch.version.cuda)
print("cuda available =", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu name =", torch.cuda.get_device_name(0))
PY
```

## 2.2 运行环境自检脚本

建议先跑项目自带的检查脚本：

```bash
python scripts/check_environment.py
python scripts/check_environment.py --test-mlatom-xtb
```

如果你当前已经位于 GPU 节点，再继续运行：

```bash
python scripts/check_environment.py --expect-gpu
python scripts/check_environment.py --expect-gpu --test-mlatom-xtb
```

如果你当前只是在登录节点上排查基础依赖，可以先不要加 `--expect-gpu`。

## 3. 检查当前配置

```bash
sed -n '1,220p' configs/base.yaml
```

重点确认这些字段：

- `training.ml_model_type: ANI`
- `training.device: cuda`
- `cluster.resources_by_method.training.queue: GPU`
- `cluster.resources_by_method.uncertainty.queue: GPU`

同时建议确认：

- 训练脚本生成的 PBS 脚本里，是否真的申请了 GPU 资源
- 不是只有 `queue=GPU`
- 如果机房要求，还应包含对应的 GPU 资源字段，例如 `gpus=1`、`ngpus=1` 或等价写法

当前仓库已经在 `cluster.resources_by_method.*.extra_pbs_lines` 中预留了入口，默认值是空列表。
如果你的机房需要额外 PBS 资源行，请把它们填在：

- `cluster.resources_by_method.training.extra_pbs_lines`
- `cluster.resources_by_method.uncertainty.extra_pbs_lines`

例如：

```yaml
extra_pbs_lines:
  - "#PBS -l gpus=1"
```

## 4. 生成初始几何池

默认生成 400 个几何：

```bash
python scripts/sample_initial_geometries.py --config configs/base.yaml
```

检查输出：

```bash
ls data/raw/geometries | head

python - <<'PY'
import json
from pathlib import Path
path = Path("data/raw/geometry_pool_manifest.json")
data = json.loads(path.read_text(encoding="utf-8"))
print("num_geometries =", len(data))
print("first_sample =", data[0]["sample_id"])
PY
```

## 5. 进行第 0 轮初始选点

这一步按默认参数从几何池里选出 250 个初始样本：

```bash
python scripts/active_learning_loop.py \
  --config configs/base.yaml \
  --manifest data/raw/geometry_pool_manifest.json \
  --round-index 0
```

检查输出：

```bash
python - <<'PY'
import json
from pathlib import Path
path = Path("data/raw/initial_selection_manifest.json")
data = json.loads(path.read_text(encoding="utf-8"))
print("initial_selected =", len(data))
print("first_sample =", data[0]["sample_id"])
PY
```

## 6. 先做一个最小的 mlatom + xtb 联通检查

```bash
python - <<'PY'
import mlatom as ml
from mlatom.interfaces.xtb_interface import xtb_methods

m = ml.data.molecule()
m.load("geometries/seed/da_eqmol_seed.xyz", format="xyz")
method = xtb_methods(method="GFN2-xTB", nthreads=4)
method.predict(
    molecule=m,
    calculate_energy=True,
    calculate_energy_gradients=True,
    calculate_hessian=False,
)
print("energy =", m.energy)
PY
```

如果你在这里看到 `ModuleNotFoundError: No module named 'pyscf'`，通常不是 `xtb` 没装好，而是通用的
`ml.models.methods(...)` 路径提前触发了 PySCF 接口导入。对于 `GFN2-xTB`，优先使用上面这段
`xtb_interface.xtb_methods` 写法，不需要额外安装 PySCF。

## 7. 标注任务前先做小样本冒烟测试

第一次上集群时，不建议一开始就直接跑完整的 250 个样本。

建议先从 `initial_selection_manifest.json` 里抽一个很小的子集做联通测试，例如：

- `xtb` 先跑 3 个样本
- Gaussian 先跑 1 到 2 个样本

等小样本确认完全打通后，再放大到完整批次。这样更容易排查：

- PBS 环境变量是否传入子作业
- `xtb` / `g16` 路径是否在计算节点可见
- scratch 目录和权限是否正常
- MLatom 调用链是否通畅

## 8. 提交 baseline 标注任务

完整批次默认走 CPU 队列：

```bash
python scripts/run_xtb_labels.py \
  --config configs/base.yaml \
  --manifest data/raw/initial_selection_manifest.json
```

完成后检查：

```bash
find labels/xtb -name status.json | wc -l
find labels/xtb -name label.json | wc -l
find labels/xtb -name stderr.log | head
```

随机查看一个样本：

```bash
python - <<'PY'
import json
from pathlib import Path
files = sorted(Path("labels/xtb").glob("*/label.json"))
print("label_files =", len(files))
if files:
    data = json.loads(files[0].read_text(encoding="utf-8"))
    print("sample_id =", data.get("sample_id"))
    print("success =", data.get("success"))
    print("energy =", data.get("energy"))
PY
```

## 9. 提交 target 标注任务

这一步也走 CPU 队列，但 PBS 脚本应自动前置 Gaussian 环境：

```bash
python scripts/run_target_labels.py \
  --config configs/base.yaml \
  --manifest data/raw/initial_selection_manifest.json
```

完成后检查：

```bash
find labels/gaussian -name status.json | wc -l
find labels/gaussian -name label.json | wc -l
find labels/gaussian -name stderr.log | head
```

随机查看一个样本：

```bash
python - <<'PY'
import json
from pathlib import Path
files = sorted(Path("labels/gaussian").glob("*/label.json"))
print("label_files =", len(files))
if files:
    data = json.loads(files[0].read_text(encoding="utf-8"))
    print("sample_id =", data.get("sample_id"))
    print("success =", data.get("success"))
    print("energy =", data.get("energy"))
PY
```

如果这一步报错，优先检查：

```bash
find labels/gaussian -name stderr.log | head -n 3 | xargs -I {} sh -c 'echo "===== {} ====="; tail -n 30 "{}"'
which g16
echo $GAUSS_EXEDIR
echo $g16root
```

## 10. 构建 delta 数据集

```bash
python scripts/build_delta_dataset.py \
  --config configs/base.yaml \
  --manifest data/raw/initial_selection_manifest.json
```

检查输出：

```bash
python - <<'PY'
import json
import numpy as np
from pathlib import Path
meta = json.loads(Path("data/processed/delta_dataset_metadata.json").read_text(encoding="utf-8"))
arr = np.load("data/processed/delta_dataset.npz")
print("num_samples =", meta["num_samples"])
print("npz_keys =", sorted(arr.files))
print("E_baseline shape =", arr["E_baseline"].shape)
print("E_target shape =", arr["E_target"].shape)
print("delta_E shape =", arr["delta_E"].shape)
print("delta_F shape =", arr["delta_F"].shape)
PY
```

## 11. 提交主模型训练

这一步应走 GPU 队列：

```bash
python scripts/train_main_model.py \
  --config configs/base.yaml \
  --submit-mode pbs
```

检查输出：

```bash
cat models/train_main_status.json
ls models
```

提交前请确认：

- 训练 PBS 脚本确实申请了 GPU
- GPU 节点内 `torch.cuda.is_available()` 为 `True`
- 不是仅仅把队列名设成 `GPU` 就结束

## 12. 提交辅助模型训练

这一步也走 GPU 队列：

```bash
python scripts/train_aux_model.py \
  --config configs/base.yaml \
  --submit-mode pbs
```

检查输出：

```bash
cat models/train_aux_status.json
ls models
```

## 13. 评估不确定性

```bash
python scripts/evaluate_uncertainty.py \
  --config configs/base.yaml \
  --manifest data/raw/geometry_pool_manifest.json \
  --submit-mode pbs
```

检查输出：

```bash
cat results/uncertainty_status.json

python - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("results/uncertainty_latest.json").read_text(encoding="utf-8"))
print("num_samples =", data["num_samples"])
print("uq_threshold =", data["uq_threshold"])
print("first_sample =", data["samples"][0]["sample_id"])
print("first_uq =", data["samples"][0]["uncertainty"])
PY
```

## 14. 选出下一轮样本

这一步会按当前不确定性结果选出下一轮最多 100 个点：

```bash
python scripts/active_learning_loop.py \
  --config configs/base.yaml \
  --manifest data/raw/geometry_pool_manifest.json \
  --uncertainty results/uncertainty_latest.json \
  --round-index 1
```

检查输出：

```bash
cat results/round_001_selection_summary.json

python - <<'PY'
import json
from pathlib import Path
path = Path("results/round_001_selected_manifest.json")
data = json.loads(path.read_text(encoding="utf-8"))
print("round_1_selected =", len(data))
if data:
    print("first_sample =", data[0]["sample_id"])
PY
```

## 15. 如果你想继续第二轮

把第 14 步选出来的清单继续拿去做标注：

```bash
python scripts/run_xtb_labels.py \
  --config configs/base.yaml \
  --manifest results/round_001_selected_manifest.json

python scripts/run_target_labels.py \
  --config configs/base.yaml \
  --manifest results/round_001_selected_manifest.json
```

然后重新构建数据集、重新训练、重新做不确定性评估。

## 16. 初学者最常用的排错命令

查看最近的训练状态文件：

```bash
cat models/train_main_status.json
cat models/train_aux_status.json
cat results/uncertainty_status.json
```

查看最近的 PBS 标准输出和错误输出：

```bash
find labels -name stdout.log | tail
find labels -name stderr.log | tail
find models/jobs -name stdout.log | tail
find models/jobs -name stderr.log | tail
find results/jobs -name stdout.log | tail
find results/jobs -name stderr.log | tail
```

查看某个 Gaussian 样本最后 50 行日志：

```bash
tail -n 50 labels/gaussian/<sample_id>/stdout.log
tail -n 50 labels/gaussian/<sample_id>/stderr.log
```

查看当前 PBS 作业：

```bash
qstat -u $USER
```

查看生成过的 PBS 脚本：

```bash
find . -name "*.pbs" | tail
```

如果集群支持，再查看具体作业详情：

```bash
qstat -f <job_id>
```

## 17. 哪些地方是论文一致，哪些地方是工程简化

论文一致：

- 初始 250 点
- 每轮最多新增 100 点
- 主模型学习 `delta_E + delta_F`
- 辅助模型只学习 `delta_E`
- 不确定性定义为两模型 `delta_E` 预测差绝对值
- 收敛条件是新增高不确定性点比例 `< 5%`

工程简化：

- 只保留 `ethene + 1,3-butadiene`
- 不做 C60
- 不做 ANI-1ccx baseline
- target 改成 `wB97X-D/6-31G*`
- 初始几何池用随机微扰生成
- Gaussian 通过 `MLatom + PBS` 调用，而不是复用旧的 `RunG16.sh`

## 18. 关键注意事项

> [!IMPORTANT]
> 安装完成后，请立刻检查：
>
> ```bash
> python - <<'PY'
> import torch
> print(torch.__version__)
> print(torch.version.cuda)
> PY
> ```
>
> 正常情况下应看到：
>
> ```text
> 1.12.0
> 11.3
> ```

> [!WARNING]
> 第一次上集群时，不建议直接完整提交 250 个 Gaussian 任务。请先做一个小样本冒烟测试，确认：
>
> - PBS 环境传递正常
> - `xtb` / `g16` 可见
> - scratch 正常
> - MLatom 调用链正常

> [!NOTE]
> 如果你已经安装了 `mlatom`，随后发现：
>
> ```bash
> python -c "import torch; print(torch.__version__)"
> ```
>
> 输出变成了 `2.x`，说明环境已经漂移。请不要继续复现流程，而应重新建立干净环境。

## 19. 建议的第一轮执行顺序

如果你是第一次跑，推荐按下面顺序走：

1. 环境安装
2. 版本检查
3. GPU 节点 CUDA 检查
4. `check_environment.py`
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
