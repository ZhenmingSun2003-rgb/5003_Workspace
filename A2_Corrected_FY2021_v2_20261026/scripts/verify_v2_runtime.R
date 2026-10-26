# Read-only post-execution verification. Does not call any author fit/recipe
# function, rerun a model, or select a different candidate.
# Usage: Rscript --vanilla verify_runtime_contract.R <audit_root>
# Rerun the same command once later runtime_environment.rds files exist.
args <- commandArgs(trailingOnly = TRUE)
script_arg <- grep("^--file=", commandArgs(), value = TRUE)
default_root <- if (length(script_arg)) dirname(dirname(sub("^--file=", "", script_arg[1]))) else getwd()
root <- normalizePath(if (length(args)) args[1] else default_root, winslash = "/", mustWork = TRUE)
.libPaths(c("C:/Users/Saberken/Documents/ChatGPT/5003_A1_A2/audit_20261024_01/r_library", "C:/Users/Saberken/AppData/Local/R/win-library/4.6", .libPaths()))
stopifnot(requireNamespace("jsonlite", quietly = TRUE), requireNamespace("nnet", quietly = TRUE))
out <- file.path(root, "independent")
dir.create(out, recursive = TRUE, showWarnings = FALSE)
prefix <- function(name) file.path(out, paste0("runtime_contract_", name))
json <- function(x, name) jsonlite::write_json(x, prefix(name), pretty = TRUE, auto_unbox = TRUE, null = "null", digits = 16)
writeLines(capture.output(sessionInfo(), options("contrasts"), RNGkind()), prefix("session.txt"))
writeLines(deparse(nnet::multinom), prefix("nnet_multinom_body.txt"))
writeLines(deparse(nnet::nnet.default), prefix("nnet_default_body.txt"))
impl <- deparse(nnet::multinom)
impl_info <- list(package_version = as.character(packageVersion("nnet")),
  multinom_calls_nnet_with_rang_zero = any(grepl("rang = 0", impl, fixed = TRUE)),
  relevant_source_lines = impl[grepl("nnet.default|rang =|size =|skip =|softmax =", impl)],
  contrasts_in_verifier_vanilla_session = getOption("contrasts"),
  note = "multinom uses size=0, skip=TRUE and rang=0 for the multiclass nnet call. The loaded implementation is preserved, so a hidden-layer random start must not be assumed. The audit saved environment does not preserve the render process's global options; model-stored contrasts and the vanilla verification options are recorded separately.")
json(impl_info, "nnet_initialization.json")

csv_path <- file.path(root, "WVS_Wave7_cleaned_for_modelling.csv")
header <- names(read.csv(csv_path, nrows = 0, check.names = FALSE))
numeric_keys <- c(Age = "Q262", HouseholdSize = "Q270", Children = "Q274")
wanted <- c("Q279", unname(numeric_keys))
types <- rep("NULL", length(header)); types[match(wanted, header)] <- NA_character_
raw <- read.csv(csv_path, colClasses = types, check.names = FALSE, stringsAsFactors = FALSE, na.strings = c("", "NA"))
reference <- read.csv(file.path(out, "reference_split.csv"), stringsAsFactors = FALSE)
labels <- c("Full-time", "Part-time", "Self-employed", "Retired", "Housewife", "Student", "Unemployed", "Other")
ref_train <- reference$row_id[reference$partition %in% c("Train", "Validation")]
ref_initial <- reference$row_id[reference$partition == "Train"]
ref_test <- reference$row_id[reference$partition == "Test"]
truth <- labels[as.integer(raw$Q279)]
stopifnot(nrow(raw) == 95987L, length(ref_train) == 76786L,
          identical(reference$row_id, seq_len(nrow(raw))), identical(reference$truth, truth))
