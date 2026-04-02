# ANI 第一轮运行手册

对应工程：`minimal_adl_ethene_butadiene`
训练环境：`ADL_env`

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

### 4.1 Local 模式

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --submit-mode-labels local \
  --submit-mode-train local \
  --submit-mode-uq local
```

### 4.2 PBS 模式

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --submit-mode-labels pbs \
  --submit-mode-train pbs \
  --submit-mode-uq pbs
```

## 5. 断点续跑与强制重跑

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --from-stage train_main_model \
  --submit-mode-train pbs \
  --submit-mode-uq pbs
```

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --from-stage train_main_model \
  --force \
  --submit-mode-train pbs \
  --submit-mode-uq pbs
```

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --to-stage export_training_diagnostics \
  --submit-mode-labels pbs \
  --submit-mode-train pbs
```

## 6. 结果产物与验收

`models/` 重点：

- `training_summary.json`
- `training_state.json`
- `train_main_predictions.csv`
- `train_aux_predictions.csv`
- `training_diagnostics.json`

`results/` 重点：

- `check_environment_latest.json`
- `uncertainty_latest.json`
- `round_001_selection_summary.json`
- `round_001_selected_manifest.json`
- `pipeline_run_summary.json`

建议验收：

- `check_environment --strict` 通过
- `train_main_model` 与 `evaluate_uncertainty` 阶段成功
- `round_001_selection_summary.json` 存在且含已选样本
