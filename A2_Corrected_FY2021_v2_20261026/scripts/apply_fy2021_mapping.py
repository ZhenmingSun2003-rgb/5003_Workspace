"""Apply only the frozen FY2021 map and mapping/legacy-result presentation text.

This is a one-shot editor for five authorized new-root copies, never originals.
It refuses to run again after its own verification manifest has been written.
"""
import csv
import difflib
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FILES = ["baseline.Rmd", "02_LDA.Rmd", "03_kNN.Rmd", "04_SVM.Rmd", "05_DecisionTree.Rmd"]
OUT = ROOT / "environment/mapping_verification.json"
if OUT.exists():
    raise FileExistsError("Five-file mapping edit already frozen; do not mutate executed sources")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def map_span(text):
    start = text.index("WB_GROUPS <- list(")
    end = start + len("WB_GROUPS <- list(")
    depth = 1
    while depth:
        depth += (text[end] == "(") - (text[end] == ")")
        end += 1
    return start, end


def parse_map(text):
    start, end = map_span(text)
    body = text[start:end]
    groups = re.findall(r'(`[^`]+`|\w+)\s*=\s*c\(([^)]*)\)', body)
    result = {}
    for group, codes in groups:
        for code in re.findall(r'"([^"]+)"', codes):
            if code in result:
                raise ValueError("Duplicate country: " + code)
            result[code] = group.strip("`")
    return result


with (ROOT / "source_evidence/crosswalk_comparison_all_66.csv").open(encoding="utf-8-sig", newline="") as handle:
    rows = list(csv.DictReader(handle))
assert len(rows) == 66
provenance = json.loads((ROOT / "source_evidence/source_provenance.json").read_text(encoding="utf-8"))
workbook = ROOT / "source_evidence/official_income_classification_history.xlsx"
assert sha(workbook.read_bytes()) == provenance["responses"]["historical_workbook"]["sha256"]
entries = []
for row in rows:
    nir = row["Country_Code"] == "NIR"
    group = "High" if nir else row["Official_FY21_Group"]
    assert group in ("Low", "Lower-middle", "Upper-middle", "High")
    entries.append({
        "code": row["Country_Code"], "group": group,
        "official_name": row["Official_Name"],
        "source_sheet": "Country Analytical History",
        "source_cell": "AI213" if nir else row["Official_Cell"],
        "source_country_code": "GBR" if nir else row["Country_Code"],
        "vintage": "FY2021", "publication_date": "2020-07-01", "gni_reference_year": 2019,
        "NIR_assumption": nir,
        "assumption_note": "Northern Ireland inherits the United Kingdom High group; no independent NIR row exists in the official workbook." if nir else "",
    })
entries.sort(key=lambda entry: entry["code"])
canonical = {entry["code"]: entry["group"] for entry in entries}
assert len(canonical) == 66
assert {code: canonical[code] for code in ("MDV", "ROU", "UKR", "TWN", "VEN", "NIR")} == {
    "MDV": "Upper-middle", "ROU": "High", "UKR": "Lower-middle", "TWN": "High", "VEN": "Upper-middle", "NIR": "High"}
canonical_doc = {
    "vintage": "FY2021", "publication_date": "2020-07-01", "gni_reference_year": 2019,
    "fiscal_year_header": "Country Analytical History!AI5", "data_year_header": "Country Analytical History!AI6",
    "authority": "Frozen official World Bank historical classification workbook archived on 2026-10-24; no live classification substitution",
    "workbook": "source_evidence/official_income_classification_history.xlsx",
    "workbook_sha256": sha(workbook.read_bytes()),
    "source_url": provenance["responses"]["historical_workbook"]["requested_url"],
    "retrieved_asia_shanghai": provenance["responses"]["historical_workbook"]["retrieved_asia_shanghai"],
    "entries": entries,
}

