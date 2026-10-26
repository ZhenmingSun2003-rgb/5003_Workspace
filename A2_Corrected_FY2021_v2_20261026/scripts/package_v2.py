from pathlib import Path
import csv,hashlib,json,zipfile,datetime

root=Path(__file__).resolve().parents[1]
for tag in ['baseline','logistic','lda','knn','svm','tree']:
 status=json.loads((root/f'results/{tag}/execution_status.json').read_text(encoding='utf-8-sig'))
 assert status['Success'] and status['Source_Unchanged_During_Render'],(tag,'Official render incomplete/failed')
summary=json.loads((root/'results/logistic/audit_runtime_summary.json').read_text())
assert summary['Final_Convergence']==0 and summary['MAXIT']==2000
assert json.loads((root/'environment/all_six_source_contract.json').read_text())['Status']=='PASS'
for name in ['model_comparison.csv','per_class_comparison.csv','split_integrity_report.csv','old_vs_new_comparison.csv','reports/STAT5003_A2_CORRECTED_V2_REPORT.md','reports/STAT5003_A2_CORRECTED_V2_REPORT.html']:
 assert (root/name).is_file() and (root/name).stat().st_size>0,name
with (root/'model_comparison.csv').open(encoding='utf-8-sig',newline='') as f:
 models=list(csv.DictReader(f))
assert len(models)==7 and all(r['Execution_Status']=='Success' and r['Macro_F1'] for r in models)
archive=root/'STAT5003_A2_Corrected_FY2021_v2_REVIEW.zip'
assert not archive.exists(),'Refusing to overwrite archive'
allowed={'.rmd','.r','.py','.md','.csv','.json','.html','.css','.log','.txt','.png','.xlsx','.npz','.diff','.patch'}
files=[]
for path in root.rglob('*'):
 if not path.is_file():continue
 rel=path.relative_to(root)
 if '__pycache__' in rel.parts or 'r_library' in rel.parts:continue
 if path.name.startswith('WVS_') or path.name=='package_v2.log' or path.suffix.lower() not in allowed:continue
 if path.suffix.lower()=='.csv' and path.stat().st_size>10_000_000:continue
 files.append(path)
rows=[dict(Path=p.relative_to(root).as_posix(),Bytes=p.stat().st_size,SHA256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)]
manifest=root/'REVIEW_MANIFEST.csv'
with manifest.open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=['Path','Bytes','SHA256']);writer.writeheader();writer.writerows(rows)
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
 for path in files+[manifest]:z.write(path,path.relative_to(root).as_posix())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
info=dict(Created_At=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),Archive=str(archive),Files=len(files)+1,Bytes=archive.stat().st_size,SHA256=hashlib.sha256(archive.read_bytes()).hexdigest(),Excluded='Large dataset CSVs, RDS model/runtime files and R libraries remain in full revision folder')
print(json.dumps(info,ensure_ascii=False,indent=2))
