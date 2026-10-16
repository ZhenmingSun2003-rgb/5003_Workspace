# STAT5003 Assignment 2｜小组建模与协作说明

> **W08G03 小组内部使用**  
> 为了方便大家并行完成 A2，我把 A1 的提交报告、处理好的数据集和各个模型的 `.Rmd` 文件整理到了同一个仓库。这份 README 简单介绍一下文件结构和协作方式，方便大家随时查看。

## 1. 项目内容

A2 主要延续我们在 **A1 报告中的 Model Plan**，在清理好的 **WVS Wave 7** 数据基础上，分别开展模型训练、实验设计、调参与结果分析。

目前已经为五个模型分别准备了独立的 `.Rmd` 文件。**大家直接在自己负责的文件中开展实验就好**，这样可以同时推进，也能尽量减少彼此之间的代码冲突。

## 2. 仓库文件一览

| 文件 | 主要用途 |
| --- | --- |
| `README.md` | 当前这份项目与协作说明 |
| `A1_Submission_EDA and Plan-1.html` | A1 提交报告，可参考 EDA 和最后的 Model Plan |
| `WVS_Wave7_cleaned_for_modelling.csv` | 已经清理好的共享数据集，供各模型读取 |
| `baseline.Rmd` | 共享的 Baseline 参考，方便后续比较模型表现 |
| `01_LogisticRegression.Rmd` | Logistic Regression 实验 |
| `02_DecisionTree.Rmd` | Decision Tree 实验 |
| `03_RandomForest.Rmd` | Random Forest 实验 |
| `04_XGBoost.Rmd` | XGBoost 实验 |
| `05_SVM.Rmd` | SVM 实验 |
| `.gitattributes` | Git LFS 的文件追踪配置 |

A1 报告和清理好的 CSV 都已经上传，大家可以直接从现有材料开始，不必重复准备数据。模型文件前面的数字只是为了让目录更整齐，并不代表需要按顺序完成。

## 3. 各自的模型实验

每位组员主要维护自己负责的 `.Rmd` 文件。实验设计、模型需要的预处理、训练与调参、性能评估、图表及结果解释，都可以直接放在这个文件里。

有几个小建议，希望能方便我们后续整合：

- **尽量保持共享 CSV 不变。** 如果模型需要不同的编码、标准化或特征选择，直接在自己的 Rmd 中处理即可，不需要修改原始数据文件。
- **使用相对路径读取数据**，例如 `read.csv("WVS_Wave7_cleaned_for_modelling.csv")`，这样其他人拉取仓库后也能运行。
- **记录关键实验设置**，如随机种子、数据划分、参数和评估指标，方便复现与比较。
- **参考 A1 的 Model Plan 和共享 Baseline**。如果实验需要调整共同的数据划分或比较口径，我们可以先在群里简单商量一下。

不需要为了完成自己的模型而修改其他成员的 Rmd；如果发现公共数据或 Baseline 有需要调整的地方，也欢迎直接在群里提出来，我们一起确认。

## 4. Git 协作：直接在 main 更新

为了让协作流程简单一些，**这次大家直接使用现有的 `main` 分支即可，不需要另外创建分支或 Pull Request**。因为每个模型都有独立文件，只要提交时注意文件范围，基本就能各自推进。

推荐的操作流程如下（以 XGBoost 为例）：

**开始前，先同步一下仓库**（本地尚无未提交的修改时）：

```bash
git switch main
git pull --ff-only origin main
```

完成一部分实验后，先确认有哪些文件发生了变化：

```bash
git status
```

**只添加自己负责的文件**，再提交并推送：

```bash
git add 04_XGBoost.Rmd
git commit -m "feat(xgboost): 添加初步模型实验"
git pull --rebase origin main
git push origin main
```

把示例中的文件名替换成自己负责的 `.Rmd` 即可。建议完成一小部分功能或实验就提交一次，后面回看版本也会更方便。

为了避免不小心把公共文件或临时结果一起上传，提交时尽量使用 `git add 文件名`，而不是直接 `git add .`。如果 Push 时遇到冲突，先不要强制覆盖，发到群里一起看看就好。

## 5. 关于 CSV 和 Git LFS

由于清理后的 CSV 文件比较大，我使用了 **Git LFS（Git Large File Storage）** 来上传。

简单来说，CSV 的实际内容存放在 Git LFS 存储中，普通 Git 历史主要保存指向该文件版本的指针；`.gitattributes` 则用于指定哪些文件通过 Git LFS 追踪，**它并不直接控制 CSV 的生命周期**。

如果本地还没有配置 Git LFS，需要先安装 Git LFS，然后在仓库中运行：

```bash
git lfs install
git lfs pull
```

之后就可以正常读取 CSV 进行实验了。**CSV 和 `.gitattributes` 暂时都请尽量保持原样**；如果后续确实需要更新数据版本，我们先统一讨论，避免大家使用不同的数据进行训练。

## 6. 后续实验与结果整合

各模型可以有不同的实验思路，但为了让最终对比更清晰，希望大家尽量以同一份数据为基础，并说明自己模型中额外做了哪些处理。

我们的数据涉及类别不平衡，因此模型评估时除了 Accuracy，也可以结合 Macro-F1、Balanced Accuracy 等合适的指标，具体以 A1 Model Plan 和小组最终讨论为准。

现阶段大家先专注于把各自负责的模型**跑通、解释清楚并保留可复现的实验过程**。等各部分有了结果，再一起整理模型对比和 A2 报告。

---

感谢大家一起推进！如果在数据、Baseline、Git 操作或实验设计上遇到问题，直接在群里交流就好。希望这套结构能让每个人都更方便地开展自己的部分，也让我们最后整合时少一些重复工作。