lines = ["WB_GROUPS <- list("]
for group in ("Low", "Lower-middle", "Upper-middle", "High"):
    codes = [code for code, value in sorted(canonical.items()) if value == group]
    label = f"`{group}`" if "-" in group else group
    prefix = f"  {label} = c("
    current = prefix
    for index, code in enumerate(codes):
        token = f'"{code}"' + (", " if index < len(codes) - 1 else "),")
        if len(current) + len(token) > 89:
            lines.append(current.rstrip())
            current = " " * len(prefix)
        current += token
    lines.append(current)
lines.extend(["  Unclassified = character(0)", ")"])
map_block = "\n".join(lines)

metadata = []
diff = []
all_edits = {}
for name in FILES:
    original_path = ROOT / "original_sources" / name
    path = ROOT / name
    original_bytes = original_path.read_bytes()
    assert path.read_bytes() == original_bytes, f"Root source already modified before owned edit: {name}"
    original = original_bytes.decode("utf-8-sig")
    eol = "\r\n" if "\r\n" in original else "\n"
    text = original
    changes = []

    def replace(old, new, kind="Mapping presentation"):
        global text
        old, new = old.replace("\n", eol), new.replace("\n", eol)
        count = text.count(old)
        if count == 0:
            raise AssertionError(f"Expected exact presentation text missing in {name}: {old[:100]!r}")
        before = text
        text = text.replace(old, new)
        changes.append({"kind": kind, "old": old, "new": new, "occurrences": count,
                        "before_first_line": before.count(eol, 0, before.index(old)) + 1})

    start, end = map_span(text)
    replace(text[start:end].replace(eol, "\n"), map_block, "WB_GROUPS mapping assignment")
    if name == "baseline.Rmd":
        old = next(line for line in text.splitlines() if line.startswith("**WB crosswalk:"))
        replace(old, "**WB crosswalk: verified FY2021 historical classification.** The embedded entries follow the frozen official World Bank historical workbook archived in `source_evidence/`; FY2021 was released on 1 July 2020 using 2019 GNI. All 65 independently classified codes match the FY2021 column. `NIR` explicitly inherits the UK's High group because the workbook has no independent NIR row. `TWN` is High and `VEN` is Upper-middle, as the official FY2021 table specifies. The unused `Unclassified` dictionary level is retained for compatibility but no country is assigned to it. This is a fixed-vintage national context proxy, not a survey-year-specific reconstruction or an individual's household income. The logistic Rmd compares specifications with and without this proxy.")
        replace("Working FY2021 income proxy", "Verified FY2021 income proxy")
        old = next(line for line in text.splitlines() if line.startswith("**Why this matters:**"))
        replace(old, "**Why this matters:** national income groups conceal large within-country differences; an economy's GNI group is not an individual's household income. The fixed FY2021 context proxy and documented NIR inheritance assumption may encode country context. The whole-sample table above is a deterministic external mapping, not an outcome-derived feature.")
        replace("4. **Income-group audit:** the provisional FY2021 crosswalk must be audited before final reporting. The primary logistic comparison should also include the model **without** this proxy.", "4. **Income-group provenance:** the FY2021 crosswalk is verified against the frozen official historical workbook; retain the NIR-to-UK inheritance assumption and fixed-vintage limitation. The primary logistic comparison also includes the model **without** this proxy.")
    elif name == "02_LDA.Rmd":
        replace("# Pre-registered predictors and provisional World Bank context", "# Pre-registered predictors and verified FY2021 World Bank context")
        replace("the shared baseline's provisional national income proxy.", "the shared baseline's verified FY2021 national income proxy.")
        replace("The country map below is copied from the current shared baseline. It is a\nprovisional FY2021 working crosswalk, not an audited survey-year classification.\nTaiwan and Venezuela are `Unclassified`; Northern Ireland follows the UK by\nassumption. `Unclassified` is a coverage indicator, not a fifth World Bank income\ntier. The candidates without this feature provide sensitivity checks. No claim\nthat the mapping has been independently verified is made here.", "The country map below matches the canonical FY2021 crosswalk verified against\nthe frozen official historical workbook in `source_evidence/`. Taiwan is High\nand Venezuela is Upper-middle. Northern Ireland explicitly inherits the UK's\nHigh group; it has no independent official row. The unused `Unclassified`\ndictionary level is retained without any country assignment. This fixed-vintage\nproxy is not survey-year-specific; candidates without it provide sensitivity checks.")
        replace("a provisional national\n  income map", "a fixed-vintage FY2021 national\n  income proxy with a documented NIR inheritance assumption")
        replace("Inherited A1 pre-split mode imputation and provisional income mapping remain limitations.", "Inherited A1 pre-split imputation and fixed-vintage national context remain limitations; NIR inherits UK.")
        replace("The selected model correctly identifies only 1 of 1,654 Part-time records and", "> **Legacy pre-correction interpretation:** the numerical claims in this paragraph describe the original map, not the FY2021-corrected rerun. Use the newly generated tables for corrected results.\n\nThe selected model correctly identifies only 1 of 1,654 Part-time records and", "Legacy result label only")
    elif name == "03_kNN.Rmd":
        replace("# Income_Group uses the SAME provisional mapping as the other models.", "# Income_Group uses the SAME verified FY2021 mapping; NIR explicitly inherits UK High.")
        replace("Income_Group follows the shared provisional map; historical entries require audit.", "Income_Group follows the verified frozen FY2021 map; NIR explicitly inherits UK High.")
    elif name == "04_SVM.Rmd":
        replace("## Shared country-income crosswalk", "## Shared verified FY2021 country-income crosswalk\n\nThe map follows the frozen official FY2021 historical workbook in `source_evidence/`. TWN is High and VEN is Upper-middle. NIR explicitly inherits the UK's High group; it has no independent official row. `Unclassified` remains an unused dictionary level. The fixed FY2021 context is not survey-year-specific.")
        replace("# SVM discussion and limitations", "# Legacy pre-correction SVM discussion and limitations\n\n> **Legacy results, not the FY2021-corrected rerun:** the fixed configuration and numerical claims below belong to the original mapping. They are retained for provenance only. Corrected results must come from this run's generated validation and Test tables; do not reuse these old figures.", "Legacy result label only")
    elif name == "05_DecisionTree.Rmd":
        replace("# Income_Group uses the SAME provisional mapping, not an independently audited one.", "# Income_Group uses the SAME verified FY2021 mapping; NIR explicitly inherits UK High.")
        replace("# the contribution of the provisional country-income proxy within extended.", "# the contribution of the fixed FY2021 country-income proxy within extended.")
        replace("Income_Group follows the shared provisional map; historical entries require audit.", "Income_Group follows the verified frozen FY2021 map; NIR explicitly inherits UK High.")
        replace("The country-income mapping is provisional and requires independent verification.", "The country-income mapping is verified against the frozen FY2021 historical table; it is not survey-year-specific and NIR inherits UK High.")
        replace("Inspect the per-class results alongside Macro F1: the tested configuration does not predict Part-time, Unemployed or Other, giving zero recall for these classes.", "> **Legacy pre-correction interpretation:** the fixed zero-prediction claim below belongs to the original map; consult newly generated class counts and recall for the corrected run.\n\nInspect the per-class results alongside Macro F1: the tested configuration does not predict Part-time, Unemployed or Other, giving zero recall for these classes.", "Legacy result label only")

    assert parse_map(text) == canonical
    assert "Unclassified = character(0)" in text
    # Exact inverse of every documented edit must restore the complete source text.
    restored = text
    for item in reversed(changes):
        assert restored.count(item["new"]) == item["occurrences"], (name, item["kind"], "inverse edit ambiguity")
        restored = restored.replace(item["new"], item["old"])
    assert restored == original, f"Undocumented change or model logic change in {name}"
    new_bytes = text.encode("utf-8")
    path.write_bytes(new_bytes)
    records = []
    matcher = difflib.SequenceMatcher(a=original.splitlines(), b=text.splitlines(), autojunk=False)
    for tag, a1, a2, b1, b2 in matcher.get_opcodes():
        if tag != "equal":
            records.append({"operation": tag, "original_lines": [a1 + 1, a2], "corrected_lines": [b1 + 1, b2]})
    metadata.append({"file": name, "original_sha256": sha(original_bytes), "corrected_sha256": sha(new_bytes),
                     "canonical_map_equal": True, "countries": len(canonical), "documented_edits_reversed_exactly": True,
                     "model_logic_outside_documented_map_and_presentation_edits_unchanged": True, "changed_line_ranges": records})
    diff.extend(difflib.unified_diff(original.splitlines(keepends=True), text.splitlines(keepends=True),
                                   fromfile="original_sources/" + name, tofile=name, n=3))
    all_edits[name] = changes