direct_numeric <- function(x) {
  value <- suppressWarnings(as.numeric(as.character(x)))
  value[!is.finite(value)] <- NA_real_
  value
}
raw_numeric <- lapply(numeric_keys, function(k) direct_numeric(raw[[k]]))
direct_stats <- function(ids, feature) {
  x <- raw_numeric[[feature]][ids]
  available <- sort(x[!is.na(x)])
  n_available <- length(available)
  stopifnot(n_available > 0)
  # Explicit order statistics and sample variance, independent of author code.
  med <- if (n_available %% 2L) available[(n_available + 1L) / 2L] else
    (available[n_available / 2L] + available[n_available / 2L + 1L]) / 2
  x[is.na(x)] <- med
  mu <- sum(x) / length(x)
  sigma <- sqrt(sum((x - mu)^2) / (length(x) - 1L))
  if (!is.finite(sigma) || sigma == 0) sigma <- 1
  c(median = med, mean = mu, sd = sigma)
}
getv <- function(e, n, fallback = NULL) if (exists(n, e, inherits = FALSE)) get(n, e, inherits = FALSE) else fallback
recipe_rows <- list(); training_rows <- list(); baseline_rows <- list(); summaries <- list()
svm_weight_rows <- list()
verify_svm_weights <- function(run, stage, ids, original_function, selected_mode) {
  y <- factor(truth[ids], levels = labels)
  counts <- vapply(labels, function(k) sum(as.character(y) == k), integer(1))
  independent_inverse <- length(ids) / (8 * counts)
  for (weight_mode in c("none", "inverse")) {
    # Explicit user-authorised observation of the original pure weight helper;
    # this does not fit a model, transform features, or select a configuration.
    actual <- original_function(y, weight_mode)
    expected <- if (weight_mode == "inverse") independent_inverse else rep(NA_real_, 8)
    observed <- if (weight_mode == "inverse") as.numeric(actual[labels]) else rep(NA_real_, 8)
    pass <- if (weight_mode == "none") rep(is.null(actual), 8) else
      is.finite(observed) & abs(observed - expected) <= 1e-12
    svm_weight_rows[[length(svm_weight_rows) + 1L]] <<- data.frame(Run = run, Stage = stage,
      Mode = weight_mode, Selected_Mode = selected_mode, Fitting_N = length(ids),
      Class = labels, Class_N = counts, Independent_Weight = expected,
      Original_Function_Weight = observed, Difference = observed - expected,
      Original_Returns_NULL = is.null(actual), Pass = pass)
  }
}
compare_recipe <- function(run, stage, recipe, ids) {
  if (is.null(recipe)) return(invisible(NULL))
  used <- names(recipe$median)
  if (is.null(used)) used <- names(numeric_keys)[seq_along(recipe$median)]
  for (feature in used) {
    expect <- direct_stats(ids, feature)
    for (stat in c("median", "mean", "sd")) {
      observed <- as.numeric(recipe[[stat]][[feature]])
      delta <- observed - expect[[stat]]
      recipe_rows[[length(recipe_rows) + 1L]] <<- data.frame(Run = run, Stage = stage,
        Feature = feature, Source = numeric_keys[[feature]], Fitting_N = length(ids),
        Parameter = stat, Independent = expect[[stat]], Runtime = observed,
        Difference = delta, Pass = isTRUE(abs(delta) <= 1e-12))
    }
  }
}

