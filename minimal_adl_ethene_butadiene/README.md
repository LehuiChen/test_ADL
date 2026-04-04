# Minimal ADL (ANI)

Project directory: `minimal_adl_ethene_butadiene`

Backend summary:

- backend: `ANI`
- training env: `ADL_env`
- training / MD device: GPU
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
- Old `geometries/seed/` inputs have been retired.
- `active_learning_loop.py` is no longer the old static-manifest driver.
- Use a separate analysis environment for notebooks and plotting.

## More Detail

- [环境配置](../docs/ani/环境配置.md)
- [训练流程](../docs/ani/训练流程.md)
- [结果说明](../docs/ani/结果说明.md)
- [数据分析 notebook](../docs/ani/数据分析.ipynb)
- [顶层新手流程](../训练总流程_新手详细版.md)
