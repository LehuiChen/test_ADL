# Minimal ADL (MACE Backend)

这个目录是与 ANI 并列的 MACE 工程版本，目标是尽量复用现有 ADL 主流程（采样、标注、构建 delta 数据集、训练、UQ、选点）。

- 项目名: `minimal_adl_ethene_butadiene_mace`
- 主模型后端: `MACE`（通过 MLatom 接口）
- 数据/模型/结果目录: 与 ANI 完全隔离

## Quick Start

### 1. 进入目录

```bash
cd D:/#sustech_work/work/adl25-main/minimal_adl_ethene_butadiene_mace
```

### 2. 环境检查

```bash
python scripts/check_environment.py --config configs/base.yaml --strict
```

可选：

```bash
python scripts/check_environment.py --config configs/base.yaml --strict --test-mlatom-xtb
```

### 3. 最小联通测试（只跑前几阶段）

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --to-stage sample_initial_geometries \
  --submit-mode-labels local \
  --submit-mode-train local \
  --submit-mode-uq local
```

### 4. 完整第一轮（本地模式）

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --submit-mode-labels local \
  --submit-mode-train local \
  --submit-mode-uq local
```

### 5. 完整第一轮（PBS 模式）

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --submit-mode-labels pbs \
  --submit-mode-train pbs \
  --submit-mode-uq pbs
```

## 断点续跑与强制重跑

从训练主模型阶段开始继续：

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --from-stage train_main_model \
  --submit-mode-train pbs \
  --submit-mode-uq pbs
```

强制重跑（忽略已完成状态）：

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --from-stage train_main_model \
  --force \
  --submit-mode-train pbs \
  --submit-mode-uq pbs
```

## 验收产物

训练侧：

- `models/training_summary.json`
- `models/training_state.json`
- `models/train_main_predictions.csv`
- `models/train_aux_predictions.csv`
- `models/training_diagnostics.json`

UQ 与选点侧：

- `results/uncertainty_latest.json`
- `results/round_001_selection_summary.json`
- `results/round_001_selected_manifest.json`
- `results/pipeline_run_summary.json`

## 常见问题

1. `mace` 或 `mace_torch` 不可导入
- 先在训练环境中安装 MACE 相关依赖，再重跑 `check_environment.py --strict`。

2. GPU 不可见
- 在 GPU 节点执行，并用 `python scripts/check_environment.py --config configs/base.yaml --expect-gpu` 验证。

3. 训练命令报模型后端相关错误
- 确认 `configs/base.yaml` 中 `training.ml_model_type: MACE`。
