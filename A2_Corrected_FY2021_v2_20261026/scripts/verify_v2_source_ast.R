# Parse-only helper. Reads JSON on stdin; evaluates no model or dataset code.
input <- jsonlite::fromJSON(paste(readLines(file("stdin"),warn=FALSE),collapse="\n"),simplifyVector=FALSE)
collect <- function(expressions, predicate) {
  found <- list()
  walk <- function(x) {
    if (missing(x)) return(invisible(NULL))
    if (predicate(x)) found[[length(found)+1L]] <<- x
    if (is.call(x) || is.expression(x) || is.pairlist(x)) for (child in as.list(x)) walk(child)
  }
  walk(expressions); found
}
is_function <- function(x) is.call(x) && identical(x[[1]],as.name("function"))
protected <- c("SEED","TRAIN_FRACTION","DEV_CAP","TARGET_LEVELS","TARGET_LABELS","REQUIRED_COLUMNS",
               "NUMERIC_KEYS","CATEGORY_KEYS","CATEGORY_SOURCES","SPECIFICATIONS","K_GRID","WEIGHTINGS",
               "DUMMY_SCALE","KNN_ALGORITHM","GRID","grid","FEATURES","NUMERIC_FEATURES")
is_protected <- function(x) is.call(x) && identical(x[[1]],as.name("<-")) && is.symbol(x[[2]]) && as.character(x[[2]]) %in% protected
results <- lapply(input$files,function(record) {
  original <- parse(text=record$original_code,keep.source=FALSE)
  corrected <- parse(text=record$corrected_code,keep.source=FALSE)
  normalized_original <- parse(text=record$normalized_original_code,keep.source=FALSE)
  normalized_corrected <- parse(text=record$normalized_corrected_code,keep.source=FALSE)
  functions_same <- identical(collect(original,is_function),collect(corrected,is_function))
  contracts_same <- identical(collect(original,is_protected),collect(corrected,is_protected))
  full_ast_same <- identical(normalized_original,normalized_corrected)
  maxit <- collect(corrected,function(x) is.call(x) && identical(x[[1]],as.name("<-")) && identical(x[[2]],as.name("MAXIT")))
  old_maxit <- collect(original,function(x) is.call(x) && identical(x[[1]],as.name("<-")) && identical(x[[2]],as.name("MAXIT")))
  maxit_ok <- if(record$file=="01_MultinomialLogisticRegression.Rmd") {
    length(maxit)==1L && length(old_maxit)==1L && identical(maxit[[1]][[3]],2000L) && identical(old_maxit[[1]][[3]],250L)
  } else identical(maxit,old_maxit)
  list(file=record$file,R_chunks_parse=TRUE,all_function_ASTs_identical=functions_same,
       protected_assignment_ASTs_identical=contracts_same,
       complete_executable_AST_identical_after_explicit_whitelist=full_ast_same,
       MAXIT_change_only_Logistic_250_to_2000=maxit_ok,
       function_count=length(collect(corrected,is_function)),protected_assignment_count=length(collect(corrected,is_protected)),
       pass=functions_same && contracts_same && full_ast_same && maxit_ok)
})
cat(jsonlite::toJSON(list(status=if(all(vapply(results,function(x)x$pass,logical(1))))"PASS" else "FAIL",
                         scope="Parse-only R native AST comparison; no model or data code evaluated",files=results),
                    pretty=TRUE,auto_unbox=TRUE))
