# Minimal ADL（ANI）

本目录是 ANI 主线工程。

- 项目目录：`minimal_adl_ethene_butadiene`
- 模型类型：`ANI`
- 训练环境：`ADL_env`

## 1. 环境准备

```bash
cd /share/home/Chenlehui/work/test_ADL/minimal_adl_ethene_butadiene
conda activate ADL_env
python -m pip install -r requirements.txt
```

## 2. 训练前门禁测试（必须先跑）

```bash
python scripts/check_environment.py --config configs/base.yaml --strict
python scripts/check_environment.py --config configs/base.yaml --strict --test-mlatom-xtb
```

GPU 节点可附加：

```bash
python scripts/check_environment.py --config configs/base.yaml --strict --expect-gpu
```

## 3. 最小联通测试

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --to-stage sample_initial_geometries \
  --submit-mode-labels local \
  --submit-mode-train local \
  --submit-mode-uq local
```

## 4. 完整第一轮

### 4.1 Local

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --submit-mode-labels local \
  --submit-mode-train local \
  --submit-mode-uq local
```

### 4.2 PBS

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --submit-mode-labels pbs \
  --submit-mode-train pbs \
  --submit-mode-uq pbs
```

## 5. 断点续跑 / 强制重跑

```bash
python scripts/run_first_round_pipeline.py --config configs/base.yaml --from-stage train_main_model --submit-mode-train pbs --submit-mode-uq pbs
python scripts/run_first_round_pipeline.py --config configs/base.yaml --from-stage train_main_model --force --submit-mode-train pbs --submit-mode-uq pbs
python scripts/run_first_round_pipeline.py --config configs/base.yaml --to-stage export_training_diagnostics --submit-mode-labels pbs --submit-mode-train pbs
```

## 6. 结果产物与文档

重点输出目录：

- `models/`
- `results/`

推荐阅读：

- [../docs/ani/RUNBOOK_ANI_FIRST_ROUND.md](../docs/ani/RUNBOOK_ANI_FIRST_ROUND.md)
- [../docs/ani/DATA_ANALYSIS.ipynb](../docs/ani/DATA_ANALYSIS.ipynb)
- [../docs/common/环境配置.md](../docs/common/环境配置.md)
