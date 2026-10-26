"""Build a Chinese evidence-based v2 report from evaluate_v2.py outputs; no fitting.
Usage: python scripts/build_v2_report.py [--root PATH] [--html]
"""
from __future__ import annotations
import argparse
import csv
import difflib
import json
import math
import shutil
import subprocess
from pathlib import Path

MODELS = ["Multinomial Logistic Regression", "LDA", "kNN", "SVM", "Decision Tree"]
LABELS = ["Full-time", "Part-time", "Self-employed", "Retired", "Housewife", "Student", "Unemployed", "Other"]
SHORT = {"Multinomial Logistic Regression": "Logistic", "Training-majority": "Majority", "Training-prior random": "Prior random", "Decision Tree": "Tree"}


def read_csv(path):
    if not Path(path).exists():
        return []
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path, default=None):
    return json.loads(Path(path).read_text(encoding="utf-8-sig")) if Path(path).exists() else ({} if default is None else default)


def fmt(value, places=6, signed=False):
    if value is None or value == "":
        return "—"
    try:
        return format(float(value), f"+.{places}f" if signed else f".{places}f")
    except (ValueError, TypeError):
        return str(value)


def display_bool(value):
    if value is True or value == "True":
        return "已核实"
    if value is False or value == "False":
        return "未通过/待核实"
    return "缺证据"


