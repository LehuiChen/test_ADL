# AIQM 集群第一轮结果总结

本总结对应 `minimal_adl_ethene_butadiene/` 在 AIQM 集群上的第一次完整闭环运行，时间为
`2026-03-25` 到 `2026-03-26`。

## 1. 实验设置

- 体系：`ethene + 1,3-butadiene`
- baseline：`GFN2-xTB`
- target：`wB97X-D/6-31G*`
- 主模型：`ANI`
- 训练设备：`cuda`
- 环境：`ADL_env`
- 兼容栈：`Python 3.10 + PyTorch 1.12.0 + cudatoolkit 11.3 + TorchANI 2.2`

## 2. 第一轮实际执行结果

### 数据与选点

- 初始几何池：`400`
- 第 0 轮初始样本：`250`
- 成功构建 delta 数据集：`250` 个样本

### 标注与训练

- `xTB` smoke test：通过
- Gaussian smoke test：通过
- 完整批次 `xTB` 标注：完成
- 完整批次 Gaussian 标注：完成
- 主模型训练：成功
- 辅助模型训练：成功
- 不确定性评估：成功，输出样本数 `400`

### 第 1 轮不确定性筛选结果

- `uq_threshold`：`0.008694517682910009`
- 剩余候选池样本数：`150`
- 高不确定性样本数：`5`
- 第 1 轮实际新增样本数：`5`
- 高不确定性比例：`0.03333333333333333`
- 收敛判断：`True`

这表示当前最小版第一轮主动学习闭环已经满足设定的收敛条件：

- 收敛阈值：新增高不确定性点比例 `< 5%`
- 本次结果：`3.33%`

## 3. 第 1 轮新增样本

本轮选出的 5 个样本为：

1. `geom_0128`
2. `geom_0087`
3. `geom_0316`
4. `geom_0389`
5. `geom_0054`

对应摘要文件位于：

- `results/round_001_selection_summary.json`
- `results/round_001_selected_manifest.json`

## 4. 关键输出文件

本轮最关键的产物包括：

- 几何池：`data/raw/geometry_pool_manifest.json`
- 第 0 轮初始样本：`data/raw/initial_selection_manifest.json`
- delta 数据集：`data/processed/delta_dataset.npz`
- delta 数据集元数据：`data/processed/delta_dataset_metadata.json`
- 主模型状态：`models/train_main_status.json`
- 辅助模型状态：`models/train_aux_status.json`
- 主模型文件：`models/delta_main_model.pt`
- 辅助模型文件：`models/delta_aux_model.pt`
- 不确定性结果：`results/uncertainty_latest.json`
- 第 1 轮选点摘要：`results/round_001_selection_summary.json`

## 5. 本轮过程中已修复的关键工程问题

这次第一轮不是一次无障碍跑通，中间定位并修复了几类关键问题：

1. 环境与版本兼容
   - 固定 `torch==1.12.0`
   - 使用 `python -m pip install mlatom --no-deps`
   - 兼容 `mlatom` 对旧版 `torch.load` 的调用差异

2. `MLatom + xTB` 接口问题
   - 避免 `GFN2-xTB` 走通用接口时触发不必要的 `PySCF` 依赖

3. PBS / Gaussian 环境问题
   - 修正 PBS 环境块中的 YAML 命令解析
   - 兼容 `g16-env.sh` / `ips2018u1.env` 在非交互 shell 下的返回码
   - 收紧 `GAUSS_SCRDIR` 清理逻辑

4. Gaussian 输入关键字问题
   - 将论文写法 `wB97X-D/6-31G*` 自动规范化为 Gaussian 可识别的 `wB97XD/6-31G*`

5. 训练后处理问题
   - 修复 `main-only training` 结束时误用旧 `aux_model` 进行 UQ 后处理，导致状态文件报错的问题

6. 集群提交策略问题
   - 保留了当前这次运行结果
   - 仓库后续默认已改为 worker 模式，避免再次一次性提交 `500` 个 PBS 小作业

## 6. 当前结论

对于“在 AIQM 集群上跑通最小版 ADL 第一轮闭环”这个目标，本次结果可以判定为：

- 环境：通过
- 标注：通过
- 训练：通过
- 不确定性评估：通过
- 第 1 轮选点：通过
- 收敛：已达到

也就是说，这个最小版项目已经在目标集群上完成了第一轮可复现验证。

## 7. 下一步建议

如果只以“最小版第一轮复现成功”为目标，到这里可以收口。

如果需要继续扩展，可以考虑：

1. 对这 5 个新增样本继续做第二轮标注与重训，作为额外验证
2. 固定一个 Git tag，保留当前可复现版本
3. 继续把 worker 调度、训练资源、日志汇总做得更自动化
