# Minimal ADL（MACE）

工程目录：`minimal_adl_ethene_butadiene_mace`  
模型类型：`MACE`  
环境名：`ADL_MACE`

当前默认主线已经与 `minimal_adl_ethene_butadiene` 对齐，只保留模型后端差异：

`TS.log -> TS seed -> Round 0 初始条件 -> 标注 -> 训练 -> 双向 MD -> 首个不确定点返回 -> 去重筛选`

这意味着：

- 不再使用旧的静态 `400` 点随机扰动几何池。
- 不再先保存整条轨迹的所有帧再事后筛选。
- 现在是每条轨迹一旦遇到首个 `UQ > threshold` 的结构，就立刻停下并把这个点送回重标注。

## 当前默认设置

- Round 0：`200` 个 TS 初始条件
- 后续每轮：`100` 个初始条件
- MD：双向 `±150 fs`
- `time_step = 0.5 fs`
- `ensemble = NVE`
- 默认计算资源：`default` 队列、`16` 核、`360:00:00`
- 默认训练设备：`cpu`

## 推荐先看

- [环境配置](D:/#sustech_work/work/adl25-main/docs/mace/环境配置.md)
- [训练流程](D:/#sustech_work/work/adl25-main/docs/mace/训练流程.md)
- [结果说明](D:/#sustech_work/work/adl25-main/docs/mace/结果说明.md)

## 核心入口脚本

- `scripts/prepare_ts_seed.py`
- `scripts/sample_ts_initial_conditions.py`
- `scripts/run_xtb_labels.py`
- `scripts/run_target_labels.py`
- `scripts/update_cumulative_manifest.py`
- `scripts/build_delta_dataset.py`
- `scripts/train_main_model.py`
- `scripts/train_aux_model.py`
- `scripts/run_md_sampling.py`
- `scripts/select_md_frames.py`
- `scripts/run_first_round_pipeline.py`

## 关键产物

- `geometries/ts_seed/TS.log`
- `geometries/ts_seed/ts_seed.json`
- `geometries/ts_seed/ts_seed.xyz`
- `results/ts_seed_summary.json`
- `results/round_000_initial_conditions_manifest.json`
- `data/processed/cumulative_labeled_manifest.json`
- `models/training_state.json`
- `results/round_001_md_frame_manifest.json`
- `results/round_001_md_trajectory_summary.json`
- `results/round_001_selection_summary.json`
- `results/active_learning_round_history.json`

## 一个关键理解

你现在要训练的不是“过渡态附近静态点云的插值器”，而是“过渡态附近以及反应通道上的局部动态 PES”。

所以 Round 0 的 `200` 个初始条件只是为了先把第一版 MACE delta model 训练出来；真正让势能面沿反应坐标扩展的，是后面双向 MD 中返回的首个不确定点，以及这些点进入下一轮重标注与重训练。
