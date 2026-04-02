# Minimal ADL（MACE）

本目录是与 ANI 并列的 MACE 工程。

- 项目目录：`minimal_adl_ethene_butadiene_mace`
- 模型类型：`MACE`
- 训练环境：`ADL_MACE`

## 1. 环境准备

```bash
cd /share/home/Chenlehui/work/test_ADL/minimal_adl_ethene_butadiene_mace
conda activate ADL_MACE
python -m pip install -r requirements.txt
python -m pip install mace-torch
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
```

## 6. 文档

- [../docs/mace/MACE_RUNBOOK.md](../docs/mace/MACE_RUNBOOK.md)
- [../docs/common/环境配置.md](../docs/common/环境配置.md)
