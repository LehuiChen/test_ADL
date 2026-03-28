# AIQM 集群第一轮运行手册

这份手册对应当前仓库中的推荐主线：

- 项目目录：`minimal_adl_ethene_butadiene/`
- 体系：`ethene + 1,3-butadiene`
- `baseline`：`GFN2-xTB`
- `target`：Gaussian `wB97X-D/6-31G*`
- 主模型：`ANI`
- 默认训练环境名：`ADL_env`

当前最推荐的方式不是手工逐条敲完整阶段命令，而是：

1. 先完成环境自检
2. 再运行 `run_first_round_pipeline.py`
3. 跑完直接打开 `docs/数据分析.ipynb`

---

## 0. 进入项目目录

```bash
cd /share/home/Chenlehui/work/test_ADL/minimal_adl_ethene_butadiene
pwd
```

---

## 1. 训练主流程使用 `ADL_env`

训练、标注、UQ 和主控脚本都默认走 `ADL_env`。先进入训练环境：

```bash
source ~/.bashrc
conda activate ADL_env
```

---

## 2. 如果只做分析，再准备 `data_env`

`docs/数据分析.ipynb` 的绘图和表格分析推荐放在 `data_env`。如果这个环境里还没有绘图库，可以先补最常缺的 `seaborn`：

```bash
source ~/.bashrc
conda activate data_env
python -m pip install "seaborn>=0.12"
```

如果 `data_env` 里还缺 `pandas`、`matplotlib` 或 `scikit-learn`，再按报错补装即可。这样 notebook 在服务器上就不会再因为缺 `seaborn` 而直接报错。

---

## 3. 加载系统程序路径

```bash
source /share/apps/gaussian/g16-env.sh
source /share/env/ips2018u1.env
source ~/.bashrc
conda activate ADL_env
export PATH=/share/apps/gaussian/g16:/share/pubbin:/share/home/Chenlehui/bin:/share/apps/xtb-6.7.1/xtb-dist/bin:$PATH
export dftd4bin=/share/apps/dftd4-3.5.0/bin/dftd4
```

基础检查：

```bash
which python
python --version
which xtb
xtb --version
which g16
```

---

## 4. 先做环境自检

```bash
conda activate ADL_env
python scripts/check_environment.py --config configs/base.yaml --strict
python scripts/check_environment.py --config configs/base.yaml --strict --test-mlatom-xtb
```

如果你已经进入 GPU 节点，再继续：

```bash
python scripts/check_environment.py --config configs/base.yaml --strict --expect-gpu
```

自检报告会写到：

- `results/check_environment_latest.json`

---

## 5. 一键跑完整第一轮

推荐命令：

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --submit-mode-labels pbs       --submit-mode-train pbs       --submit-mode-uq pbs
```

如果你是第一次在当前机房跑，建议先插入 smoke test：

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --submit-mode-labels pbs       --submit-mode-train pbs       --submit-mode-uq pbs       --with-smoke-tests
```

这个主控脚本会顺序执行：

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

阶段状态会写到：

- `results/pipeline_run_summary.json`

---

## 6. 如何恢复执行

`run_first_round_pipeline.py` 默认启用 `resume`，如果标准产物已存在，会自动跳过已完成阶段。

常见用法：

从训练阶段继续往后跑：

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --from-stage train_main_model       --submit-mode-train pbs       --submit-mode-uq pbs
```

强制重跑训练及之后阶段：

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --from-stage train_main_model       --force       --submit-mode-train pbs       --submit-mode-uq pbs
```

只想跑到诊断产物导出为止：

```bash
python scripts/run_first_round_pipeline.py       --config configs/base.yaml       --to-stage export_training_diagnostics       --submit-mode-labels pbs       --submit-mode-train pbs
```

---

## 7. 如果你仍然需要单阶段命令
主控脚本不会废弃原有脚本。如果你要排错，仍然可以单独运行：

```bash
python scripts/sample_initial_geometries.py --config configs/base.yaml

python scripts/active_learning_loop.py       --config configs/base.yaml       --manifest data/raw/geometry_pool_manifest.json       --mode initial-selection       --round-index 0

python scripts/run_xtb_labels.py       --config configs/base.yaml       --manifest data/raw/initial_selection_manifest.json       --submit-mode pbs

python scripts/run_target_labels.py       --config configs/base.yaml       --manifest data/raw/initial_selection_manifest.json       --submit-mode pbs

python scripts/build_delta_dataset.py       --config configs/base.yaml       --manifest data/raw/initial_selection_manifest.json

python scripts/train_main_model.py       --config configs/base.yaml       --submit-mode pbs

python scripts/train_aux_model.py       --config configs/base.yaml       --submit-mode pbs

python scripts/export_training_diagnostics.py       --config configs/base.yaml

python scripts/evaluate_uncertainty.py       --config configs/base.yaml       --manifest data/raw/geometry_pool_manifest.json       --submit-mode pbs

python scripts/active_learning_loop.py       --config configs/base.yaml       --manifest data/raw/geometry_pool_manifest.json       --mode next-round       --uncertainty results/uncertainty_latest.json       --round-index 1
```

---

## 8. 跑完以后该检查哪些文件

训练相关：

- `models/training_summary.json`
- `models/training_state.json`
- `models/training_split.json`
- `models/train_main_predictions.csv`
- `models/train_aux_predictions.csv`
- `models/train_main_history.json`
- `models/train_aux_history.json`
- `models/training_diagnostics.json`

结果相关：

- `results/uncertainty_latest.json`
- `results/round_001_selection_summary.json`
- `results/round_001_selected_manifest.json`
- `results/pipeline_run_summary.json`

快速检查：

```bash
ls models
ls results
cat results/pipeline_run_summary.json
cat models/training_diagnostics.json
```

---

## 9. 如何打开分析 notebook

跑完以后直接打开：

- `docs/数据分析.ipynb`

如果服务器上已经有 Jupyter：

```bash
cd /share/home/Chenlehui/work/test_ADL
conda activate data_env
jupyter lab
```

标准路径下，这个 notebook 默认会优先读取：

- `minimal_adl_ethene_butadiene/models/train_main_history.json`
- `minimal_adl_ethene_butadiene/models/train_main_predictions.csv`
- `minimal_adl_ethene_butadiene/models/training_summary.json`
- `minimal_adl_ethene_butadiene/results/uncertainty_latest.json`
- `minimal_adl_ethene_butadiene/results/round_001_selection_summary.json`

如果这些文件都在标准位置，通常不需要先改 `CONFIG`。

---

## 10. 常见排错命令

查看主控流程状态：

```bash
cat results/pipeline_run_summary.json
```

查看最近训练状态：

```bash
cat models/train_main_status.json
cat models/train_aux_status.json
```

查看最近 UQ 状态：

```bash
cat results/uncertainty_status.json
```

查看 PBS 日志：

```bash
find labels -name stdout.log | tail
find labels -name stderr.log | tail
find models/jobs -name stdout.log | tail
find models/jobs -name stderr.log | tail
find results/jobs -name stdout.log | tail
find results/jobs -name stderr.log | tail
```

查看当前 PBS 作业：

```bash
qstat -u $USER
```

---

## 11. 当前这版主线最重要的变化

与之前相比，当前版本多了三件非常关键的事情：

- notebook 缺 `seaborn` 时不再直接崩掉
- 训练阶段会统一导出逐样本预测、split 和 history 占位文件
- 第一轮现在可以通过一个主控脚本完成，而不必手工管理所有阶段
