# A2 FY2021 更正版 v2：完整运行结果

本目录是 2026-10-26 更正实验的完整发布快照，包含六份新版 Rmd、正式运行输出、预测、模型 RDS、数据、日志、独立复核与报告。原实验文件逐字节复制，仅省略 Python 自动生成的 `__pycache__` 缓存。仓库根目录的历史六份 Rmd 与共享 CSV 保留原样。

## 阅读入口

- [完整结果报告](reports/STAT5003_A2_CORRECTED_V2_REPORT.md)（[HTML](reports/STAT5003_A2_CORRECTED_V2_REPORT.html)）。
- [模型指标汇总](model_comparison.csv)、[旧版与新版比较](old_vs_new_comparison.csv)、[逐类结果](per_class_comparison.csv)、[划分与数据一致性](split_integrity_report.csv)。
- 六份当前源文件：[baseline](baseline.Rmd)、[Logistic](01_MultinomialLogisticRegression.Rmd)、[LDA](02_LDA.Rmd)、[kNN](03_kNN.Rmd)、[SVM](04_SVM.Rmd)、[Decision Tree](05_DecisionTree.Rmd)。
- [映射更正](MAPPING_CHANGES.md)、[Logistic 优化修复](LOGISTIC_OPTIMISATION_CHANGES.md)、[FY2021 映射来源](FY2021_crosswalk.json)、[原实验使用说明](README_V2.md)。
- `results/`：六次正式执行的冻结 Rmd、HTML、预测、模型对象和运行环境；`execution_logs/`：运行日志；`independent/`：独立评估与 bootstrap；`diagnostics/`：Logistic 优化预检；`source_evidence/`：来源证据；`original_sources/`：更正前 Rmd。

## 本轮更正与结果

六份 Rmd 同步使用 FY2021 映射：MDV→Upper-middle、ROU→High、UKR→Lower-middle、TWN→High、VEN→Upper-middle；TWN/VEN 使用 FY2021 引用版本。NIR 保留有明确说明的英国 High 继承假设。Logistic 的 `MAXIT` 从 250 提高到 2000，并添加非收敛停止检查；六个候选及最终模型均收敛。其余模型逻辑、候选网格、划分及种子保持原规则。

| 模型 | Test Macro F1 | Test Weighted F1 | Test Accuracy |
|---|---:|---:|---:|
| Logistic | 0.350914 | 0.471159 | 0.530858 |
| LDA | 0.340672 | 0.461671 | 0.514817 |
| kNN | 0.339867 | 0.457148 | 0.502943 |
| SVM | 0.377763 | 0.454392 | 0.462476 |
| Decision Tree | 0.335269 | 0.461998 | 0.527108 |

六份正式渲染全部成功，共用原来的 19,201 行 Test。每份 Rmd 本轮正式完整运行一次；Logistic 另有不做 Test 评分的优化预检。此实验沿用已曝光的 Test，属于透明记录的更正，不代表新的未见 holdout。Logistic 同时变更映射与优化设置，分数变化不能单独归因于其中一项。

Rmd 内标注 `Legacy pre-correction` 的历史说明只用于溯源；本轮结论以新报告和 CSV 为准。

## 下载及文件校验

大型数据和 RDS 通过 Git LFS 保存。克隆或更新仓库后，在仓库根目录执行：

```bash
git lfs install
git lfs pull
python A2_Corrected_FY2021_v2_20261026/verify_snapshot.py
```

`PUBLICATION_MANIFEST.csv` 记录除清单自身以外的本目录发布文件大小及 SHA-256。`verify_snapshot.py` 只读取文件并验证清单、六次执行状态及原始交付清单，不重新训练模型，也不要求本机保留旧审计目录。GitHub 网页和普通 source ZIP 中的 LFS 文件可能只是指针，应通过 Git LFS 获取实际内容。

## 历史审计记录与复现路径

本次 Git 发布发生在实验和审计结束之后。保留的 `README_V2.md` 中“没有提交或推送 GitHub”、`DELIVERABLE_CHECKS.json` 中原仓库未改动，以及报告中的旧 HEAD/工作区检查，均描述**运行当时**的状态。它们不描述发布后的仓库；这次发布新增本目录并更新根 README。

原 `scripts/verify_v2_sources.py` 等脚本包含旧仓库 HEAD、原隔离审计和本机绝对路径断言，保留以供溯源，不能直接当作跨机器发布校验。发布文件完整性请使用上面的 `verify_snapshot.py`。自动化复现实验前，需根据 `environment/` 的 R/包版本记录准备环境，并调整原脚本中的 R、Pandoc、隔离库和旧审计路径；源 Rmd 保留原相对数据路径。完整原始、cleaned CSV 均已随此目录提供。
