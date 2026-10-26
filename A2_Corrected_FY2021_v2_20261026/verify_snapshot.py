"""Read-only verification of this published snapshot; no model fitting."""
from pathlib import Path
import csv
import hashlib
import json
import sys

root = Path(__file__).resolve().parent

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

errors = []
total = 0
with (root / 'PUBLICATION_MANIFEST.csv').open(encoding='utf-8', newline='') as stream:
    rows = list(csv.DictReader(stream))
seen = set()
for row in rows:
    rel = Path(row['Path'])
    path = (root / rel).resolve()
    if rel.is_absolute() or not path.is_relative_to(root) or row['Path'] in seen:
        errors.append(f'Invalid or duplicate path: {row["Path"]}')
        continue
    seen.add(row['Path'])
    if not path.is_file():
        errors.append(f'Missing: {row["Path"]}')
        continue
    total += path.stat().st_size
    if path.stat().st_size != int(row['Bytes']) or sha(path) != row['SHA256']:
        errors.append(f'Content mismatch (check Git LFS): {row["Path"]}')

if not errors:
    checks = load(root / 'DELIVERABLE_CHECKS.json')
    for row in checks['Files']:
        path = root / row['File']
        if path.stat().st_size != row['Bytes'] or sha(path) != row['SHA256']:
            errors.append(f'Original deliverable check mismatch: {row["File"]}')
    for tag in ('baseline', 'logistic', 'lda', 'knn', 'svm', 'tree'):
        status = load(root / 'results' / tag / 'execution_status.json')
        if status['Success'] is not True or status['Source_Unchanged_During_Render'] is not True:
            errors.append(f'Execution status failed: {tag}')
    summary = load(root / 'independent' / 'evaluation_summary.json')
    if summary['Issues'] or not summary['Data_Integrity_Verified']:
        errors.append('Independent evaluation reported issues')
    with (root / 'model_comparison.csv').open(encoding='utf-8-sig', newline='') as stream:
        models = list(csv.DictReader(stream))
    if len(models) != 7 or any(r['Execution_Status'] != 'Success' or int(r['Test_N']) != 19201 for r in models):
        errors.append('Model summary failed')
print(json.dumps({'Status': 'FAIL' if errors else 'PASS', 'Files_Checked': len(rows),
                  'Bytes_Checked': total, 'Errors': errors}, indent=2))
sys.exit(1 if errors else 0)
