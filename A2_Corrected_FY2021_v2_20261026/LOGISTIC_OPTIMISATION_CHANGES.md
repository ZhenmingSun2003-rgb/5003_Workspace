# Logistic iteration-only correction and convergence gates

2026-10-26。工作范围仅为本新目录的 `01_MultinomialLogisticRegression.Rmd` 及诊断文件；旧仓库、旧审计目录、`original_sources/` 和共享CSV均不修改。

原审计已验证：旧版6候选中 `extended_quadratic_age / decay=0.001` 返回 convergence=1；原winner候选收敛，但完整80% final refit 返回 convergence=1。因此旧版渲染成功不能证明最终充分优化。

本修订的建模设置只把 `MAXIT <- 250L` 提高为 `MAXIT <- 2000L`。模型仍为 `nnet::multinom`，原三套formulas × 两个decay值、MaxNWts=10000、DEV_CAP=25000（实际24996）、seeds5003/5005/5006、同一CSV和split、numeric recipe、类别levels、Validation ranking/tie-break均保留。没有以Test score选择iteration上限、公式或decay。

候选非零/不可用convergence现在立即停止，不能进入validation scoring或selection；6候选汇总后额外要求全部convergence=0。final refit非零/不可用convergence立即停止，不能产生Test预测和评分。

Income_Group另按本次共同FY2021契约改动5个国家：MDV→Upper-middle、ROU→High、UKR→Lower-middle、TWN→High、VEN→Upper-middle；NIR仍为明确的UK→High假定；WB_GROUPS的Unclassified为空，但CATEGORY_KEYS原level保留。它与iteration修订是两种同时记录的变化，不能把最终分数变化单独归因于其中之一。

诊断通过 `scripts/run_logistic_preflight.R` 从新版01提取原setup/country-map/preprocessing/evaluation/validation代码，并提取final-fit到收敛门槛，删除Test preprocessing及其后Test prediction/scoring。生成的 `diagnostics/Logistic_Preflight.Rmd` 用真正的 `rmarkdown::render()` 执行。额外trace原`predict.multinom`，只允许19,199-row Validation输入，记录所有调用，禁止19,201-row Test预测。诊断不改原fit settings、不再选择超参数，也不生成Test metrics。

## Preflight verified result and frozen official source

`rmarkdown::render()` 已成功完成，MAXIT=2000 足够，未进行任何后续迭代搜索或升级。

- 六个候选全部 `Convergence=0`，candidate fitting N=24,996；Validation N=19,199。
- 原有Validation ranking选择 `extended_linear / decay=0.01`，Validation Macro F1=0.353359398108762。这是原选择规则的结果，**没有用该分数决定MAXIT**，也没有访问Test score。
- 最终全80% fitting N=76,786，`final_fit$convergence=0`，penalised objective `final_fit$value=101183.82310294952`。
- final preprocessing/refit block=82.58秒，整个preflight render=206.89秒，无warnings/errors。
- 方法trace恰有6次预测，全部输入19,199行Validation；Test预测0次。环境中不存在 `X_test`、`predicted`、`majority_met` 或 `comparison`；静态执行代码检查也未发现Test prediction/scoring。
- 新版01的SHA-256运行前后均为 `516d23f073cfff3ded7a107a9d6cbc6904e937cf33bd470bff4789be78364141`；MD5=`942da8967e097bbbe6c381160f887ae5`。源文件、preflight Rmd和orchestration script在执行期间均未编辑。

证据包括 `diagnostics/logistic_preflight_maxit2000/preflight_status.json`、`candidate_convergence_and_validation.csv`、实际渲染的 `Logistic_Preflight.html`、完整保存环境及 `diagnostics/Logistic_Preflight_MAXIT2000.log`。预处理、评价/公式、split/cap构造、最终refit调用与原版本的逐段一致性检查保存在 `diagnostics/logistic_preserved_contract.json`，完整可review差异在 `diagnostics/logistic_source_diff.patch`。

全部66国 `country_map` 另用独立Python解析逐项核对 `FY2021_crosswalk.json`，完全一致：Low2、Lower-middle18、Upper-middle23、High23、Unclassified0；证明见 `diagnostics/logistic_mapping_equality.json`。

**官方01源文件现已冻结，准备官方render。** 上述preflight只有训练/验证及final convergence证据，不能当作官方Test性能结果；正式Test metrics必须来自之后相同冻结源文件的官方运行。
