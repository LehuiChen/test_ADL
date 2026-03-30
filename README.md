# Minimal Active Delta-Learning for Ethene + 1,3-Butadiene

这是一个面向教学、复现和第一轮上手的最小版 ADL 仓库。它围绕 `ethene + 1,3-butadiene` 体系，保留一条尽量短但能真正闭环的主动 delta-learning 主线：

- `baseline`: `GFN2-xTB`
- `target`: Gaussian `wB97X-D/6-31G*`
- 主模型: `ANI`
- 学习目标:
  - `delta_E = E_target - E_baseline`
  - `delta_F = F_target - F_baseline`

这份仓库现在的目标不只是“第一轮能跑通”，而是“跑完就能直接分析和汇报”。

## 推荐入口
第一次接触这个项目，建议按下面顺序看：

1. [minimal_adl_ethene_butadiene/README.md](./minimal_adl_ethene_butadiene/README.md)
2. [docs/流程介绍.md](./docs/流程介绍.md)
3. [docs/AIQM_FIRST_ROUND_RUNBOOK.md](./docs/AIQM_FIRST_ROUND_RUNBOOK.md)
4. [docs/数据分析.ipynb](./docs/数据分析.ipynb)
5. [docs/AIQM_FIRST_ROUND_RESULT_SUMMARY.md](./docs/AIQM_FIRST_ROUND_RESULT_SUMMARY.md)

- `流程介绍` 适合第一次读懂整个项目在做什么、每一步为什么存在、核心文件分别负责什么。
- `数据分析` 适合分析本次或后续轮次跑出来的结果，默认围绕回归任务组织，并会自动识别最新轮次、汇总历史轮次。
- `AIQM_FIRST_ROUND_RUNBOOK` 适合在服务器上按标准路径实际执行。

## 这次升级后的主线能力
当前推荐主线位于 [minimal_adl_ethene_butadiene](./minimal_adl_ethene_butadiene/)，已经升级为“可复跑、可分析、可汇报”的第一轮流程：

- 新增一键主控脚本 `scripts/run_first_round_pipeline.py`
- 保留现有单阶段脚本，便于局部重跑和排错
- 训练后自动补齐 notebook 默认需要的分析产物
- `docs/数据分析.ipynb` 默认直接读取标准输出路径
- 缺失可选文件时 notebook 会清晰降级，而不是整本报错

## 一键跑第一轮
在服务器仓库根目录更新代码后，进入子项目目录执行：

```bash
cd /share/home/Chenlehui/work/test_ADL/minimal_adl_ethene_butadiene
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --submit-mode-labels pbs       --submit-mode-train pbs       --submit-mode-uq pbs
```

如果你想先插入一个小规模联通检查，再跑完整主线：

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --submit-mode-labels pbs       --submit-mode-train pbs       --submit-mode-uq pbs       --with-smoke-tests
```

这个主控脚本固定编排以下阶段：

1. `check_environment`
2. `sample_initial_geometries`
3. `initial_selection`
4. `run_xtb_labels`
5. `run_target_labels`
6. `build_delta_dataset`
7. `train_main_model`
8. `train_aux_model`
9. `export_training_diagnostics`
10. `evaluate_uncertainty`
11. `select_round_001`

它默认启用 `resume`，如果某阶段已有成功产物，会自动跳过；也支持 `--from-stage`、`--to-stage` 和 `--force` 做局部重跑。

## 跑完之后会多出哪些标准分析产物
升级后，第一轮训练和 UQ 完成后会统一输出这些标准文件：

`models/`

- `training_summary.json`
- `training_state.json`
- `training_split.json`
- `train_main_predictions.csv`
- `train_aux_predictions.csv`
- `train_main_history.json`
- `train_aux_history.json`
- `training_diagnostics.json`

`results/`

- `uncertainty_latest.json`
- `round_001_selection_summary.json`
- `round_001_selected_manifest.json`
- `active_learning_round_history.json`
- `pipeline_run_summary.json`
- `check_environment_latest.json`

其中：

- `predictions.csv` 负责逐样本误差分析
- `history.json` 负责训练曲线
- `training_diagnostics.json` 负责告诉 notebook 应该默认读哪些文件
- `pipeline_run_summary.json` 负责记录主控流程的阶段状态

## 如何分析结果
升级后的 notebook 位于 [docs/数据分析.ipynb](./docs/数据分析.ipynb)。

它默认围绕四个问题组织：

1. 数据长什么样
2. 模型训练得顺不顺
3. 模型预测得准不准
4. 模型为什么这样预测

标准路径下，优先直接读取：

- `models/train_main_history.json`
- `models/train_main_predictions.csv`
- `models/training_summary.json`
- `results/uncertainty_latest.json`
- `results/active_learning_round_history.json` 或 `results/round_*_selection_summary.json`

如果你的服务器产物路径和标准路径一致，通常不需要先手改 notebook 顶部 `CONFIG`。

## 环境说明
当前 `base.yaml` 里的 PBS 默认环境名仍然是 `ADL_env`，用于训练、标注和 UQ 主流程。  
如果你只是在服务器上打开分析 notebook，可以继续使用单独的 `data_env`。也就是说：

- 训练、标注、UQ：默认按 `conda activate ADL_env`
- notebook 分析与可视化：可以使用 `conda activate data_env`

依赖方面，`minimal_adl_ethene_butadiene/requirements.txt` 已补充 `seaborn`，这样 notebook 在常规环境下可以直接绘图；如果服务器环境里暂时没有 `seaborn`，notebook 也会自动降级到 `matplotlib` 风格继续运行。

## 仓库里还有什么
历史参考目录仍然保留，但当前不作为新手主入口：

- `adl/`
- `static/`

它们更适合对照论文思路，不建议第一次复现时直接从里面继续开发。

## 集群同步建议
推荐在服务器上保留完整仓库 clone，而不是只拷贝子目录。标准更新流程是：

```bash
cd /share/home/Chenlehui/work
git clone https://github.com/LehuiChen/test_ADL.git
cd test_ADL
git status
```

以后本地推送新版本后，服务器统一这样更新：

```bash
cd /share/home/Chenlehui/work/test_ADL
git pull --ff-only
cd /share/home/Chenlehui/work/test_ADL/minimal_adl_ethene_butadiene
```

## 论文来源

- Yaohuang Huang, Yi-Fan Hou, Pavlo O. Dral. *Active delta-learning for fast construction of interatomic potentials and stable molecular dynamics simulations*. Mach. Learn.: Sci. Technol. 2025.
- ChemRxiv 预印本: [10.26434/chemrxiv-2024-fb02r](https://doi.org/10.26434/chemrxiv-2024-fb02r)
- MLatom 官方仓库: [dralgroup/mlatom](https://github.com/dralgroup/mlatom)