lda_diagnostic <- function(run, e, final, train_ids) {
  # Reconstruct the final treatment-coded design using only observed raw input,
  # verified recipe, fixed category definitions, and frozen selected features.
  tr <- getv(e, "train")
  recipe <- final$recipe
  processed <- data.frame(row.names = seq_along(train_ids))
  for (nm in names(numeric_keys)) {
    x <- raw_numeric[[nm]][train_ids]
    missing <- is.na(x); x[missing] <- recipe$median[[nm]]
    processed[[nm]] <- (x - recipe$mean[[nm]]) / recipe$sd[[nm]]
    processed[[paste0(nm, "_missing")]] <- as.integer(missing)
  }
  category_keys <- getv(e, "CATEGORY_KEYS")
  category_sources <- getv(e, "CATEGORY_SOURCES")
  for (nm in names(category_keys)) {
    v <- trimws(as.character(tr[[category_sources[[nm]]]]))
    v[is.na(v) | !(v %in% category_keys[[nm]])] <- "Missing"
    processed[[nm]] <- factor(v, levels = c(category_keys[[nm]], "Missing"))
  }
  features <- getv(e, "SPECIFICATIONS")[[final$spec]]
  cats <- intersect(features, names(category_keys))
  contrasts <- lapply(processed[cats], function(x) stats::contr.treatment(levels(x), base = 1))
  mm <- stats::model.matrix(stats::reformulate(features), data = processed, contrasts.arg = contrasts)
  mm <- mm[, colnames(mm) != "(Intercept)", drop = FALSE]
  selected_matrix <- mm[, final$columns, drop = FALSE]
  y <- factor(truth[train_ids], levels = labels)
  classmeans <- t(vapply(labels, function(k) colMeans(selected_matrix[y == k, , drop = FALSE]), numeric(ncol(selected_matrix))))
  rownames(classmeans) <- labels
  residual <- selected_matrix - classmeans[as.integer(y), , drop = FALSE]
  pooled <- crossprod(residual) / (nrow(residual) - length(labels))
  eigenvalues <- eigen(pooled, symmetric = TRUE, only.values = TRUE)$values
  rank <- qr(residual, tol = 1e-8, LAPACK = FALSE)$rank
  model <- final$model
  expected_prior <- if (final$prior_policy == "equal") rep(1/8, 8) else as.numeric(table(y) / length(y))
  cand <- getv(e, "candidate_fits", list())
  candidate_details <- lapply(seq_along(cand), function(i) {
    fit <- cand[[i]]
    if (is.null(fit)) return(NULL)
    initial_y <- factor(truth[ref_initial], levels = labels)
    candidate_expected_prior <- if (fit$prior_policy == "equal") rep(1/8, 8) else as.numeric(table(initial_y) / length(initial_y))
    list(candidate = i, specification = fit$spec, prior_policy = fit$prior_policy,
      N = fit$model$N, prior = fit$model$prior, counts = fit$model$counts,
      prior_matches_independent_initial_labels = isTRUE(all.equal(unname(fit$model$prior), candidate_expected_prior, tolerance = 1e-14)),
      retained_columns = fit$columns, dropped_columns = fit$dropped,
      scaling_dimension = dim(fit$model$scaling), discriminant_singular_values = fit$model$svd)
  })
  write.csv(pooled, prefix(paste0(run, "_lda_pooled_covariance.csv")))
  write.csv(model$scaling, prefix(paste0(run, "_lda_scaling.csv")))
  write.csv(classmeans, prefix(paste0(run, "_lda_independent_class_means.csv")))
  result <- list(specification = final$spec, prior_policy = final$prior_policy,
    model_N = model$N, classes = rownames(model$means), counts = model$counts,
    prior = model$prior, independent_expected_prior = expected_prior,
    prior_matches = isTRUE(all.equal(unname(model$prior), expected_prior, tolerance = 1e-14)),
    encoded_before_rank_filter = ncol(mm), retained_columns = final$columns,
    dropped_columns = final$dropped, independently_dropped = setdiff(colnames(mm), final$columns),
    residual_rank = rank, retained_dimension = ncol(selected_matrix),
    covariance_eigen_min = min(eigenvalues), covariance_eigen_max = max(eigenvalues),
    covariance_condition_number = max(eigenvalues) / min(eigenvalues),
    covariance_all_finite = all(is.finite(pooled)), covariance_positive_definite = min(eigenvalues) > 0,
    independent_class_means_max_difference = max(abs(classmeans - model$means)),
    scaling_dimension = dim(model$scaling), scaling_all_finite = all(is.finite(model$scaling)),
    scaling_whitens_independent_pooled_covariance_max_difference = max(abs(crossprod(model$scaling, pooled %*% model$scaling) - diag(ncol(model$scaling)))),
    discriminant_singular_values = model$svd, candidates = candidate_details,
    note = "Pooled covariance = crossprod(class-centred independent encoded design)/(N-K); no model fitting or prior re-selection. Numerical full rank does not prove Gaussian distributions or equal class covariance assumptions.")
  json(result, paste0(run, "_lda_diagnostics.json"))
  result[c("prior_matches", "encoded_before_rank_filter", "retained_dimension", "residual_rank",
           "covariance_eigen_min", "covariance_condition_number", "independent_class_means_max_difference")]
}

