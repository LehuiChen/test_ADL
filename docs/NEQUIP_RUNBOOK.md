# NequIP 运行手册（并列工程，预留版）

本文档对应目录：`D:/#sustech_work/work/adl25-main/minimal_adl_ethene_butadiene_nequip`

当前版本目标：先完成工程位点预留与可诊断报错。

- `ml_model_type: NequIP` 可识别
- 训练后端未实现时会抛出明确 `NotImplementedError`

## 1. 环境准备

### 1.1 进入项目

```bash
cd D:/#sustech_work/work/adl25-main/minimal_adl_ethene_butadiene_nequip
```

### 1.2 检查依赖

```bash
python scripts/check_environment.py --config configs/base.yaml --strict
```

如果你计划继续实现 NequIP adapter，建议提前安装：

```bash
pip install nequip
```

## 2. 最小联通测试（前置阶段）

验证到 delta 数据集构建为止：

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --to-stage build_delta_dataset \
  --submit-mode-labels local \
  --submit-mode-train local \
  --submit-mode-uq local
```

## 3. 训练阶段预期行为（未实现提示）

```bash
python scripts/train_main_model.py --config configs/base.yaml --submit-mode local
```

预期：抛出 `NotImplementedError`，提示需实现 NequIP adapter。

这一步用于验证“可识别 + 清晰失败”，避免静默失败或难定位错误。

## 4. 完整第一轮命令模板（待 NequIP 训练实现后使用）

### 4.1 Local 模式模板

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --submit-mode-labels local \
  --submit-mode-train local \
  --submit-mode-uq local
```

### 4.2 PBS 模式模板

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --submit-mode-labels pbs \
  --submit-mode-train pbs \
  --submit-mode-uq pbs
```

## 5. 断点续跑 / 强制重跑

从训练阶段开始（当前用于验证预留行为）：

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --from-stage train_main_model \
  --submit-mode-train local \
  --submit-mode-uq local
```

强制重跑：

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --from-stage train_main_model \
  --force \
  --submit-mode-train local \
  --submit-mode-uq local
```

## 6. 结果产物与当前验收点

当前可验收产物（训练前置阶段）：

- `data/processed/delta_dataset.npz`
- `data/processed/delta_dataset_metadata.json`
- `results/check_environment_latest.json`
- `results/pipeline_run_summary.json`

训练阶段当前验收点：

- 触发 `NotImplementedError` 信息明确
- 错误信息包含下一步实现建议

## 7. 常见错误与处理

### 7.1 `NotImplementedError` 是否正常？

是正常行为。当前版本就是预留实现位点。

### 7.2 NequIP 安装后仍无法训练

仅安装依赖不代表后端实现已完成。
需要继续补 `DeltaMLModel` 中的训练/预测适配逻辑。

### 7.3 会影响 ANI / MACE 吗？

不会。三个工程目录与产物完全隔离。
