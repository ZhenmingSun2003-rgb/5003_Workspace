# STAT5003 A2：FY2021 修正 v2 实验与独立核验报告

生成时间（Asia/Shanghai）：2026-10-26T12:11:39.369424+08:00。本报告由已保存的正式输出、逐行预测和独立评估生成；主版本目录为 `STAT5003_A2_Corrected_FY2021_v2_20261026`。

## 1. 执行结论

**总体判断：Ready with minor corrections：可整合 v2 正式报告，保留以下局限和提交前文字核对。**

按本次相同 Test 的 Macro F1，最高为 **SVM（0.377763）**。这是点估计排序，不能等同统计显著性、跨国家泛化或未来数据表现。

此次同时实施两项修正：六份 Rmd 的国家收入组统一改用官方 FY2021 分类；Logistic 增加优化迭代上限并在候选、选优和最终 Test 计分前强制检查 convergence。**Logistic的新旧变化不能单独归因于映射或优化；其余四模型的流程未改，新旧差异反映映射更新及其在原流程中的后续影响。相对Logistic的差值还涉及基准模型的变化。** 未为提升 Test 分数改变候选网格、选优准则、种子、训练 cap 或共享数据。

每份修改后的 Rmd 仅安排一次正式执行。Logistic 的训练/验证 preflight 不调用 Test预测或计分，不作为第二次正式评估；已有旧版重复执行证据不能替代 v2 的重复执行。本报告**不声称 v2 已经重复运行复现**。

计划交付完成性：候选表/状态证据=已核实；5000次、11组配对bootstrap及旧新身份核验=已核实。使用`--skip-bootstrap`生成的表属于预览，不能据此形成最终Ready判断。

证据等级：`Verified` 为本次运行与独立计算；`Source-checked` 为源码检查；`Author-reported` 仅指文档自述；`Unverified/Pending` 保留缺失。执行成功、指标正确、样本身份一致、优化收敛和重复执行是不同条件。

## 2. 环境与实际执行

| Rmd / 模型 | 正式状态 | 秒 | 错误 |
| --- | --- | --- | --- |
| baseline.Rmd | Success | 14.02 | — |
| 01_MultinomialLogisticRegression.Rmd | Success | 207.32 | — |
| 02_LDA.Rmd | Success | 23.81 | — |
| 03_kNN.Rmd | Success | 305.37 | — |
| 04_SVM.Rmd | Success | 2944.10 | — |
| 05_DecisionTree.Rmd | Success | 37.89 | — |

运行平台信息依据 `detected_environment.json` 和各 `results/<model>/sessionInfo.txt` / `package_manifest.csv`。Rscript：`C:\Program Files\R\R-4.6.1\bin\Rscript.exe`。包与版本以本次各运行导出为准，不能仅因沿用机器就假设版本不变。

R version 4.6.1 (2026-06-24 ucrt)；Platform: x86_64-w64-mingw32/x64；Running under: Windows 10 x64 (build 19045)

| 相关包 | v2版本 | 与旧版版本/构建/路径一致 |
| --- | --- | --- |
| rmarkdown | 2.32 | 已核实 |
| knitr | 1.52 | 已核实 |
| nnet | 7.3-20 | 已核实 |
| MASS | 7.3-65 | 已核实 |
| rpart | 4.1.27 | 已核实 |
| ggplot2 | 4.0.3 | 已核实 |
| FNN | 1.1.4.1 | 已核实 |
| e1071 | 1.7-17 | 已核实 |
| proxy | 0.4-29 | 已核实 |

独立评估运行环境：Python `3.13.7 (tags/v3.13.7:bcee1c3, Aug 14 2025, 14:15:11) [MSC v.1944 64 bit (AMD64)]`；NumPy `2.3.2`；Pandas `2.3.2`。bootstrap RNG为NumPy default_rng/PCG64，逐模型配对重置seed。

耗时包含模型搜索、最终拟合、输出及 HTML render；若同时运行，受到资源竞争影响，不构成严格的算法速度基准。对象大小不等于进程峰值内存。

## 3. 数据、种子与共享行身份

共享输入：`C:\Users\Saberken\Documents\ChatGPT\5003_A1_A2\STAT5003_A2_Corrected_FY2021_v2_20261026\WVS_Wave7_cleaned_for_modelling.csv`；95987 行。完整原始数据列数为519，模型只读取约定源列，未因映射修正增删受访者。独立数据完整性：**已核实**。

