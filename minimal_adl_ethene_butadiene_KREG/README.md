# Minimal ADL (KREG)

Project directory: `minimal_adl_ethene_butadiene_KREG`

Backend summary:

- backend: `KREG`
- training env: `ADL_KREG`
- training device: `cuda` (GPU queue)
- label device: CPU (`xTB` + `Gaussian`)
- workflow: `TS seed + bidirectional MD + stop on first uncertain point`

## Quick Start

```bash
python scripts/check_environment.py --config configs/base.yaml --strict
python scripts/check_environment.py --config configs/base.yaml --strict --test-mlatom-xtb
python scripts/active_learning_loop.py \
  --config configs/base.yaml \
  --submit-mode-labels pbs \
  --submit-mode-train pbs \
  --submit-mode-md pbs
```

## Important Notes

- The authoritative seed file is `geometries/ture_seed/TS.log`.
- KREG labels remain CPU tasks, while training / uncertainty / MD sampling jobs are submitted to the GPU queue.
- KREG with `training.device=cuda` must show real GPU usage in training status files, otherwise training is marked failed.
- `active_learning_loop.py` is now the recommended one-command multi-round experiment entry.
- By default, all returned uncertain points are kept for relabeling unless you explicitly pass `--max-new-points`.
- The KREG backend comes from MLatom and does not need a separate `torchani` or `mace` package.
- Use a separate analysis environment for notebooks and plotting.

## More Detail

- [环境配置](../docs/kreg/环境配置.md)
- [训练流程](../docs/kreg/训练流程.md)
- [结果说明](../docs/kreg/结果说明.md)
- [数据分析 notebook](../docs/kreg/数据分析.ipynb)
- [顶层新手流程](../训练总流程_新手详细版.md)
