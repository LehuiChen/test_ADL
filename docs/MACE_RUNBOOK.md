# MACE 运行手册（并列工程）

本文档对应目录：`D:/#sustech_work/work/adl25-main/minimal_adl_ethene_butadiene_mace`

## 1. 环境准备

### 1.1 进入项目

```bash
cd D:/#sustech_work/work/adl25-main/minimal_adl_ethene_butadiene_mace
```

### 1.2 安装/检查依赖

建议在训练环境中保证以下依赖可用：

- `mlatom`
- `torch`
- `mace` 或 `mace_torch`
- `xtb`（命令可见）
- 若 target 使用 Gaussian：`g16` 命令可见

执行严格检查：

```bash
python scripts/check_environment.py --config configs/base.yaml --strict
```

可选联通测试：

```bash
python scripts/check_environment.py --config configs/base.yaml --strict --test-mlatom-xtb
```

GPU 节点可额外检查：

```bash
python scripts/check_environment.py --config configs/base.yaml --strict --expect-gpu
```

## 2. 最小联通测试

只跑前两阶段，验证配置和路径正确：

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --to-stage sample_initial_geometries \
  --submit-mode-labels local \
  --submit-mode-train local \
  --submit-mode-uq local
```

如果要连同标注前置一起验证：

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --to-stage build_delta_dataset \
  --submit-mode-labels local \
  --submit-mode-train local \
  --submit-mode-uq local
```

## 3. 完整第一轮

### 3.1 Local 模式

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --submit-mode-labels local \
  --submit-mode-train local \
  --submit-mode-uq local
```

### 3.2 PBS 模式

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --submit-mode-labels pbs \
  --submit-mode-train pbs \
  --submit-mode-uq pbs
```

## 4. 断点续跑 / 强制重跑

从训练主模型开始续跑：

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --from-stage train_main_model \
  --submit-mode-train pbs \
  --submit-mode-uq pbs
```

只跑到训练诊断导出：

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --to-stage export_training_diagnostics \
  --submit-mode-labels pbs \
  --submit-mode-train pbs
```

强制从训练阶段重跑：

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --from-stage train_main_model \
  --force \
  --submit-mode-train pbs \
  --submit-mode-uq pbs
```

## 5. 结果产物与验收清单

### 5.1 models/

- `models/training_summary.json`
- `models/training_state.json`
- `models/training_split.json`
- `models/train_main_predictions.csv`
- `models/train_aux_predictions.csv`
- `models/train_main_history.json`
- `models/train_aux_history.json`
- `models/training_diagnostics.json`

### 5.2 results/

- `results/check_environment_latest.json`
- `results/uncertainty_latest.json`
- `results/round_001_selection_summary.json`
- `results/round_001_selected_manifest.json`
- `results/pipeline_run_summary.json`

### 5.3 验收建议

- `check_environment --strict` 通过
- `train_main_model` 与 `evaluate_uncertainty` 阶段成功
- `round_001_selection_summary.json` 生成且包含 `selected_sample_ids`

## 6. 常见错误与处理

### 6.1 依赖缺失（mace / mlatom / torch）

症状：`check_environment --strict` 失败。
处理：在训练环境安装缺失依赖后重试。

### 6.2 GPU 不可见

症状：`--expect-gpu` 下 `torch.cuda.is_available() = False`。
处理：切换到 GPU 节点，确认驱动与 CUDA 运行时可用。

### 6.3 模型类型不匹配

症状：训练阶段报后端类型错误。
处理：确认 `configs/base.yaml` 中 `training.ml_model_type: MACE`。
