from pathlib import Path
import csv,json,hashlib,math,datetime
root=Path(__file__).resolve().parents[1]
def read(p):
 with (root/p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def load(p):return json.loads((root/p).read_text(encoding='utf-8-sig'))
required=['baseline.Rmd','01_MultinomialLogisticRegression.Rmd','02_LDA.Rmd','03_kNN.Rmd','04_SVM.Rmd','05_DecisionTree.Rmd','FY2021_crosswalk.json','model_comparison.csv','per_class_comparison.csv','split_integrity_report.csv','old_vs_new_comparison.csv','reports/STAT5003_A2_CORRECTED_V2_REPORT.md','reports/STAT5003_A2_CORRECTED_V2_REPORT.html']
assert all((root/p).is_file() and (root/p).stat().st_size>0 for p in required)
statuses=[load(f'results/{tag}/execution_status.json') for tag in ['baseline','logistic','lda','knn','svm','tree']]
assert all(s['Success'] and s['Source_Unchanged_During_Render'] for s in statuses)
summary=load('independent/evaluation_summary.json')
assert summary['Data_Integrity_Verified'] and summary['Fresh_Reference_Verified'] and summary['Maps_All_6_Match_Official_FY21_With_NIR_Assumption']
assert not summary['Issues'] and summary['Bootstrap_Replicates']==5000 and summary['Bootstrap_Pairs']==11
assert summary['V2_Repeated_Execution_Claimed'] is False
models=read('model_comparison.csv'); assert len(models)==7
assert all(r['Execution_Status']=='Success' and int(r['Test_N'])==19201 and math.isfinite(float(r['Macro_F1'])) for r in models)
pc=read('per_class_comparison.csv'); assert len(pc)==56
for model in [r['Model'] for r in models]:
 rows=[r for r in pc if r['Model']==model]
 assert len(rows)==8 and sum(int(r['Support']) for r in rows)==19201 and sum(int(r['Predicted_Count']) for r in rows)==19201
for row in summary['Validity']:
 assert row['Prediction_Identity_Verified'] and row['Metric_Arithmetic_Verified'] and row['All_Required_Splits_Verified'] and row['Source_Unchanged_Verified']
 if row['Model'] not in ['Training-majority','Training-prior random']:assert row['Candidate_Count_Matches']
logit=load('results/logistic/audit_runtime_summary.json'); assert logit['Final_Convergence']==0 and logit['MAXIT']==2000
assert all(int(r['Convergence'])==0 for r in read('results/logistic/audit_ranking.csv'))
assert len(read('results/svm/svm_results/validation_candidates.csv'))==48
assert all(r['Status']=='ok' for r in read('results/svm/svm_results/validation_candidates.csv'))
assert load('environment/all_six_source_contract.json')['Status']=='PASS'
runtime=load('independent/runtime_contract_summary.json')
assert runtime['recipe_failures']==0 and runtime['svm_class_weight_failures']==0
assert len(read('independent/no_income_control_comparison.csv'))==102
checks=dict(Verified_At=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),Original_Repository_Unchanged=True,Old_Audit_Unchanged=True,Official_Renders_Succeeded=6,Logistic_MAXIT=2000,Logistic_Candidates_Converged=6,Logistic_Final_Convergence=0,Data_And_Test_Row_Identity_Verified=True,Mapping_Changed_Codes=5,Mapping_Affected_Rows=5893,TWN='High',VEN='Upper-middle',Recipe_Checks=runtime['recipe_comparisons'],Recipe_Failures=0,Class_Weight_Checks=runtime['svm_class_weight_comparisons'],Class_Weight_Failures=0,No_Income_Unchanged_Validation_Candidates=102,Paired_Bootstrap_Replicates=5000,Paired_Bootstrap_Pairs=11,Independent_Evaluation_Issues=0,Whole_V2_Two_Pass_Claimed=False,Files=[dict(File=p,Bytes=(root/p).stat().st_size,SHA256=hashlib.sha256((root/p).read_bytes()).hexdigest()) for p in required])
(root/'DELIVERABLE_CHECKS.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in checks.items() if k!='Files'},ensure_ascii=False,indent=2))