requested <- c("baseline", "logistic", "lda", "tree", "knn", "svm")
for (run in requested) {
  path <- file.path(root, "results", run, "runtime_environment.rds")
  if (!file.exists(path)) { summaries[[run]] <- list(status = "runtime environment not yet available"); next }
  cat("Checking saved runtime:", run, "\n")
  e <- readRDS(path)
  train_id <- getv(e, "train_id"); test_id <- getv(e, "test_id")
  train <- getv(e, "train"); dev_id <- getv(e, "dev_id")
  identity <- list(train_ids_equal_reference = identical(as.integer(train_id), as.integer(ref_train)),
    test_ids_equal_reference = identical(as.integer(test_id), as.integer(ref_test)),
    full_refit_N = nrow(train), full_refit_rows_76786 = nrow(train) == 76786L,
    full_refit_labels_match_csv = identical(as.character(train$Outcome), truth[train_id]),
    full_refit_numeric_source_values_match_csv = all(vapply(numeric_keys, function(k)
      identical(as.character(train[[k]]), as.character(raw[[k]][train_id])), logical(1))))
  training_rows[[length(training_rows) + 1L]] <- data.frame(Run = run,
    as.data.frame(identity, stringsAsFactors = FALSE), check.names = FALSE)
  final <- getv(e, "final_fit"); selected <- NULL; design <- NULL; extra <- list()
  if (grepl("baseline$", run)) {
    proportions <- as.numeric(table(factor(truth[ref_train], levels = labels)) / length(ref_train))
    majority <- labels[which.max(proportions)]
    expected_majority <- rep(majority, length(ref_test))
    set.seed(5004)
    expected_chance <- sample(labels, length(ref_test), replace = TRUE, prob = proportions)
    for (nm in c("majority", "chance")) {
      observed <- getv(e, paste0("pred_", nm))
      expected <- if (nm == "majority") expected_majority else expected_chance
      baseline_rows[[length(baseline_rows) + 1L]] <- data.frame(Run = run, Predictor = nm,
        N = length(expected), Prediction_Exact_Match = identical(as.character(observed), expected),
        Mismatched_Rows = sum(as.character(observed) != expected),
        Seed = if (nm == "chance") 5004L else NA_integer_, Majority = majority)
    }
    extra$training_class_proportions <- setNames(proportions, labels)
    design <- "Training-majority / independent training-prior sample; no predictive design matrix"
  } else if (grepl("logistic$", run)) {
    compare_recipe(run, "candidate_capped_fitting", getv(e, "r_dev"), train_id[dev_id])
    compare_recipe(run, "final_full80_fitting", getv(e, "recipe_final"), train_id)
    selected <- getv(e, "winning_spec")
    design <- "Formula design: R factor contrasts, numeric z-scores/missing flags; selected quadratic age adds squared standardised Age"
    ranking <- getv(e, "ranking")
    write.csv(ranking, prefix("logistic_candidate_convergence.csv"), row.names = FALSE)
    extra <- list(selected_spec = selected, selected_decay = getv(e, "winning_decay"),
      candidate_fitting_N = nrow(getv(e, "development")),
      all_candidate_convergence = ranking[, c("Spec", "Decay", "Dev_N", "Val_N", "Convergence", "Macro_F1", "Weighted_F1", "Accuracy")],
      final_convergence = final$convergence, final_value = final$value,
      final_decay = final$decay, final_fitted_rows = nrow(final$fitted.values),
      final_fitted_rows_76786 = nrow(final$fitted.values) == 76786L,
      stored_model_contrasts = final$contrasts, actual_formula_terms = attr(final$terms, "term.labels"))
    json(extra, "logistic_convergence.json")
  } else if (grepl("lda$", run)) {
    candidates <- getv(e, "candidate_fits")
    for (i in seq_along(candidates)) compare_recipe(run, paste0("candidate_", i), candidates[[i]]$recipe, ref_initial)
    compare_recipe(run, "final_full80_fitting", final$recipe, train_id)
    selected <- final$spec
    design <- "Explicit treatment contrasts, intercept removed; fitting-only within-class variance and QR rank filtering; classical pooled covariance"
    extra <- lda_diagnostic(run, e, final, train_id)
  } else if (grepl("tree$|knn$", run)) {
    compare_recipe(run, "candidate_full_initial_fitting", getv(e, "initial_recipe"), train_id[dev_id])
    compare_recipe(run, "final_full80_fitting", getv(e, "final_recipe"), train_id)
    selected <- getv(e, "best")$Spec[[1]]
    if (grepl("tree$", run)) {
      model <- getv(e, "final_tree")
      design <- "rpart factor-aware formula design; numeric z-scores/missing flags, no one-hot requirement"
      extra <- list(final_model_N = length(model$where), final_model_rows_76786 = length(model$where) == 76786L,
                    actual_formula_terms = attr(model$terms, "term.labels"))
    } else {
      matrix <- getv(e, "M_train_final")
      design <- "All-level categorical one-hot /sqrt(2); numeric z-scores; missingness 0/1 left unscaled"
      extra <- list(final_matrix_dimensions = dim(matrix), matrix_columns = colnames(matrix),
                    final_matrix_rows_76786 = nrow(matrix) == 76786L,
                    dummy_scale = getv(e, "DUMMY_SCALE"))
    }
  } else if (grepl("svm", run)) {
    fit_id <- getv(e, "fit_id")
    recipe_by_spec <- getv(e, "recipe_by_spec")
    fit_original_ids <- train_id[dev_id[fit_id]]
    for (s in names(recipe_by_spec)) compare_recipe(run, paste0("candidate_", s), recipe_by_spec[[s]], fit_original_ids)
    final_record <- getv(e, "final_record")
    recipe <- getv(e, "recipe_final", if (!is.null(final_record)) final_record$Recipe else NULL)
    compare_recipe(run, "final_full80_fitting", recipe, train_id)
    winner <- getv(e, "winner")
    selected <- winner$Spec[[1]]
    weight_function <- getv(e, "class_weights")
    if (!is.null(weight_function)) {
      verify_svm_weights(run, "candidate_capped_fitting", fit_original_ids, weight_function, winner$Weight[[1]])
      verify_svm_weights(run, "final_full80_fitting", train_id, weight_function, winner$Weight[[1]])
    }
    svm_model <- if (!is.null(final)) final else if (!is.null(final_record)) final_record$Model else NULL
    native_details <- NULL
    if (!is.null(svm_model)) {
      support_indices <- svm_model$index
      support_valid <- !is.null(support_indices) && length(support_indices) > 0L &&
        all(is.finite(support_indices)) && all(support_indices == as.integer(support_indices)) &&
        min(support_indices) >= 1L && max(support_indices) <= length(train_id)
      if (isTRUE(support_valid)) write.csv(data.frame(
        Support_Vector_Order = seq_along(support_indices),
        Full80_Local_Index = support_indices,
        CSV_Row_ID = train_id[support_indices],
        Truth = truth[train_id[support_indices]]), prefix("svm_support_vector_mapping.csv"), row.names = FALSE)
      native_kernel_names <- c("linear", "polynomial", "radial", "sigmoid", "precomputed")
      kernel_name <- if (!is.null(svm_model$kernel) && length(svm_model$kernel) == 1L &&
        svm_model$kernel %in% 0:4) native_kernel_names[as.integer(svm_model$kernel) + 1L] else NULL
      native_details <- list(native_object_fields = names(svm_model),
        kernel_code = svm_model$kernel, kernel_name = kernel_name,
        cost = svm_model$cost, gamma = svm_model$gamma,
        selected_source_kernel = winner$Kernel[[1]], selected_source_cost = winner$Cost[[1]],
        selected_source_gamma = winner$Gamma[[1]],
        kernel_matches_winner = if (!is.null(kernel_name)) identical(kernel_name, winner$Kernel[[1]]) else NULL,
        cost_matches_winner = if (!is.null(svm_model$cost)) isTRUE(all.equal(svm_model$cost, winner$Cost[[1]])) else NULL,
        radial_gamma_matches_winner = if (winner$Kernel[[1]] == "radial" && !is.null(svm_model$gamma))
          isTRUE(all.equal(svm_model$gamma, winner$Gamma[[1]])) else NULL,
        native_scaled = svm_model$scaled,
        all_native_scaling_disabled = if (!is.null(svm_model$scaled)) all(!svm_model$scaled) else NULL,
        native_probability_flag_compprob = svm_model$compprob,
        native_probability_coefficients_lengths = c(probA = length(svm_model$probA), probB = length(svm_model$probB)),
        probability_argument_in_source = FALSE,
        probability_argument_verification_status = "Source-checked in original fit_svm(); native flag retained separately if available",
        nclasses = svm_model$nclasses, class_levels = svm_model$levels,
        native_class_label_codes = svm_model$labels,
        nSV_by_native_class_order = svm_model$nSV, total_nSV_native = svm_model$tot.nSV,
        support_index_N = length(support_indices),
        support_index_min = if (length(support_indices)) min(support_indices) else NULL,
        support_index_max = if (length(support_indices)) max(support_indices) else NULL,
        support_index_unique = if (length(support_indices)) !anyDuplicated(support_indices) else NULL,
        support_indices_within_full80 = support_valid,
        mapped_original_ids_all_in_shared_train = if (isTRUE(support_valid)) all(train_id[support_indices] %in% ref_train) else NULL,
        support_vector_matrix_dimensions = dim(svm_model$SV),
        native_class_weight_field_present = "class.weights" %in% names(svm_model),
        native_class_weight_values = if ("class.weights" %in% names(svm_model)) svm_model$class.weights else NULL,
        class_weight_evidence_limit = "Independent N/(8*n_k) values compared with original class_weights() on exact fitting labels; source fit_svm passes that helper to e1071. No claim that native LIBSVM per-class weights can be recovered if the saved model does not store them.")
      json(native_details, "svm_native_model_parameters.json")
    }
    design <- "All-level 0/1 one-hot, fitting-only constant-column filter; numeric z-scores, missingness 0/1; e1071 scale=FALSE"
    extra <- list(candidate_fitting_N = length(fit_original_ids),
      candidate_fitting_only_initial_train = all(fit_original_ids %in% ref_initial),
      final_evaluation_available = !is.null(final_record),
      final_record_N = if (!is.null(final_record)) final_record$Train_N else NULL,
      final_record_rows_76786 = if (!is.null(final_record)) final_record$Train_N == 76786L else NULL,
      recipe_numeric = if (!is.null(recipe)) recipe$numeric else NULL,
      retained_columns = if (!is.null(recipe)) recipe$keep else NULL,
      dropped_columns = if (!is.null(recipe)) recipe$removed else NULL,
      native_model_parameters = native_details)
  }
  specifications <- getv(e, "SPECIFICATIONS")
  features <- if (!is.null(selected)) specifications[[selected]] else character()
  forbidden <- intersect(features, c("Outcome", "Q279", "B_COUNTRY_ALPHA", "Country", "country"))
  summaries[[run]] <- list(status = "observed saved unchanged-Rmd environment", identity = identity,
    selected_specification = selected, selected_source_features = features,
    forbidden_selected_source_features = forbidden, no_forbidden_source_predictors = !length(forbidden),
    design_representation = design, details = extra)
  rm(e, final, train); gc(verbose = FALSE)
}
recipes <- if (length(recipe_rows)) do.call(rbind, recipe_rows) else data.frame()
training <- if (length(training_rows)) do.call(rbind, training_rows) else data.frame()
baseline <- if (length(baseline_rows)) do.call(rbind, baseline_rows) else data.frame()
svm_weights <- if (length(svm_weight_rows)) do.call(rbind, svm_weight_rows) else data.frame()
write.csv(recipes, prefix("recipe_comparison.csv"), row.names = FALSE)
write.csv(training, prefix("training_identity.csv"), row.names = FALSE)
write.csv(baseline, prefix("baseline_prediction_check.csv"), row.names = FALSE)
write.csv(svm_weights, prefix("svm_class_weights.csv"), row.names = FALSE)
report <- list(mode = "Read-only post-execution observation; no model rerun/reselection",
  recipe_comparisons = nrow(recipes), recipe_failures = if (nrow(recipes)) sum(!recipes$Pass) else 0L,
  max_absolute_recipe_difference = if (nrow(recipes)) max(abs(recipes$Difference)) else NULL,
  baseline_predictors_exact = if (nrow(baseline)) all(baseline$Prediction_Exact_Match) else NULL,
  svm_class_weight_comparisons = nrow(svm_weights),
  svm_class_weight_failures = if (nrow(svm_weights)) sum(!svm_weights$Pass) else NULL,
  internal_multinom_initialization = impl_info, runs = summaries)
