# STAT5003 A2 FY2021 更正版 v2

这是2026-10-26新建的独立实验目录。原仓库、旧审计结果和共享CSV保留原样，没有提交或推送GitHub。

## 六份新版源文件

根部的baseline及01至05六份Rmd是更正后的版本；original_sources是更正前原像。变更包括：

- 收入映射统一为FY2021：MDV→Upper-middle、ROU→High、UKR→Lower-middle、TWN→High、VEN→Upper-middle。NIR保留明确的英国High继承假设。
- Logistic迭代上限从250提高至2000；候选和final非收敛时立即停止，避免继续生成正式Test结论。
- 对应的映射说明与Legacy历史结果标识。

其他算法、函数、特征构造、候选网格、种子、划分、权重及排名规则不变。FY2021_crosswalk.json逐项记录66个code和官方单元格。运行时六份Rmd仍使用相同内嵌WB_GROUPS，以保持原代码结构；修改JSON不会自动改变Rmd。

详见MAPPING_CHANGES.md、LOGISTIC_OPTIMISATION_CHANGES.md及environment/source_changes.diff。R原生AST检查仅允许上述白名单差异。

## 结果与证据

先阅读reports/STAT5003_A2_CORRECTED_V2_REPORT.md或同内容HTML。阶段报告会明确标记Pending；最终以六份正式执行完成后的报告为准。

- model_comparison.csv：本轮指标与相对本轮majority/Logistic的差值。
- old_vs_new_comparison.csv：旧版到新版的绝对变化和预测变化。
- per_class_comparison.csv：八类support、predicted count、precision、recall、F1。
- split_integrity_report.csv：行身份、标签、种子、数据散列核验。
- results/各模型目录：冻结Rmd副本、HTML、模型输出、运行环境、包清单、执行状态。
- execution_logs及independent：日志、独立confusion/metrics/bootstrap和专项核查。
- diagnostics：Logistic训练/验证与final优化预检，没有Test预测或评分。

源Rmd中明确标为Legacy pre-correction的旧解释仅用于溯源，不是本轮成绩。请使用本轮新生成的表、预测和报告，不要复制Legacy数字作为新版结论。

每份Rmd本轮只做一次正式完整渲染。Logistic预检不是五模型第二轮Test复现。

## 数据与环境

根部cleaned CSV未改，95,987×519；SHA-256为ee392676dbb42dde0ea74ebf643862f3900e7d13a7aa03842ed2d7665ac98ee0，MD5为98bf573170f0cb6bd65a4e9a8070d4d8。raw CSV只供SVM默认missingness审查使用。

R4.6.1；rmarkdown2.32、knitr1.52、nnet7.3-20、MASS7.3-65、rpart4.1.27、ggplot2 4.0.3、FNN1.1.4.1、e1071 1.7-17。九个关键包的版本、build、library路径与旧审计一致，见environment/package_comparison_vs_audit.json。

自动化脚本记录本机R/Pandoc和原审计隔离库绝对路径。跨机器需准备相同包环境并调整工具路径；Rmd自身保留原相对路径规则。组员使用时应确保CSV已实际下载，SVM的raw审查依赖已准备。

## 使用入口

用rmarkdown::render渲染，不要将Rmd直接当R脚本。自动化入口要求新的结果标签，拒绝覆盖旧输出：

```powershell
$v2Root = (Get-Location).Path
$env:LC_ALL = 'C'
& 'C:\Program Files\R\R-4.6.1\bin\Rscript.exe' --vanilla .\scripts\render_one.R $v2Root new_logistic_check 01_MultinomialLogisticRegression.Rmd
```

以下复核只读取已保存结果，不重新拟合模型：

```powershell
python .\scripts\verify_v2_sources.py
python .\scripts\evaluate_v2.py
& 'C:\Program Files\R\R-4.6.1\bin\Rscript.exe' --vanilla .\scripts\verify_v2_runtime.R $v2Root
python .\scripts\build_v2_report.py --html
```

本轮仍使用已经曝光的同一Test集，是透明记录的实验更正，不是新的未见holdout。Logistic同时改变映射和优化，分数差不能只归因于一项。评阅ZIP省略大型CSV、R库和RDS模型；完整文件保留在此目录。
