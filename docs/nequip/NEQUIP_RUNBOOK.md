# NequIP 运行手册（预留版）

对应工程：`minimal_adl_ethene_butadiene_nequip`
训练环境：`ADL_NequIP`

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

GPU 节点可附加：

```bash
python scripts/check_environment.py --config configs/base.yaml --strict --expect-gpu
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

## 4. 预期行为验证（训练占位）

```bash
python scripts/train_main_model.py --config configs/base.yaml --submit-mode local
```

预期结果：抛出明确的 `NotImplementedError`，提示 NequIP adapter 尚未实现。

## 5. 断点续跑 / 强制重跑

前置阶段可正常使用：

```bash
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --from-stage sample_initial_geometries \
  --to-stage build_delta_dataset \
  --force \
  --submit-mode-labels local
```

## 6. 当前验收标准

- `check_environment --strict` 通过
- 前置数据阶段可跑通到 `build_delta_dataset`
- 触发训练时出现预期未实现提示（而不是误导性底层错误）
