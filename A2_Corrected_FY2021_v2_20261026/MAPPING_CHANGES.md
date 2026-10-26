# FY2021 映射修正与冻结记录

**冻结后的独立复核均通过**：`environment/mapping_R_independent_check.json` 记录 R 原生 parser 对五份全部 chunks 解析成功，逐 code 的 R 计算映射等于 canonical，全部 function AST 与受保护的 seed/split/feature/hyperparameter/candidate assignments 相同。`environment/mapping_workbook_cell_verification.json` 从冻结 XLSX 再次直接读出每项 source cell，65 个官方国家行与 1 个明确 NIR→GBR 继承项全部匹配；没有依赖当前年度分类或重新下载证据。

此目录是 2026-10-26 新建的更正版本。原仓库、旧审计目录、original_sources 均未修改。本记录覆盖 baseline/LDA/kNN/SVM/Tree 五份 Rmd；Logistic 由另一审查者应用相同 canonical map 并处理收敛。

权威来源为 source_evidence 中冻结的 World Bank 历史工作簿 FY21/AI 列（2020-07-01 发布，2019 GNI），不是当前年度分类。

| Code | 原映射 | 更正 FY2021 | 官方 cell |
| --- | --- | --- | --- |
| MDV | High | Upper-middle | AI128 |
| ROU | Upper-middle | High | AI167 |
| UKR | Upper-middle | Lower-middle | AI211 |
| TWN | Unclassified | High | AI197 |
| VEN | Unclassified | Upper-middle | AI218 |
| NIR | High | High（显式 UK 继承假设） | 使用 GBR!AI213，官方无 NIR 独立行 |

canonical JSON 列出全部 66 code 的 group、vintage、source cell 和 NIR assumption。组数 Low=2、Lower-middle=18、Upper-middle=23、High=23；WB_GROUPS 保留 Unclassified=character(0)，原 CATEGORY_KEYS/固定因子字典完全保留。

只改 WB_GROUPS assignment 及对应 mapping provenance/显示文字；旧 SVM/LDA/Tree 固定数值或结论段落加 legacy 标签，避免充当新结果。未改 recipe、model matrix 代码、超参数、候选集、split、seed、权重规则或选择/评价逻辑。因输入映射变化导致的实际编码列数变化由原算法自行产生，不强制保留旧数据下的 P。

每项编辑按相反顺序精确逆转后能恢复完整原文件文本；五份 map 均逐 code 等于 canonical。逐文件 SHA-256、精确变更行范围见 environment/mapping_verification.json；统一差异见 environment/mapping_changes.diff。

## baseline.Rmd

更正 SHA-256：`8d344a2dc81a34868b81e0562a60f405c8eda3e83aa00288abc01532d8c9ab87`

变更行范围（原 → 更正）：[102, 102] → [102, 102]; [109, 117] → [109, 117]; [126, 126] → [126, 126]; [129, 129] → [129, 129]; [224, 224] → [224, 224]

## 02_LDA.Rmd

更正 SHA-256：`f2d9d22cabaa105329de1ad0688887b98749016309bbfcfc34074a5e48cc6c8f`

变更行范围（原 → 更正）：[168, 168] → [168, 168]; [173, 173] → [173, 173]; [177, 182] → [177, 182]; [187, 195] → [187, 196]; [490, 489] → [491, 492]; [500, 501] → [503, 504]; [553, 553] → [556, 556]

## 03_kNN.Rmd

更正 SHA-256：`9d228929e8887f8855a04b6dcf902c6936ec2cc1822e53ac9d7b97e216d622b0`

变更行范围（原 → 更正）：[23, 23] → [23, 23]; [115, 123] → [115, 123]; [382, 382] → [382, 382]

## 04_SVM.Rmd

更正 SHA-256：`55a4c54dce1ae72cc1ec6b213147b9ff8677b8ccf803bf3a6ece84849eec2814`

变更行范围（原 → 更正）：[121, 121] → [121, 123]; [126, 134] → [128, 136]; [624, 624] → [626, 628]

## 05_DecisionTree.Rmd

更正 SHA-256：`0f9740f70cb5222054e54db3f10056d95e2b71ba39aab09aed21cf3eb5747995`

变更行范围（原 → 更正）：[36, 36] → [36, 36]; [257, 265] → [257, 265]; [382, 382] → [382, 382]; [514, 514] → [514, 514]; [559, 558] → [559, 560]; [561, 561] → [563, 563]

## Six-source preservation verification

核验时间：2026-10-26T12:12:22.852442+08:00。`scripts/verify_v2_sources.py` 的全部断言通过，记录于 `environment/all_six_source_contract.json`；六份完整差异见 `environment/source_changes.diff`。

六份 map 均匹配 canonical 与冻结官方 cells；所有 function AST 完全相同；全部 executable AST 在仅归一化 map、明确显示文字和 Logistic MAXIT250→2000/三处收敛 gate 后完全相同。seed、split/cap、feature recipes、class weights、kernel/formula 和候选/排序逻辑保留。原仓库完整非 Git 文件集/散列/clean Git 状态与原 manifest 相同，original_sources 与原像一致；旧审计六项主要交付物与旧 DELIVERABLE_CHECKS.json 完全匹配。

当前已观察到 6/6 个模型的执行 Rmd 副本，全部与 root/frozen hash 一致；本核验不表示所有渲染已完成，可在全部运行后重复执行。
