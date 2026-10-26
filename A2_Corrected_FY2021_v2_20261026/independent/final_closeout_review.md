# v2 最终收尾只读一致性复核

日期：2026-10-26（Asia/Shanghai）。结论：**Ready，可打包交付；未发现需修正的实际不一致。**

本次仅阅读最终报告、已有 CSV/JSON 与正式状态，不运行模型、评价器、报告 builder 或新的数值测试；没有修改源码、报告或主审计脚本。它是交付前的一致性检查，不冒称新增一次模型复现或对全部指标作再次独立计算。

复核报告：`reports/STAT5003_A2_CORRECTED_V2_REPORT.md`，生成时间 2026-10-26T12:01:16.241528+08:00，SHA-256 `dd75f2d265433c524d6bcf43472902a1b7402934be39bd82df1a4495c62be155`。

- 六份正式 render 的实际状态均为 Success。SVM 的 saved execution status 显示 2,944.10 秒、Error=null、Source_Unchanged_During_Render=true，与报告表一致。
- `model_comparison.csv` 中 SVM Macro F1 为 **0.3777627809101025**，Logistic 为 **0.3509141767975126**；报告六位小数分别写 0.377763 与 0.350914，吻合。SVM−Logistic 为 **0.026848604112589936**，与 bootstrap 表及主性能表一致。
- Logistic saved final convergence code 为 **0**；validity matrix 的六候选 convergence 全零与 final code=0 相符。报告同时说明 2000 是 iteration ceiling，而非每次实际迭代次数，不把收敛视为假设正确的证据。
- `evaluation_summary.json` 的 Issues 为空，`evaluation_issues.csv` 仅有表头；原计算、身份、split、实际 map、源码未变等 verification statuses 与报告的已核实表述相符。
- Bootstrap summary 为 **5,000 replicates、11 pairs、evaluation seed20261026**，CSV 包含4组新模型对新Logistic、7组旧新配对；报告按 conditional fitted-model uncertainty 解读，保留 iid/country-cluster/训练选优/多重比较与不能因果拆分两项修正的限制。此次没有重新抽样计算。
- 全部 `Repeat_V2_Execution_Verified=false`，summary 的 `V2_Repeated_Execution_Claimed=false`；报告开头、限制及最终附录均明确 v2 每份只有一次正式运行。训练/验证 preflight 没有被混称为第二遍 Test 复现。
- source-preservation evidence `environment/all_six_source_contract.json` 为 PASS，最终报告附录准确限定获准更改为 FY2021 map、显示文字及 Logistic MAXIT/收敛 gates。102 个无 income Validation control 的三项最大差均为0，作为既有只读证据引用，未拿 income-containing score 的预期变化当成逻辑错误。
- 原仓库/原像/旧审计主要交付物保持不变的结论与最终 source contract 一致。旧固定结果在源 Rmd 标为 Legacy，报告以本轮新输出为准，没有混贴旧 SVM 分数。

最终报告的 **Ready with minor corrections** 是对当前 v2 整合可用性的判断，仍保留单次运行、单一固定 split、既有 holdout exposure 和 A1 历史预处理等研究局限；没有读到与这些边界矛盾的过度声明。
