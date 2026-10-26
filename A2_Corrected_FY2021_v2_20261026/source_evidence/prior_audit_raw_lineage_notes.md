# 原始CSV到清洗CSV：11个建模源列独立lineage核验

结论：**PASS**。流式读取原始 97,220×613 CSV，保留Q279属于1:8的 95,987 行，按原顺序与清洗CSV及reference split逐行对齐。

- 被排除raw target无效行：1,233；分布 `{'-2.0': 792, '-1.0': 118, '-5.0': 323}`。
- target/country/observed selected value等各类mismatches：`{}`。
- 原raw row ID → cleaned row ID完整映射保存在raw_lineage_row_mapping.csv；保留了逐行target/country/partition以便追溯。

| Source | 原始有效/有限observed cells | 原值保持cells | 原始missing/sentinel cells | 清洗后的replacement counts |
|---|---:|---:|---:|---|
| Q262 | 95,517 | 95,517 | 470 | `{'Unknown': 470}` |
| Q270 | 95,229 | 95,229 | 758 | `{'Unknown': 758}` |
| Q274 | 91,398 | 91,398 | 4,589 | `{'Unknown': 4589}` |
| Q260 | 95,916 | 95,916 | 71 | `{'2': 71}` |
| Q273 | 95,608 | 95,608 | 379 | `{'1': 379}` |
| Q275 | 95,229 | 95,229 | 758 | `{'3': 758}` |
| Q286 | 93,420 | 93,420 | 2,567 | `{'2': 2567}` |
| Q287 | 90,798 | 90,798 | 5,189 | `{'3': 5189}` |
| Q288 | 93,374 | 93,374 | 2,613 | `{'5': 2613}` |

数值字段按数值意义比较，同时JSON保留lexical unchanged计数；raw missing/sentinel按A1的-1:-5规则，未将大年龄或较大household count自动当outlier删除。

| Category | 全部valid-target raw mode | 原始initial Train mode | 原始Train+Validation mode | Logistic24996 mode | SVM9997 mode | 全部missing replacements均为global mode |
|---|---:|---:|---:|---:|---:|---|
| Q260 | 2 | 2 | 2 | 2 | 2 | True |
| Q273 | 1 | 1 | 1 | 1 | 1 | True |
| Q275 | 3 | 3 | 3 | 3 | 3 | True |
| Q286 | 2 | 2 | 2 | 2 | 2 | True |
| Q287 | 3 | 3 | 3 | 3 | 3 | True |
| Q288 | 5 | 5 | 5 | 5 | 5 | True |

各mode的最高频数、全部并列mode values及并列数量已写入JSON。实际并列mode列表：`[]`。
Logistic24996/SVM9997采用reference_cap_25000.csv/reference_cap_10000.csv的精确原cleaned row IDs；所有IDs均被观察且只属于初始Train，并非重新抽样近似。

这里核实了**selected11个source columns**在valid-target cohort中的顺序与清洗变化；没有重现全部519列A1 pipeline，也没有据此验证全部codebook约束或证明无重复受访者。

A1确实使用整个valid-target样本的mode完成这些类别插补。上表另列training-only modes以区分程序性leakage风险与本数据中的实际replacement值差异；即使mode恰好一致，也不能将历史流程称为split-first preprocessing。此检查不使用结果重调模型，也不直接证明少数类错误的因果来源。

运行时间：11.005s。输入CSV及任何Rmd未修改。