def table(headers, rows):
    def cell(value):
        return str(value if value is not None else "—").replace("|", "\\|").replace("\n", " ")
    return "\n".join(["| " + " | ".join(map(cell, headers)) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"] + ["| " + " | ".join(map(cell, row)) + " |" for row in rows])


def make_report(root, html=False):
    independent = root / "independent"
    summary_path = independent / "evaluation_summary.json"
    if not summary_path.exists():
        raise SystemExit("Run evaluate_v2.py first; no unverified scores will be inserted.")
    summary = read_json(summary_path)
    comparison = read_csv(root / "model_comparison.csv")
    per_class = read_csv(root / "per_class_comparison.csv")
    oldnew = read_csv(root / "old_vs_new_comparison.csv")
    boot = read_csv(independent / "paired_bootstrap_macro_f1.csv")
    split_rows = read_csv(root / "split_integrity_report.csv")
    source_versions = read_csv(independent / "v2_source_versions.csv")
    map_changes = read_csv(independent / "map_changes.csv")
    old_new_pc = read_csv(independent / "old_vs_new_per_class.csv")
    metrics_checks = read_csv(independent / "metric_verification.csv")
    issues = summary.get("Issues", [])
    by_model = {r["Model"]: r for r in comparison}
    validity = {r["Model"]: r for r in summary.get("Validity", [])}
    old_new_by_model = {r["Model"]: r for r in oldnew}
    pc = {(r["Model"], r["Class"]): r for r in per_class}
    executed = summary.get("Execution", [])
    all_success = len(executed) == 6 and all(r["Execution_Status"] == "Success" for r in executed)
    all_predictions = all(m in summary.get("Verified_Prediction_Models", []) for m in MODELS + ["Training-majority", "Training-prior random"])
    logit_valid = validity.get("Multinomial Logistic Regression", {})
    converged = logit_valid.get("Final_Convergence") == 0 and logit_valid.get("Candidate_Convergence_All_Zero") is True
    contracts = all(all(validity.get(m, {}).get(k) is True for k in (
        "Prediction_Identity_Verified", "Metric_Arithmetic_Verified", "Original_Overall_Matches", "Numeric_Main_Seed_Verified",
        "Runtime_Data_Path_and_MD5_Verified", "Runtime_Label_Order_Verified", "All_Required_Splits_Verified", "Runtime_Income_Map_Verified", "Source_Unchanged_Verified")) for m in MODELS + ["Training-majority", "Training-prior random"])
    major_issues = [r for r in issues if r["Severity"] in ("Critical", "Major")]
    tree_complexity = summary.get("Tree_Complexity", {})
    candidate_evidence_complete = (all(validity.get(m, {}).get("Candidate_Count_Matches") is True for m in MODELS)
                                   and validity.get("SVM", {}).get("All_Candidate_Status_Ok") is True)
    all_model_names = MODELS + ["Training-majority", "Training-prior random"]
    expected_boot_pairs = ({("New_vs_new_Logistic", f"v2:{m}", "v2:Multinomial Logistic Regression") for m in MODELS if m != "Multinomial Logistic Regression"}
                           | {("Paired_old_vs_new", f"v2:{m}", f"v1:{m}") for m in all_model_names})
    def valid_boot_row(row):
        try:
            return (int(row["Bootstrap_Replicates"]) >= 5000 and int(row["Evaluation_Seed"]) == 20261026
                    and all(math.isfinite(float(row[k])) for k in ("Observed_Delta_Macro_F1", "CI_2_5", "CI_97_5"))
                    and float(row["CI_2_5"]) <= float(row["CI_97_5"]))
        except (KeyError, TypeError, ValueError):
            return False
    bootstrap_complete = (summary.get("Bootstrap_Replicates", 0) >= 5000 and summary.get("Bootstrap_Pairs", 0) == 11
                          and len(boot) == 11 and all(valid_boot_row(r) for r in boot)
                          and {(r.get("Family"), r.get("Model_A"), r.get("Model_B")) for r in boot} == expected_boot_pairs
                          and len(oldnew) == 7 and {r.get("Model") for r in oldnew} == set(all_model_names)
                          and all(r.get("Paired_Identity_Verified") == "True" for r in oldnew))
    complete = (all_success and all_predictions and converged and contracts and summary.get("Data_Integrity_Verified")
                and summary.get("Fresh_Reference_Verified") and summary.get("Maps_All_6_Match_Official_FY21_With_NIR_Assumption")
                and candidate_evidence_complete and bootstrap_complete and not major_issues)
    failed_runs = [r for r in executed if r["Execution_Status"] == "Failed"]
    all_terminal = len(executed) == 6 and all(r["Execution_Status"] in ("Success", "Failed") for r in executed)
    if not all_terminal:
        judgement = "阶段报告：正式执行尚未全部完成，暂不形成最终判断。"
    elif complete:
        judgement = "Ready with minor corrections：可整合 v2 正式报告，保留以下局限和提交前文字核对。"
    elif failed_runs or (logit_valid.get("Final_Convergence") not in (None, 0)):
        judgement = "Requires substantial experiment correction：存在执行或优化失败，不能把未完成的 v2 当作最终实验。"
    else:
        judgement = "Not sufficiently verified：正式执行或核验尚未齐备；表中缺失值不是零分。"
    strongest = "尚未获得全部五模型的可比核验结果，暂不作完整模型排名。"
    if all_predictions:
        winner = max(MODELS, key=lambda m: float(by_model[m]["Macro_F1"]))
        strongest = f"按本次相同 Test 的 Macro F1，最高为 **{winner}（{fmt(by_model[winner]['Macro_F1'])}）**。这是点估计排序，不能等同统计显著性、跨国家泛化或未来数据表现。"
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    diff_dir = independent / "v2_source_diffs"
    diff_dir.mkdir(exist_ok=True)
    base_commit_file = root / "environment/original_commit.txt"
    base_commit = base_commit_file.read_text(encoding="utf-8-sig").strip() if base_commit_file.exists() else "待核实"
    for source in source_versions:
        original, changed = root / "original_sources" / source["File"], root / source["File"]
        if original.exists() and changed.exists():
            diff = difflib.unified_diff(original.read_text(encoding="utf-8-sig").splitlines(True), changed.read_text(encoding="utf-8-sig").splitlines(True), fromfile="original_sources/" + source["File"], tofile=source["File"])
            (diff_dir / (source["File"] + ".diff")).write_text("".join(diff), encoding="utf-8")
    lines = [
        "# STAT5003 A2：FY2021 修正 v2 实验与独立核验报告", "",
        f"生成时间（Asia/Shanghai）：{summary.get('Created_At_Asia_Shanghai', '未提供')}。本报告由已保存的正式输出、逐行预测和独立评估生成；主版本目录为 `{root.name}`。", "",
        "## 1. 执行结论", "", f"**总体判断：{judgement}**", "", strongest, "",
        "此次同时实施两项修正：六份 Rmd 的国家收入组统一改用官方 FY2021 分类；Logistic 增加优化迭代上限并在候选、选优和最终 Test 计分前强制检查 convergence。**Logistic的新旧变化不能单独归因于映射或优化；其余四模型的流程未改，新旧差异反映映射更新及其在原流程中的后续影响。相对Logistic的差值还涉及基准模型的变化。** 未为提升 Test 分数改变候选网格、选优准则、种子、训练 cap 或共享数据。", "",
        "每份修改后的 Rmd 仅安排一次正式执行。Logistic 的训练/验证 preflight 不调用 Test预测或计分，不作为第二次正式评估；已有旧版重复执行证据不能替代 v2 的重复执行。本报告**不声称 v2 已经重复运行复现**。", "",
        f"计划交付完成性：候选表/状态证据={display_bool(candidate_evidence_complete)}；5000次、11组配对bootstrap及旧新身份核验={display_bool(bootstrap_complete)}。使用`--skip-bootstrap`生成的表属于预览，不能据此形成最终Ready判断。", "",
        "证据等级：`Verified` 为本次运行与独立计算；`Source-checked` 为源码检查；`Author-reported` 仅指文档自述；`Unverified/Pending` 保留缺失。执行成功、指标正确、样本身份一致、优化收敛和重复执行是不同条件。", "",
        "## 2. 环境与实际执行", "",
        table(["Rmd / 模型", "正式状态", "秒", "错误"], [(r["File"], r["Execution_Status"], fmt(r.get("Elapsed_Seconds"), 2), r.get("Error") or "—") for r in executed]), "",
    ]
    env_path = root / "environment" / "detected_environment.json"
    if not env_path.exists():
        env_path = Path(summary["Old_Root_Read_Only"]) / "environment/detected_environment.json"
    env = read_json(env_path)
    evaluation_environment = summary.get("Evaluation_Environment", {})
    session_path = root / "results/baseline/sessionInfo.txt"
    session_lead = session_path.read_text(encoding="utf-8-sig").splitlines()[:3] if session_path.exists() else []
    package_comparison = read_json(root / "environment/package_comparison_vs_audit.json", [])
    lines += [f"运行平台信息依据 `{env_path.name}` 和各 `results/<model>/sessionInfo.txt` / `package_manifest.csv`。Rscript：`{env.get('Rscript', '见运行环境清单')}`。包与版本以本次各运行导出为准，不能仅因沿用机器就假设版本不变。", "",
              "；".join(session_lead) if session_lead else "本次R/platform信息待sessionInfo导出。", "",
              table(["相关包", "v2版本", "与旧版版本/构建/路径一致"], [(p["Package"], p["New_Version"], display_bool(p["Version_Match"] and p["Build_Match"] and p["Library_Match"])) for p in package_comparison]) if package_comparison else "包版本对照待导出。", "",
              f"独立评估运行环境：Python `{evaluation_environment.get('Python', '待导出')}`；NumPy `{evaluation_environment.get('NumPy', '待导出')}`；Pandas `{evaluation_environment.get('Pandas', '待导出')}`。bootstrap RNG为NumPy default_rng/PCG64，逐模型配对重置seed。", "",
              "耗时包含模型搜索、最终拟合、输出及 HTML render；若同时运行，受到资源竞争影响，不构成严格的算法速度基准。对象大小不等于进程峰值内存。", "",
              "## 3. 数据、种子与共享行身份", ""]
    data = summary.get("Data_Integrity", {})
    lines += [
        f"共享输入：`{data.get('Path', '')}`；{data.get('Rows', '待核实')} 行。完整原始数据列数为519，模型只读取约定源列，未因映射修正增删受访者。独立数据完整性：**{display_bool(summary.get('Data_Integrity_Verified'))}**。", "",
        f"SHA-256：`{data.get('SHA256', '未计算')}`；MD5：`{data.get('MD5', '未计算')}`。对照共享预期哈希及全部 Q279 标签，均以 `independent/evaluation_summary.json` 为准。", "",
        f"本次新建 reference split 与旧版不可变 reference 逐行一致：**{display_bool(summary.get('Fresh_Reference_Verified'))}**。主数字种子5003；outer 80/20使用5003，内部75/25使用5005；baseline随机预测5004；训练 cap 抽样5006。", "",
        "共享初始 Train=57,587、Validation=19,199、Test=19,201，最终80%重拟合=76,786。Logistic候选只用24,996条、SVM候选只用9,997条；两者均须来自共同初始Train。Logistic局部dev_id被cap替换，原始Train由不变Validation的补集独立恢复，不能误称共享划分不同。", "",
        table(["模型", "Test行/标签", "数字种子", "物理CSV+MD5", "全部所需split", "实际Income map", "本次源码未变"], [(
            SHORT.get(m, m), display_bool(validity.get(m, {}).get("Prediction_Identity_Verified")), display_bool(validity.get(m, {}).get("Numeric_Main_Seed_Verified")),
            display_bool(validity.get(m, {}).get("Runtime_Data_Path_and_MD5_Verified")), display_bool(validity.get(m, {}).get("All_Required_Splits_Verified")),
            display_bool(validity.get(m, {}).get("Runtime_Income_Map_Verified")), display_bool(validity.get(m, {}).get("Source_Unchanged_Verified"))) for m in MODELS]), "",
        f"逐partition的实际/预期行数及有序ID SHA256见 `../split_integrity_report.csv`（{len(split_rows)}行）。计数一致不是身份一致的替代证据。", "",
        "## 4. FY2021 映射、版本和修正边界", "",
        f"记录的原始仓库base commit：`{base_commit}`。本v2为隔离文件副本，以各Rmd SHA256及完整diff标识，不声称创建新Git commit；原始仓库状态保护以主流程manifest为准。", "",
        "依据World Bank历史工作簿 `Country Analytical History` 的FY21列（AI5=FY21；AI6标注2019 GNI数据年），而不是当前年度分类。官方经济体名称为来源标签。Northern Ireland没有独立工作簿条目，按United Kingdom继承High；这项明确假设保持不变。", "",
        "来源：[World Bank历史分类工作簿](https://ddh-openapi.worldbank.org/resources/DR0095334/download)、[FY2021发布说明](https://blogs.worldbank.org/en/opendata/new-world-bank-country-classifications-income-level-2020-2021)、[分类说明页](https://datahelpdesk.worldbank.org/knowledgebase/articles/906519-world-bank-country-and-lending-groups)。下载文件、哈希、官方单元格和提取记录均保存在 `../source_evidence/`，报告使用已验证的本地证据。", "",
        table(["国家代码", "旧组", "FY2021 v2", "影响CSV行数", "官方单元格"], [(r["Country_Code"], r["Old_Group"], r["V2_Group"], r["CSV_Rows"], r["Official_Cell"]) for r in map_changes]), "",
        f"共改变{len(map_changes)}个代码、{summary.get('Map_Affected_Rows', '待核实')}行的Income_Group值。六文件源码覆盖66代码（65条官方分类匹配，加1条NIR继承假设），一致性：**{display_bool(summary.get('Maps_All_6_Match_Official_FY21_With_NIR_Assumption'))}**。TWN和VEN分别采用官方High与Upper-middle；Unclassified当前无国家，但保留原factor levels以避免附带改变编码契约。", "",
        "Logistic MAXIT从250增加到2000，目标是达到既有优化问题的收敛条件；weight decay、三种spec、cap、Validation选优顺序保持约定。仅根据训练/验证 preflight确认迭代上限，不利用 Test 选择。", "",
        table(["文件", "v2 SHA256", "原始SHA256"], [(r["File"], f"`{r['V2_SHA256']}`", f"`{r['Original_SHA256']}`") for r in source_versions]), "",
        "完整逐行diff见 `../independent/v2_source_diffs/`；这些diff是可审阅证据，不代表原始仓库被编辑。原始仓库、原CSV和 `original_sources/` 的前后保护验证由主执行流程单独保存，提交前应与其最终manifest一起核对。", "",
        "## 5. 独立 Test 指标与新基准差值", "",
        "从正式输出的逐行 `row_id, truth, prediction` 独立构造8×8混淆矩阵；固定上述八类顺序，缺少预测/分母为零的Precision、Recall、F1按0处理。Macro指标包含全部八类；Weighted F1用真实support加权。以下Δ均为**本次新版本Macro F1差**，不是百分比改善率。", "",
        table(["模型", "状态", "Macro F1", "Weighted F1", "Accuracy", "Δ新Majority", "Δ新Logistic", "Validation F1"], [(SHORT.get(r["Model"], r["Model"]), r["Execution_Status"], fmt(r["Macro_F1"]), fmt(r["Weighted_F1"]), fmt(r["Accuracy"]), fmt(r["Delta_vs_Majority"], signed=True), fmt(r["Delta_vs_Logistic"], signed=True), fmt(r["Validation_Macro_F1"])) for r in comparison]), "",
        "全精度数值见 `../model_comparison.csv`。Macro Precision和Macro Recall见 `../independent/all_metrics.csv`；逐类全部精度/召回/F1/support/预测数见 `../per_class_comparison.csv`；完整矩阵和少数类错误去向见 `../independent/all_confusion_matrices.csv` 与 `minority_error_flows.csv`。", "",
        f"独立结果与Rmd已计算输出的比较共有{len(metrics_checks)}项，核验表为 `../independent/metric_verification.csv`。总指标比较容差1e-12；原逐类表若四舍五入4位，容许误差至0.00005；最终排名使用独立未舍入值。", "",
        "评估工具经只读同行复核，见 `../independent/evaluator_v2_peer_review.md`；数学、异常输入和Ready状态夹具已检查。同行复核时SVM尚未完成，因此不把这份阶段性复核说成对后来SVM数值的第二次独立认证；最终SVM按同一脚本正常核验。", "",
        "## 6. 旧版与新版：配对变化", "",
        table(["模型", "旧Macro F1", "新Macro F1", "Δ新−旧", "不同Test预测数", "配对身份"], [(SHORT.get(r["Model"], r["Model"]), fmt(r["V1_Macro_F1"]), fmt(r["V2_Macro_F1"]), fmt(r["Delta_V2_minus_V1_Macro_F1"], signed=True), r["Changed_Test_Predictions"] or "0" if r["Paired_Identity_Verified"] == "True" else "—", display_bool(r["Paired_Identity_Verified"])) for r in oldnew]), "",
        "旧分数来自旧版已核验的原始预测，并重新检查相同Test行/标签与旧CSV数值。旧Logistic最终convergence=1，其旧分数可描述既有预测，但不代表优化完成的线性基准。v2是映射与收敛控制同时变化后的总版本比较，缺少只改单项的对照组，不能作单项因果归因。", "",
        "## 7. 优化、候选网格与算法限制", "",
        table(["模型", "候选数/约定数", "已选配置", "优化/状态证据"], [(
            SHORT.get(m, m), f"{validity.get(m, {}).get('Candidate_Count', '待')} / {validity.get(m, {}).get('Expected_Candidate_Count', '待')}", by_model.get(m, {}).get("Selected_Configuration", "待"),
            (f"全部候选convergence=0：{display_bool(validity.get(m, {}).get('Candidate_Convergence_All_Zero'))}；最终code={validity.get(m, {}).get('Final_Convergence')}" if m == "Multinomial Logistic Regression" else (f"全部candidate status=ok：{display_bool(validity.get(m, {}).get('All_Candidate_Status_Ok'))}" if m == "SVM" else "见运行日志、候选表和数值检查"))) for m in MODELS]), "",
        "- **Logistic：** 3 specs×2 decay=6；candidate cap24,996；最终80%重拟合必须convergence=0。收敛码通过并不证明模型假设正确，也不是统计不确定性的估计。", "",
        "- **LDA：** 3 specs×2 priors=6；保留既有零方差/线性相关处理与共享协方差方法。分类类别prior和feature规格由Validation选择；连续多元正态与共同协方差仍是近似假设，分类dummy不满足严格连续正态。", "",
        "- **kNN：** 3 specs×9 k×2 weighting=54；全部水平one-hot，dummy乘1/√2，类别不匹配贡献平方距离1；数值缩放仅由拟合分区估计。原平局函数保留；旧版已选distance-k21无实际tie影响的结论不能自动转移为新版结论，新版以所选参数/实际预测为准。", "",
        "- **SVM：** 既有48候选，线性/radial、cost/gamma和权重规则不改；候选cap9,997；记录实际P和gamma、inverse class weights、fit状态及cache签名。新目录避免复用旧版Test输出，不能把旧缓存误记为本次完整拟合。", "",
        "- **Tree：** 54候选，Gini，cp/maxdepth/minsplit按既定网格；`xval=0`，实际是单次holdout Validation，不是CV。展示用剪枝图若存在，不是正式评估模型；最终完整树和其重拟合复杂度应以本次model bundle与RUN_SUMMARY为准。", "",
        (f"从正式导出的完整树rules独立数得：最终{tree_complexity['Nodes']}节点、{tree_complexity['Leaves']}叶、最大深度{tree_complexity['Maximum_Depth']}；被选中的Validation拟合有{tree_complexity.get('Selected_Validation_Leaves', '待核实')}叶。两者是不同训练样本上的拟合，不能混用叶数。展示剪枝文件存在：{tree_complexity.get('Illustrative_Pruning_File_Present')}。" if tree_complexity else "完整树复杂度导出尚待核验。"), "",
        "## 8. 少数类、预测分布与错误流向", "",
        table(["类别", "Logistic Recall", "LDA Recall", "kNN Recall", "SVM Recall", "Tree Recall"], [(label, *[fmt(pc.get((m, label), {}).get("Recall"), 4) for m in MODELS]) for label in LABELS]), "",
        table(["模型", "Part-time预测数/Recall", "Unemployed预测数/Recall", "Other预测数/Recall"], [(SHORT.get(m, m), *[f"{pc.get((m, label), {}).get('Predicted_Count', '—')} / {fmt(pc.get((m, label), {}).get('Recall'), 4)}" for label in ("Part-time", "Unemployed", "Other")]) for m in MODELS]), "",
    ]
    for m in MODELS:
        if m not in summary.get("Verified_Prediction_Models", []):
            continue
        zero_pred = [label for label in LABELS if pc.get((m, label), {}).get("Predicted_Count") == "0"]
        zero_recall = [label for label in LABELS if float(pc.get((m, label), {}).get("Recall", "nan")) == 0]
        lines += [f"{SHORT.get(m, m)}：从不预测的类别为{', '.join(zero_pred) if zero_pred else '无'}；精确零召回类别为{', '.join(zero_recall) if zero_recall else '无'}。", ""]
    lines += ["少数类旧→新变化如下；它们是整体版本变化的描述，不能从中孤立估计映射修正的作用。", "",
              table(["模型", "类别", "旧Recall→新Recall", "ΔRecall", "旧F1→新F1", "旧预测数→新预测数"], [(
                  SHORT.get(r["Model"], r["Model"]), r["Class"], f"{fmt(r['V1_Recall'], 4)} → {fmt(r['V2_Recall'], 4)}", fmt(r["Delta_Recall"], 4, signed=True),
                  f"{fmt(r['V1_F1'], 4)} → {fmt(r['V2_F1'], 4)}", f"{r['V1_Predicted_Count']} → {r['V2_Predicted_Count'] or '—'}")
                  for r in old_new_pc if r["Model"] in MODELS and r["Class"] in ("Part-time", "Unemployed", "Other")]), ""]
    flows = read_csv(independent / "minority_error_flows.csv")
    flow_table = []
    for m in MODELS:
        for label in ("Part-time", "Unemployed", "Other"):
            relevant = sorted([r for r in flows if r["Model"] == m and r["True_Class"] == label], key=lambda r: int(r["Count"]), reverse=True)[:2]
            if relevant:
                flow_table.append([SHORT.get(m, m), label, "; ".join(f"{r['Predicted_Class']}: {r['Count']} ({fmt(r['Row_Percent'], 1)}% of support)" for r in relevant)])
    lines += [table(["模型", "真实少数类", "最多的两个错误去向"], flow_table), "",
        "零召回与从不预测必须分开：Predicted_Count>0且Recall=0意味着所有该类预测均为假阳性。类别不平衡、特征重叠、类别定义的跨国差异或算法限制是可能解释，但这里没有识别单一原因的因果设计；不能仅凭低召回指责预处理。比较precision/accuracy trade-off时应同时引用逐类表。", "",
        "## 9. 评估不确定性", "",
        f"本次按已拟合模型做paired Test-row bootstrap，{summary.get('Bootstrap_Replicates', 0)}次，evaluation-only seed=20261026。每对模型用相同被重抽受访者，joint-pattern multinomial与逐行有放回抽样等价；逐对重置相同seed便于重算。", "",
        table(["比较A−B", "ΔMacro F1", "95% percentile CI"], [(r["Model_A"] + " − " + r["Model_B"], fmt(r["Observed_Delta_Macro_F1"], signed=True), f"[{fmt(r['CI_2_5'], signed=True)}, {fmt(r['CI_97_5'], signed=True)}]") for r in boot]), "",
        "区间仅conditional on本次固定训练/选择结果与split，按individual iid抽样，未纳入国家聚类、训练与调参不确定性；多个区间未作多重比较校正，作为描述性证据。不能据Test区间重新调参或从旧/新结果中择优提交，旧/新配对变化也不是映射单项效果的因果检验。", "",
        "## 10. 现存局限与提交前优先事项", "",
        "1. **P0：仅纳入本次完整且核验通过的正式结果。** 若仍有Pending、失败、缺失导出、split不一致或非零convergence，先解决对应证据，不填入旧数值。禁止利用已看到的Test结果追加网格搜索。", "",
        "2. **P1：最终整合只使用本次结果。** LDA和SVM保留的旧数字段已明确标为Legacy pre-correction，不应误报为未披露的v2错误；也不能把这些provenance段复制成v2结论。选中配置、Logistic优化状态、Tree零召回/零预测及minority表现均引用本次逐行指标，明确所有Δ基于新Majority和新Logistic。", "",
        "3. **P1：保留完整版本与来源证据。** 统一引用FY2021及NIR继承假设，附六份源码diff/哈希、实际运行map、数据hash、package/session、候选和预测文件。最终将主流程的原仓库与original_sources前后保护manifest一并归档。", "",
        "4. **P2：准确界定结论。** 单一固定Validation存在选优偏差，训练cap不同；单一Test仅估计当前个体随机holdout，不代表未见国家、未来年度或加权总体估计。已有Test结果已被团队看到，所以它不保证对研究者完全未见。v2仅一次正式运行，不声称新版本重复执行验证。", "",
        "5. **P2：披露A1原有众数处理。** A1在A2 split之前众数填补带来原则上的无监督预处理泄漏风险；前次审计曾核对被选变量的整体/训练众数一致，这使已选流程的实际影响较小，但不是删除风险披露的理由。v2共享CSV未重建，也没有声称消除该风险；没有直接目标作为预测变量的证据。", "",
        "## 11. 当前异常与缺失证据", "",
        table(["严重度", "模型", "证据问题"], [(r["Severity"], r["Model"], r["Issue"]) for r in issues]) if issues else ("已完成run未发现执行/契约/指标差异；仍有Pending正式run，其缺少的输出尚未获得通过结论。" if not all_terminal else "独立评估未发现未解决的执行/契约/指标异常。原始资料保护及额外运行诊断仍以主执行流程的最终证据为准。"), "",
        "## 12. 交付文件与最终判断", "",
        "- `../model_comparison.csv`：本次七个模型/基准的完整精度分数与新基准差值。", "",
        "- `../per_class_comparison.csv`、`../split_integrity_report.csv`、`../old_vs_new_comparison.csv`：逐类、行身份和旧新配对比较。", "",
        "- `../independent/`：完整混淆、错误流向、原计算比较、map/source检查、bootstrap和机器可读summary。", "",
        "- `../results/<model>/`、`../execution_logs/`：各自一次正式render、实际预测、模型输出、runtime和环境。", "",
        "- `../original_sources/`、`../source_evidence/`：未改动原稿与官方来源证据。", "",
        f"**{judgement}**", "",
    ]
    addendum = reports / "report_addendum.md"
    if addendum.exists():
        lines += ["## 主执行流程补充核验", "", addendum.read_text(encoding="utf-8-sig"), ""]
    target = reports / "STAT5003_A2_CORRECTED_V2_REPORT.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    if html:
        pandoc = shutil.which("pandoc")
        candidate = Path("C:/Program Files/RStudio/resources/app/bin/quarto/bin/tools/pandoc.exe")
        if not pandoc and candidate.exists():
            pandoc = str(candidate)
        if pandoc:
            style = reports / "report_style.html"
            style.write_text("<style>body{font-family:Arial,'Microsoft YaHei',sans-serif;max-width:1280px;margin:40px auto;padding:0 22px;line-height:1.65;color:#182234}table{border-collapse:collapse;width:100%;font-size:.9em;margin:18px 0;display:block;overflow:auto}th,td{border:1px solid #cad3df;padding:7px 9px;text-align:left}th{background:#edf2f9}tr:nth-child(even){background:#f8fafc}code{overflow-wrap:anywhere;font-size:.9em}h1,h2{color:#16436a}a{color:#1467a0}</style>", encoding="utf-8")
            subprocess.run([pandoc, str(target), "-o", str(target.with_suffix(".html")), "--standalone", "--metadata", "lang=zh-CN", "--metadata", "title=STAT5003 A2 Corrected FY2021 v2", "--include-in-header", str(style)], check=True)
        else:
            print("Pandoc unavailable; Markdown preserved; HTML not fabricated.")
    print(target)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--html", action="store_true")
    args = parser.parse_args()
    make_report(args.root.resolve(), args.html)
