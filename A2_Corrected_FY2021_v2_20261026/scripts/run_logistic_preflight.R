# Builds a diagnostic Rmd from the corrected 01 code and renders it without
# Test transformation, prediction or scoring. No source changes during render.
args <- commandArgs(trailingOnly = TRUE)
root <- normalizePath(args[1], winslash = "/", mustWork = TRUE)
old_root <- "C:/Users/Saberken/Documents/ChatGPT/5003_A1_A2/audit_20261024_01"
.libPaths(c(file.path(old_root, "r_library"), "C:/Users/Saberken/AppData/Local/R/win-library/4.6", .libPaths()))
Sys.setenv(RSTUDIO_PANDOC = "C:/Program Files/RStudio/resources/app/bin/quarto/bin/tools", LC_ALL = "C")
stopifnot(requireNamespace("rmarkdown", quietly = TRUE), requireNamespace("nnet", quietly = TRUE),
          requireNamespace("jsonlite", quietly = TRUE), requireNamespace("digest", quietly = TRUE))
source_path <- file.path(root, "01_MultinomialLogisticRegression.Rmd")
source_lines <- readLines(source_path, encoding = "UTF-8", warn = FALSE)
source_sha <- digest::digest(file = source_path, algo = "sha256")
source_md5 <- unname(tools::md5sum(source_path))
maxit_line <- grep("^MAXIT <- [0-9]+L$", source_lines, value = TRUE)
stopifnot(length(maxit_line) == 1L)
maxit <- as.integer(sub("^MAXIT <- ([0-9]+)L$", "\\1", maxit_line))
diagnostic_path <- file.path(root, "diagnostics", "Logistic_Preflight.Rmd")
run_dir <- file.path(root, "diagnostics", paste0("logistic_preflight_maxit", maxit))
if (dir.exists(run_dir)) stop("Preserve prior preflight outputs; this MAXIT run directory already exists: ", run_dir)
dir.create(run_dir, recursive = TRUE)
chunk <- function(label) {
  hit <- grep(paste0("^```\\{r ", label, "[,}]"), source_lines)
  stopifnot(length(hit) == 1L)
  tail_lines <- source_lines[seq.int(hit + 1L, length(source_lines))]
  closing <- match("```", tail_lines)
  stopifnot(!is.na(closing))
  tail_lines[seq_len(closing - 1L)]
}
labels <- c("setup", "country-map", "preprocessing", "evaluation", "validation")
chunks <- lapply(labels, chunk); names(chunks) <- labels
original_final <- chunk("final-fit")
prediction_line <- grep("^predicted <- predict\\(", original_final)
stopifnot(length(prediction_line) == 1L)
final_training <- original_final[seq_len(prediction_line - 1L)]
# Test preprocessing is unnecessary for convergence and is intentionally absent.
final_training <- final_training[!grepl("^X_test <-", final_training)]
execution_code <- c(unlist(chunks, use.names = FALSE), final_training)
forbidden_pattern <- "newdata\\s*=\\s*(X_test|test\\b)|evaluate_8class\\s*\\(\\s*(X_test|test)\\$|^predicted\\s*<-"
stopifnot(!any(grepl(forbidden_pattern, execution_code, perl = TRUE)))
rmd <- c("---", "title: 'Logistic convergence preflight: Train and Validation only'",
  "output:", "  html_document:", "    toc: true", "---", "",
  paste0("Corrected 01 source SHA-256: `", source_sha, "`."), "",
  "This diagnostic preserves the original six candidates, validation ranking and full-80% refit. It omits Test preprocessing, predictions and scores. MAXIT is assessed for convergence only; no Test metric is available to this diagnostic.", "",
  "```{r preflight-options, include=FALSE}",
  "knitr::opts_chunk$set(error=FALSE, cache=FALSE, warning=TRUE)", "```", "")
for (label in labels) rmd <- c(rmd, paste0("## Original corrected chunk: ", label), "",
  paste0("```{r ", label, "}"), chunks[[label]], "```", "")
rmd <- c(rmd, "## Final full-80% refit without Test prediction", "",
  "```{r preflight-final-training}", "preflight_final_start <- proc.time()[['elapsed']]",
  final_training, "preflight_final_elapsed <- proc.time()[['elapsed']] - preflight_final_start",
  "stopifnot(all(ranking$Convergence==0L), identical(as.integer(final_fit$convergence),0L),",
  "          nrow(X_train)==76786L, !exists('X_test',inherits=FALSE),",
  "          !exists('predicted',inherits=FALSE), !exists('majority_met',inherits=FALSE),",
  "          !exists('comparison',inherits=FALSE))",
  "cat('Candidate convergence codes:',ranking$Convergence,'\\n')",
  "cat('Final convergence:',final_fit$convergence,'objective:',format(final_fit$value,digits=16),'\\n')",
  "cat('Final full-80% block seconds:',preflight_final_elapsed,'\\n')", "```", "",
  "No Test prediction or Test performance is produced by this preflight.", "")
