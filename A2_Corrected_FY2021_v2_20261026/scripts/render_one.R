# Frozen orchestration script: observes a corrected Rmd without altering its model code.
args <- commandArgs(trailingOnly = TRUE)
root <- normalizePath(args[1], winslash = "/", mustWork = TRUE)
tag <- args[2]
filename <- args[3]
old_audit <- "C:/Users/Saberken/Documents/ChatGPT/5003_A1_A2/audit_20261024_01"
.libPaths(c(file.path(old_audit, "r_library"), "C:/Users/Saberken/AppData/Local/R/win-library/4.6", .libPaths()))
Sys.setenv(LC_ALL = "C", RSTUDIO_PANDOC = "C:/Program Files/RStudio/resources/app/bin/quarto/bin/tools")
out <- file.path(root, "results", tag)
if (dir.exists(out)) stop("Refusing to reuse an existing experimental output directory: ", out)
dir.create(out, recursive = TRUE)
source_path <- file.path(root, filename)
copy_path <- file.path(out, filename)
stopifnot(file.copy(source_path, copy_path, overwrite = FALSE))
source_md5 <- unname(tools::md5sum(source_path))
stopifnot(identical(source_md5, unname(tools::md5sum(copy_path))))
data_path <- normalizePath(file.path(root, "WVS_Wave7_cleaned_for_modelling.csv"), winslash = "/")
stopifnot(identical(unname(tools::md5sum(data_path)), "98bf573170f0cb6bd65a4e9a8070d4d8"))
Sys.setenv(STAT5003_DATA_PATH = data_path, STAT5003_OUT_DIR = file.path(out, "model_outputs"),
           STAT5003_LDA_OUT_DIR = file.path(out, "model_outputs"))
setwd(root)
started <- format(Sys.time(), "%Y-%m-%d %H:%M:%S %z")
cat("V2 OFFICIAL RENDER", tag, filename, "\nSTART", started, "\n")
cat("SOURCE MD5", source_md5, "\nDATA", data_path, "\n")
print(sessionInfo()); print(.libPaths()); print(RNGkind()); print(options("contrasts"))
writeLines(capture.output(sessionInfo()), file.path(out, "sessionInfo.txt"))
ip <- installed.packages()
write.csv(ip[, c("Package", "Version", "LibPath", "Built"), drop = FALSE], file.path(out, "package_manifest.csv"), row.names = FALSE)
e <- new.env(parent = globalenv())
start <- proc.time()[["elapsed"]]
render_error <- NULL
notices <- list()
rendered <- tryCatch(withCallingHandlers(
  rmarkdown::render(copy_path, envir = e, knit_root_dir = root,
                    quiet = FALSE, clean = FALSE, output_options = list(keep_md = TRUE)),
  warning = function(w) { notices[[length(notices)+1L]] <<- list(Type="warning", Message=conditionMessage(w)) },
  message = function(m) { notices[[length(notices)+1L]] <<- list(Type="message", Message=conditionMessage(m)) }
), error = function(x) { render_error <<- conditionMessage(x); cat("\nRENDER ERROR:", render_error, "\n"); NULL })
elapsed <- proc.time()[["elapsed"]] - start
unchanged <- identical(source_md5, unname(tools::md5sum(source_path))) && identical(source_md5, unname(tools::md5sum(copy_path)))
status <- list(Run=tag, File=filename, Mode="corrected_v2_official", Success=is.null(render_error), Error=render_error,
  Elapsed_Seconds=elapsed, Started_At=started, Finished_At=format(Sys.time(), "%Y-%m-%d %H:%M:%S %z"),
  Source_MD5=source_md5, Source_Unchanged_During_Render=unchanged, Output=rendered,
  Data_Path=data_path, Data_MD5=unname(tools::md5sum(data_path)), RNG=RNGkind(), Conditions=notices)
