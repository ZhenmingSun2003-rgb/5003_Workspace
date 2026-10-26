"""Independent evaluation of already rendered v2 models. Never fits or selects a model.

Usage: python scripts/evaluate_v2.py [--root PATH] [--old-root PATH]
       [--bootstrap 5000] [--skip-bootstrap]
Missing/failed runs remain Pending/Failed; unknown predictions and identity failures
withhold model scores instead of substituting author-reported or v1 results.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

LABELS = ["Full-time", "Part-time", "Self-employed", "Retired", "Housewife", "Student", "Unemployed", "Other"]
LABEL_ID = {label: i for i, label in enumerate(LABELS)}
EXPECTED_SHA256 = "ee392676dbb42dde0ea74ebf643862f3900e7d13a7aa03842ed2d7665ac98ee0"
EXPECTED_MD5 = "98bf573170f0cb6bd65a4e9a8070d4d8"
SPECS = [
    ("Training-majority", "baseline", "baseline.Rmd", ["independent_export_pred_majority.csv"], ["majority_eval", "majority_met"]),
    ("Training-prior random", "baseline", "baseline.Rmd", ["independent_export_pred_chance.csv"], ["chance_eval", "chance_met"]),
    ("Multinomial Logistic Regression", "logistic", "01_MultinomialLogisticRegression.Rmd", ["independent_export_predicted.csv"], ["met", "test_eval"]),
    ("LDA", "lda", "02_LDA.Rmd", ["independent_export_test_prediction.csv", "model_outputs/lda_test_predictions.csv", "STAT5003_B_lda_results/lda_test_predictions.csv"], ["test_evaluation", "test_eval"]),
    ("kNN", "knn", "03_kNN.Rmd", ["independent_export_test_prediction.csv", "model_outputs/knn_test_predictions.csv"], ["test_eval"]),
    ("SVM", "svm", "04_SVM.Rmd", ["independent_export_final_prediction.csv", "svm_results/test_predictions.csv", "model_outputs/test_predictions.csv"], ["final_metrics", "test_eval"]),
    ("Decision Tree", "tree", "05_DecisionTree.Rmd", ["independent_export_test_prediction.csv", "model_outputs/decision_tree_test_predictions.csv"], ["test_eval"]),
]
OLD_PREDICTIONS = {
    "Training-majority": ("pass1_baseline", "independent_export_pred_majority.csv"),
    "Training-prior random": ("pass1_baseline", "independent_export_pred_chance.csv"),
    "Multinomial Logistic Regression": ("pass1_logistic", "independent_export_predicted.csv"),
    "LDA": ("pass1_lda", "STAT5003_B_lda_results/lda_test_predictions.csv"),
    "kNN": ("pass2_knn", "model_outputs/knn_test_predictions.csv"),
    "SVM": ("pass1_svm_with_raw", "svm_results/test_predictions.csv"),
    "Decision Tree": ("pass1_tree", "model_outputs/decision_tree_test_predictions.csv"),
}
COMPARISON_FIELDS = ["Model", "Execution_Status", "Test_N", "Macro_F1", "Weighted_F1", "Accuracy", "Delta_vs_Majority", "Delta_vs_Logistic", "Validation_Macro_F1", "Selected_Configuration", "Notes"]


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def json_read(path, default=None):
    if not Path(path).exists():
        return {} if default is None else default
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def clean_json(obj):
    if isinstance(obj, dict):
        return {k: clean_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean_json(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return clean_json(obj.tolist())
    if isinstance(obj, np.generic):
        return clean_json(obj.item())
    if isinstance(obj, float) and not np.isfinite(obj):
        return None
    return obj


def hash_file(path):
    sha, md5 = hashlib.sha256(), hashlib.md5()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(2**20), b""):
            sha.update(block)
            md5.update(block)
    return {"SHA256": sha.hexdigest(), "MD5": md5.hexdigest(), "Bytes": Path(path).stat().st_size}


def hash_ids(ids):
    return hashlib.sha256("".join(f"{int(i)}\n" for i in ids).encode("ascii")).hexdigest()


def metrics_from_confusion(cm):
    cm = np.asarray(cm, dtype=float)
    tp, support, predicted = np.diag(cm), cm.sum(1), cm.sum(0)
    precision = np.divide(tp, predicted, out=np.zeros(8), where=predicted > 0)
    recall = np.divide(tp, support, out=np.zeros(8), where=support > 0)
    f1 = np.divide(2 * tp, support + predicted, out=np.zeros(8), where=support + predicted > 0)
    total = cm.sum()
    overall = {"Accuracy": float(tp.sum() / total), "Macro_Precision": float(precision.mean()),
               "Macro_Recall": float(recall.mean()), "Macro_F1": float(f1.mean()),
               "Weighted_F1": float(np.dot(support, f1) / total)}
    return overall, precision, recall, f1


def prediction_codes(path, expected_ids, expected_truth):
    rows = read_csv(path)
    if not rows:
        raise ValueError("Empty prediction file")
    first = rows[0]
    idkey = next((k for k in ("row_id", "CSV_row", "Row_ID") if k in first), None)
    ykey = next((k for k in ("truth", "True", "Truth") if k in first), None)
    pkey = next((k for k in ("prediction", "Predicted", "Prediction") if k in first), None)
    if None in (idkey, ykey, pkey):
        raise ValueError(f"Missing row identity/truth/prediction columns: {list(first)}")
    ids = np.array([int(r[idkey]) for r in rows], dtype=np.int64)
    truth = np.array([r[ykey] for r in rows])
    prediction = np.array([r[pkey] for r in rows])
    if not np.array_equal(ids, expected_ids):
        raise ValueError("Test row IDs/order do not exactly match independent reference")
    if len(np.unique(ids)) != len(ids):
        raise ValueError("Duplicate Test row IDs")
    if not np.array_equal(truth, expected_truth):
        raise ValueError("Test truth/order do not exactly match independent reference")
    unknown = set(prediction) - set(LABELS)
    if unknown:
        raise ValueError(f"Unknown/missing predicted classes: {sorted(unknown)}")
    return np.array([LABEL_ID[x] for x in prediction], dtype=np.int64)


def read_ids(path):
    rows = read_csv(path)
    if not rows:
        return np.array([], dtype=np.int64)
    key = next((k for k in ("Row_ID", "row_id", "CSV_row", "local_dev_id", "local_val_id", "fit_id") if k in rows[0]), next(iter(rows[0])))
    return np.array([int(r[key]) for r in rows], dtype=np.int64)


def source_map(path):
    text = Path(path).read_text(encoding="utf-8-sig")
    start = text.index("WB_GROUPS <- list(")
    end = re.search(r"\ncountry_(?:map|group)\s*<-", text[start:])
    block = text[start:start + end.start()] if end else text[start:start + 2500]
    mapping = {}
    pattern = r"(`?(?:Low|Lower-middle|Upper-middle|High|Unclassified)`?)\s*=\s*(?:c\((.*?)\)|character\(0\))"
    for match in re.finditer(pattern, block, re.S):
        group = match.group(1).strip("`")
        for country in re.findall(r'"([A-Z]{3})"', match.group(2) or ""):
            if country in mapping:
                raise ValueError(f"Duplicate country mapping {country}")
            mapping[country] = group
    if not mapping:
        raise ValueError("No country mapping parsed")
    return mapping


def choose_configuration(rd, model):
    order = {"Multinomial Logistic Regression": ["audit_selected.csv", "audit_best.csv", "audit_ranking.csv"],
             "LDA": ["audit_selected.csv", "audit_best.csv"], "kNN": ["audit_best.csv"],
             "SVM": ["audit_winner.csv", "audit_best.csv"], "Decision Tree": ["audit_best.csv"]}.get(model, [])
    for name in order:
        path = rd / name
        if path.exists():
            rows = read_csv(path)
            if rows:
                selected = rows[0]
                keys = ["Spec", "Specification", "Prior", "Kernel", "Cost", "Gamma", "Weight", "k", "Weighting", "cp", "maxdepth", "minsplit", "Decay"]
                cfg = "; ".join(f"{k}={selected[k]}" for k in keys if k in selected)
                return cfg, selected.get("Macro_F1", selected.get("Validation_Macro_F1", "")), selected, str(path)
    return "", "", {}, ""


def paired_bootstrap(truth, pred_a, pred_b, replicates, seed):
    """Joint-pattern multinomial resampling is exactly paired ordinary row bootstrap."""
    joint, counts = np.unique(np.column_stack((truth, pred_a, pred_b)), axis=0, return_counts=True)
    rng = np.random.default_rng(seed)
    draws = np.empty(replicates, dtype=float)
    index_a = joint[:, 0] * 8 + joint[:, 1]
    index_b = joint[:, 0] * 8 + joint[:, 2]
    for start in range(0, replicates, 200):
        weights = rng.multinomial(len(truth), counts / counts.sum(), size=min(200, replicates - start))
        for offset, weight in enumerate(weights):
            cm_a = np.bincount(index_a, weights=weight, minlength=64).reshape(8, 8)
            cm_b = np.bincount(index_b, weights=weight, minlength=64).reshape(8, 8)
            f_a = np.divide(2 * np.diag(cm_a), cm_a.sum(0) + cm_a.sum(1), out=np.zeros(8), where=cm_a.sum(0) + cm_a.sum(1) > 0).mean()
            f_b = np.divide(2 * np.diag(cm_b), cm_b.sum(0) + cm_b.sum(1), out=np.zeros(8), where=cm_b.sum(0) + cm_b.sum(1) > 0).mean()
            draws[start + offset] = f_a - f_b
    lo, hi = np.quantile(draws, [0.025, 0.975])
    return float(lo), float(hi)


def evaluate(root, old_root, bootstrap=5000, skip_bootstrap=False):
    independent = root / "independent"
    independent.mkdir(parents=True, exist_ok=True)
    issues, comparison, pcs, cms, splitrows, metric_checks, execution, oldnew, bootstrap_rows = [], [], [], [], [], [], [], [], []
    old_scores = {r["Model"]: r for r in read_csv(old_root / "model_comparison.csv")}
    fresh_ref_path = independent / "reference_split.csv"
    reference_path = fresh_ref_path if fresh_ref_path.exists() else old_root / "independent/reference_split.csv"
    reference = read_csv(reference_path)
    old_reference = read_csv(old_root / "independent/reference_split.csv")
    fresh_reference_verified = fresh_ref_path.exists() and reference == old_reference
    if not fresh_ref_path.exists():
        issues.append({"Model": "All", "Severity": "Pending", "Issue": "Fresh split reconstruction unavailable; immutable v1 expected reference used only provisionally."})
    elif not fresh_reference_verified:
        issues.append({"Model": "All", "Severity": "Major", "Issue": "Fresh independently reconstructed reference differs from immutable v1 reference."})
    ref_ids = np.array([int(r["row_id"]) for r in reference], dtype=np.int64)
    ref_truth = np.array([r["truth"] for r in reference])
    partitions = np.array([r["partition"] for r in reference])
    test_ids, truth = ref_ids[partitions == "Test"], ref_truth[partitions == "Test"]
    truth_codes = np.array([LABEL_ID[x] for x in truth], dtype=np.int64)
    pool, original_train, validation = ref_ids[partitions != "Test"], ref_ids[partitions == "Train"], ref_ids[partitions == "Validation"]
    localdev, localval = np.searchsorted(pool, original_train) + 1, np.searchsorted(pool, validation) + 1
    data_path = root / "WVS_Wave7_cleaned_for_modelling.csv"
    data_integrity = {"Path": str(data_path), "Reference_Path": str(reference_path), "Fresh_Reference_Verified": fresh_reference_verified}
    data_ok = False
    raw = None
    try:
        data_integrity.update(hash_file(data_path))
        raw = pd.read_csv(data_path, usecols=["Q279", "B_COUNTRY_ALPHA"], dtype=str)
        data_integrity["Rows"] = len(raw)
        data_integrity["Target_Distribution"] = raw["Q279"].value_counts().sort_index().to_dict()
        data_integrity["Hash_Match"] = data_integrity["SHA256"] == EXPECTED_SHA256 and data_integrity["MD5"] == EXPECTED_MD5
        targets = np.array([LABELS[int(x) - 1] if x in map(str, range(1, 9)) else "INVALID" for x in raw["Q279"]])
        data_integrity["Reference_Targets_Match"] = len(raw) == 95987 and np.array_equal(targets, ref_truth)
        data_ok = data_integrity["Hash_Match"] and data_integrity["Reference_Targets_Match"] and len(ref_ids) == 95987
    except Exception as err:
        data_integrity["Error"] = str(err)
    if not data_ok:
        issues.append({"Model": "All", "Severity": "Critical", "Issue": "Shared data integrity failed; comparative performance is withheld."})

    maps, map_rows, source_versions = {}, [], []
    crosswalk = read_csv(root / "source_evidence/crosswalk_comparison_all_66.csv")
    expected_map = {r["Country_Code"]: ("High" if r["Country_Code"] == "NIR" else r["Official_FY21_Group"]) for r in crosswalk}
    for filename in dict.fromkeys(s[2] for s in SPECS):
        path = root / filename
        try:
            maps[filename] = source_map(path)
            original = root / "original_sources" / filename
            current_hash = hash_file(path)
            original_hash = hash_file(original) if original.exists() else {}
            source_versions.append({"File": filename, "V2_SHA256": current_hash["SHA256"], "V2_MD5": current_hash["MD5"], "Original_SHA256": original_hash.get("SHA256", ""), "Different_From_Original": current_hash["SHA256"] != original_hash.get("SHA256")})
            for code in sorted(set(expected_map) | set(maps[filename])):
                actual, expected = maps[filename].get(code, "MISSING"), expected_map.get(code, "UNEXPECTED")
                map_rows.append({"File": filename, "Country_Code": code, "V2_Group": actual, "Official_FY21_Expected": expected, "Match": actual == expected, "NIR_Assumption": code == "NIR"})
        except Exception as err:
            issues.append({"Model": filename, "Severity": "Pending", "Issue": f"Source map verification unavailable: {err}"})
    maps_valid = len(maps) == 6 and all(m == expected_map for m in maps.values())
    map_changes = []
    for row in crosswalk:
        code = row["Country_Code"]
        if row["Original_Group"] != expected_map[code]:
            map_changes.append({"Country_Code": code, "Old_Group": row["Original_Group"], "V2_Group": expected_map[code], "CSV_Rows": int(row["CSV_Rows"]), "Official_Cell": row["Official_Cell"]})

    predictions, metric_by_model, validities, configurations = {}, {}, {}, {}
    for name, run, filename, prediction_options, object_aliases in SPECS:
        rd = root / "results" / run
        status = json_read(rd / "execution_status.json")
        runtime = json_read(rd / "audit_runtime_summary.json")
        state = "Success" if status.get("Success") is True else ("Failed" if status else "Pending")
        row = {field: "" for field in COMPARISON_FIELDS}
        row.update(Model=name, Execution_Status=state)
        config, validation_f1, selected, config_path = choose_configuration(rd, name)
        if name == "Training-majority":
            config = "80% development majority; numeric main seed5003"
        elif name == "Training-prior random":
            config = "80% development class priors; one random draw seed5004"
        row.update(Selected_Configuration=config, Validation_Macro_F1=validation_f1)
        configurations[name] = {"Selected": selected, "File": config_path}
        valid = {"Model": name, "Run": run, "Execution_Status": state, "Prediction_Identity_Verified": False,
                 "Metric_Arithmetic_Verified": False, "Original_Overall_Matches": None,
                 "Numeric_Main_Seed_Verified": False, "Runtime_Data_Path_and_MD5_Verified": False,
                 "Runtime_Label_Order_Verified": False, "All_Required_Splits_Verified": False,
                 "Runtime_Income_Map_Verified": False, "Source_Unchanged_Verified": False,
                 "Final_Convergence": runtime.get("Final_Convergence"), "Candidate_Convergence_All_Zero": None,
                 "Repeat_V2_Execution_Verified": False}
        if not name.startswith("Training-") or name == "Training-majority":
            execution.append({"Model": name, "Run": run, "File": filename, "Execution_Status": state,
                              "Elapsed_Seconds": status.get("Elapsed_Seconds", ""), "Error": status.get("Error") or "",
                              "Official_Executions_Requested": 1, "Source_MD5": status.get("Source_MD5", "")})
        if runtime:
            seed = runtime.get("Seed")
            seed_type = runtime.get("Seed_Type", "")
            valid["Numeric_Main_Seed_Verified"] = seed == 5003 and not isinstance(seed, str) and seed_type in ("double", "integer", "numeric")
            valid["Runtime_Label_Order_Verified"] = runtime.get("Labels") == LABELS
            try:
                valid["Runtime_Data_Path_and_MD5_Verified"] = Path(runtime.get("Data_Path", "")).resolve() == data_path.resolve() and runtime.get("Data_MD5") == EXPECTED_MD5
            except Exception:
                pass
            map_export = rd / "audit_actual_income_map.csv"
            if map_export.exists():
                actual_map_rows = read_csv(map_export)
                actual_map = {r["Country"]: r["Income_Group"] for r in actual_map_rows}
                valid["Runtime_Income_Map_Verified"] = actual_map == expected_map and len(actual_map_rows) == len(expected_map)
            source_version = next((r for r in source_versions if r["File"] == filename), {})
            valid["Source_Unchanged_Verified"] = (status.get("Source_Unchanged_During_Render") is True and status.get("Source_MD5") == source_version.get("V2_MD5"))
        for label, result in (("numeric_seed", valid["Numeric_Main_Seed_Verified"]), ("label_order", valid["Runtime_Label_Order_Verified"]), ("data_path_MD5", valid["Runtime_Data_Path_and_MD5_Verified"]), ("actual_income_map", valid["Runtime_Income_Map_Verified"]), ("rendered_source_unchanged", valid["Source_Unchanged_Verified"])):
            if status and not result:
                issues.append({"Model": name, "Severity": "Major" if state == "Success" else "Observation", "Issue": f"Runtime contract evidence missing or failed: {label}"})

        model_split_rows = []
        if not name.startswith("Training-") or name == "Training-majority":
            split_defs = [("Final_refit", "audit_train_id.csv", pool, 5003), ("Test", "audit_test_id.csv", test_ids, 5003),
                          ("Validation_local", "audit_val_id.csv", localval, 5005)]
            if name != "Multinomial Logistic Regression":
                split_defs.append(("Initial_Train_local", "audit_dev_id.csv", localdev, 5005))
            for partition, relative, expected_ids, partition_seed in split_defs:
                target = rd / relative
                actual_ids = read_ids(target) if target.exists() else np.array([], dtype=np.int64)
                match = target.exists() and np.array_equal(actual_ids, expected_ids)
                evidence = "Verified" if match else ("Missing" if not target.exists() else "Mismatch")
                split_row = {"Model": name, "Run": run, "Partition": partition, "Expected_N": len(expected_ids), "Actual_N": len(actual_ids),
                             "Expected_ID_SHA256": hash_ids(expected_ids), "Actual_ID_SHA256": hash_ids(actual_ids) if target.exists() else "",
                             "Main_Seed": 5003, "Partition_Seed": partition_seed, "Seed_Type": runtime.get("Seed_Type", ""),
                             "Data_MD5": runtime.get("Data_MD5", ""), "Data_Path": runtime.get("Data_Path", ""),
                             "Identity_Match": match, "Verification": evidence, "Fresh_Reference_Verified": fresh_reference_verified,
                             "Notes": "Local within 80% pool" if partition.endswith("local") else "Original CSV row IDs"}
                model_split_rows.append(split_row)
            if name == "Multinomial Logistic Regression":
                val_file = rd / "audit_val_id.csv"
                dev_file = rd / "audit_dev_id.csv"
                if val_file.exists():
                    recovered = np.setdiff1d(np.arange(1, len(pool) + 1), read_ids(val_file))
                    model_split_rows.append({"Model": name, "Run": run, "Partition": "Original_Initial_Train_local", "Expected_N": len(localdev), "Actual_N": len(recovered), "Expected_ID_SHA256": hash_ids(localdev), "Actual_ID_SHA256": hash_ids(recovered), "Main_Seed": 5003, "Partition_Seed": 5005, "Identity_Match": np.array_equal(recovered, localdev), "Verification": "Recovered from unchanged Validation complement", "Fresh_Reference_Verified": fresh_reference_verified})
                cap_path = independent / "reference_cap_25000.csv"
                if not cap_path.exists():
                    cap_path = old_root / "independent/reference_cap_25000.csv"
                expected_cap = np.array([int(r["local_dev_id"]) for r in read_csv(cap_path)], dtype=np.int64)
                actual_cap = read_ids(dev_file) if dev_file.exists() else np.array([], dtype=np.int64)
                allowed = bool(np.isin(actual_cap, localdev).all()) if len(actual_cap) else False
                model_split_rows.append({"Model": name, "Run": run, "Partition": "Candidate_Fit_local", "Expected_N": len(expected_cap), "Actual_N": len(actual_cap), "Expected_ID_SHA256": hash_ids(expected_cap), "Actual_ID_SHA256": hash_ids(actual_cap) if dev_file.exists() else "", "Main_Seed": 5003, "Partition_Seed": 5006, "Identity_Match": np.array_equal(actual_cap, expected_cap) and allowed, "Verification": "Exact capped subset and permitted initial-Train membership" if dev_file.exists() else "Missing", "Fresh_Reference_Verified": fresh_reference_verified, "Notes": "Capped candidate subset is not the shared original Train"})
            if name == "SVM":
                cap_path = independent / "reference_cap_10000.csv"
                if not cap_path.exists():
                    cap_path = old_root / "independent/reference_cap_10000.csv"
                cap_ref = read_csv(cap_path)
                expected_fit = np.array([int(r["fit_id"]) for r in cap_ref])
                fit_path = rd / "audit_fit_id.csv"
                actual_fit = read_ids(fit_path) if fit_path.exists() else np.array([], dtype=np.int64)
                model_split_rows.append({"Model": name, "Run": run, "Partition": "Candidate_Fit_within_initial_Train", "Expected_N": len(expected_fit), "Actual_N": len(actual_fit), "Expected_ID_SHA256": hash_ids(expected_fit), "Actual_ID_SHA256": hash_ids(actual_fit) if fit_path.exists() else "", "Main_Seed": 5003, "Partition_Seed": 5006, "Identity_Match": np.array_equal(actual_fit, expected_fit), "Verification": "Exact 9997 capped initial-Train subset" if fit_path.exists() else "Missing", "Fresh_Reference_Verified": fresh_reference_verified})
                original_fit_path = next((rd / relative for relative in ("svm_results/candidate_fit_rows.csv", "model_outputs/candidate_fit_rows.csv") if (rd / relative).exists()), None)
                expected_original_fit = np.array([int(r["row_id"]) for r in cap_ref], dtype=np.int64)
                actual_original_fit = read_ids(original_fit_path) if original_fit_path else np.array([], dtype=np.int64)
                model_split_rows.append({"Model": name, "Run": run, "Partition": "Candidate_Fit_original_CSV_rows", "Expected_N": len(expected_original_fit), "Actual_N": len(actual_original_fit), "Expected_ID_SHA256": hash_ids(expected_original_fit), "Actual_ID_SHA256": hash_ids(actual_original_fit) if original_fit_path else "", "Main_Seed": 5003, "Partition_Seed": 5006, "Identity_Match": np.array_equal(actual_original_fit, expected_original_fit) and bool(np.isin(actual_original_fit, original_train).all()), "Verification": "Exact original CSV identity and permitted initial-Train membership" if original_fit_path else "Missing", "Fresh_Reference_Verified": fresh_reference_verified})
            for split_row in model_split_rows:
                split_row.setdefault("Seed", 5003)
                split_row.setdefault("Seed_Type", runtime.get("Seed_Type", ""))
                split_row.setdefault("Data_MD5", runtime.get("Data_MD5", ""))
                split_row.setdefault("Data_Path", runtime.get("Data_Path", ""))
            splitrows.extend(model_split_rows)
            valid["All_Required_Splits_Verified"] = bool(model_split_rows) and all(r["Identity_Match"] for r in model_split_rows)
            if state == "Success" and not valid["All_Required_Splits_Verified"]:
                failed_parts = [r["Partition"] for r in model_split_rows if not r["Identity_Match"]]
                issues.append({"Model": name, "Severity": "Major", "Issue": "Required split identity evidence failed or missing: " + ", ".join(failed_parts)})
        elif name == "Training-prior random":
            valid["All_Required_Splits_Verified"] = validities.get("Training-majority", {}).get("All_Required_Splits_Verified", False)

        ranking_path = next((rd / f for f in ("audit_ranking.csv", "audit_validation_results.csv") if (rd / f).exists()), None)
        if ranking_path:
            candidates = read_csv(ranking_path)
            valid["Candidate_Count"] = len(candidates)
            expected_candidates = {"Multinomial Logistic Regression": 6, "LDA": 6, "kNN": 54, "SVM": 48, "Decision Tree": 54}.get(name)
            valid["Expected_Candidate_Count"] = expected_candidates
            if expected_candidates is not None:
                valid["Candidate_Count_Matches"] = len(candidates) == expected_candidates
                if not valid["Candidate_Count_Matches"]:
                    issues.append({"Model": name, "Severity": "Major", "Issue": f"Candidate table has {len(candidates)} rows, expected {expected_candidates}."})
            if candidates and "Status" in candidates[0]:
                valid["All_Candidate_Status_Ok"] = all(r["Status"] == "ok" for r in candidates)
                if not valid["All_Candidate_Status_Ok"]:
                    issues.append({"Model": name, "Severity": "Major", "Issue": "At least one candidate status is not ok."})
        elif state == "Success" and name in ("Multinomial Logistic Regression", "LDA", "kNN", "SVM", "Decision Tree"):
            issues.append({"Model": name, "Severity": "Major", "Issue": "Successful learned-model render lacks exported candidate table; full prespecified search completion is unverified."})
        if name == "Multinomial Logistic Regression" and ranking_path:
            candidates = read_csv(ranking_path)
            codes = [r.get("Convergence") for r in candidates]
            if codes and all(c is not None and c != "" for c in codes):
                valid["Candidate_Convergence_All_Zero"] = all(float(c) == 0 for c in codes)
            valid["Candidate_Count"] = len(candidates)
            if valid["Candidate_Convergence_All_Zero"] is False:
                issues.append({"Model": name, "Severity": "Major", "Issue": "At least one v2 candidate has nonzero convergence code."})
        if name == "Multinomial Logistic Regression" and state == "Success" and valid["Final_Convergence"] != 0:
            issues.append({"Model": name, "Severity": "Major", "Issue": "Successful render lacks verified final convergence=0."})

        if state == "Success" and data_ok:
            available = [rd / f for f in prediction_options if (rd / f).exists()]
            if not available:
                row["Notes"] = "Execution succeeded; standardized Test prediction export unavailable."
                issues.append({"Model": name, "Severity": "Major", "Issue": row["Notes"]})
            else:
                try:
                    codes = prediction_codes(available[0], test_ids, truth)
                    for alternate in available[1:]:
                        if not np.array_equal(codes, prediction_codes(alternate, test_ids, truth)):
                            raise ValueError(f"Prediction exports disagree: {alternate}")
                    cm = np.bincount(truth_codes * 8 + codes, minlength=64).reshape(8, 8)
                    metrics, precision, recall, f1 = metrics_from_confusion(cm)
                    predictions[name], metric_by_model[name] = codes, metrics
                    valid.update(Prediction_Identity_Verified=True, Metric_Arithmetic_Verified=True, Prediction_Export=str(available[0]))
                    row.update(Test_N=len(codes), **{k: metrics[k] for k in ("Macro_F1", "Weighted_F1", "Accuracy")})
                    row["Notes"] = "Independent zero-division=0 metrics; one official v2 execution; no v2 repeat claimed."
                    for i, label in enumerate(LABELS):
                        pcs.append({"Model": name, "Class": label, "Support": int(cm.sum(1)[i]), "Predicted_Count": int(cm.sum(0)[i]), "Precision": float(precision[i]), "Recall": float(recall[i]), "F1": float(f1[i])})
                        for j, pred_label in enumerate(LABELS):
                            cms.append({"Model": name, "True_Class": label, "Predicted_Class": pred_label, "Count": int(cm[i, j]), "Row_Percent": float(100 * cm[i, j] / cm.sum(1)[i])})
                    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", name)
                    write_csv(independent / f"confusion_{safe_name}.csv", [{"True": LABELS[i], **{LABELS[j]: int(cm[i, j]) for j in range(8)}} for i in range(8)])
                    orig_file = rd / "audit_original_overall.csv"
                    if orig_file.exists():
                        matches = [r for r in read_csv(orig_file) if r.get("Object") in object_aliases]
                        if matches:
                            agrees = True
                            for original in matches:
                                for metric in ("Macro_F1", "Weighted_F1", "Accuracy"):
                                    if metric not in original:
                                        continue
                                    difference = metrics[metric] - float(original[metric])
                                    agrees = agrees and abs(difference) < 1e-12
                                    metric_checks.append({"Model": name, "Object": original.get("Object"), "Metric": metric, "Independent": metrics[metric], "Original": float(original[metric]), "Difference": difference, "Verified": abs(difference) < 1e-12})
                            valid["Original_Overall_Matches"] = agrees
                            if not agrees:
                                issues.append({"Model": name, "Severity": "Major", "Issue": "Independent Test metrics differ from original computed metrics."})
                            obj = matches[0].get("Object")
                            pc_path = rd / f"audit_original_per_class_{obj}.csv"
                            if pc_path.exists():
                                original_pc = read_csv(pc_path)
                                pc_agrees = len(original_pc) == 8 and [r.get("Class") for r in original_pc] == LABELS
                                if pc_agrees:
                                    for i, original_pc_row in enumerate(original_pc):
                                        for metric, independent_value in (("Precision", precision[i]), ("Recall", recall[i]), ("F1", f1[i])):
                                            if metric in original_pc_row:
                                                difference = float(independent_value) - float(original_pc_row[metric])
                                                ok = abs(difference) <= 0.00005000001
                                                pc_agrees = pc_agrees and ok
                                                metric_checks.append({"Model": name, "Object": obj, "Metric": f"{LABELS[i]}:{metric}", "Independent": float(independent_value), "Original": float(original_pc_row[metric]), "Difference": difference, "Verified": ok})
                                        pc_agrees = pc_agrees and int(original_pc_row["Support"]) == int(cm.sum(1)[i])
                                valid["Original_Per_Class_Matches"] = pc_agrees
                                if not pc_agrees:
                                    issues.append({"Model": name, "Severity": "Major", "Issue": "Original per-class table differs from independent results beyond 4-decimal rounding tolerance."})
                            cm_path = rd / f"audit_original_confusion_{obj}.csv"
                            if cm_path.exists():
                                original_cm_rows = read_csv(cm_path)
                                original_cm = np.zeros((8, 8), dtype=np.int64)
                                for cm_row in original_cm_rows:
                                    original_cm[LABEL_ID[cm_row["True"]], LABEL_ID[cm_row["Predicted"]]] = int(cm_row["Freq"])
                                cm_agrees = bool(np.array_equal(cm, original_cm))
                                valid["Original_Confusion_Matches"] = cm_agrees
                                metric_checks.append({"Model": name, "Object": obj, "Metric": "Confusion_matrix_max_absolute_difference", "Independent": 0, "Original": 0, "Difference": int(np.abs(cm - original_cm).max()), "Verified": cm_agrees})
                                if not cm_agrees:
                                    issues.append({"Model": name, "Severity": "Major", "Issue": "Original confusion matrix differs from independent predictions."})
                    if valid["Original_Overall_Matches"] is None:
                        issues.append({"Model": name, "Severity": "Observation", "Issue": "Original overall metric object not exported/matched; independent prediction-based metrics are still computed."})
                except Exception as err:
                    if valid["Prediction_Identity_Verified"] and valid["Metric_Arithmetic_Verified"]:
                        row["Notes"] = f"Independent prediction-based metrics verified; original-output cross-check failed: {err}"
                        valid["Original_Output_Crosscheck_Error"] = str(err)
                    else:
                        row["Notes"] = f"Independent evaluation withheld: {err}"
                        predictions.pop(name, None)
                        metric_by_model.pop(name, None)
                        for field in ("Test_N", "Macro_F1", "Weighted_F1", "Accuracy"):
                            row[field] = ""
                    issues.append({"Model": name, "Severity": "Major", "Issue": row["Notes"]})
        elif state == "Failed":
            row["Notes"] = status.get("Error") or "Official render failed; no substituted v1 scores."
        elif not data_ok:
            row["Notes"] = "Data integrity failed; comparative performance withheld."
        else:
            row["Notes"] = "Official execution/export pending."
        comparison.append(row)
        validities[name] = valid

    for row in comparison:
        model = row["Model"]
        if model in metric_by_model:
            for base, field in (("Training-majority", "Delta_vs_Majority"), ("Multinomial Logistic Regression", "Delta_vs_Logistic")):
                if base in metric_by_model:
                    row[field] = metric_by_model[model]["Macro_F1"] - metric_by_model[base]["Macro_F1"]

    old_predictions, old_metric_by_model, old_pc_rows = {}, {}, []
    for name, (run, relative) in OLD_PREDICTIONS.items():
        old_path = old_root / "runs" / run / relative
        old_row = old_scores.get(name, {})
        new_row = next(r for r in comparison if r["Model"] == name)
        paired_ready, changed = False, ""
        try:
            old_codes = prediction_codes(old_path, test_ids, truth)
            old_cm = np.bincount(truth_codes * 8 + old_codes, minlength=64).reshape(8, 8)
            old_metrics, old_precision, old_recall, old_f1 = metrics_from_confusion(old_cm)
            if abs(old_metrics["Macro_F1"] - float(old_row["Macro_F1"])) >= 1e-12:
                raise ValueError("v1 raw predictions do not reproduce immutable v1 comparison score")
            old_predictions[name], old_metric_by_model[name] = old_codes, old_metrics
            for i, label in enumerate(LABELS):
                old_pc_rows.append({"Model": name, "Class": label, "Support": int(old_cm.sum(1)[i]), "Predicted_Count": int(old_cm.sum(0)[i]), "Precision": float(old_precision[i]), "Recall": float(old_recall[i]), "F1": float(old_f1[i])})
            paired_ready = name in predictions
            if paired_ready:
                changed = int(np.sum(old_codes != predictions[name]))
        except Exception as err:
            issues.append({"Model": name, "Severity": "Observation", "Issue": f"Paired v1/v2 prediction verification unavailable: {err}"})
        old_f1 = float(old_row["Macro_F1"]) if old_row.get("Macro_F1") else None
        new_f1 = metric_by_model.get(name, {}).get("Macro_F1")
        oldnew.append({"Model": name, "V1_Macro_F1": old_f1, "V2_Macro_F1": new_f1,
                       "Delta_V2_minus_V1_Macro_F1": new_f1 - old_f1 if old_f1 is not None and new_f1 is not None else "",
                       "V1_Accuracy": old_row.get("Accuracy", ""), "V2_Accuracy": new_row.get("Accuracy", ""),
                       "V1_Weighted_F1": old_row.get("Weighted_F1", ""), "V2_Weighted_F1": new_row.get("Weighted_F1", ""),
                       "Changed_Test_Predictions": changed, "Paired_Identity_Verified": paired_ready,
                       "V1_Selected_Configuration": old_row.get("Selected_Configuration", ""), "V2_Selected_Configuration": new_row["Selected_Configuration"],
                       "Interpretation": ("FY2021 mapping and optimisation changed together for Logistic; its old/new difference cannot isolate either change. v1 final fit had not converged." if name == "Multinomial Logistic Regression" else ("Trivial reference predictions are unchanged; no optimisation or feature-based fitting is involved." if name.startswith("Training-") else "This model's code and candidate grid were preserved; old/new differences reflect the mapping update and its downstream effects under the same procedure. Comparisons against Logistic also use a changed benchmark."))})

    if not skip_bootstrap and bootstrap > 0 and data_ok:
        pairs = []
        logit = "Multinomial Logistic Regression"
        if logit in predictions:
            pairs.extend(("New_vs_new_Logistic", f"v2:{m}", f"v2:{logit}", predictions[m], predictions[logit]) for m in ("LDA", "kNN", "SVM", "Decision Tree") if m in predictions)
        pairs.extend(("Paired_old_vs_new", f"v2:{m}", f"v1:{m}", predictions[m], old_predictions[m]) for m in predictions if m in old_predictions)
        for family, name_a, name_b, pred_a, pred_b in pairs:
            lo, hi = paired_bootstrap(truth_codes, pred_a, pred_b, bootstrap, 20261026)
            def score(version_name):
                version, model_name = version_name.split(":", 1)
                return (metric_by_model if version == "v2" else old_metric_by_model)[model_name]["Macro_F1"]
            bootstrap_rows.append({"Family": family, "Model_A": name_a, "Model_B": name_b, "Observed_Delta_Macro_F1": score(name_a) - score(name_b),
                                   "CI_2_5": lo, "CI_97_5": hi, "Bootstrap_Replicates": bootstrap, "Evaluation_Seed": 20261026,
                                   "Method": "Paired ordinary Test-row percentile bootstrap via joint-pattern multinomial; RNG reset per pair",
                                   "Caveat": "Conditional on fitted models/fixed split; iid individuals, no country-cluster/training/tuning uncertainty; multiple unadjusted descriptive intervals; no Test-based selection or causal attribution"})

    write_csv(root / "model_comparison.csv", comparison, COMPARISON_FIELDS)
    write_csv(root / "per_class_comparison.csv", pcs, ["Model", "Class", "Support", "Predicted_Count", "Precision", "Recall", "F1"])
    split_fields = ["Model", "Run", "Partition", "Expected_N", "Actual_N", "Expected_ID_SHA256", "Actual_ID_SHA256", "Seed", "Main_Seed", "Partition_Seed", "Seed_Type", "Data_MD5", "Data_Path", "Identity_Match", "Verification", "Fresh_Reference_Verified", "Notes"]
    write_csv(root / "split_integrity_report.csv", splitrows, split_fields)
    write_csv(root / "old_vs_new_comparison.csv", oldnew)
    new_pc_lookup = {(r["Model"], r["Class"]): r for r in pcs}
    old_new_pc = []
    for old_pc in old_pc_rows:
        new_pc = new_pc_lookup.get((old_pc["Model"], old_pc["Class"]))
        old_new_pc.append({"Model": old_pc["Model"], "Class": old_pc["Class"], "Support": old_pc["Support"],
                           "V1_Predicted_Count": old_pc["Predicted_Count"], "V2_Predicted_Count": new_pc["Predicted_Count"] if new_pc else "",
                           "V1_Recall": old_pc["Recall"], "V2_Recall": new_pc["Recall"] if new_pc else "", "Delta_Recall": new_pc["Recall"] - old_pc["Recall"] if new_pc else "",
                           "V1_F1": old_pc["F1"], "V2_F1": new_pc["F1"] if new_pc else "", "Delta_F1": new_pc["F1"] - old_pc["F1"] if new_pc else ""})
    write_csv(independent / "old_vs_new_per_class.csv", old_new_pc)
    write_csv(independent / "all_metrics.csv", [{"Model": name, **value} for name, value in metric_by_model.items()], ["Model", "Accuracy", "Macro_Precision", "Macro_Recall", "Macro_F1", "Weighted_F1"])
    write_csv(independent / "all_confusion_matrices.csv", cms, ["Model", "True_Class", "Predicted_Class", "Count", "Row_Percent"])
    write_csv(independent / "minority_error_flows.csv", [r for r in cms if r["True_Class"] in ("Part-time", "Unemployed", "Other") and r["True_Class"] != r["Predicted_Class"]], ["Model", "True_Class", "Predicted_Class", "Count", "Row_Percent"])
    write_csv(independent / "metric_verification.csv", metric_checks, ["Model", "Object", "Metric", "Independent", "Original", "Difference", "Verified"])
    write_csv(independent / "execution_summary.csv", execution)
    write_csv(independent / "execution_validity_matrix.csv", list(validities.values()))
    write_csv(independent / "paired_bootstrap_macro_f1.csv", bootstrap_rows, ["Family", "Model_A", "Model_B", "Observed_Delta_Macro_F1", "CI_2_5", "CI_97_5", "Bootstrap_Replicates", "Evaluation_Seed", "Method", "Caveat"])
    write_csv(independent / "v2_source_map_verification.csv", map_rows)
    write_csv(independent / "v2_source_versions.csv", source_versions)
    write_csv(independent / "map_changes.csv", map_changes)
    write_csv(independent / "evaluation_issues.csv", issues, ["Model", "Severity", "Issue"])
    tree_complexity = {}
    tree_rules = root / "results/tree/model_outputs/decision_tree_rules.txt"
    if tree_rules.exists():
        node_rows = [(int(match.group(1)), line.rstrip().endswith("*"))
                     for line in tree_rules.read_text(encoding="utf-8-sig").splitlines()
                     if (match := re.match(r"\s*(\d+)\)", line))]
        if node_rows:
            tree_complexity = {"Evidence": "Independent node/terminal-marker count from exported full final_tree rules; no fitting", "Path": str(tree_rules),
                               "Nodes": len(node_rows), "Leaves": sum(terminal for _, terminal in node_rows),
                               "Maximum_Depth": max(node.bit_length() - 1 for node, _ in node_rows),
                               "Node_IDs_Unique": len({node for node, _ in node_rows}) == len(node_rows),
                               "Selected_Validation_Leaves": configurations.get("Decision Tree", {}).get("Selected", {}).get("Leaves"),
                               "Illustrative_Pruning_File_Present": (tree_rules.parent / "decision_tree_illustrative_pruning.png").exists()}
    (independent / "tree_complexity_from_export.json").write_text(json.dumps(tree_complexity, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {"Created_At_Asia_Shanghai": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(), "Root": str(root), "Old_Root_Read_Only": str(old_root),
               "Evaluation_Environment": {"Python": sys.version, "Executable": sys.executable, "NumPy": np.__version__, "Pandas": pd.__version__, "Bootstrap_RNG": "NumPy default_rng / PCG64; reset per model pair"},
               "Labels": LABELS, "Zero_Division": 0, "Data_Integrity": data_integrity, "Data_Integrity_Verified": data_ok,
               "Fresh_Reference_Verified": fresh_reference_verified, "Maps_All_6_Match_Official_FY21_With_NIR_Assumption": maps_valid,
               "Map_Changed_Codes": [r["Country_Code"] for r in map_changes], "Map_Affected_Rows": sum(r["CSV_Rows"] for r in map_changes),
               "Verified_Prediction_Models": list(predictions), "Model_Comparison": comparison, "Execution": execution, "Validity": list(validities.values()),
               "Issues": issues, "Tree_Complexity": tree_complexity, "Bootstrap_Replicates": bootstrap if not skip_bootstrap else 0, "Bootstrap_Pairs": len(bootstrap_rows), "Evaluation_Seed": 20261026,
               "No_Model_Fits_Performed": True, "V2_Repeated_Execution_Claimed": False,
               "Interpretation_Boundary": "Logistic changed both FY2021 mapping and optimisation, so its old/new difference does not isolate either correction. The other four model procedures were preserved and reflect mapping-update effects; comparisons against Logistic also use a changed benchmark. Existing Test holdout was already seen by research team."}
    (independent / "evaluation_summary.json").write_text(json.dumps(clean_json(summary), ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--old-root", type=Path, default=Path(__file__).resolve().parents[2] / "audit_20261024_01")
    parser.add_argument("--bootstrap", type=int, default=5000)
    parser.add_argument("--skip-bootstrap", action="store_true")
    args = parser.parse_args()
    result = evaluate(args.root.resolve(), args.old_root.resolve(), args.bootstrap, args.skip_bootstrap)
    print(json.dumps({"Verified_Models": result["Verified_Prediction_Models"], "Data_Integrity_Verified": result["Data_Integrity_Verified"], "Maps_Verified": result["Maps_All_6_Match_Official_FY21_With_NIR_Assumption"], "Issue_Count": len(result["Issues"]), "Bootstrap_Pairs": result["Bootstrap_Pairs"]}, ensure_ascii=False, indent=2))