writeLines(rmd, diagnostic_path, useBytes = TRUE)
writeLines(execution_code, file.path(run_dir, "training_validation_execution_code.R"), useBytes = TRUE)
writeLines(capture.output(sessionInfo(), .libPaths(), RNGkind(), options("contrasts")), file.path(run_dir, "session_before.txt"))
assign(".LOGISTIC_PREFLIGHT_PREDICTION_LOG", list(), envir = .GlobalEnv)
# Observe the original predict method and reject every non-validation newdata
# size, including all 19,201 Test rows, without changing model parameters.
trace("predict.multinom", where = asNamespace("nnet"), print = FALSE, tracer = quote({
  if (missing(newdata) || !identical(as.integer(nrow(newdata)), 19199L))
    stop("Preflight allows Validation prediction only; no Test/final prediction permitted.")
  .log <- get(".LOGISTIC_PREFLIGHT_PREDICTION_LOG", envir = .GlobalEnv)
  .log[[length(.log) + 1L]] <- list(newdata_rows = nrow(newdata), requested_type = as.character(type))
  assign(".LOGISTIC_PREFLIGHT_PREDICTION_LOG", .log, envir = .GlobalEnv)
}))
e <- new.env(parent = globalenv())
conditions <- list(); error <- NULL; rendered <- NULL
started <- proc.time()[["elapsed"]]
tryCatch({
  rendered <- withCallingHandlers(rmarkdown::render(diagnostic_path, envir = e,
    knit_root_dir = root, output_dir = run_dir, intermediates_dir = run_dir,
    quiet = FALSE, clean = FALSE, output_options = list(keep_md = TRUE)),
    warning = function(w) conditions[[length(conditions) + 1L]] <<- conditionMessage(w))
}, error = function(err) error <<- conditionMessage(err), finally =
  untrace("predict.multinom", where = asNamespace("nnet")))
elapsed <- proc.time()[["elapsed"]] - started
getv <- function(name, fallback = NULL) if (exists(name, e, inherits = FALSE)) get(name, e, inherits = FALSE) else fallback
ranking <- getv("ranking")
if (!is.null(ranking)) write.csv(ranking, file.path(run_dir, "candidate_convergence_and_validation.csv"), row.names = FALSE)
partial <- getv("result_rows")
if (is.null(ranking) && !is.null(partial)) {
  partial <- Filter(is.data.frame, partial)
  if (length(partial)) write.csv(do.call(rbind, partial), file.path(run_dir, "partial_candidate_rows.csv"), row.names = FALSE)
}
final <- getv("final_fit")
prediction_log <- get(".LOGISTIC_PREFLIGHT_PREDICTION_LOG", envir = .GlobalEnv)
source_after <- digest::digest(file = source_path, algo = "sha256")
no_test <- !exists("X_test", e, inherits = FALSE) && !exists("predicted", e, inherits = FALSE) &&
  !exists("majority_met", e, inherits = FALSE) && !exists("comparison", e, inherits = FALSE) &&
  all(vapply(prediction_log, function(x) identical(as.integer(x$newdata_rows), 19199L), logical(1)))
all_converged <- !is.null(ranking) && nrow(ranking) == 6L && all(ranking$Convergence == 0L) &&
  !is.null(final) && identical(as.integer(final$convergence), 0L)
status <- list(Success = is.null(error) && all_converged && no_test && identical(source_sha, source_after),
  Error = error, MAXIT = maxit, Source = source_path, Source_SHA256_Before = source_sha,
  Source_SHA256_After = source_after, Source_MD5 = source_md5,
  Diagnostic_Source_SHA256 = digest::digest(file = diagnostic_path, algo = "sha256"),
  Source_Stayed_Unchanged = identical(source_sha, source_after),
  Candidate_N = if (!is.null(ranking)) nrow(ranking) else NULL,
  Candidate_Fitting_N = if (!is.null(getv("development"))) nrow(getv("development")) else NULL,
  Candidate_Convergence = if (!is.null(ranking)) ranking$Convergence else NULL,
  Selected_Specification = getv("winning_spec"), Selected_Decay = getv("winning_decay"),
  Final_Refit_N = if (!is.null(getv("X_train"))) nrow(getv("X_train")) else NULL,
  Final_Convergence = if (!is.null(final)) final$convergence else NULL,
  Final_Objective = if (!is.null(final)) final$value else NULL,
  Final_Block_Elapsed_Seconds = getv("preflight_final_elapsed"), Total_Elapsed_Seconds = elapsed,
  No_Test_Prediction_Or_Scoring = no_test, Prediction_Method_Trace = prediction_log,
  Expected_Validation_Prediction_Calls = 6L, Observed_Prediction_Calls = length(prediction_log),
  Static_Execution_Code_Has_No_Test_Prediction_Or_Scoring = !any(grepl(forbidden_pattern, execution_code, perl = TRUE)),
  Model_Hyperparameters_Changed = "Only MAXIT 250 -> current limit; family, six-candidate grid, decay, cap, formula, MaxNWts, seeds, recipes and selection order retained",
  Conditions = conditions, HTML = rendered)
jsonlite::write_json(status, file.path(run_dir, "preflight_status.json"), pretty = TRUE, auto_unbox = TRUE, null = "null", digits = 16)
saveRDS(e, file.path(run_dir, "preflight_environment.rds"), compress = FALSE)
writeLines(capture.output(sessionInfo()), file.path(run_dir, "session_after.txt"))
cat(jsonlite::toJSON(status, pretty = TRUE, auto_unbox = TRUE, null = "null", digits = 16), "\n")
if (!isTRUE(status$Success)) quit(status = 1L)
