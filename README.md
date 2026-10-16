# STAT 5003 Assignment 2: 模型设计与实现 (Model Implementation)

## 📌 项目简介 (Project Overview)

本项目为 STAT 5003 课程的 Assignment 2 (A2) 代码仓库。本阶段的核心任务是基于我们在 Assignment 1 (A1) 阶段提交的报告文件 `EDA and Plan-1.html`，对报告最后部分 **"Model Plan"** 的延伸与具体代码实现。

我们将严格按照 A1 中的 Model Plan 设计实验，涵盖五个不同的数据处理与模型设计实验。为了保证团队协作的高效性与代码的可维护性，本项目将采用 Git 进行版本控制与迭代。

## 📂 目录结构与协作分配 (File Structure & Collaboration)

为了方便小组成员并行开发、避免代码冲突，我们的核心代码结构如下（带有数字前缀以保持目录排序整洁）：

* **`baseline.Rmd`**: 基线模型文件。包含统一的数据加载、数据清洗、预处理以及最基础的 Baseline 模型。所有其他模型都应以此为基准进行性能对比。

* **`01_LogisticRegression.Rmd`**: 模型一实验文件 (逻辑回归/线性回归等基础广义线性模型)

* **`02_DecisionTree.Rmd`**: 模型二实验文件 (决策树模型)

* **`03_RandomForest.Rmd`**: 模型三实验文件 (随机森林集成模型)

* **`04_XGBoost.Rmd`**: 模型四实验文件 (XGBoost 梯度提升树)

* **`05_SVM.Rmd`**: 模型五实验文件 (支持向量机 或根据实际情况替换为 KNN/神经网络)

**协作说明**：每位组员在负责各自的模型时，请在对应的 `.Rmd` 空白文件中进行开发。共享的数据预处理逻辑应尽量在 `baseline.Rmd` 中完善，或通过输出中间数据供各模型读取，以保证数据的一致性。

## 🔄 Git 版本迭代与协作规范 (Git Version Control Rules)

为了确保版本迭代的清晰和小组成员之间的顺利协作，请所有成员严格遵守以下 Git 规范：

### 1. 分支管理策略 (Branching Strategy)

我们采用经典的功能分支工作流 (Feature Branch Workflow)：

* **`main` 分支**: 主分支，**绝对稳定**。仅用于存放最终准备提交 (Submission) 的版本。任何人不得直接向 `main` 分支 Push 代码。

* **`dev` 分支**: 开发分支，作为日常合并的基础分支。各模型的最新进展都将合并到这里。

* **`feature/[模型名称或功能]` 分支**: 个人开发分支。

  * *示例*: `feature/baseline-setup` 或 `feature/xgboost-model`。

  * 每位成员在开始编写自己负责的模型前，必须从 `dev` 分支拉取并创建一个新的 feature 分支。

### 2. 提交流程规范 (Commit Workflow)

1. **拉取最新代码**: 每次开发前，先切换到 `dev` 分支执行 `git pull`，确保本地是最新的。

2. **创建/切换分支**: `git checkout -b feature/your-model-name`

3. **开发与提交**: 建议**小步提交 (Frequent Commits)**。完成一个特征工程、调好一组参数或跑通一个模型后，立即 Commit。

4. **推送与合并请求**: 开发完成后，将分支 Push 到远程仓库，并向 `dev` 分支发起 **Pull Request (PR)**。

5. **代码合并**: 经由至少一位其他组员 Review 并确认无误（且能成功运行）后，方可合并入 `dev` 分支。

### 3. 提交信息规范 (Commit Message Format)

提交信息必须清晰明了，采用以下前缀格式说明本次提交的目的：

* `feat:` (Feature) 新增功能或新建了某个模型的代码。*例：feat: 增加支持向量机(SVM)的初步代码*

* `fix:` (Bug Fix) 修复代码报错或逻辑 Bug。*例：fix: 修复模型二中由于缺失值导致的运行中断问题*

* `docs:` (Documentation) 仅仅修改了文档，比如 README。

* `style:` (Style) 代码格式调整（不影响代码运行逻辑的修改）。

* `refactor:` (Refactor) 代码重构（即不新增功能，也不修改 bug 的代码变动）。

* `test:` (Test) 增加或修改测试/实验对比代码。

### 4. 冲突解决规范 (Conflict Resolution)

* **隔离原则**：得益于我们为五个模型分别建立了独立的 `.Rmd` 文件，大部分情况下不会产生严重的合并冲突。

* **公共文件修改**：如果需要修改公共文件（如 `baseline.Rmd`），请务必提前在小组群内沟通。

* **处理冲突**：如果在合并 PR 时出现冲突，提交者需要在本地将 `dev` 分支 merge 到自己的 feature 分支，手动解决冲突，测试通过后再推送到远程。

## 🚀 实验计划 (Experiment Plan)

本项目将严格落实 A1 (`EDA and Plan-1.html`) 报告中的 Model Plan，具体包括五个模型实验的：

1. **特征选择与处理**: 基于基线数据进行针对特定模型的特征工程。

2. **模型训练与调参**: 使用交叉验证 (Cross-Validation) 等方法寻找最优超参数。

3. **模型评估与对比**: 统一使用准确率、F1-Score、RMSE 等指标（视具体任务而定）与 `baseline.Rmd` 结果进行对比。

*Happy Coding! 祝 W08G03 小组 A2 顺利高分通过！*