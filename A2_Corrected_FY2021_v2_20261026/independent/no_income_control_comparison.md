# 不含 Income_Group 的旧/新 Validation 候选控制核验

核验时间：2026-10-26T11:34:32.429992+08:00。容差：1e-12。只读源码常量和保存的 Validation 候选表；没有拟合、没有读取/额外评价 Test 预测。

## 结果

当前配对候选总数 **102**；实际数值/配置不一致 **0**。

| Model | 从原/新 source SPECIFICATIONS 独立识别的无 income 规格 | OLD/NEW 候选 | 三项指标最大绝对差 | 结论 |
| --- | --- | --- | --- | --- |
| Multinomial Logistic Regression | core_linear | 2/2 | Macro_F1=0.0; Weighted_F1=0.0; Accuracy=0.0 | PASS |
| LDA | core_linear, extended_no_income_group | 4/4 | Macro_F1=0.0; Weighted_F1=0.0; Accuracy=0.0 | PASS |
| kNN | core_linear, extended_no_income_group | 36/36 | Macro_F1=0.0; Weighted_F1=0.0; Accuracy=0.0 | PASS |
| SVM | core | 24/24 | Macro_F1=0.0; Weighted_F1=0.0; Accuracy=0.0 | PASS |
| Decision Tree | core_linear, extended_no_income_group | 36/36 | Macro_F1=0.0; Weighted_F1=0.0; Accuracy=0.0 | PASS |

## 方法与范围

- R parser 读取旧 original_sources 与新 root Rmd 的 chunks，仅在干净 base environment 中计算定义 core/extended/SPECIFICATIONS 的常量 c()/list() assignments。两版 specification dictionaries 必须逐项相等，随后按是否包含 Income_Group 识别 controls；没有硬编码 no-income spec 名单或候选总数。
- 在每个 control specification 内按原 hyperparameter 配置 keys 对齐，检查配置集合和唯一性。比较 Macro_F1/Weighted_F1/Accuracy 的实际数值，逐项要求 absolute difference ≤1e-12；CSV 保存双方值、差、配对配置和 PASS。
- Seconds/Search_Seconds/Fit_seconds/Predict_seconds 等计时字段分开放入 CSV 的 Old_Timing_Fields/New_Timing_Fields，不用其相等作为通过条件；并行/机器负载可改变耗时。
- Logistic MAXIT 上限250→2000及新增收敛 gate 属获准修正；本检查确认两个 no-income 候选在 OLD 和 NEW 均 convergence=0。没有声称恢复或核对未保存的逐次优化轨迹。
- 包含 Income_Group 的规格被明确排除；该组受映射更新影响，score 变化属于预期，不能算作本 preservation control 失败。
- 相同 controls 的 Validation 结果支持本次实际执行未意外改变无 income 流程；不替代独立的 source AST、split/cap identity、完整 metric 或外推有效性检查。

## 可复查来源

### Multinomial Logistic Regression

源文件：01_MultinomialLogisticRegression.Rmd；无 income features：`{"core_linear": ["Age", "Age_missing", "Gender", "Marital", "Education", "SocialClass", "IncomeBracket"]}`。
OLD table：`C:\Users\Saberken\Documents\ChatGPT\5003_A1_A2\audit_20261024_01\runs\pass1_logistic\audit_ranking.csv`；SHA-256：`e14bc10b5a2a5eb539840baa37f20c25cacf147e53a18ce97bc1880e9b3527a7`。
NEW table：`C:\Users\Saberken\Documents\ChatGPT\5003_A1_A2\STAT5003_A2_Corrected_FY2021_v2_20261026\results\logistic\audit_ranking.csv`；SHA-256：`e3c0acadf6c704c239c842591fc13e3fef5f56b3056b919cce3dc821d09e52ec`。

### LDA