json(report, "summary.json")
notes <- c("# 已保存运行环境的独立合同核验", "",
  "本程序只读取原始Rmd渲染后保存的runtime_environment.rds与共享CSV；未调用作者learn_recipe、fit或候选选择函数，未重跑模型、修改Rmd或重选超参数。",
  "独立median用排序次序统计量求出；filled mean=sum(x)/n；sample sd=sqrt(sum((x-mean)^2)/(n-1))。仅在正确fitting rows上计算，并与runtime recipe逐参数比较。",
  paste0("已比较 ", nrow(recipes), " 个recipe参数，失败数 ", report$recipe_failures,
    "；最大绝对差 ", format(report$max_absolute_recipe_difference, digits = 16), "（容差1e-12）。"),
  "逐项证据见runtime_contract_recipe_comparison.csv；final80% row IDs、labels、原numeric值见runtime_contract_training_identity.csv。",
  "", "## Level A独立预测复现", "",
  "从完整80% labels独立计算majority和class proportions，以seed5004调用base sample生成chance预测，与baseline的两个原始预测向量逐元素比较；不是只核对汇总metric。",
  capture.output(print(baseline, row.names = FALSE)), "", "## 各模型运行观察", "")
for (run in names(summaries)) {
  s <- summaries[[run]]
  notes <- c(notes, paste0("- ", run, ": ", s$status))
  if (!is.null(s$identity)) notes <- c(notes, paste0("  - final refit N=", s$identity$full_refit_N,
    "; shared Train/Test IDs match=", s$identity$train_ids_equal_reference, "/", s$identity$test_ids_equal_reference,
    "; labels/raw numeric match=", s$identity$full_refit_labels_match_csv, "/", s$identity$full_refit_numeric_source_values_match_csv),
    paste0("  - selected=", if (is.null(s$selected_specification)) "reference only" else s$selected_specification,
      "; forbidden predictors=", paste(s$forbidden_selected_source_features, collapse = ",")),
    paste0("  - design: ", s$design_representation))
}
notes <- c(notes, "", "## 收敛与LDA数值解释", "",
  "Logistic完整candidate convergence/value/最终convergence保存在runtime_contract_logistic_convergence.json及candidate CSV。返回码非0的分数可计算，但不能据渲染成功宣称充分优化。",
  "已保存实际安装nnet::multinom与nnet.default实现；multinom多分类调用使用size=0、skip=TRUE、rang=0，初始weights为零。因此不能凭nnet通常随机初始化而编造本multinom拟合具有未设seed的随机start。",
  "LDA final pooled within-class covariance、class means及scaling分别导出；诊断JSON含empirical/equal prior、candidate/final N、rank、eigenvalues、dropped列及有限性检查。共享covariance可逆和rank充分并不证明Gaussian或类间协方差相等。",
  "SVM class weights按精确candidate/final labels独立计算N/(8*n_k)，与原class_weights()纯函数输出比较（none应返回NULL）；没有调用fit_svm。native model parameters JSON及support-vector index→original CSV映射只读取已保存final model；未存储的native class weights或probability flags保留null，不虚构。",
  "全局R options不存于runtime environment；本次保存vanilla verifier的contrasts及Logistic fitted model中的实际contrasts，不冒称已恢复原render的全部global options。",
  "后续kNN/SVM保存环境后重跑本脚本即可补全，不会重新执行任何Rmd。", "")
writeLines(notes, prefix("notes.md"), useBytes = TRUE)
cat("Recipe parameter comparisons:", nrow(recipes), "failures:", report$recipe_failures,
    "max abs diff:", report$max_absolute_recipe_difference, "\n")
print(training, row.names = FALSE)
print(baseline, row.names = FALSE)
if (nrow(recipes)) stopifnot(all(recipes$Pass))
if (nrow(baseline)) stopifnot(all(baseline$Prediction_Exact_Match))
if (nrow(svm_weights)) stopifnot(all(svm_weights$Pass))
