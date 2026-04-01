# Minimal ADL (NequIP Backend Placeholder)

这个目录是与 ANI / MACE 并列的 NequIP 预留工程。

当前状态：

- 项目名: `minimal_adl_ethene_butadiene_nequip`
- 配置可识别: `training.ml_model_type: NequIP`
- 训练后端状态: 预留中（尚未实现）

也就是说，数据生成、标注、delta 数据集构建等前置阶段可继续复用，训练阶段会给出明确 `NotImplementedError` 提示。

## Quick Start

### 1. 进入目录

```bash
cd D:/#sustech_work/work/adl25-main/minimal_adl_ethene_butadiene_nequip
```

### 2. 环境检查

```bash
python scripts/check_environment.py --config configs/base.yaml --strict
```

### 3. 最小联通测试（只跑前几阶段）

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --to-stage build_delta_dataset \
  --submit-mode-labels local \
  --submit-mode-train local \
  --submit-mode-uq local
```

### 4. 预期验证（训练阶段会明确提示未实现）

```bash
python scripts/train_main_model.py --config configs/base.yaml --submit-mode local
```

预期行为：抛出 `NotImplementedError`，提示需先实现 NequIP adapter，而不是出现模糊的底层报错。

## 后续实现入口

NequIP 真正落地时，优先补这三个位置：

- `src/minimal_adl/delta_model.py`
- `src/minimal_adl/training.py`
- `src/minimal_adl/uncertainty.py`

实现目标：

- 主模型训练（delta_E + delta_F）
- 辅助模型训练（delta_E）
- 与现有 UQ、选点与产物格式兼容

## 常见问题

1. 为什么配置识别了 NequIP 仍不能训练？
- 这是当前阶段的设计目标：先完成工程位点预留与清晰报错，再做后端实现。

2. 是否会影响 ANI / MACE 项目？
- 不会。三个目录互相隔离，数据与结果不会混用。
