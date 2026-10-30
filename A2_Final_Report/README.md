# A2 Final Report (W08G03)

| 文件 | 说明 |
|---|---|
| `STAT5003_A2_W08G03_Report.Rmd` | 报告源文件（R Markdown，代码默认折叠） |
| `STAT5003_A2_W08G03_Report.html` | 提交用的单文件 HTML（self-contained） |
| `supplementary/svm_linear_vs_rbf_validation_per_class.csv` | §7.2 的 validation-only linear vs RBF SVM 逐类结果 |
| `supplementary/reproducibility_check.csv` | 全量重跑（五个模型的调参搜索 + 最终重拟合）与冻结 v2 预测的逐行比对 |

## 放置位置

把整个 `A2_Final_Report/` 文件夹放在仓库根目录，与 `A2_Corrected_FY2021_v2_20261026/` 同级（报告通过 `../A2_Corrected_FY2021_v2_20261026` 读取数据、调参表和逐行预测）。需要先 `git lfs pull`，确保两个 CSV 和 `results/svm/svm_results/final_evaluation.rds` 是真实文件而非 LFS 指针。

## 渲染

在 RStudio 打开 Rmd 直接 Knit，或：

```r
rmarkdown::render("STAT5003_A2_W08G03_Report.Rmd")
```

默认约 1 分钟：所有图表和数字都从冻结的 v2 数据、调参表和逐行 Test 预测**现场重算**（输入 MD5 校验、划分重建并与 v2 记录逐行比对）。

所需包：`rmarkdown`、`knitr`、`ggplot2`、`patchwork`（`data.table` 可选，用于加速读 CSV）。

可选参数：

* `params = list(refit = "fast")`：重跑 LR / LDA / kNN / Tree 的完整 validation 搜索与最终重拟合（需 `nnet`、`MASS`、`FNN`、`rpart`）；
* `params = list(refit = "all")`：再加上 SVM（需 `e1071`，约 1 小时）；
* `params = list(run_probes = TRUE)`：重算 §7.2 的 linear vs RBF SVM 检查（约 3 分钟）。

重跑结果会替换冻结结果参与绘图，并写入 `supplementary/reproducibility_check.csv`。

## 页数

用 Chromium 打印成 PDF 的结果：A4 页边距 1 cm 为 8 页，A4 或 Letter 页边距 2 cm 为 9 页；即使按屏幕样式转换（显示 Show 按钮）、页边距 2 cm，也是 10 页。折叠的代码在打印时不显示。

## 复现核验（2026-10-30）

在 R 4.3.3 / Linux 上用 `refit = "all"` 从头重跑了五个模型的全部 validation 搜索和最终重拟合（原始运行环境为 R 4.6.1 / Windows）。结果：所有 validation 分数差异在 3e-05 以内，选出的配置完全相同，五个模型的 19,201 条 Test 预测全部逐行一致。详见 `supplementary/reproducibility_check.csv`。
