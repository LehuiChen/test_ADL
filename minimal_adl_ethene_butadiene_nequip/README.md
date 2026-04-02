# Minimal ADL（NequIP 占位）

本目录是与 ANI / MACE 并列的 NequIP 预留工程。

- 项目目录：`minimal_adl_ethene_butadiene_nequip`
- 模型类型：`NequIP`
- 训练环境：`ADL_NequIP`
- 当前阶段：训练后端未实现（占位）

## 1. 环境准备

```bash
cd /share/home/Chenlehui/work/test_ADL/minimal_adl_ethene_butadiene_nequip
conda activate ADL_NequIP
python -m pip install -r requirements.txt
python -m pip install nequip
```

## 2. 训练前门禁测试（必须先跑）

```bash
python scripts/check_environment.py --config configs/base.yaml --strict
python scripts/check_environment.py --config configs/base.yaml --strict --test-mlatom-xtb
```

## 3. 最小联通测试（前置阶段）

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --to-stage build_delta_dataset \
  --submit-mode-labels local \
  --submit-mode-train local \
  --submit-mode-uq local
```

## 4. 训练阶段预期行为

```bash
python scripts/train_main_model.py --config configs/base.yaml --submit-mode local
```

预期结果：明确抛出 `NotImplementedError`，提示需要先实现 NequIP adapter。

## 5. 文档

- [../docs/nequip/NEQUIP_RUNBOOK.md](../docs/nequip/NEQUIP_RUNBOOK.md)
- [../docs/common/环境配置.md](../docs/common/环境配置.md)
