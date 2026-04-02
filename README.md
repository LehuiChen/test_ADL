# Minimal Active Delta-Learning (ANI / MACE / NequIP)

这是一个面向教学与复现的最小版 ADL 仓库，提供三个并列工程：

- ANI：`minimal_adl_ethene_butadiene`
- MACE：`minimal_adl_ethene_butadiene_mace`
- NequIP（预留）：`minimal_adl_ethene_butadiene_nequip`

三套工程数据与产物目录互相隔离，便于并行测试和后续扩展。

## 1. 文档入口

- 文档总索引：[docs/README.md](./docs/README.md)
- 环境配置（重点）：[docs/common/环境配置.md](./docs/common/环境配置.md)
- ANI 文档入口：[docs/ani/README.md](./docs/ani/README.md)
- MACE 文档入口：[docs/mace/README.md](./docs/mace/README.md)
- NequIP 文档入口：[docs/nequip/README.md](./docs/nequip/README.md)

## 2. 三模型环境约定

- ANI：`conda activate ADL_env`
- MACE：`conda activate ADL_MACE`
- NequIP：`conda activate ADL_NequIP`

三个工程的 `configs/base.yaml` 已分别设置对应 `cluster.conda_env`。

## 3. 训练前统一门禁（强约定）

进入对应子项目目录后，先执行：

```bash
python scripts/check_environment.py --config configs/base.yaml --strict
python scripts/check_environment.py --config configs/base.yaml --strict --test-mlatom-xtb
```

通过后再执行主流程。

## 4. 快速运行（示例）

### 4.1 ANI

```bash
cd /share/home/Chenlehui/work/test_ADL/minimal_adl_ethene_butadiene
conda activate ADL_env
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --submit-mode-labels pbs \
  --submit-mode-train pbs \
  --submit-mode-uq pbs
```

### 4.2 MACE

```bash
cd /share/home/Chenlehui/work/test_ADL/minimal_adl_ethene_butadiene_mace
conda activate ADL_MACE
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --submit-mode-labels pbs \
  --submit-mode-train pbs \
  --submit-mode-uq pbs
```

### 4.3 NequIP（当前阶段）

```bash
cd /share/home/Chenlehui/work/test_ADL/minimal_adl_ethene_butadiene_nequip
conda activate ADL_NequIP
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --to-stage build_delta_dataset \
  --submit-mode-labels local
```

NequIP 当前为占位版本：训练阶段会给出明确 `NotImplementedError`。

## 5. 关于 docs 与 tmp

- `docs/` 已按 `ani/mace/nequip/common` 重整，旧路径保留兼容跳转页。
- `tmp/` 是临时工作目录，已在 `.gitignore` 忽略，不是正式产物目录。

## 6. 论文来源

- Yaohuang Huang, Yi-Fan Hou, Pavlo O. Dral. *Active delta-learning for fast construction of interatomic potentials and stable molecular dynamics simulations*. Mach. Learn.: Sci. Technol. 2025.
- ChemRxiv: [10.26434/chemrxiv-2024-fb02r](https://doi.org/10.26434/chemrxiv-2024-fb02r)
- MLatom: [dralgroup/mlatom](https://github.com/dralgroup/mlatom)
