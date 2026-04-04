# ADL25 Minimal TS-Seeded Active Learning Workflows

This repository contains three aligned minimal active-learning workflows for the ethene + 1,3-butadiene transition state:

- `minimal_adl_ethene_butadiene`: ANI backend, GPU training and GPU MD
- `minimal_adl_ethene_butadiene_mace`: MACE backend, CPU-only
- `minimal_adl_ethene_butadiene_KREG`: KREG backend, CPU-only

All three projects now share the same non-model logic:

1. Parse the authoritative TS seed from `geometries/ture_seed/TS.log`
2. Generate harmonic-quantum-Boltzmann initial conditions around the TS
3. Label round 0 with baseline (`GFN2-xTB`) and target (`Gaussian`) methods
4. Build a delta dataset and train the backend-specific model
5. Run bidirectional short NVE MD from TS initial conditions
6. Stop each trajectory at the first uncertain point
7. Deduplicate and relabel the returned uncertain points for the next round, without a default per-round hard cap

## Backend Matrix

| Backend | Project Directory | Training Env | Device |
| --- | --- | --- | --- |
| ANI | `minimal_adl_ethene_butadiene` | `ADL_env` | GPU |
| MACE | `minimal_adl_ethene_butadiene_mace` | `ADL_MACE` | CPU only |
| KREG | `minimal_adl_ethene_butadiene_KREG` | `ADL_KREG` | CPU only |

## Shared Conventions

- `minimal_adl_ethene_butadiene/geometries/ture_seed/TS.log` is the authoritative seed source.
- Each project keeps its own self-contained copy under `geometries/ture_seed/`.
- Old static seed folders such as `geometries/seed/` have been retired.
- NequIP has been removed from this repository.
- Training environments and notebook / plotting environments should stay separate.

## Where To Start

- Repository-level onboarding: [训练总流程_新手详细版](训练总流程_新手详细版.md)
- ANI docs: [环境配置](docs/ani/环境配置.md) | [训练流程](docs/ani/训练流程.md) | [结果说明](docs/ani/结果说明.md)
- MACE docs: [环境配置](docs/mace/环境配置.md) | [训练流程](docs/mace/训练流程.md) | [结果说明](docs/mace/结果说明.md)
- KREG docs: [环境配置](docs/kreg/环境配置.md) | [训练流程](docs/kreg/训练流程.md) | [结果说明](docs/kreg/结果说明.md)

## Important Outputs

Each project writes the same core artifacts, just under its own directory:

- `results/ts_seed_summary.json`
- `results/round_000_initial_conditions_manifest.json`
- `data/processed/cumulative_labeled_manifest.json`
- `data/processed/delta_dataset_metadata.json`
- `models/training_state.json`
- `results/round_001_md_sampling_status.json`
- `results/round_001_selection_summary.json`
- `results/round_001_selected_manifest.json`

## Server Refresh Pattern

After local updates are pushed to GitHub, the recommended server refresh is to delete the old checkout and reclone a clean copy:

```bash
cd /share/home/Chenlehui/work
rm -rf /share/home/Chenlehui/work/test_ADL
git clone https://github.com/LehuiChen/test_ADL.git /share/home/Chenlehui/work/test_ADL
```

Then enter the matching project directory and activate the matching conda environment before running `scripts/check_environment.py`.

For day-to-day experiments, the recommended entrypoint inside each project is:

```bash
python scripts/active_learning_loop.py \
  --config configs/base.yaml \
  --submit-mode-labels pbs \
  --submit-mode-train pbs \
  --submit-mode-md pbs
```