(ROOT / "FY2021_crosswalk.json").write_text(json.dumps(canonical_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(ROOT / "environment/mapping_changes.diff").write_text("".join(diff), encoding="utf-8", newline="")
OUT.write_text(json.dumps({"scope": "Five authorized corrected-root Rmd copies only; Logistic owned by separate agent", "canonical_countries": 66,
                          "group_counts": {group: sum(value == group for value in canonical.values()) for group in ("Low", "Lower-middle", "Upper-middle", "High", "Unclassified")},
                          "authority_workbook_sha256": sha(workbook.read_bytes()), "files": metadata}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
notes = ["# FY2021 映射修正与冻结记录", "", "此目录是 2026-10-26 新建的更正版本。原仓库、旧审计目录、original_sources 均未修改。本记录覆盖 baseline/LDA/kNN/SVM/Tree 五份 Rmd；Logistic 由另一审查者应用相同 canonical map 并处理收敛。", "",
         "权威来源为 source_evidence 中冻结的 World Bank 历史工作簿 FY21/AI 列（2020-07-01 发布，2019 GNI），不是当前年度分类。", "",
         "| Code | 原映射 | 更正 FY2021 | 官方 cell |", "| --- | --- | --- | --- |",
         "| MDV | High | Upper-middle | AI128 |", "| ROU | Upper-middle | High | AI167 |", "| UKR | Upper-middle | Lower-middle | AI211 |",
         "| TWN | Unclassified | High | AI197 |", "| VEN | Unclassified | Upper-middle | AI218 |",
         "| NIR | High | High（显式 UK 继承假设） | 使用 GBR!AI213，官方无 NIR 独立行 |", "",
         "canonical JSON 列出全部 66 code 的 group、vintage、source cell 和 NIR assumption。组数 Low=2、Lower-middle=18、Upper-middle=23、High=23；WB_GROUPS 保留 Unclassified=character(0)，原 CATEGORY_KEYS/固定因子字典完全保留。", "",
         "只改 WB_GROUPS assignment 及对应 mapping provenance/显示文字；旧 SVM/LDA/Tree 固定数值或结论段落加 legacy 标签，避免充当新结果。未改 recipe、model matrix 代码、超参数、候选集、split、seed、权重规则或选择/评价逻辑。因输入映射变化导致的实际编码列数变化由原算法自行产生，不强制保留旧数据下的 P。", "",
         "每项编辑按相反顺序精确逆转后能恢复完整原文件文本；五份 map 均逐 code 等于 canonical。逐文件 SHA-256、精确变更行范围见 environment/mapping_verification.json；统一差异见 environment/mapping_changes.diff。", ""]
for item in metadata:
    notes.extend(["## " + item["file"], "", f"更正 SHA-256：`{item['corrected_sha256']}`", "",
                  "变更行范围（原 → 更正）：" + "; ".join(f"{r['original_lines']} → {r['corrected_lines']}" for r in item["changed_line_ranges"]), ""])
(ROOT / "MAPPING_CHANGES.md").write_text("\n".join(notes), encoding="utf-8")
print(json.dumps({"FIVE_ROOT_RMDS_FROZEN": True, "metadata": str(OUT), "canonical": str(ROOT / "FY2021_crosswalk.json"), "files": metadata}, ensure_ascii=False, indent=2))
