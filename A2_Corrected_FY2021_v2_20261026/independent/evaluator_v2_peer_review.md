# v2 独立评估器与报告生成器同行复核

审阅日期：2026-10-26。范围为 `scripts/evaluate_v2.py`、`scripts/build_v2_report.py` 及截至11:28生成的阶段输出；随后只读检查主执行者对本轮发现的修订。本审阅仅新增本文件，没有修改源码、Rmd、数据、模型或既有输出，没有拟合、重渲染Rmd或查询模型。

**结论：已完成的六项模型/基准结果未发现数值错误；评估和报告逻辑的以下问题已经修正。当前正式产物仍是阶段报告，SVM及正式bootstrap产物尚不能视为核验完成。**

## 发现与处理状态

| 优先级 | 位置（修订后行号） | 问题及状态 |
| --- | --- | --- |
| P1 | `evaluate_v2.py:359–374`；`build_v2_report.py:83–102` | 原逻辑在候选表缺失时既不产生Major，也不阻止Ready。已增加成功学习模型缺候选表的Major；最终Ready要求五模型候选数完整，且SVM候选状态全部ok。 |
| P1 | `build_v2_report.py:85–102` | 原Ready不要求计划中的bootstrap，随后仅相信summary计数也可能漏掉缺失CSV。现要求真实CSV恰含11组预期比较、每组至少5000次、正确种子、有限且有序的CI端点，并要求7组旧新身份全部通过。跳过bootstrap的预览不能Ready。 |
| P2 | `evaluate_v2.py:454–464` | 原始输出表在后续解析中异常时，先前已保存独立分数，但Notes却称“withheld”。现明确保留已通过身份/算术核验的独立分数，记录原表交叉核验错误及Major；较早的预测核验失败则清空分数。语义矛盾已消除。 |
| P2 | `build_v2_report.py:164` | 原“官方66代码+NIR”有67条之歧义。实际crosswalk共66条，其中NIR无官方独立条目。现明确65条官方匹配加1条NIR继承假设。 |

## 独立检查结果

- **八类指标：通过。** `evaluate_v2.py:95–105` 固定包含八类，Precision/Recall/F1零分母置0，Weighted F1按真实support加权。独立复算当前六项完整混淆矩阵（各19,201人），Macro F1、Weighted F1、Accuracy与已写CSV差值全部为0。仅一类存在且完美的内存夹具得到Macro F1=0.125、Weighted F1=Accuracy=1，确认没有丢弃其余七类。
- **身份与fresh reference：通过。** 新旧reference逐行完全相同，CSV行号为1至95,987，唯一、完整、有序；Train/Validation/Test分别57,587/19,199/19,201。预测解析内存夹具正确拒绝行乱序、重复ID、truth错误、未知及空预测标签；备用预测文件也须逐行相同。
- **cap：通过。** fresh 24,996/9,997条reference分别与旧cap逐行相同，无重复且均属于共同初始Train；CSV行号、80%池内局部编号、初始Train内fit编号三种坐标一致。Logistic从不变Validation补集恢复初始Train是合理处理，不是共享划分错误。
- **旧新比较：通过。** 七份旧预测均核验相同Test行/标签，三个总指标与不可变旧表差值均为0。新−旧及新模型−新Logistic的差值方向正确。
- **配对bootstrap算法：通过。** `evaluate_v2.py:175–191` 对联合 `(truth,predA,predB)` 模式进行多项分布重抽，与ordinary paired row bootstrap分布等价。内存夹具同预测得到CI=[0,0]；完美−全错为正，反向为负。实际正式5000次区间尚未在本次阶段产物中生成；本审阅未代为执行正式bootstrap。
- **最终状态gate：12个内存夹具通过。** 仅完整合格情形Ready；候选标记缺失、SVM状态缺失、跳过bootstrap、缺CSV、错误pair、非有限CI、缺旧新表、Pending、Failed、Logistic非零收敛及Major均阻止Ready。Pending仍为阶段报告，Failed进入执行失败判断。

## 不应误判为缺陷的边界

当前SVM Pending、总排名保留、bootstrap为0次/0组均符合阶段输出身份；不能用旧SVM分数填补。主种子必须为数值5003、实际CSV路径/MD5、标签顺序、收入map及渲染源码不变均单独核验，避免把“执行成功”等同于“契约通过”。

报告对区间明确限定为固定模型/划分下的individual iid重抽，不包含国家聚类、训练/调参不确定性，且多个区间未经多重校正；这些是必要的解释边界。整体版本变化不作映射或优化单项因果归因、旧Logistic未收敛不作为合格优化基准、仅一次v2正式运行不声称重复复现，均是合理而审慎的文案。

主流程最终生成后仍需核对SVM正式状态、11组实际bootstrap及报告中的完成性行；本文件对截至11:28的阶段产物不作最终Ready认证。原仓库、源文件及共享CSV前后保护由主流程manifest负责。