jsonlite::write_json(status, file.path(out, "execution_status.json"), pretty=TRUE, auto_unbox=TRUE, null="null", digits=16)
saveRDS(e, file.path(out, "runtime_environment.rds"), compress=FALSE)
getv <- function(nm) if (exists(nm, e, inherits=FALSE)) get(nm, e, inherits=FALSE) else NULL
for (nm in c("train_id","test_id","dev_id","val_id","fit_id","initial_original_id","validation_original_id")) {
  value <- getv(nm)
  if (!is.null(value)) write.csv(data.frame(Row_ID=value), file.path(out,paste0("audit_",nm,".csv")),row.names=FALSE)
}
for (nm in c("ranking","selected","best","winner","validation_results","grid","GRID")) {
  value <- getv(nm)
  if (is.data.frame(value)) write.csv(value,file.path(out,paste0("audit_",nm,".csv")),row.names=FALSE)
}
test_id <- getv("test_id")
truth <- if (!is.null(getv("test"))) getv("test")$Outcome else NULL
if (is.null(truth) && !is.null(getv("wvs")) && !is.null(test_id)) truth <- getv("wvs")$Outcome[test_id]
for (nm in c("predicted","test_prediction","final_prediction","pred_majority","pred_chance")) {
  pr <- getv(nm)
  if (is.list(pr) && !is.null(pr$class)) pr <- pr$class
  if (!is.null(pr) && is.atomic(pr) && length(pr)==length(test_id) && length(truth)==length(test_id)) {
    write.csv(data.frame(row_id=test_id,truth=as.character(truth),prediction=as.character(pr)),
      file.path(out,paste0("independent_export_",nm,".csv")),row.names=FALSE)
  }
}
overall <- list()
for (nm in c("met","test_eval","test_evaluation","final_metrics","majority_eval","chance_eval","majority_met")) {
  value <- getv(nm)
  if (is.list(value) && is.data.frame(value$overall)) {
    overall[[nm]] <- cbind(Object=nm,value$overall)
    pc <- value$by_class; if (is.null(pc)) pc <- value$per_class
    if (is.data.frame(pc)) write.csv(pc,file.path(out,paste0("audit_original_per_class_",nm,".csv")),row.names=FALSE)
    if (!is.null(value$confusion)) write.csv(as.data.frame(value$confusion),file.path(out,paste0("audit_original_confusion_",nm,".csv")),row.names=FALSE)
  }
}
if (length(overall)) write.csv(do.call(rbind,overall),file.path(out,"audit_original_overall.csv"),row.names=FALSE)
final_fit <- getv("final_fit")
if (!is.null(final_fit$convergence)) writeLines(as.character(final_fit$convergence),file.path(out,"audit_final_convergence.txt"))
map <- getv("country_map"); if (is.null(map)) map <- getv("country_group")
if (!is.null(map)) write.csv(data.frame(Country=names(map),Income_Group=unname(map)),file.path(out,"audit_actual_income_map.csv"),row.names=FALSE)
recipe <- getv("recipe_final"); if (is.null(recipe)) recipe <- getv("final_recipe")
if (is.null(recipe) && is.list(final_fit)) recipe <- final_fit$recipe
if (!is.null(recipe)) jsonlite::write_json(recipe,file.path(out,"audit_final_recipe.json"),pretty=TRUE,auto_unbox=TRUE,null="null",digits=16)
resolved_path <- getv("csv_path"); if (is.null(resolved_path)) resolved_path <- getv("DATA_PATH")
if (is.null(resolved_path)) resolved_path <- getv("data_path")
if (is.null(resolved_path) && is.function(getv("resolve_dataset"))) resolved_path <- getv("resolve_dataset")()
if (is.null(resolved_path)) resolved_path <- data_path
resolved_path <- normalizePath(resolved_path,winslash="/",mustWork=TRUE)
stopifnot(identical(resolved_path,data_path))
summary <- list(Run=tag,Seed=getv("SEED"),Seed_Type=typeof(getv("SEED")),Labels=getv("TARGET_LABELS"),
  Columns=getv("REQUIRED_COLUMNS"),N=if(!is.null(getv("wvs")))nrow(getv("wvs"))else NULL,
  Data_Path=resolved_path,Data_MD5=unname(tools::md5sum(resolved_path)),Final_Convergence=final_fit$convergence,
  MAXIT=getv("MAXIT"),Main_Source_MD5=source_md5,Source_Unchanged=unchanged,Contrasts=getOption("contrasts"))
jsonlite::write_json(summary,file.path(out,"audit_runtime_summary.json"),pretty=TRUE,auto_unbox=TRUE,null="null",digits=16)
cat("FINISHED",tag,"SECONDS",elapsed,"RENDER_SUCCESS",is.null(render_error),"SOURCE_UNCHANGED",unchanged,"\n")
if (!is.null(render_error) || !unchanged) quit(status=1L)
