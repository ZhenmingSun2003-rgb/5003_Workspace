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
