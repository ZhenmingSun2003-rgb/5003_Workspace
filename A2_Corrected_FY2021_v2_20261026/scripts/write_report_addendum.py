from pathlib import Path
import json,csv,hashlib,datetime
root=Path(__file__).resolve().parents[1]
def load(p):return json.loads((root/p).read_text(encoding='utf-8-sig'))
def digest(p,kind='sha256'):
 h=hashlib.new(kind)
 with p.open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()
statuses={m:load(f'results/{m}/execution_status.json') for m in ['baseline','logistic','lda','knn','svm','tree']}
assert all(s['Success'] and s['Source_Unchanged_During_Render'] for s in statuses.values())
contract=load('environment/all_six_source_contract.json'); assert contract['Status']=='PASS'
runtime=load('independent/runtime_contract_summary.json')
assert runtime['recipe_failures']==0 and runtime['svm_class_weight_failures']==0
assert all(v['status']=='observed saved unchanged-Rmd environment' for v in runtime['runs'].values())
replay=load('diagnostics/logistic_training_replay_comparison.json')
assert replay['Official_Final_Convergence']==0 and replay['Final_Weights_Maximum_Absolute_Difference']==0
preflight=load('diagnostics/logistic_preflight_maxit2000/preflight_status.json')
assert preflight['No_Test_Prediction_Or_Scoring'] and preflight['Source_Stayed_Unchanged']
svm=load('independent/runtime_contract_svm_native_model_parameters.json')
lda=load('independent/runtime_contract_lda_lda_diagnostics.json')
inputs=[]
for name in ['WVS_Wave7_cleaned_for_modelling.csv','WVS_Cross-National_Wave_7_rds_v6_0.csv']:
 p=root/name;inputs.append(dict(File=name,Bytes=p.stat().st_size,SHA256=digest(p),MD5=digest(p,'md5')))
assert inputs[0]['SHA256']=='ee392676dbb42dde0ea74ebf643862f3900e7d13a7aa03842ed2d7665ac98ee0'
(root/'environment/input_data_manifest.json').write_text(json.dumps(inputs,indent=2),encoding='utf-8')
with (root/'independent/no_income_control_comparison.csv').open(encoding='utf-8-sig',newline='') as f:controls=list(csv.DictReader(f))
text=f'''## 附录：冻结源码、数据与执行对象的最终复核

本附录只观察已保存对象，没有重新拟合模型、追加Test评分或改变候选选择。

- 六份正式执行均成功；每一份执行副本在运行前后都与本目录冻结源文件逐字节一致。原仓库完整非Git文件集、SHA-256、HEAD、main和clean状态与运行前相同，original_sources与原像相同；旧审计六项主要交付物也与旧散列清单一致。证据：environment/all_six_source_contract.json。
- R原生可执行AST比对只允许FY2021映射、明确列出的显示文字，以及Logistic迭代上限和收敛gate；所有函数、种子、切分、cap、features、class weights、kernel/formula及候选/排序逻辑均保留。完整差异见environment/source_changes.diff。
- 无Income_Group的{len(controls)}个Validation候选新旧Macro F1、Weighted F1、Accuracy最大差均为0。该控制仅读取候选表，未额外拟合或评价Test；详见independent/no_income_control_comparison.md。
- 独立重算{runtime['recipe_comparisons']}项median/filled mean/sample SD参数，失败0，最大绝对差{runtime['max_absolute_recipe_difference']:.3g}。SVM class-weight检查{runtime['svm_class_weight_comparisons']}项，失败0。相关runtime_contract文件保存在independent。
- LDA最终保留{lda['retained_dimension']}列，独立within-class rank={lda['residual_rank']}，pooled covariance最小特征值{lda['covariance_eigen_min']:.8g}；数值满秩不等于已证明Gaussian或相同类内协方差假设。
- SVM实际native kernel={svm['kernel_name']}、C={svm['cost']}、gamma={svm['gamma']:.17g}，scaling全部关闭，probability flag={svm['native_probability_flag_compprob']}；support vectors={svm['total_nSV_native']}，全部indices只属于共同80%训练pool。保存对象未保留native class.weights时不假称直接恢复该字段；权重依据独立公式、原helper结果和源调用核对。
- Logistic训练内预检与正式运行的selected spec/decay、六行Validation ranking、拟合row IDs、最终目标函数及全部weights完全一致，weights最大差0；两次final convergence均为0。预检没有Test预测，正式Test只按冻结源文件评价一次。2000是迭代上限，并非声称每个模型实际执行了2000步。
- 包版本、build和library路径与旧审计九个关键包全部匹配。运行耗时受并行任务、文件缓存和本机负载影响，属于观察到的工程成本，不是控制条件下的算法速度实验。

输入完整性：

| 文件 | bytes | SHA-256 |
|---|---:|---|
'''
for row in inputs:text+=f"| {row['File']} | {row['Bytes']} | {row['SHA256']} |\n"
text+='''
共享CSV内容未变，收入分组只在六份Rmd运行时按更正表生成。先前A1 selected11列lineage及五种fitting partitions的六分类mode一致性证据副本位于source_evidence/prior_audit_raw_lineage_*；本轮没有重做A1全519列pipeline。

源Rmd中的旧固定数字均有Legacy标识，仅供溯源。新版结论以本次生成的表、独立预测核验和新报告为准。全五模型本轮只有一轮正式执行，不能把Logistic训练预检说成全模型第二轮Test复现。
'''
(root/'reports/report_addendum.md').write_text(text,encoding='utf-8')
print('Wrote final report addendum; all source/data/runtime guards passed')