源文件：02_LDA.Rmd；无 income features：`{"core_linear": ["Age", "Age_missing", "Gender", "Marital", "Education", "SocialClass", "IncomeBracket"], "extended_no_income_group": ["Age", "Age_missing", "Gender", "Marital", "Education", "SocialClass", "IncomeBracket", "HouseholdSize", "HouseholdSize_missing", "Children", "Children_missing", "Savings"]}`。
OLD table：`C:\Users\Saberken\Documents\ChatGPT\5003_A1_A2\audit_20261024_01\runs\pass1_lda\audit_validation_results.csv`；SHA-256：`cdc7f28704ad7d81c685af38df5d16e3ed6e76f66a332af97c61caa7124dfdf1`。
NEW table：`C:\Users\Saberken\Documents\ChatGPT\5003_A1_A2\STAT5003_A2_Corrected_FY2021_v2_20261026\results\lda\audit_validation_results.csv`；SHA-256：`609743123d6489f2d2fefedae4771efb3df368b211917342a774854be613cf5a`。

### kNN

源文件：03_kNN.Rmd；无 income features：`{"core_linear": ["Age", "Age_missing", "Gender", "Marital", "Education", "SocialClass", "IncomeBracket"], "extended_no_income_group": ["Age", "Age_missing", "HouseholdSize", "HouseholdSize_missing", "Children", "Children_missing", "Gender", "Marital", "Education", "SocialClass", "IncomeBracket", "Savings"]}`。
OLD table：`C:\Users\Saberken\Documents\ChatGPT\5003_A1_A2\audit_20261024_01\runs\pass2_knn\audit_ranking.csv`；SHA-256：`cb30e6c29ae86cfa001fa49045335af56c54cf5d71fd2775eafd81de32b46c6b`。
NEW table：`C:\Users\Saberken\Documents\ChatGPT\5003_A1_A2\STAT5003_A2_Corrected_FY2021_v2_20261026\results\knn\audit_ranking.csv`；SHA-256：`1f1ee240efb7dfb9bcb41d048f38c9d14a7252da6c81afbc279583111dc1f6a3`。

### SVM

源文件：04_SVM.Rmd；无 income features：`{"core": ["Age", "Gender", "Marital", "Education", "SocialClass", "IncomeBracket"]}`。
OLD table：`C:\Users\Saberken\Documents\ChatGPT\5003_A1_A2\audit_20261024_01\runs\pass1_svm_with_raw\svm_results\validation_candidates.csv`；SHA-256：`4aab0a9ee597d105908bc3f2669377ed35dbba188ef73e5240e2665ebec16682`。
NEW table：`C:\Users\Saberken\Documents\ChatGPT\5003_A1_A2\STAT5003_A2_Corrected_FY2021_v2_20261026\results\svm\svm_results\validation_candidates.csv`；SHA-256：`4d35aaa56f1b849222292b37bf8c444e692325afb5f21f5fdaca474e32f39765`。

### Decision Tree

源文件：05_DecisionTree.Rmd；无 income features：`{"core_linear": ["Age", "Age_missing", "Gender", "Marital", "Education", "SocialClass", "IncomeBracket"], "extended_no_income_group": ["Age", "Age_missing", "HouseholdSize", "HouseholdSize_missing", "Children", "Children_missing", "Gender", "Marital", "Education", "SocialClass", "IncomeBracket", "Savings"]}`。
OLD table：`C:\Users\Saberken\Documents\ChatGPT\5003_A1_A2\audit_20261024_01\runs\pass1_tree\audit_ranking.csv`；SHA-256：`3c223cbd6dcb29e506f34ca7520bdc06f0e24fa111111488607a5a9f29bb242b`。
NEW table：`C:\Users\Saberken\Documents\ChatGPT\5003_A1_A2\STAT5003_A2_Corrected_FY2021_v2_20261026\results\tree\audit_ranking.csv`；SHA-256：`6491b7d66d4ce4ee5100b90d9dd03a9e538b7d0814bced59786c13cffaa71b60`。
