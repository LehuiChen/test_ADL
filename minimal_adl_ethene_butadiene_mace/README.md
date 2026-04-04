# Minimal ADL (MACE)

Project directory: `minimal_adl_ethene_butadiene_mace`

Backend summary:

- backend: `MACE`
- training env: `ADL_MACE`
- training / MD device: CPU only
- workflow: `TS seed + bidirectional MD + stop on first uncertain point`

## Quick Start

```bash
python scripts/check_environment.py --config configs/base.yaml --strict
python scripts/check_environment.py --config configs/base.yaml --strict --test-mlatom-xtb
python scripts/run_first_round_pipeline.py \
  --config configs/base.yaml \
  --submit-mode-labels pbs \
  --submit-mode-train pbs \
  --submit-mode-md pbs
```

## Important Notes

- The authoritative seed file is `geometries/ture_seed/TS.log`.
- MACE stays CPU-only in this repository.
- Use `environment.cpu.yml` and `scripts/install_mace_deps_stepwise.sh` for the training environment.
- Use a separate analysis environment for notebooks and plotting.

## More Detail

- [环境配置](../docs/mace/环境配置.md)
- [训练流程](../docs/mace/训练流程.md)
- [结果说明](../docs/mace/结果说明.md)
- [数据分析 notebook](../docs/mace/数据分析.ipynb)
- [顶层新手流程](../训练总流程_新手详细版.md)