SHA-256：`ee392676dbb42dde0ea74ebf643862f3900e7d13a7aa03842ed2d7665ac98ee0`；MD5：`98bf573170f0cb6bd65a4e9a8070d4d8`。对照共享预期哈希及全部 Q279 标签，均以 `independent/evaluation_summary.json` 为准。

本次新建 reference split 与旧版不可变 reference 逐行一致：**已核实**。主数字种子5003；outer 80/20使用5003，内部75/25使用5005；baseline随机预测5004；训练 cap 抽样5006。

共享初始 Train=57,587、Validation=19,199、Test=19,201，最终80%重拟合=76,786。Logistic候选只用24,996条、SVM候选只用9,997条；两者均须来自共同初始Train。Logistic局部dev_id被cap替换，原始Train由不变Validation的补集独立恢复，不能误称共享划分不同。

| 模型 | Test行/标签 | 数字种子 | 物理CSV+MD5 | 全部所需split | 实际Income map | 本次源码未变 |
| --- | --- | --- | --- | --- | --- | --- |
| Logistic | 已核实 | 已核实 | 已核实 | 已核实 | 已核实 | 已核实 |
| LDA | 已核实 | 已核实 | 已核实 | 已核实 | 已核实 | 已核实 |
| kNN | 已核实 | 已核实 | 已核实 | 已核实 | 已核实 | 已核实 |
| SVM | 已核实 | 已核实 | 已核实 | 已核实 | 已核实 | 已核实 |
| Tree | 已核实 | 已核实 | 已核实 | 已核实 | 已核实 | 已核实 |

逐partition的实际/预期行数及有序ID SHA256见 `../split_integrity_report.csv`（27行）。计数一致不是身份一致的替代证据。

## 4. FY2021 映射、版本和修正边界

记录的原始仓库base commit：`9b3db1d3207d9af492af0099848248cee73df918`。本v2为隔离文件副本，以各Rmd SHA256及完整diff标识，不声称创建新Git commit；原始仓库状态保护以主流程manifest为准。

依据World Bank历史工作簿 `Country Analytical History` 的FY21列（AI5=FY21；AI6标注2019 GNI数据年），而不是当前年度分类。官方经济体名称为来源标签。Northern Ireland没有独立工作簿条目，按United Kingdom继承High；这项明确假设保持不变。

