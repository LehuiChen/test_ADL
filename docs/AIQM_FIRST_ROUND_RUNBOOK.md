# AIQM 集群第一轮运行清单（ADL_env 版）

这份清单对应当前仓库里的最小版项目：

- 项目目录：[minimal_adl_ethene_butadiene](/D:/#sustech_work/work/adl25-main/minimal_adl_ethene_butadiene)
- 体系：`ethene + 1,3-butadiene`
- baseline：`GFN2-xTB`
- target：`wB97X-D/6-31G*`
- 主模型：`ANI`
- 训练设备：`cuda`

这份清单假设你是在集群的 Linux shell 里操作，而不是在当前这台 Windows 机器上操作。
集群上推荐的新 conda 环境名是 `ADL_env`，并且直接复用系统 `xtb`：

- `/share/apps/xtb-6.7.1/xtb-dist/bin/xtb`
- `/share/apps/gaussian/g16/g16`

## 0. 一次性进入项目目录

如果你的仓库放在别的位置，只改第一行：

```bash
export PROJECT_DIR=/share/home/Chenlehui/test_ADL
cd "$PROJECT_DIR/minimal_adl_ethene_butadiene"
pwd
```

## 1. 创建并激活 ADL_env

```bash
source ~/.bashrc
conda create -n ADL_env python=3.10 -y
conda activate ADL_env

conda install -y -c conda-forge numpy scipy pyyaml matplotlib h5py pyarrow pandas statsmodels tqdm rich typer ase zarr numcodecs fasteners huggingface_hub httpx ninja
conda install -y pytorch pytorch-cuda=12.1 -c pytorch -c nvidia

python -m pip install --upgrade pip setuptools wheel
python -m pip install mlatom
python -m pip install torchani --no-deps
```

说明：

- 这里故意把 `h5py`、`pyarrow`、`pandas` 等重型依赖放到 `conda-forge` 安装，避免 `pip` 在集群上源码编译失败
- `torchani` 放到最后并使用 `--no-deps`，前提是上面的依赖已经通过 conda 装好

## 2. 加载系统程序路径并检查依赖

```bash
source /share/apps/gaussian/g16-env.sh
source /share/env/ips2018u1.env
source ~/.bashrc
conda activate ADL_env
export PATH=/share/apps/gaussian/g16:/share/pubbin:/share/home/Chenlehui/bin:/share/apps/xtb-6.7.1/xtb-dist/bin:$PATH
export dftd4bin=/share/apps/dftd4-3.5.0/bin/dftd4

which python
python --version
python -c "import yaml; print('PyYAML OK')"
python -c "import mlatom as ml; print('mlatom OK')"
python -c "import torch; print(torch.cuda.is_available())"
python -c "import torchani; print('torchani OK')"
which xtb
xtb --version
which Gau_Mlatom.py
which g16
ls /share/apps/gaussian/g16/g16
```

如果你想顺手确认 GPU 节点上能看到显卡，可以在 GPU 节点里再执行：

```bash
nvidia-smi
```

## 3. 先检查当前配置

```bash
sed -n '1,220p' configs/base.yaml
```

重点确认这些字段：

- `training.ml_model_type: ANI`
- `training.device: cuda`
- `cluster.resources_by_method.training.queue: GPU`
- `cluster.resources_by_method.uncertainty.queue: GPU`

## 4. 生成初始几何池

默认会生成 400 个几何：

```bash
python scripts/sample_initial_geometries.py --config configs/base.yaml
```

检查输出：

```bash
ls data/raw/geometries | head
python - <<'PY'
import json
from pathlib import Path
path = Path('data/raw/geometry_pool_manifest.json')
data = json.loads(path.read_text(encoding='utf-8'))
print('num_geometries =', len(data))
print('first_sample =', data[0]['sample_id'])
PY
```

## 5. 进行第 0 轮初始选点

这一步会按论文一致的默认参数，从几何池里选出 250 个初始样本：

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
path = Path('data/raw/initial_selection_manifest.json')
data = json.loads(path.read_text(encoding='utf-8'))
print('initial_selected =', len(data))
print('first_sample =', data[0]['sample_id'])
PY
```

## 6. 先做一个最小的 mlatom + xtb 联通检查

```bash
python - <<'PY'
import mlatom as ml
m = ml.data.molecule()
m.load('geometries/seed/da_eqmol_seed.xyz', format='xyz')
method = ml.models.methods(method='GFN2-xTB', nthreads=4)
method.predict(
    molecule=m,
    calculate_energy=True,
    calculate_energy_gradients=True,
    calculate_hessian=False,
)
print('energy =', m.energy)
PY
```

## 7. 提交 baseline 标注任务

这一步默认走 CPU 队列：

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
files = sorted(Path('labels/xtb').glob('*/label.json'))
print('label_files =', len(files))
if files:
    data = json.loads(files[0].read_text(encoding='utf-8'))
    print('sample_id =', data.get('sample_id'))
    print('success =', data.get('success'))
    print('energy =', data.get('energy'))
PY
```

## 8. 提交 target 标注任务

这一步也走 CPU 队列，但 PBS 脚本会自动前置 Gaussian 环境：

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
files = sorted(Path('labels/gaussian').glob('*/label.json'))
print('label_files =', len(files))
if files:
    data = json.loads(files[0].read_text(encoding='utf-8'))
    print('sample_id =', data.get('sample_id'))
    print('success =', data.get('success'))
    print('energy =', data.get('energy'))
PY
```

如果这一步报错，优先查看：

```bash
find labels/gaussian -name stderr.log | head -n 3 | xargs -I {} sh -c 'echo "===== {} ====="; tail -n 30 "{}"'
```

## 9. 构建 delta 数据集

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
meta = json.loads(Path('data/processed/delta_dataset_metadata.json').read_text(encoding='utf-8'))
arr = np.load('data/processed/delta_dataset.npz')
print('num_samples =', meta['num_samples'])
print('npz_keys =', sorted(arr.files))
print('E_baseline shape =', arr['E_baseline'].shape)
print('E_target shape =', arr['E_target'].shape)
print('delta_E shape =', arr['delta_E'].shape)
print('delta_F shape =', arr['delta_F'].shape)
PY
```

## 10. 提交主模型训练

这一步默认走 GPU 队列 `GPU`：

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

## 11. 提交辅助模型训练

这一步也走 GPU 队列 `GPU`：

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

## 12. 评估不确定性

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
data = json.loads(Path('results/uncertainty_latest.json').read_text(encoding='utf-8'))
print('num_samples =', data['num_samples'])
print('uq_threshold =', data['uq_threshold'])
print('first_sample =', data['samples'][0]['sample_id'])
print('first_uq =', data['samples'][0]['uncertainty'])
PY
```

## 13. 选出下一轮样本

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
path = Path('results/round_001_selected_manifest.json')
data = json.loads(path.read_text(encoding='utf-8'))
print('round_1_selected =', len(data))
if data:
    print('first_sample =', data[0]['sample_id'])
PY
```

## 14. 如果你想继续第二轮

把第 11 步选出来的清单继续拿去做标注：

```bash
python scripts/run_xtb_labels.py \
  --config configs/base.yaml \
  --manifest results/round_001_selected_manifest.json

python scripts/run_target_labels.py \
  --config configs/base.yaml \
  --manifest results/round_001_selected_manifest.json
```

然后重新构建数据集、重新训练、重新做不确定性评估。

## 15. 初学者最常用的排错命令

看最近的训练状态文件：

```bash
cat models/train_main_status.json
cat models/train_aux_status.json
cat results/uncertainty_status.json
```

看最近的 PBS 标准输出和错误输出：

```bash
find labels -name stdout.log | tail
find labels -name stderr.log | tail
find models/jobs -name stdout.log | tail
find models/jobs -name stderr.log | tail
find results/jobs -name stdout.log | tail
find results/jobs -name stderr.log | tail
```

看某个 Gaussian 样本最后 50 行日志：

```bash
tail -n 50 labels/gaussian/<sample_id>/stdout.log
tail -n 50 labels/gaussian/<sample_id>/stderr.log
```

## 16. 这一版哪些地方是论文一致，哪些地方是工程简化

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
