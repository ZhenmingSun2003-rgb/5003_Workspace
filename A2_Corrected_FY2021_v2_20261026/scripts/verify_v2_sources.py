"""Rerunnable read-only source, authority, executed-copy and preimage verifier.

Writes only its own environment evidence, complete source diff, and a marked
appendix in MAPPING_CHANGES.md. No Rmd, data, render script, repo or old audit is
modified. R native AST checks parse code only, never fit or evaluate a model.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
FILES = ("baseline.Rmd", "01_MultinomialLogisticRegression.Rmd", "02_LDA.Rmd", "03_kNN.Rmd", "04_SVM.Rmd", "05_DecisionTree.Rmd")
LOGISTIC_FROZEN_SHA256 = "516d23f073cfff3ded7a107a9d6cbc6904e937cf33bd470bff4789be78364141"
GROUPS = {"L": "Low", "LM": "Lower-middle", "UM": "Upper-middle", "H": "High"}


def digest(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def csv_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def map_span(text):
    start = text.index("WB_GROUPS <- list(")
    end, depth = start + len("WB_GROUPS <- list("), 1
    while depth:
        depth += (text[end] == "(") - (text[end] == ")")
        end += 1
    return start, end


def map_dictionary(text):
    start, end = map_span(text)
    result = {}
    for group, codes in re.findall(r'(`[^`]+`|\w+)\s*=\s*c\(([^)]*)\)', text[start:end]):
        for code in re.findall(r'"([^"]+)"', codes):
            if code in result:
                raise ValueError("Duplicate map code " + code)
            result[code] = group.strip("`")
    assert re.search(r"Unclassified\s*=\s*character\(0\)", text[start:end])
    return result


def r_code(text):
    active, output = False, []
    for line in text.splitlines():
        if re.match(r"^```\{r[ ,}]", line):
            active = True
            continue
        if active and re.match(r"^```\s*$", line):
            active = False
            continue
        if active:
            output.append(line)
    return "\n".join(output)


def replace_once(text, old, new, description, evidence):
    if text.count(old) != 1:
        raise AssertionError(f"Whitelist match must occur once: {description}; observed {text.count(old)}")
    evidence.append(description)
    return text.replace(old, new, 1)


def normalize_pair(filename, old, new):
    evidence = ["WB_GROUPS only: validated separately against all66 canonical/workbook cells"]
    for which in ("old", "new"):
        text = old if which == "old" else new
        start, end = map_span(text)
        text = text[:start] + 'WB_GROUPS <- list(.ALLOWED_FY2021_MAPPING = "verified_separately")' + text[end:]
        if which == "old": old = text
        else: new = text
    presentation = {
        "baseline.Rmd": [("Working FY2021 income proxy", "Verified FY2021 income proxy")],
        "02_LDA.Rmd": [("Inherited A1 pre-split mode imputation and provisional income mapping remain limitations.", "Inherited A1 pre-split imputation and fixed-vintage national context remain limitations; NIR inherits UK.")],
        "03_kNN.Rmd": [("Income_Group follows the shared provisional map; historical entries require audit.", "Income_Group follows the verified frozen FY2021 map; NIR explicitly inherits UK High.")],
        "05_DecisionTree.Rmd": [("Income_Group follows the shared provisional map; historical entries require audit.", "Income_Group follows the verified frozen FY2021 map; NIR explicitly inherits UK High.")],
    }
    for index, (before, after) in enumerate(presentation.get(filename, [])):
        marker = f"PRESENTATION_ONLY_LITERAL_{index}"
        old = replace_once(old, before, marker, "Original presentation string: " + before, evidence)
        new = replace_once(new, after, marker, "Corrected presentation string: " + after, evidence)
    if filename == "01_MultinomialLogisticRegression.Rmd":
        old = replace_once(old, "MAXIT <- 250L", "MAXIT <- 250L", "Original MAXIT exactly250L", evidence)
        new = replace_once(new, "MAXIT <- 2000L", "MAXIT <- 250L", "Only Logistic MAXIT2000L normalized to original250L", evidence)
        old_candidate = '  if(!is.null(fit$convergence)&&fit$convergence!=0)\n    warning("Candidate not fully converged: ",spec," decay=",decay)'
        new_candidate = '  if(!identical(as.integer(fit$convergence),0L))\n    stop("Candidate did not converge; selection blocked: ",spec," decay=",decay,\n         "; convergence=",fit$convergence,"; MAXIT=",MAXIT)'
        old_final = 'if(!is.null(final_fit$convergence)&&final_fit$convergence!=0)\n  warning("Final optimisation did not fully converge.")'
        new_final = 'if(!identical(as.integer(final_fit$convergence),0L))\n  stop("Final optimisation did not converge; Test scoring blocked. convergence=",\n       final_fit$convergence,"; MAXIT=",MAXIT)'
        rank_gate = 'stopifnot(nrow(ranking)==nrow(grid),all(ranking$Convergence==0L))'
        assert new.index('fit <- nnet::multinom(') < new.index(new_candidate) < new.index('pred <- predict(fit,newdata=x_val')
        assert new.index('ranking <- do.call(rbind,result_rows)') < new.index(rank_gate) < new.index('ranking <- ranking[order(')
        assert new.index('final_fit <- nnet::multinom(') < new.index(new_final) < new.index('predicted <- predict(final_fit')
        old = replace_once(old, old_candidate, "", "Original candidate warning gate removed solely for AST matching", evidence)
        new = replace_once(new, new_candidate, "", "New strict convergence gate before candidate Validation prediction", evidence)
        old = replace_once(old, old_final, "", "Original final warning gate removed solely for AST matching", evidence)
        new = replace_once(new, new_final, "", "New strict final convergence gate before Test prediction", evidence)
        new = replace_once(new, rank_gate, "", "New all-candidate convergence/row-count gate before ranking and selection", evidence)
    return old, new, evidence


def run_git(git, repo, *arguments):
    result = subprocess.run([str(git), "-C", str(repo), *arguments], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--repository", type=Path, default=Path(r"C:\Users\Saberken\Downloads\5003_Workspace"))
    parser.add_argument("--old-audit", type=Path, default=ROOT.parent / "audit_20261024_01")
    parser.add_argument("--rscript", type=Path, default=Path(r"C:\Program Files\R\R-4.6.1\bin\Rscript.exe"))
    args = parser.parse_args()
    root, repo, old_audit = args.root.resolve(), args.repository.resolve(), args.old_audit.resolve()
    timestamp = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8))).isoformat()
    manifest_file = root / "environment/original_repository_manifest_before.csv"
    manifest = {row["File"]: row for row in csv_rows(manifest_file)}
    authority = json.loads((root / "FY2021_crosswalk.json").read_text(encoding="utf-8-sig"))
    canonical = {entry["code"]: entry["group"] for entry in authority["entries"]}
    assert len(canonical) == 66
    workbook_path = root / authority["workbook"]
    assert digest(workbook_path) == authority["workbook_sha256"]
    workbook = openpyxl.load_workbook(workbook_path, read_only=True, data_only=True)
    sheet = workbook["Country Analytical History"]
    assert sheet["AI5"].value == "FY21" and sheet["AI6"].value == 2019
    authority_checks = []
    for entry in authority["entries"]:
        cell = sheet[entry["source_cell"]]
        actual_code = sheet.cell(cell.row, 1).value
        is_nir = entry["code"] == "NIR"
        ok = GROUPS[cell.value] == entry["group"] and actual_code == entry["source_country_code"] and bool(entry["NIR_assumption"]) == is_nir
        if is_nir:
            ok = ok and actual_code == "GBR" and entry["source_cell"] == "AI213" and entry["group"] == "High"
        assert ok, (entry["code"], "canonical differs from frozen workbook")
        authority_checks.append(dict(Code=entry["code"], Group=entry["group"], Source_Cell=entry["source_cell"], NIR_Assumption=is_nir, Pass=ok))
    workbook.close()
    frozen_five = json.loads((root / "environment/mapping_verification.json").read_text(encoding="utf-8"))
    expected_frozen = {record["file"]: record["corrected_sha256"] for record in frozen_five["files"]}
    expected_frozen["01_MultinomialLogisticRegression.Rmd"] = LOGISTIC_FROZEN_SHA256
    original_checks, root_checks, ast_input, diff = [], [], [], []
    for filename in FILES:
        original_path, corrected_path = root / "original_sources" / filename, root / filename
        original_hash, corrected_hash = digest(original_path), digest(corrected_path)
        assert original_hash == manifest[filename]["SHA256"].lower(), (filename, "original_sources preimage changed")
        assert corrected_hash == expected_frozen[filename], (filename, "corrected source changed after freeze")
        original_text, corrected_text = original_path.read_text(encoding="utf-8-sig"), corrected_path.read_text(encoding="utf-8-sig")
        assert map_dictionary(corrected_text) == canonical, (filename, "map differs")
        original_code, corrected_code = r_code(original_text), r_code(corrected_text)
        normalized_old, normalized_new, allowed = normalize_pair(filename, original_code, corrected_code)
        ast_input.append(dict(file=filename, original_code=original_code, corrected_code=corrected_code,
                              normalized_original_code=normalized_old, normalized_corrected_code=normalized_new))
        root_checks.append(dict(File=filename, Frozen_SHA256=expected_frozen[filename], Actual_SHA256=corrected_hash,
                                Matches_Frozen=True, Canonical_66_Map_Matches=True, Explicit_Executable_Whitelist=allowed,
                                Normalized_Original_Code_SHA256=hashlib.sha256(normalized_old.encode()).hexdigest(),
                                Normalized_Corrected_Code_SHA256=hashlib.sha256(normalized_new.encode()).hexdigest(),
                                Presentation_Changes="Markdown/YAML/comment text and explicitly listed output-caption/summary literals only; legacy numerical interpretations visibly labelled"))
        diff.extend(difflib.unified_diff(original_text.splitlines(keepends=True), corrected_text.splitlines(keepends=True),
                                       fromfile="original_sources/" + filename, tofile=filename, n=3))
    for path in sorted((root / "original_sources").rglob("*")):
        if not path.is_file(): continue
        relative = path.relative_to(root / "original_sources").as_posix()
        assert relative in manifest, (relative, "original_sources contains unmanifested file")
        expected = manifest[relative]["SHA256"].lower()
        assert digest(path) == expected, (relative, "original_sources hash mismatch")
        original_checks.append(dict(File=relative, Expected_SHA256=expected, Actual_SHA256=digest(path), Match=True))
    env = dict(os.environ, LC_ALL="C")
    helper = root / "scripts/verify_v2_source_ast.R"
    completed = subprocess.run([str(args.rscript), str(helper)], input=json.dumps(dict(files=ast_input)),
                               capture_output=True, text=True, env=env, check=True)
    ast_result = json.loads(completed.stdout)
    assert ast_result["status"] == "PASS", ast_result
    repository_checks = []
    actual_file_set = {path.relative_to(repo).as_posix() for path in repo.rglob("*") if path.is_file() and ".git" not in path.relative_to(repo).parts}
    assert actual_file_set == set(manifest), "Original repository non-Git file set changed"
    for relative, record in manifest.items():
        path = repo / relative
        actual = digest(path)
        assert actual == record["SHA256"].lower() and path.stat().st_size == int(record["Length"]), (relative, "original repository modified")
        repository_checks.append(dict(File=relative, Bytes=path.stat().st_size, Expected_SHA256=record["SHA256"].lower(), Actual_SHA256=actual, Match=True))
    git = Path(r"C:\Users\Saberken\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe")
    commit = run_git(git, repo, "rev-parse", "HEAD")
    expected_commit = (root / "environment/original_commit.txt").read_text(encoding="utf-8-sig").strip()
    branch = run_git(git, repo, "rev-parse", "--abbrev-ref", "HEAD")
    status = run_git(git, repo, "status", "--porcelain")
    assert commit == expected_commit and branch == "main" and status == "", "Original Git state changed"
    copies = []
    seen = set()
    for path in sorted((root / "results").rglob("*.Rmd")):
        filename = path.name
        assert filename in expected_frozen, (str(path), "Unexpected executed Rmd")
        actual = digest(path)
        assert actual == expected_frozen[filename], (str(path), "Executed copy does not match frozen source")
        seen.add(filename)
        copies.append(dict(Path=path.relative_to(root).as_posix(), Source=filename, SHA256=actual, Matches_Root_and_Frozen=True))
    ledger_path = old_audit / "DELIVERABLE_CHECKS.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8-sig"))
    old_checks = []
    for record in ledger["Required_Files"]:
        path = old_audit / record["File"]
        actual = digest(path)
        assert actual == record["SHA256"].lower() and path.stat().st_size == record["Bytes"], (str(path), "Old audit deliverable changed")
        old_checks.append(dict(File=record["File"], Expected_SHA256=record["SHA256"].lower(), Actual_SHA256=actual, Bytes=path.stat().st_size, Match=True))
    evidence = dict(Status="PASS", Verified_At_Asia_Shanghai=timestamp,
                    Scope="All six frozen Rmd sources and existing executed copies; parse-only AST, authority/preimage hashes; no model fit/data transformation",
                    FY2021_Authority_Workbook_SHA256=digest(workbook_path), Canonical_Workbook_Cells=authority_checks,
                    Source_Contracts=root_checks, R_Native_AST_Contracts=ast_result,
                    Original_Sources_Preimage=original_checks,
                    Original_Repository=dict(Path=str(repo), Branch=branch, Commit=commit, Working_Tree_Status=status,
                                             Manifest_SHA256=digest(manifest_file), Exact_NonGit_File_Set_Unchanged=True, Files=repository_checks),
                    Executed_Copies=copies, Executed_Copy_Coverage=dict(Available=len(seen), Expected=6,
                        Missing_Sources=sorted(set(FILES)-seen), Note="Missing copies are evidence pending, not source changes; rerun after remaining runs"),
                    Old_Audit=dict(Path=str(old_audit), Ledger_SHA256=digest(ledger_path), Primary_Deliverables=old_checks, All_Match=True),
                    Helper_Stderr=completed.stderr.strip(), Verifier_SHA256=digest(Path(__file__)), R_Helper_SHA256=digest(helper))
    (root / "environment/all_six_source_contract.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "environment/source_changes.diff").write_text("".join(diff), encoding="utf-8")
    marker = "\n## Six-source preservation verification\n"
    doc = root / "MAPPING_CHANGES.md"
    previous = doc.read_text(encoding="utf-8").split(marker)[0]
    appendix = (marker + "\n" + f"核验时间：{timestamp}。`scripts/verify_v2_sources.py` 的全部断言通过，记录于 `environment/all_six_source_contract.json`；六份完整差异见 `environment/source_changes.diff`。\n\n"
                + "六份 map 均匹配 canonical 与冻结官方 cells；所有 function AST 完全相同；全部 executable AST 在仅归一化 map、明确显示文字和 Logistic MAXIT250→2000/三处收敛 gate 后完全相同。seed、split/cap、feature recipes、class weights、kernel/formula 和候选/排序逻辑保留。原仓库完整非 Git 文件集/散列/clean Git 状态与原 manifest 相同，original_sources 与原像一致；旧审计六项主要交付物与旧 DELIVERABLE_CHECKS.json 完全匹配。\n\n"
                + f"当前已观察到 {len(seen)}/6 个模型的执行 Rmd 副本，全部与 root/frozen hash 一致；本核验不表示所有渲染已完成，可在全部运行后重复执行。\n")
    doc.write_text(previous + appendix, encoding="utf-8")
    print(json.dumps(dict(Status="PASS", Files=6, Canonical_Cells=len(authority_checks),
                          Function_ASTs_All_Identical=True, Full_Executable_AST_Whitelist_Only=True,
                          Original_Repository_Unchanged=True, Old_Primary_Deliverables_Unchanged=len(old_checks),
                          Executed_Copies_Checked=len(copies), Evidence=str(root / "environment/all_six_source_contract.json")), indent=2))


if __name__ == "__main__":
    main()
