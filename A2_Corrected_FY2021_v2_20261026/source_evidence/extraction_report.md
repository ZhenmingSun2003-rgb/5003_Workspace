# World Bank FY2021 分类核验原始证据

检索时区：Asia/Shanghai。逐响应时间、来源 URL、HTTP metadata、bytes、MD5 与 SHA-256 见 source_provenance.json。

本目录保存官方历史工作簿和两篇官方来源网页。crosswalk_comparison_all_66.csv 为六文件共同映射的全量 66 code 比较；crosswalk_discrepancies.csv 包含三项档位错置、两项主动 Unclassified 覆盖和 NIR 继承假设。

FY21 位于 Country Analytical History!AI5，其对应日历数据年 Country Analytical History!AI6 为 2019。

| Code | 原映射 | 官方 FY21 | 官方 cell | CSV 行数 | 状态 |
| --- | --- | --- | --- | ---: | --- |
| MDV | High | Upper-middle | AI128 | 1019 | classification_mismatch |
| NIR | High | 无独立 code | 不适用 | 444 | documented_UK_inheritance_assumption |
| ROU | Upper-middle | High | AI167 | 1198 | classification_mismatch |
| TWN | Unclassified | High | AI197 | 1223 | explicit_coverage_choice_despite_official_classification |
| UKR | Upper-middle | Lower-middle | AI211 | 1266 | classification_mismatch |
| VEN | Unclassified | Upper-middle | AI218 | 1187 | explicit_coverage_choice_despite_official_classification |

三项档位错误影响 3,483 行；两项主动覆盖选择另涉及 2,410 行；合计 5,893 行。NIR 的 444 行另列为已披露英国继承假设，不算作已证实档位错误。

运行 scripts/verify_world_bank.py --verify-existing 可不联网、不写文件地重抽取工作簿、检查源 Rmd hash、CSV row counts、全部比较表及下载文件散列。使用 --output-dir 指向新的空目录可重新检索；脚本拒绝覆盖已有证据。

来源：
- [historical_workbook](https://ddh-openapi.worldbank.org/resources/DR0095334/download)
- [classification_landing_page](https://datahelpdesk.worldbank.org/knowledgebase/articles/906519-world-bank-country-and-lending-groups)
- [fy2021_release_page](https://blogs.worldbank.org/en/opendata/new-world-bank-country-classifications-income-level-2020-2021)