来源：[World Bank历史分类工作簿](https://ddh-openapi.worldbank.org/resources/DR0095334/download)、[FY2021发布说明](https://blogs.worldbank.org/en/opendata/new-world-bank-country-classifications-income-level-2020-2021)、[分类说明页](https://datahelpdesk.worldbank.org/knowledgebase/articles/906519-world-bank-country-and-lending-groups)。下载文件、哈希、官方单元格和提取记录均保存在 `../source_evidence/`，报告使用已验证的本地证据。

| 国家代码 | 旧组 | FY2021 v2 | 影响CSV行数 | 官方单元格 |
| --- | --- | --- | --- | --- |
| MDV | High | Upper-middle | 1019 | AI128 |
| ROU | Upper-middle | High | 1198 | AI167 |
| TWN | Unclassified | High | 1223 | AI197 |
| UKR | Upper-middle | Lower-middle | 1266 | AI211 |
| VEN | Unclassified | Upper-middle | 1187 | AI218 |

共改变5个代码、5893行的Income_Group值。六文件源码覆盖66代码（65条官方分类匹配，加1条NIR继承假设），一致性：**已核实**。TWN和VEN分别采用官方High与Upper-middle；Unclassified当前无国家，但保留原factor levels以避免附带改变编码契约。

Logistic MAXIT从250增加到2000，目标是达到既有优化问题的收敛条件；weight decay、三种spec、cap、Validation选优顺序保持约定。仅根据训练/验证 preflight确认迭代上限，不利用 Test 选择。

| 文件 | v2 SHA256 | 原始SHA256 |
| --- | --- | --- |
| baseline.Rmd | `8d344a2dc81a34868b81e0562a60f405c8eda3e83aa00288abc01532d8c9ab87` | `d2ce36360dfd74df07f894d04e9ace61448f9ed850543b2db9620c1e140e5efb` |
| 01_MultinomialLogisticRegression.Rmd | `516d23f073cfff3ded7a107a9d6cbc6904e937cf33bd470bff4789be78364141` | `9dc52ee768e723e349236bf4d3e16fb44b0d9f3210324ee352f3317416bec729` |
| 02_LDA.Rmd | `f2d9d22cabaa105329de1ad0688887b98749016309bbfcfc34074a5e48cc6c8f` | `d5e5e045ad62da4b31d70f567098693b81c6dd7d5aaf27410b1f20e035c2b1a1` |
| 03_kNN.Rmd | `9d228929e8887f8855a04b6dcf902c6936ec2cc1822e53ac9d7b97e216d622b0` | `e0c45c31cfacb4c1ca5c215db54d995ccd9527cb58f9cef63d7c48b11aa31a18` |
| 04_SVM.Rmd | `55a4c54dce1ae72cc1ec6b213147b9ff8677b8ccf803bf3a6ece84849eec2814` | `c420c78bd90c22ad5a6fd9d4cc66de12993463ae28373db83def9111024e07a8` |
| 05_DecisionTree.Rmd | `0f9740f70cb5222054e54db3f10056d95e2b71ba39aab09aed21cf3eb5747995` | `ed013bf1480eb9a307f44e4aa7ae50f35b47a7443be4110c18f9e41522129442` |

完整逐行diff见 `../independent/v2_source_diffs/`；这些diff是可审阅证据，不代表原始仓库被编辑。原始仓库、原CSV和 `original_sources/` 的前后保护验证由主执行流程单独保存，提交前应与其最终manifest一起核对。

## 5. 独立 Test 指标与新基准差值

从正式输出的逐行 `row_id, truth, prediction` 独立构造8×8混淆矩阵；固定上述八类顺序，缺少预测/分母为零的Precision、Recall、F1按0处理。Macro指标包含全部八类；Weighted F1用真实support加权。以下Δ均为**本次新版本Macro F1差**，不是百分比改善率。

| 模型 | 状态 | Macro F1 | Weighted F1 | Accuracy | Δ新Majority | Δ新Logistic | Validation F1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Majority | Success | 0.066749 | 0.194509 | 0.364252 | +0.000000 | -0.284165 | — |
| Prior random | Success | 0.129382 | 0.209011 | 0.209052 | +0.062633 | -0.221532 | — |
| Logistic | Success | 0.350914 | 0.471159 | 0.530858 | +0.284165 | +0.000000 | 0.353359 |
| LDA | Success | 0.340672 | 0.461671 | 0.514817 | +0.273923 | -0.010242 | 0.339464 |
| kNN | Success | 0.339867 | 0.457148 | 0.502943 | +0.273118 | -0.011047 | 0.342990 |
| SVM | Success | 0.377763 | 0.454392 | 0.462476 | +0.311013 | +0.026849 | 0.365181 |
| Tree | Success | 0.335269 | 0.461998 | 0.527108 | +0.268520 | -0.015645 | 0.339115 |

全精度数值见 `../model_comparison.csv`。Macro Precision和Macro Recall见 `../independent/all_metrics.csv`；逐类全部精度/召回/F1/support/预测数见 `../per_class_comparison.csv`；完整矩阵和少数类错误去向见 `../independent/all_confusion_matrices.csv` 与 `minority_error_flows.csv`。

独立结果与Rmd已计算输出的比较共有196项，核验表为 `../independent/metric_verification.csv`。总指标比较容差1e-12；原逐类表若四舍五入4位，容许误差至0.00005；最终排名使用独立未舍入值。

评估工具经只读同行复核，见 `../independent/evaluator_v2_peer_review.md`；数学、异常输入和Ready状态夹具已检查。同行复核时SVM尚未完成，因此不把这份阶段性复核说成对后来SVM数值的第二次独立认证；最终SVM按同一脚本正常核验。

## 6. 旧版与新版：配对变化

| 模型 | 旧Macro F1 | 新Macro F1 | Δ新−旧 | 不同Test预测数 | 配对身份 |
| --- | --- | --- | --- | --- | --- |
| Majority | 0.066749 | 0.066749 | +0.000000 | 0 | 已核实 |
| Prior random | 0.129382 | 0.129382 | +0.000000 | 0 | 已核实 |
| Logistic | 0.353107 | 0.350914 | -0.002193 | 485 | 已核实 |
| LDA | 0.340248 | 0.340672 | +0.000424 | 546 | 已核实 |
| kNN | 0.341888 | 0.339867 | -0.002020 | 1126 | 已核实 |
| SVM | 0.380130 | 0.377763 | -0.002367 | 1200 | 已核实 |
| Tree | 0.333168 | 0.335269 | +0.002101 | 568 | 已核实 |

旧分数来自旧版已核验的原始预测，并重新检查相同Test行/标签与旧CSV数值。旧Logistic最终convergence=1，其旧分数可描述既有预测，但不代表优化完成的线性基准。v2是映射与收敛控制同时变化后的总版本比较，缺少只改单项的对照组，不能作单项因果归因。

## 7. 优化、候选网格与算法限制

| 模型 | 候选数/约定数 | 已选配置 | 优化/状态证据 |
| --- | --- | --- | --- |
| Logistic | 6 / 6 | Spec=extended_linear; Decay=0.01 | 全部候选convergence=0：已核实；最终code=0 |
| LDA | 6 / 6 | Specification=extended_linear; Prior=empirical | 见运行日志、候选表和数值检查 |
| kNN | 54 / 54 | Spec=extended_linear; k=21; Weighting=distance | 见运行日志、候选表和数值检查 |
| SVM | 48 / 48 | Spec=extended; Kernel=radial; Cost=1; Gamma=0.217391304347826; Weight=inverse | 全部candidate status=ok：已核实 |
| Tree | 54 / 54 | Spec=extended_linear; cp=5e-04; maxdepth=8; minsplit=100 | 见运行日志、候选表和数值检查 |

- **Logistic：** 3 specs×2 decay=6；candidate cap24,996；最终80%重拟合必须convergence=0。收敛码通过并不证明模型假设正确，也不是统计不确定性的估计。

- **LDA：** 3 specs×2 priors=6；保留既有零方差/线性相关处理与共享协方差方法。分类类别prior和feature规格由Validation选择；连续多元正态与共同协方差仍是近似假设，分类dummy不满足严格连续正态。

- **kNN：** 3 specs×9 k×2 weighting=54；全部水平one-hot，dummy乘1/√2，类别不匹配贡献平方距离1；数值缩放仅由拟合分区估计。原平局函数保留；旧版已选distance-k21无实际tie影响的结论不能自动转移为新版结论，新版以所选参数/实际预测为准。

- **SVM：** 既有48候选，线性/radial、cost/gamma和权重规则不改；候选cap9,997；记录实际P和gamma、inverse class weights、fit状态及cache签名。新目录避免复用旧版Test输出，不能把旧缓存误记为本次完整拟合。

- **Tree：** 54候选，Gini，cp/maxdepth/minsplit按既定网格；`xval=0`，实际是单次holdout Validation，不是CV。展示用剪枝图若存在，不是正式评估模型；最终完整树和其重拟合复杂度应以本次model bundle与RUN_SUMMARY为准。

从正式导出的完整树rules独立数得：最终31节点、16叶、最大深度8；被选中的Validation拟合有21叶。两者是不同训练样本上的拟合，不能混用叶数。展示剪枝文件存在：False。

## 8. 少数类、预测分布与错误流向

| 类别 | Logistic Recall | LDA Recall | kNN Recall | SVM Recall | Tree Recall |
| --- | --- | --- | --- | --- | --- |
| Full-time | 0.7835 | 0.7358 | 0.7376 | 0.4099 | 0.7811 |
| Part-time | 0.0000 | 0.0018 | 0.0320 | 0.1300 | 0.0000 |
| Self-employed | 0.1625 | 0.1687 | 0.1778 | 0.2912 | 0.2116 |
| Retired | 0.7434 | 0.7508 | 0.7078 | 0.7939 | 0.7641 |
| Housewife | 0.6291 | 0.5844 | 0.5765 | 0.7131 | 0.5640 |
| Student | 0.6543 | 0.7190 | 0.5771 | 0.8271 | 0.7030 |
| Unemployed | 0.0873 | 0.1062 | 0.0853 | 0.2064 | 0.0000 |
| Other | 0.0000 | 0.0043 | 0.0000 | 0.1034 | 0.0000 |

| 模型 | Part-time预测数/Recall | Unemployed预测数/Recall | Other预测数/Recall |
| --- | --- | --- | --- |
| Logistic | 0 / 0.0000 | 414 / 0.0873 | 0 / 0.0000 |
| LDA | 5 / 0.0018 | 538 / 0.1062 | 6 / 0.0043 |
| kNN | 356 / 0.0320 | 460 / 0.0853 | 19 / 0.0000 |
| SVM | 1192 / 0.1300 | 1365 / 0.2064 | 507 / 0.1034 |
| Tree | 0 / 0.0000 | 0 / 0.0000 | 0 / 0.0000 |

Logistic：从不预测的类别为Part-time, Other；精确零召回类别为Part-time, Other。

LDA：从不预测的类别为无；精确零召回类别为无。

kNN：从不预测的类别为无；精确零召回类别为Other。

SVM：从不预测的类别为无；精确零召回类别为无。

Tree：从不预测的类别为Part-time, Unemployed, Other；精确零召回类别为Part-time, Unemployed, Other。

少数类旧→新变化如下；它们是整体版本变化的描述，不能从中孤立估计映射修正的作用。

| 模型 | 类别 | 旧Recall→新Recall | ΔRecall | 旧F1→新F1 | 旧预测数→新预测数 |
| --- | --- | --- | --- | --- | --- |
| Logistic | Part-time | 0.0000 → 0.0000 | +0.0000 | 0.0000 → 0.0000 | 0 → 0 |
| Logistic | Unemployed | 0.0886 → 0.0873 | -0.0014 | 0.1381 → 0.1364 | 419 → 414 |
| Logistic | Other | 0.0000 → 0.0000 | +0.0000 | 0.0000 → 0.0000 | 0 → 0 |
| LDA | Part-time | 0.0006 → 0.0018 | +0.0012 | 0.0012 → 0.0036 | 3 → 5 |
| LDA | Unemployed | 0.1076 → 0.1062 | -0.0014 | 0.1577 → 0.1558 | 538 → 538 |
| LDA | Other | 0.0043 → 0.0043 | +0.0000 | 0.0084 → 0.0084 | 6 → 6 |
| kNN | Part-time | 0.0320 → 0.0320 | +0.0000 | 0.0529 → 0.0527 | 351 → 356 |
| kNN | Unemployed | 0.0853 → 0.0853 | +0.0000 | 0.1300 → 0.1300 | 461 → 460 |
| kNN | Other | 0.0000 → 0.0000 | +0.0000 | 0.0000 → 0.0000 | 21 → 19 |
| SVM | Part-time | 0.1457 → 0.1300 | -0.0157 | 0.1679 → 0.1511 | 1217 → 1192 |
| SVM | Unemployed | 0.2064 → 0.2064 | +0.0000 | 0.2150 → 0.2146 | 1359 → 1365 |
| SVM | Other | 0.0991 → 0.1034 | +0.0043 | 0.0627 → 0.0650 | 502 → 507 |
| Tree | Part-time | 0.0000 → 0.0000 | +0.0000 | 0.0000 → 0.0000 | 0 → 0 |
| Tree | Unemployed | 0.0000 → 0.0000 | +0.0000 | 0.0000 → 0.0000 | 0 → 0 |
| Tree | Other | 0.0000 → 0.0000 | +0.0000 | 0.0000 → 0.0000 | 0 → 0 |

| 模型 | 真实少数类 | 最多的两个错误去向 |
| --- | --- | --- |
| Logistic | Part-time | Full-time: 988 (59.7% of support); Housewife: 258 (15.6% of support) |
| Logistic | Unemployed | Full-time: 636 (43.0% of support); Housewife: 245 (16.6% of support) |
| Logistic | Other | Full-time: 125 (53.9% of support); Retired: 38 (16.4% of support) |
| LDA | Part-time | Full-time: 900 (54.4% of support); Housewife: 228 (13.8% of support) |
| LDA | Unemployed | Full-time: 520 (35.2% of support); Student: 330 (22.3% of support) |
| LDA | Other | Full-time: 106 (45.7% of support); Retired: 44 (19.0% of support) |
| kNN | Part-time | Full-time: 887 (53.6% of support); Housewife: 274 (16.6% of support) |
| kNN | Unemployed | Full-time: 622 (42.1% of support); Housewife: 242 (16.4% of support) |
| kNN | Other | Full-time: 113 (48.7% of support); Retired: 40 (17.2% of support) |
| SVM | Part-time | Housewife: 345 (20.9% of support); Full-time: 269 (16.3% of support) |
| SVM | Unemployed | Student: 313 (21.2% of support); Housewife: 270 (18.3% of support) |
| SVM | Other | Retired: 42 (18.1% of support); Full-time: 36 (15.5% of support) |
| Tree | Part-time | Full-time: 980 (59.3% of support); Housewife: 215 (13.0% of support) |
| Tree | Unemployed | Full-time: 705 (47.7% of support); Student: 250 (16.9% of support) |
| Tree | Other | Full-time: 134 (57.8% of support); Retired: 38 (16.4% of support) |

零召回与从不预测必须分开：Predicted_Count>0且Recall=0意味着所有该类预测均为假阳性。类别不平衡、特征重叠、类别定义的跨国差异或算法限制是可能解释，但这里没有识别单一原因的因果设计；不能仅凭低召回指责预处理。比较precision/accuracy trade-off时应同时引用逐类表。

## 9. 评估不确定性

本次按已拟合模型做paired Test-row bootstrap，5000次，evaluation-only seed=20261026。每对模型用相同被重抽受访者，joint-pattern multinomial与逐行有放回抽样等价；逐对重置相同seed便于重算。

| 比较A−B | ΔMacro F1 | 95% percentile CI |
| --- | --- | --- |
| v2:LDA − v2:Multinomial Logistic Regression | -0.010242 | [-0.014217, -0.006066] |
| v2:kNN − v2:Multinomial Logistic Regression | -0.011047 | [-0.017237, -0.005129] |
| v2:SVM − v2:Multinomial Logistic Regression | +0.026849 | [+0.020230, +0.033362] |
| v2:Decision Tree − v2:Multinomial Logistic Regression | -0.015645 | [-0.020080, -0.011190] |
| v2:Training-majority − v1:Training-majority | +0.000000 | [+0.000000, +0.000000] |
| v2:Training-prior random − v1:Training-prior random | +0.000000 | [+0.000000, +0.000000] |
| v2:Multinomial Logistic Regression − v1:Multinomial Logistic Regression | -0.002193 | [-0.003802, -0.000575] |
| v2:LDA − v1:LDA | +0.000424 | [-0.001200, +0.002147] |
| v2:kNN − v1:kNN | -0.002020 | [-0.004467, +0.000421] |
| v2:SVM − v1:SVM | -0.002367 | [-0.004986, +0.000314] |
| v2:Decision Tree − v1:Decision Tree | +0.002101 | [+0.000681, +0.003561] |

区间仅conditional on本次固定训练/选择结果与split，按individual iid抽样，未纳入国家聚类、训练与调参不确定性；多个区间未作多重比较校正，作为描述性证据。不能据Test区间重新调参或从旧/新结果中择优提交，旧/新配对变化也不是映射单项效果的因果检验。

## 10. 现存局限与提交前优先事项

1. **P0：仅纳入本次完整且核验通过的正式结果。** 若仍有Pending、失败、缺失导出、split不一致或非零convergence，先解决对应证据，不填入旧数值。禁止利用已看到的Test结果追加网格搜索。

2. **P1：最终整合只使用本次结果。** LDA和SVM保留的旧数字段已明确标为Legacy pre-correction，不应误报为未披露的v2错误；也不能把这些provenance段复制成v2结论。选中配置、Logistic优化状态、Tree零召回/零预测及minority表现均引用本次逐行指标，明确所有Δ基于新Majority和新Logistic。

3. **P1：保留完整版本与来源证据。** 统一引用FY2021及NIR继承假设，附六份源码diff/哈希、实际运行map、数据hash、package/session、候选和预测文件。最终将主流程的原仓库与original_sources前后保护manifest一并归档。

4. **P2：准确界定结论。** 单一固定Validation存在选优偏差，训练cap不同；单一Test仅估计当前个体随机holdout，不代表未见国家、未来年度或加权总体估计。已有Test结果已被团队看到，所以它不保证对研究者完全未见。v2仅一次正式运行，不声称新版本重复执行验证。

5. **P2：披露A1原有众数处理。** A1在A2 split之前众数填补带来原则上的无监督预处理泄漏风险；前次审计曾核对被选变量的整体/训练众数一致，这使已选流程的实际影响较小，但不是删除风险披露的理由。v2共享CSV未重建，也没有声称消除该风险；没有直接目标作为预测变量的证据。

## 11. 当前异常与缺失证据

独立评估未发现未解决的执行/契约/指标异常。原始资料保护及额外运行诊断仍以主执行流程的最终证据为准。

## 12. 交付文件与最终判断

- `../model_comparison.csv`：本次七个模型/基准的完整精度分数与新基准差值。

- `../per_class_comparison.csv`、`../split_integrity_report.csv`、`../old_vs_new_comparison.csv`：逐类、行身份和旧新配对比较。

- `../independent/`：完整混淆、错误流向、原计算比较、map/source检查、bootstrap和机器可读summary。

- `../results/<model>/`、`../execution_logs/`：各自一次正式render、实际预测、模型输出、runtime和环境。

- `../original_sources/`、`../source_evidence/`：未改动原稿与官方来源证据。

**Ready with minor corrections：可整合 v2 正式报告，保留以下局限和提交前文字核对。**

## 主执行流程补充核验

## 附录：冻结源码、数据与执行对象的最终复核

本附录只观察已保存对象，没有重新拟合模型、追加Test评分或改变候选选择。

- 六份正式执行均成功；每一份执行副本在运行前后都与本目录冻结源文件逐字节一致。原仓库完整非Git文件集、SHA-256、HEAD、main和clean状态与运行前相同，original_sources与原像相同；旧审计六项主要交付物也与旧散列清单一致。证据：environment/all_six_source_contract.json。
- R原生可执行AST比对只允许FY2021映射、明确列出的显示文字，以及Logistic迭代上限和收敛gate；所有函数、种子、切分、cap、features、class weights、kernel/formula及候选/排序逻辑均保留。完整差异见environment/source_changes.diff。
- 无Income_Group的102个Validation候选新旧Macro F1、Weighted F1、Accuracy最大差均为0。该控制仅读取候选表，未额外拟合或评价Test；详见independent/no_income_control_comparison.md。
- 独立重算138项median/filled mean/sample SD参数，失败0，最大绝对差2.22e-16。SVM class-weight检查32项，失败0。相关runtime_contract文件保存在independent。
- LDA最终保留39列，独立within-class rank=39，pooled covariance最小特征值0.0041311547；数值满秩不等于已证明Gaussian或相同类内协方差假设。
- SVM实际native kernel=radial、C=1、gamma=0.21739130434782608，scaling全部关闭，probability flag=False；support vectors=67060，全部indices只属于共同80%训练pool。保存对象未保留native class.weights时不假称直接恢复该字段；权重依据独立公式、原helper结果和源调用核对。
- Logistic训练内预检与正式运行的selected spec/decay、六行Validation ranking、拟合row IDs、最终目标函数及全部weights完全一致，weights最大差0；两次final convergence均为0。预检没有Test预测，正式Test只按冻结源文件评价一次。2000是迭代上限，并非声称每个模型实际执行了2000步。
- 包版本、build和library路径与旧审计九个关键包全部匹配。运行耗时受并行任务、文件缓存和本机负载影响，属于观察到的工程成本，不是控制条件下的算法速度实验。

输入完整性：

| 文件 | bytes | SHA-256 |
|---|---:|---|
| WVS_Wave7_cleaned_for_modelling.csv | 171923121 | ee392676dbb42dde0ea74ebf643862f3900e7d13a7aa03842ed2d7665ac98ee0 |
| WVS_Cross-National_Wave_7_rds_v6_0.csv | 279494669 | a20fd7653d1fbcff1014449990a5346c2fb3a994e076fed9e611dd364cb10822 |

共享CSV内容未变，收入分组只在六份Rmd运行时按更正表生成。先前A1 selected11列lineage及五种fitting partitions的六分类mode一致性证据副本位于source_evidence/prior_audit_raw_lineage_*；本轮没有重做A1全519列pipeline。

源Rmd中的旧固定数字均有Legacy标识，仅供溯源。新版结论以本次生成的表、独立预测核验和新报告为准。全五模型本轮只有一轮正式执行，不能把Logistic训练预检说成全模型第二轮Test复现。

