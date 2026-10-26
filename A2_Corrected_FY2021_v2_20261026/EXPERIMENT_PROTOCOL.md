# STAT5003 A2 corrected FY2021 v2 protocol

Date: 2026-10-26 (Asia/Shanghai). This is an explicitly authorised corrected experiment, separate from the read-only audit of 2026-10-24.

## Frozen scope before evaluation

The original repository is `C:/Users/Saberken/Downloads/5003_Workspace`, commit `9b3db1d3207d9af492af0099848248cee73df918`. Original source files, dataset, Git working tree and previous audit results are preserved. The six new Rmd versions live in this folder. `original_sources/` holds immutable before-copies.

Allowed changes:

1. All six embedded income maps use the archived official World Bank FY2021 classification: MDV Upper-middle, ROU High, UKR Lower-middle, TWN High and VEN Upper-middle. The user explicitly requires the official FY2021 treatment of TWN and VEN. NIR retains the clearly documented UK High inheritance assumption because there is no independent NIR row. Other country entries remain as verified. Unclassified stays an empty map entry for compatibility with the existing fixed categorical dictionaries.
2. Logistic optimisation gets a larger iteration ceiling and hard convergence gates, with the same family, regularisation candidates, formulas, sample cap, preprocessing, splits, seeds and validation ranking. The initial proposed ceiling is 2000. If convergence still fails, any further iteration-only escalation must be motivated solely by optimisation status, before Test prediction/scoring, and explicitly recorded. No Test metric may determine this change.
3. Mapping-related prose and stale narrative results may be labelled or made dynamic so the new files do not present old numbers as new results. Such presentation changes must not alter modelling logic.

Unchanged experimental contract:

- Same materialised CSV; SHA-256 `ee392676dbb42dde0ea74ebf643862f3900e7d13a7aa03842ed2d7665ac98ee0`, MD5 `98bf573170f0cb6bd65a4e9a8070d4d8`.
- Numeric main seed5003; outer80/20 seed5003, internal75/25 seed5005, fitting caps seed5006, random reference seed5004.
- Same original Train57587, Validation19199, Test19201, final refit76786; compare original row IDs, labels and class order, not just counts.
- Same non-Logistic modelling/preprocessing code, grids, weights, candidate sizes and ranking criteria. A changed encoded dimension and thus formula-derived SVM gamma is an expected consequence of the same algorithm acting on the corrected map, not a new gamma search rule.
- Same package versions as prior audit, using its isolated r_library plus the existing user/system libraries.

## Execution and evidence

Use `rmarkdown::render()` once per frozen corrected Rmd in a new output directory. No old validation/model/Test caches are reused. All models resolve the same physical CSV in this folder. Every executed copy must be byte-identical to its frozen corrected source, checked before and after rendering. All generated files remain here. No GitHub commit/push or original-repository edit is authorised by this workflow.

A separate clearly labelled Logistic preflight executes training/validation and the final full80% fit, without Test prediction or Test metrics. It is not a second official result or evidence of full v2 reproducibility. One complete official execution is requested; do not claim a two-pass v2 replication.

Independent evaluation must recalculate metrics from exported Test predictions, verify shared rows/labels/seeds/data hashes, confirm convergence and candidate completeness, and compare with old results. Use the new Logistic result for new delta-vs-Logistic comparisons. Because both mapping and Logistic optimisation change, do not attribute the Logistic old/new difference to one of them alone.

The same Test set has already been exposed. This is a transparent correction of previously evaluated experiments, not a new unseen holdout. Bootstrap is evaluation-only and may not trigger reselection. Prior A1 preprocessing limitations remain; the previous audit verified identical raw-observed modes for the six selected categorical features across all actual fitting partitions.
