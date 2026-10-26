"""Compare OLD/NEW Validation candidates whose source specs omit Income_Group.

Only reads saved candidates and source constants; never fits or scores models,
and never reads or evaluates Test predictions. Timing values remain separate.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
METRICS = ("Macro_F1", "Weighted_F1", "Accuracy")
MODELS = (
    dict(Model="Multinomial Logistic Regression", File="01_MultinomialLogisticRegression.Rmd", Old_Run="pass1_logistic", New_Run="logistic", Table="audit_ranking.csv", Spec="Spec", Keys=("Spec", "Decay")),
    dict(Model="LDA", File="02_LDA.Rmd", Old_Run="pass1_lda", New_Run="lda", Table="audit_validation_results.csv", Spec="Specification", Keys=("Specification", "Prior")),
    dict(Model="kNN", File="03_kNN.Rmd", Old_Run="pass2_knn", New_Run="knn", Table="audit_ranking.csv", Spec="Spec", Keys=("Spec", "k", "Weighting")),
    dict(Model="SVM", File="04_SVM.Rmd", Old_Run="pass1_svm_with_raw", New_Run="svm", Table="svm_results/validation_candidates.csv", Spec="Spec", Keys=("Spec", "Kernel", "Cost", "Gamma_factor", "Weight")),
    dict(Model="Decision Tree", File="05_DecisionTree.Rmd", Old_Run="pass1_tree", New_Run="tree", Table="audit_ranking.csv", Spec="Spec", Keys=("Spec", "cp", "maxdepth", "minsplit")),
)
R_SPEC_READER = r'''
input <- jsonlite::fromJSON(paste(readLines(file("stdin"),warn=FALSE),collapse="\n"),simplifyVector=FALSE)
extract <- function(path) {
  lines <- readLines(path,warn=FALSE,encoding="UTF-8"); active<-FALSE; code<-character()
  for(line in lines) {
    if(grepl("^\x60\x60\x60\\{r[ ,}]",line)){active<-TRUE;next}
    if(active && grepl("^\x60\x60\x60[[:space:]]*$",line)){active<-FALSE;next}
    if(active)code<-c(code,line)
  }
  expressions <- parse(text=code,keep.source=FALSE); found<-list()
  walk <- function(x) {
    if(missing(x))return(invisible(NULL))
    if(is.call(x) && identical(x[[1]],as.name("<-")) && is.symbol(x[[2]]) && as.character(x[[2]]) %in% c("core","extended","SPECIFICATIONS"))found[[length(found)+1L]]<<-x
    if(is.call(x)||is.expression(x)||is.pairlist(x))for(child in as.list(x))walk(child)
  }
  walk(expressions); e<-new.env(parent=baseenv())
  for(assignment in found) {
    rhs<-assignment[[3]]
    stopifnot(is.call(rhs),as.character(rhs[[1]]) %in% c("c","list"))
    eval(assignment,e)
  }
  stopifnot(exists("SPECIFICATIONS",e,inherits=FALSE),is.list(e$SPECIFICATIONS),length(e$SPECIFICATIONS)>0L)
  list(specifications=e$SPECIFICATIONS,constant_assignments_evaluated=vapply(found,function(x)as.character(x[[2]]),""),
       scope="Only constant c()/list() assignments defining core/extended/SPECIFICATIONS evaluated; no model/data/Test code")
}
results<-lapply(input$files,function(item)list(file=item$file,original=extract(item$old),corrected=extract(item$new)))
cat(jsonlite::toJSON(list(files=results),pretty=TRUE,auto_unbox=TRUE))
'''


def read(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize(value):
    if value in (None, "", "NA", "NaN", "nan", "NULL"):
        return None
    try:
        parsed = Decimal(str(value))
        return parsed if parsed.is_finite() else str(value)
    except InvalidOperation:
        return str(value)


def key(row, fields):
    return tuple(normalize(row[field]) for field in fields)


def config_json(configuration, fields):
    return json.dumps({field: None if value is None else str(value) for field, value in zip(fields, configuration)}, ensure_ascii=False, sort_keys=True)


def separate_times(row):
    return {field: value for field, value in row.items() if "second" in field.lower() or "time" in field.lower()}


def sha(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--old-audit", type=Path, default=ROOT.parent / "audit_20261024_01")
    parser.add_argument("--tolerance", type=float, default=1e-12)
    parser.add_argument("--rscript", type=Path, default=Path(r"C:\Program Files\R\R-4.6.1\bin\Rscript.exe"))
    args = parser.parse_args()
    root, old_audit = args.root.resolve(), args.old_audit.resolve()
    sources = [dict(file=model["File"], old=str(root / "original_sources" / model["File"]), new=str(root / model["File"])) for model in MODELS]
    helper = root / "scripts/read_no_income_specs.R"
    if helper.exists():
        assert helper.read_text(encoding="utf-8") == R_SPEC_READER, "Owned constant-spec helper unexpectedly changed"
    else:
        helper.write_text(R_SPEC_READER, encoding="utf-8")
    done = subprocess.run([str(args.rscript), str(helper)], input=json.dumps(dict(files=sources)),
                          text=True, capture_output=True, env=dict(os.environ, LC_ALL="C"))
    if done.returncode:
        raise RuntimeError(f"Constant-only R spec extraction failed: {done.returncode}; {done.stderr}")
    evidence = json.loads(done.stdout)
    specs_by_file = {item["file"]: item for item in evidence["files"]}
    output, summaries, discrepancies = [], [], []
    for model in MODELS:
        specification_evidence = specs_by_file[model["File"]]
        original_specs = specification_evidence["original"]["specifications"]
        corrected_specs = specification_evidence["corrected"]["specifications"]
        assert original_specs == corrected_specs, (model["Model"], "source feature specifications changed")
        controls = [name for name, features in original_specs.items() if "Income_Group" not in features]
        excluded = [name for name in original_specs if name not in controls]
        old_path = old_audit / "runs" / model["Old_Run"] / model["Table"]
        new_path = root / "results" / model["New_Run"] / model["Table"]
        base = dict(Model=model["Model"], Source_File=model["File"], No_Income_Specifications=", ".join(controls),
                    Excluded_Income_Specifications=", ".join(excluded), Old_Validation_Table=str(old_path), New_Validation_Table=str(new_path), Tolerance=args.tolerance)
        summary = dict(**base, Source_Specifications_Equal=True,
                       Source_No_Income_Features={name: original_specs[name] for name in controls},
                       Original_Source_SHA256=sha(root / "original_sources" / model["File"]), Corrected_Source_SHA256=sha(root / model["File"]))
        if not old_path.exists() or not new_path.exists():
            output.append(dict(**base, Comparison_Status="PENDING", Notes="One or both candidate tables missing; no metric result fabricated"))
            summaries.append(dict(**summary, Status="PENDING", Compared_Candidates=0))
            continue
        old_all, new_all = read(old_path), read(new_path)
        assert all(row[model["Spec"]] in original_specs for row in old_all + new_all), "Observed unknown source specification"
        old_rows = [row for row in old_all if row[model["Spec"]] in controls]
        new_rows = [row for row in new_all if row[model["Spec"]] in controls]
        old_counts = Counter(key(row, model["Keys"]) for row in old_rows)
        new_counts = Counter(key(row, model["Keys"]) for row in new_rows)
        assert all(count == 1 for count in old_counts.values()) and all(count == 1 for count in new_counts.values()), (model["Model"], "duplicate control configurations")
        old_map, new_map = {key(row, model["Keys"]): row for row in old_rows}, {key(row, model["Keys"]): row for row in new_rows}
        config_equal = set(old_map) == set(new_map)
        maximum = {metric: 0.0 for metric in METRICS}
        matched, failed, unpaired = 0, 0, 0
        for configuration in sorted(set(old_map) | set(new_map), key=str):
            old_row, new_row = old_map.get(configuration), new_map.get(configuration)
            row = dict(**base, Specification=(old_row or new_row)[model["Spec"]], Configuration=config_json(configuration, model["Keys"]))
            if old_row is None or new_row is None:
                row.update(Comparison_Status="UNPAIRED", Notes="Missing matching control configuration in " + ("old" if old_row is None else "new"))
                output.append(row); discrepancies.append(row); unpaired += 1
                continue
            finite, equal = True, True
            for metric in METRICS:
                old_value, new_value = float(old_row[metric]), float(new_row[metric])
                valid = math.isfinite(old_value) and math.isfinite(new_value)
                difference = new_value - old_value if valid else None
                passed = valid and abs(difference) <= args.tolerance
                finite = finite and valid; equal = equal and passed
                if valid: maximum[metric] = max(maximum[metric], abs(difference))
                row.update({"Old_"+metric: old_value, "New_"+metric: new_value, "Delta_"+metric: difference, metric+"_Within_Tolerance": passed})
            row.update(All_Three_Metrics_Finite=finite, All_Three_Metrics_Within_Tolerance=equal,
                       Old_Timing_Fields=json.dumps(separate_times(old_row), ensure_ascii=False, sort_keys=True),
                       New_Timing_Fields=json.dumps(separate_times(new_row), ensure_ascii=False, sort_keys=True),
                       Old_Convergence=old_row.get("Convergence", ""), New_Convergence=new_row.get("Convergence", ""),
                       Old_Candidate_Status=old_row.get("Status", ""), New_Candidate_Status=new_row.get("Status", ""),
                       Comparison_Status="MATCH" if equal else "MISMATCH", Notes="Validation-only control comparison; elapsed times excluded; income-containing specs intentionally excluded")
            if equal: matched += 1
            else: failed += 1; discrepancies.append(row)
            output.append(row)
        if model["Model"] == "Multinomial Logistic Regression":
            assert all(row.get("Convergence") == "0" for row in old_rows + new_rows), "No-income Logistic control unexpectedly nonconverged"
        summaries.append(dict(**summary, Status="PASS" if config_equal and failed == 0 and unpaired == 0 else "FAIL",
                              Old_Controls=len(old_rows), New_Controls=len(new_rows), Compared_Candidates=matched+failed,
                              Configurations_Identical=config_equal, Metric_Matches=matched, Metric_Discrepancies=failed,
                              Unpaired_Configurations=unpaired, Maximum_Absolute_Metric_Differences=maximum,
                              Old_Table_SHA256=sha(old_path), New_Table_SHA256=sha(new_path)))
    stamp = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8))).isoformat()
    for row in output: row["Verified_At_Asia_Shanghai"] = stamp
    destination = root / "independent/no_income_control_comparison.csv"
    columns = list(dict.fromkeys(field for row in output for field in row))
    with destination.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns); writer.writeheader(); writer.writerows(output)
    total = sum(summary["Compared_Candidates"] for summary in summaries)
    lines = ["# 不含 Income_Group 的旧/新 Validation 候选控制核验", "", f"核验时间：{stamp}。容差：{args.tolerance:g}。只读源码常量和保存的 Validation 候选表；没有拟合、没有读取/额外评价 Test 预测。", "",
             "## 结果", "", f"当前配对候选总数 **{total}**；实际数值/配置不一致 **{len(discrepancies)}**。", "",
             "| Model | 从原/新 source SPECIFICATIONS 独立识别的无 income 规格 | OLD/NEW 候选 | 三项指标最大绝对差 | 结论 |", "| --- | --- | --- | --- | --- |"]
    for summary in summaries:
        maxima = "; ".join(f"{metric}={summary.get('Maximum_Absolute_Metric_Differences',{}).get(metric,'Pending')}" for metric in METRICS)
        lines.append(f"| {summary['Model']} | {summary['No_Income_Specifications']} | {summary.get('Old_Controls','Pending')}/{summary.get('New_Controls','Pending')} | {maxima} | {summary['Status']} |")
    lines.extend(["", "## 方法与范围", "",
                  "- R parser 读取旧 original_sources 与新 root Rmd 的 chunks，仅在干净 base environment 中计算定义 core/extended/SPECIFICATIONS 的常量 c()/list() assignments。两版 specification dictionaries 必须逐项相等，随后按是否包含 Income_Group 识别 controls；没有硬编码 no-income spec 名单或候选总数。",
                  "- 在每个 control specification 内按原 hyperparameter 配置 keys 对齐，检查配置集合和唯一性。比较 Macro_F1/Weighted_F1/Accuracy 的实际数值，逐项要求 absolute difference ≤1e-12；CSV 保存双方值、差、配对配置和 PASS。",
                  "- Seconds/Search_Seconds/Fit_seconds/Predict_seconds 等计时字段分开放入 CSV 的 Old_Timing_Fields/New_Timing_Fields，不用其相等作为通过条件；并行/机器负载可改变耗时。",
                  "- Logistic MAXIT 上限250→2000及新增收敛 gate 属获准修正；本检查确认两个 no-income 候选在 OLD 和 NEW 均 convergence=0。没有声称恢复或核对未保存的逐次优化轨迹。",
                  "- 包含 Income_Group 的规格被明确排除；该组受映射更新影响，score 变化属于预期，不能算作本 preservation control 失败。",
                  "- 相同 controls 的 Validation 结果支持本次实际执行未意外改变无 income 流程；不替代独立的 source AST、split/cap identity、完整 metric 或外推有效性检查。", "", "## 可复查来源", ""])
    for summary in summaries:
        lines.extend([f"### {summary['Model']}", "", f"源文件：{summary['Source_File']}；无 income features：`{json.dumps(summary['Source_No_Income_Features'],ensure_ascii=False)}`。",
                      f"OLD table：`{summary['Old_Validation_Table']}`；SHA-256：`{summary.get('Old_Table_SHA256','Pending')}`。",
                      f"NEW table：`{summary['New_Validation_Table']}`；SHA-256：`{summary.get('New_Table_SHA256','Pending')}`。", ""])
    if discrepancies:
        lines.extend(["## 不一致明细", "", "```json", json.dumps(discrepancies, ensure_ascii=False, indent=2), "```", ""])
    (root / "independent/no_income_control_comparison.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(dict(Status="PASS" if all(summary["Status"] == "PASS" for summary in summaries) else "NOT_ALL_PASS",
                          Total_Compared_Candidates=total, Discrepancies=len(discrepancies), Summaries=summaries,
                          Scope="No fits, no Test evaluation, no original outputs changed"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
