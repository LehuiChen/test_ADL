# Git 版本管理指南

这份说明是专门给这个项目准备的，重点是两件事：

- 如何安全回退
- 如何给项目打版本标签并在 GitHub 上发版

下面的命令默认都在仓库根目录运行。

## 1. 日常最常用流程

先看当前状态：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' status
```

把改动加入暂存区：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add .
```

提交：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' commit -m "说明你这次改了什么"
```

推送到 GitHub：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' push
```

看提交历史：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' log --oneline --decorate --graph -n 20
```

## 2. 回退前，先分清你现在处于哪一种情况

Git 回退不是只有一种操作。

你要先判断：

1. 改动还没 `add`
2. 已经 `add` 但还没 `commit`
3. 已经 `commit` 但还没 `push`
4. 已经 `push` 到 GitHub

这四种情况，推荐命令不一样。

## 3. 还没 add：撤销工作区改动

如果你改坏了某个文件，但还没 `git add`，可以恢复到上一次提交的版本：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' restore 路径\文件名
```

例如：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' restore minimal_adl_ethene_butadiene\configs\base.yaml
```

如果想恢复整个仓库里所有未暂存改动：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' restore .
```

注意：

- 这会丢掉你还没提交的修改。
- 所以执行前最好先 `git status` 看清楚。

## 4. 已经 add 但还没 commit：取消暂存

如果你已经 `git add` 了，但发现不想提交：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' restore --staged 路径\文件名
```

取消整个暂存区：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' restore --staged .
```

这一步只会把文件从“已暂存”变回“未暂存”，不会删除你实际写的代码。

## 5. 已经 commit 但还没 push：回退最近一次提交

### 保留改动，回到“已暂存”状态

如果你只是想重写提交说明或把这次提交拆开：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' reset --soft HEAD~1
```

效果：

- 最后一次 commit 被撤销
- 文件改动还在
- 而且保留在暂存区

### 保留改动，回到“未暂存”状态

如果你想重新整理代码再提交：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' reset HEAD~1
```

效果：

- 最后一次 commit 被撤销
- 文件改动还在
- 但不再处于暂存区

### 不推荐初学者直接用

```powershell
& 'C:\Program Files\Git\cmd\git.exe' reset --hard HEAD~1
```

这个会直接丢掉你的代码改动。除非你非常确定，否则先不要用。

## 6. 已经 push 到 GitHub：优先用 revert

如果提交已经推到 GitHub，最安全的做法通常不是 `reset`，而是新建一个“反向提交”：

先看历史：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' log --oneline --decorate -n 20
```

找到想撤销的提交，比如：

```text
8610a24 Add minimal ADL teaching workflow project
```

执行：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' revert 8610a24
```

效果：

- Git 会新建一个提交
- 这个新提交会把目标提交的改动反向撤销
- 历史仍然是完整可追踪的

然后再推送：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' push
```

这是团队协作里最稳的方式。

## 7. 如果只是想临时回到旧版本看一眼

可以先查看历史：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' log --oneline --decorate --graph -n 20
```

假设你想暂时切到旧提交：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' checkout 8610a24
```

这时你会进入“detached HEAD”状态，适合查看代码，不适合长期开发。

看完再回主分支：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' checkout main
```

## 8. 推荐的版本号规则

建议你从最简单的语义化版本开始：

- `v0.1.0`
- `v0.2.0`
- `v0.3.0`

一个实用习惯是：

- `v0.1.0`：第一版能跑通“几何 -> 标注 -> delta 数据集”
- `v0.2.0`：第一版能跑通“训练 + 不确定性”
- `v0.3.0`：第一版能跑通最小主动学习循环

如果是中间实验版，也可以用：

- `v0.1.0-alpha`
- `v0.1.0-beta`

## 9. 如何打标签

先确认工作区是干净的：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' status
```

然后创建带说明的标签：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' tag -a v0.1.0 -m "First runnable minimal ADL workflow"
```

查看本地标签：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' tag
```

把标签推到 GitHub：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' push origin v0.1.0
```

如果想一次推送所有标签：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' push origin --tags
```

## 10. 如何在 GitHub 上发 Release

推送标签之后：

1. 打开你的 GitHub 仓库
2. 进入 `Releases`
3. 点击 `Draft a new release`
4. 选择刚才的 tag，比如 `v0.1.0`
5. 填写标题和说明

建议 Release 标题写得直白一点，例如：

- `v0.1.0 - Initial runnable delta dataset workflow`
- `v0.2.0 - Add main/aux model training`
- `v0.3.0 - Add minimal active learning loop`

## 11. 常用组合场景

### 场景 A：刚改坏了一个文件，但还没提交

```powershell
& 'C:\Program Files\Git\cmd\git.exe' restore 路径\文件名
```

### 场景 B：刚提交了，但提交说明写错了，而且还没 push

```powershell
& 'C:\Program Files\Git\cmd\git.exe' reset --soft HEAD~1
& 'C:\Program Files\Git\cmd\git.exe' commit -m "新的提交说明"
```

### 场景 C：已经 push 了，发现一个提交有问题

```powershell
& 'C:\Program Files\Git\cmd\git.exe' log --oneline -n 20
& 'C:\Program Files\Git\cmd\git.exe' revert 提交号
& 'C:\Program Files\Git\cmd\git.exe' push
```

### 场景 D：准备做一个阶段性发布

```powershell
& 'C:\Program Files\Git\cmd\git.exe' status
& 'C:\Program Files\Git\cmd\git.exe' tag -a v0.1.0 -m "First runnable minimal ADL workflow"
& 'C:\Program Files\Git\cmd\git.exe' push origin v0.1.0
```

## 12. 对这个项目的建议

对这个最小 ADL 项目，我建议这样打版本：

- `v0.1.0`
  - 标注工作流打通
  - 可以构建 delta 数据集
- `v0.2.0`
  - 主模型和辅助模型训练打通
- `v0.3.0`
  - 最小主动学习循环打通
- `v0.4.0`
  - PBS 集群运行说明完善
  - README 和文档完善

## 13. 最后一个重要提醒

初学阶段，优先使用：

- `git status`
- `git log --oneline`
- `git restore`
- `git revert`

谨慎使用：

- `git reset --hard`
- 强制推送 `git push --force`

如果你不确定，就先不要删历史，优先保留历史再修正。
